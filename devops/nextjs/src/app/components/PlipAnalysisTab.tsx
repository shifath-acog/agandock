'use client';

import { useState, useEffect, useCallback } from 'react';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Loader2, FileText, Download, BarChart3, Filter, RefreshCw, Info } from 'lucide-react';
import { AgGridReact } from 'ag-grid-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import type { ColDef, GridApi } from 'ag-grid-community';
import Slider from 'rc-slider';
import 'rc-slider/assets/index.css';
import { Button } from '@/components/ui/button';
import * as Switch from '@radix-ui/react-switch';
import Papa from 'papaparse';

interface ExperimentData {
  outputCsv: string; // Content of output.csv
  outputWithPbCsv: string; // Content of output_with_pb.csv
  plipCsvs: { name: string; displayName: string }[]; // Available PLIP CSVs
  selectedPlipCsv: string; // Content of selected PLIP CSV
  isPlipRun: boolean; // Tracks if PLIP was run
}

interface PlipAnalysisTabProps {
  // Add props if needed
}

export function PlipAnalysisTab({}: PlipAnalysisTabProps) {
  const [experimentFolders, setExperimentFolders] = useState<string[]>([]);
  const [selectedFolder, setSelectedFolder] = useState<string | null>(null);
  const [experimentData, setExperimentData] = useState<Record<string, ExperimentData>>({});
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [gridApi, setGridApi] = useState<GridApi | null>(null);
  const [scoreRange, setScoreRange] = useState<[number, number]>([-10, 0]);
  const [usePbFiltered, setUsePbFiltered] = useState<boolean>(false);
  const [hasPbCsv, setHasPbCsv] = useState<boolean>(true);
  const [plipLoading, setPlipLoading] = useState<boolean>(false);
  const [selectedPlipCsvName, setSelectedPlipCsvName] = useState<string>('');

  // Fetch experiment folders on mount
  useEffect(() => {
    async function fetchExperiments() {
      setLoading(true);
      try {
        const response = await fetch('/api/get-experiments');
        if (!response.ok) throw new Error('Failed to fetch experiment folders');
        const data = await response.json();
        setExperimentFolders(data.folders || []);
      } catch (err) {
        setError('Error fetching experiment folders. Please try again.');
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    fetchExperiments();
  }, []);

  // Fetch experiment data and check for output_with_pb.csv
  useEffect(() => {
    async function fetchExperimentData() {
      if (!selectedFolder || selectedFolder in experimentData) return;
      setLoading(true);
      setError(null);
      setScoreRange([-10, 0]);
      setUsePbFiltered(false);
      setSelectedPlipCsvName('');
      try {
        // Fetch experiment data
        const response = await fetch(`/api/get-experiments?folder=${encodeURIComponent(selectedFolder)}`);
        if (!response.ok) throw new Error(`Failed to load data for ${selectedFolder}`);
        const data = await response.json();

        // Check for output_with_pb.csv
        const pbResponse = await fetch(`/api/check-pb?folder=${encodeURIComponent(selectedFolder)}`);
        const pbData = await pbResponse.json();
        setHasPbCsv(pbData.exists);

        // Check for PLIP results
        const plipResponse = await fetch(`/api/get-plip-results?folder=${encodeURIComponent(selectedFolder)}`);
        let plipCsvs: { name: string; displayName: string }[] = [];
        let isPlipRun = false;
        if (plipResponse.ok) {
          const plipData = await plipResponse.json();
          plipCsvs = plipData.csvFiles || [];
          isPlipRun = plipCsvs.length > 0;
        }

        setExperimentData((prev) => ({
          ...prev,
          [selectedFolder]: {
            outputCsv: data.outputCsv,
            outputWithPbCsv: data.outputWithPbCsv || '',
            plipCsvs,
            selectedPlipCsv: '',
            isPlipRun,
          },
        }));
      } catch (err) {
        setError(`Error loading data for ${selectedFolder}. Please try again.`);
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    fetchExperimentData();
  }, [selectedFolder]);

  // Parse CSV content with papaparse
  const parseCsv = (csvContent: string): { headers: string[]; rowData: Record<string, string>[]; columnDefs: ColDef[] } => {
    const parsed = Papa.parse<Record<string, string>>(csvContent, { header: true, skipEmptyLines: true });
    const headers = parsed.meta.fields || [];
    const rowData = parsed.data;
    const columnDefs: ColDef[] = headers.map((header) => {
      const isNumeric = [
        'num_hydrophobic_interactions',
        'num_hydrogen_bonding_interactions',
        'strong_hydrogen_bonds',
        'moderate_hydrogen_bonds',
        'weak_hydrogen_bonds',
        'num_water_bridges',
        'num_salt_bridges',
        'num_halogen',
        'num_halogen_bonds',
        'num_pi_stacks',
        'num_pi_cation_interactions',
        'num_metal_complexes',
      ].includes(header);
      return {
        headerName: header.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase()),
        field: header,
        sortable: true,
        filter: true,
        resizable: true,
        minWidth: 120,
        flex: 1,
        pinned: header === 'Name' ? 'left' : null,
        cellRenderer: isNumeric
          ? (params: { value: string }) => {
              const value = parseFloat(params.value);
              return isNaN(value) ? params.value : value.toFixed(2);
            }
          : (params: { value: string }) => {
              const value = params.value;
              return typeof value === 'string' && (value.startsWith('[') || value.startsWith('{'))
                ? value.slice(0, 20) + (value.length > 20 ? '...' : '')
                : value;
            },
      };
    });
    return { headers, rowData, columnDefs };
  };

  // Parse docking CSV for histogram and filtering
  const parseDockingCsv = (csvContent: string): { headers: string[]; rowData: Record<string, string>[] } => {
    const parsed = Papa.parse<Record<string, string>>(csvContent, { header: true, skipEmptyLines: true });
    const headers = parsed.meta.fields || ['Name', 'SMILES', 'Docking score (kcal/mol)', 'Ligand efficiency'];
    const rowData = parsed.data;
    return { headers, rowData };
  };

  // Filter data by docking score range
  const filterByScoreRange = (rowData: Record<string, string>[]): Record<string, string>[] => {
    return rowData.filter((row) => {
      const score = parseFloat(row['Docking score (kcal/mol)']);
      return !isNaN(score) && score >= scoreRange[0] && score <= scoreRange[1];
    });
  };

  // Prepare data for histogram
  const getHistogramData = (rowData: Record<string, string>[]): { range: string; count: number }[] => {
    const scores = rowData
      .map((row) => parseFloat(row['Docking score (kcal/mol)']))
      .filter((score) => !isNaN(score));
    const minScore = Math.floor(Math.min(...scores, -10));
    const maxScore = Math.ceil(Math.max(...scores, 0));
    const binSize = 2;
    const bins: { range: string; count: number }[] = [];
    for (let i = minScore; i < maxScore; i += binSize) {
      const rangeStart = i;
      const rangeEnd = i + binSize;
      const count = scores.filter((score) => score >= rangeStart && score < rangeEnd).length;
      bins.push({ range: `${rangeStart} to ${rangeEnd}`, count });
    }
    return bins;
  };

  // Check if histogram should be displayed
  const shouldShowHistogram = (rowData: Record<string, string>[]): boolean => {
    return rowData.length > 1;
  };

  // Get filtered docking data
  const getFilteredDockingData = (): Record<string, string>[] => {
    if (!selectedFolder || !experimentData[selectedFolder]) return [];
    const csvContent = usePbFiltered && hasPbCsv && experimentData[selectedFolder].outputWithPbCsv
      ? experimentData[selectedFolder].outputWithPbCsv
      : experimentData[selectedFolder].outputCsv;
    if (!csvContent) return [];
    const { rowData } = parseDockingCsv(csvContent);
    return filterByScoreRange(rowData);
  };

  // Get score range bounds
  const getScoreBounds = (): [number, number] => {
    if (!selectedFolder || !experimentData[selectedFolder]) return [-10, 0];
    const csvContent = usePbFiltered && hasPbCsv && experimentData[selectedFolder].outputWithPbCsv
      ? experimentData[selectedFolder].outputWithPbCsv
      : experimentData[selectedFolder].outputCsv;
    if (!csvContent) return [-10, 0];
    const { rowData } = parseDockingCsv(csvContent);
    const scores = rowData
      .map((row) => parseFloat(row['Docking score (kcal/mol)']))
      .filter((score) => !isNaN(score));
    return [Math.floor(Math.min(...scores, -10)), Math.ceil(Math.max(...scores, 0))];
  };

  // Run PLIP analysis
  const runPlipAnalysis = async () => {
    if (!selectedFolder) return;
    setPlipLoading(true);
    setError(null);
    try {
      const response = await fetch('/api/run-plip', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          folder_name: selectedFolder,
          lower_range: scoreRange[0],
          higher_range: scoreRange[1],
          use_pb_filtered_ligands: usePbFiltered && hasPbCsv,
        }),
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to run PLIP analysis');
      }
      const { outputPlipDir } = await response.json();

      // Fetch PLIP CSVs
      const plipResponse = await fetch(`/api/get-plip-results?folder=${encodeURIComponent(selectedFolder)}`);
      if (!plipResponse.ok) throw new Error('Failed to fetch PLIP results');
      const plipData = await plipResponse.json();
      const plipCsvs = plipData.csvFiles || [];

      setExperimentData((prev) => ({
        ...prev,
        [selectedFolder]: {
          ...prev[selectedFolder],
          plipCsvs,
          isPlipRun: true,
          selectedPlipCsv: '',
        },
      }));
      setSelectedPlipCsvName(plipCsvs.length > 0 ? plipCsvs[0].name : '');
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Error running PLIP analysis. Please try again.';
      setError(errorMessage);
      console.error('PLIP error:', err);
    } finally {
      setPlipLoading(false);
    }
  };

  // Fetch selected PLIP CSV content
  useEffect(() => {
    async function fetchPlipCsv() {
      if (!selectedFolder || !selectedPlipCsvName || !experimentData[selectedFolder]?.isPlipRun) return;
      try {
        const response = await fetch(`/api/get-plip-results?folder=${encodeURIComponent(selectedFolder)}&csv_file=${encodeURIComponent(selectedPlipCsvName)}`);
        if (!response.ok) throw new Error('Failed to fetch PLIP CSV');
        const { csvContent } = await response.json();
        setExperimentData((prev) => ({
          ...prev,
          [selectedFolder]: {
            ...prev[selectedFolder],
            selectedPlipCsv: csvContent,
          },
        }));
      } catch (err) {
        setError('Error fetching PLIP CSV. Please try again.');
        console.error(err);
      }
    }
    fetchPlipCsv();
  }, [selectedFolder, selectedPlipCsvName]);

  // Export PLIP CSV
  const exportPlipCsv = useCallback(() => {
    if (gridApi && selectedPlipCsvName) {
      gridApi.exportDataAsCsv({
        fileName: `${selectedFolder}_${selectedPlipCsvName.replace('.csv', '')}_results.csv`,
      });
    }
  }, [gridApi, selectedFolder, selectedPlipCsvName]);

  // Reset filters
  const resetFilters = useCallback(() => {
    setScoreRange(getScoreBounds());
    setError(null);
    if (selectedFolder && experimentData[selectedFolder]?.plipCsvs.length > 0) {
      setSelectedPlipCsvName(experimentData[selectedFolder].plipCsvs[0].name);
    } else {
      setSelectedPlipCsvName('');
    }
  }, [selectedFolder, experimentData]);

  return (
    <div className="space-y-6 border border-gray-200 shadow-md hover:shadow-lg transition-shadow duration-200 bg-white rounded-xl px-6 py-4">
      <div className="border-b border-gray-200 pb-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <FileText className="h-5 w-5 text-blue-600" />
            <h3 className="text-xl font-semibold text-gray-800">PLIP Analysis</h3>
          </div>
          {selectedFolder && experimentData[selectedFolder]?.isPlipRun && selectedPlipCsvName && (
            <Button
              onClick={exportPlipCsv}
              className="flex items-center gap-2 bg-gray-800 text-white rounded-lg hover:bg-gray-700 text-sm font-medium shadow-sm"
            >
              <Download className="h-4 w-4" />
              Export PLIP CSV
            </Button>
          )}
        </div>
        <p className="text-sm text-gray-600 mt-2">
          Analyze protein-ligand interactions for docking results
          {selectedFolder && experimentData[selectedFolder]?.isPlipRun
            ? ` (Showing ${selectedPlipCsvName.replace('.csv', '').replace(/_/g, ' ')})`
            : ''}
        </p>
      </div>

      {loading && (
        <div className="flex items-center justify-center py-8">
          <Loader2 className="h-6 w-6 animate-spin text-blue-600" />
          <span className="ml-2 text-gray-600">Loading...</span>
        </div>
      )}

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-xl">
          <p className="text-sm text-red-600">{error}</p>
        </div>
      )}

      {!loading && !error && experimentFolders.length === 0 && (
        <div className="p-6 bg-yellow-50 border border-yellow-200 rounded-xl text-center">
          <p className="text-sm text-yellow-700">No experiments found. Please run the docking process first.</p>
        </div>
      )}

      {experimentFolders.length > 0 && (
        <div className="space-y-6">
          <Select
            value={selectedFolder ?? undefined}
            onValueChange={(value) => {
              setSelectedFolder(value);
              setError(null);
              setScoreRange([-10, 0]);
              setUsePbFiltered(false);
              setSelectedPlipCsvName('');
            }}
          >
            <SelectTrigger className="w-full max-w-md h-12 border-gray-300 rounded-xl shadow-sm focus:ring-2 focus:ring-blue-200 focus:border-blue-500">
              <SelectValue placeholder="Select an experiment" />
            </SelectTrigger>
            <SelectContent>
              {experimentFolders.map((folder) => (
                <SelectItem key={folder} value={folder}>
                  {folder}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          {selectedFolder && experimentData[selectedFolder] && (
            <div className="space-y-6">
              {/* Ligand Selection Toggle */}
              <div className="flex items-center gap-4">
                <span className="text-sm font-medium text-gray-700">Ligand Selection:</span>
                <Switch.Root
                  checked={usePbFiltered}
                  onCheckedChange={(checked) => {
                    setUsePbFiltered(checked);
                    setScoreRange(getScoreBounds());
                    setError(checked && !hasPbCsv ? 'PoseBusters filtration not done. Run it in the Filtration tab.' : null);
                  }}
                  className="w-11 h-6 bg-gray-200 rounded-full relative data-[state=checked]:bg-blue-600"
                  disabled={!hasPbCsv}
                >
                  <Switch.Thumb className="block w-5 h-5 bg-white rounded-full transition-transform translate-x-0.5 data-[state=checked]:translate-x-5.5" />
                </Switch.Root>
                <span className="text-sm text-gray-600">
                  {usePbFiltered ? 'PoseBusters Filtered Ligands' : 'All Ligands'}
                </span>
                {!hasPbCsv && usePbFiltered && (
                  <span className="text-sm text-red-600">PoseBusters filtration not done. Run it in the Filtration tab.</span>
                )}
              </div>

              {/* Data Summary */}
              {experimentData[selectedFolder].outputCsv && (!usePbFiltered || (usePbFiltered && experimentData[selectedFolder].outputWithPbCsv)) && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="bg-white border border-gray-200 rounded-lg p-4 flex flex-col items-center">
                    <div className="text-2xl font-semibold text-black-600">
                      {getFilteredDockingData().length}
                    </div>
                    <div className="text-xs text-gray-500 font-normal mt-1">Total Compounds</div>
                  </div>
                  <div className="bg-white border border-gray-300 rounded-lg p-4 flex flex-col items-center">
                    <div className="text-2xl font-semibold text-black-600">
                      {(() => {
                        const scores = getFilteredDockingData()
                          .map((row) => parseFloat(row['Docking score (kcal/mol)']))
                          .filter((score) => !isNaN(score));
                        return scores.length > 0 ? Math.min(...scores).toFixed(1) : 'N/A';
                      })()}
                    </div>
                    <div className="text-xs text-gray-500 font-normal mt-1">Best Score (kcal/mol)</div>
                  </div>
                  <div className="bg-white border border-gray-200 rounded-lg p-4 flex flex-col items-center">
                    <div className="text-2xl font-semibold text-black-600">
                      {(() => {
                        const scores = getFilteredDockingData()
                          .map((row) => parseFloat(row['Docking score (kcal/mol)']))
                          .filter((score) => !isNaN(score));
                        return scores.length > 0 ? (scores.reduce((a, b) => a + b, 0) / scores.length).toFixed(1) : 'N/A';
                      })()}
                    </div>
                    <div className="text-xs text-gray-500 font-normal mt-1">Average Score (kcal/mol)</div>
                  </div>
                </div>
              )}

              {/* Score Range Filter */}
              {experimentData[selectedFolder].outputCsv && (!usePbFiltered || (usePbFiltered && experimentData[selectedFolder].outputWithPbCsv)) && (
                <div className="border border-gray-200 rounded-xl p-6 shadow-lg bg-gradient-to-br from-white to-gray-50">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2">
                      <Filter className="h-5 w-5 text-blue-600" />
                      <h4 className="text-lg font-semibold text-gray-800">Filter by Docking Score</h4>
                    </div>
                    <Button
                      onClick={resetFilters}
                      className="flex items-center gap-2 bg-gray-500 hover:bg-gray-600 text-white text-sm"
                    >
                      <RefreshCw className="h-4 w-4" />
                      Reset
                    </Button>
                  </div>
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">
                        Range: {scoreRange[0].toFixed(1)} to {scoreRange[1].toFixed(1)} kcal/mol
                      </span>
                      <Button
                        onClick={() => setScoreRange(getScoreBounds())}
                        className="bg-blue-600 hover:bg-blue-700 text-white text-sm"
                      >
                        Apply Filter
                      </Button>
                    </div>
                    <Slider
                      range
                      min={getScoreBounds()[0]}
                      max={getScoreBounds()[1]}
                      value={scoreRange}
                      onChange={(value) => setScoreRange(value as [number, number])}
                      allowCross={false}
                      step={0.1}
                      className="rc-slider"
                    />
                  </div>
                </div>
              )}

              {/* Run PLIP Button */}
              <div className="flex justify-end">
                <Button
                  onClick={runPlipAnalysis}
                  disabled={plipLoading || !selectedFolder || (usePbFiltered && !hasPbCsv) || !experimentData[selectedFolder]?.outputCsv}
                  className="flex items-center gap-2 bg-green-600 hover:bg-green-700 text-white text-sm disabled:bg-gray-400"
                >
                  {plipLoading ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Filter className="h-4 w-4" />
                  )}
                  Analyze Ligand-Protein Interactions
                </Button>
              </div>

              {/* PLIP Results */}
              {experimentData[selectedFolder]?.isPlipRun && (
                <div className="space-y-6">
                  <Select
                    value={selectedPlipCsvName}
                    onValueChange={(value) => setSelectedPlipCsvName(value)}
                  >
                    <SelectTrigger className="w-full max-w-md h-12 border-gray-300 rounded-xl shadow-sm focus:ring-2 focus:ring-blue-200 focus:border-blue-500">
                      <SelectValue placeholder="Select interaction type" />
                    </SelectTrigger>
                    <SelectContent>
                      {experimentData[selectedFolder].plipCsvs.map((csv) => (
                        <SelectItem key={csv.name} value={csv.name}>
                          {csv.displayName}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>

                  {selectedPlipCsvName && experimentData[selectedFolder].selectedPlipCsv ? (
                    (() => {
                      const { rowData, columnDefs } = parseCsv(experimentData[selectedFolder].selectedPlipCsv);
                      return rowData.length === 0 ? (
                        <div className="p-6 bg-green-50 border border-green-200 rounded-xl text-center">
                          <div className="flex items-center justify-center gap-2">
                            <Info className="h-5 w-5 text-green-600" />
                            <p className="text-sm text-green-700">No interactions of this type found.</p>
                          </div>
                        </div>
                      ) : (
                        <div className="border border-gray-200 rounded-xl shadow-lg overflow-hidden">
                          <div className="ag-theme-alpine-custom">
                            <AgGridReact
                              columnDefs={columnDefs}
                              rowData={rowData}
                              defaultColDef={{
                                flex: 1,
                                minWidth: 120,
                                filter: true,
                                sortable: true,
                                resizable: true,
                                cellClass: 'custom-cell',
                              }}
                              pagination
                              paginationPageSize={20}
                              rowBuffer={15}
                              domLayout="autoHeight"
                              headerHeight={48}
                              rowHeight={42}
                              animateRows
                              suppressMovableColumns={false}
                              onGridReady={(params) => {
                                setGridApi(params.api);
                                params.api.sizeColumnsToFit();
                              }}
                              onFirstDataRendered={(params) => {
                                params.api.sizeColumnsToFit();
                              }}
                            />
                          </div>
                        </div>
                      );
                    })()
                  ) : (
                    <div className="p-6 bg-yellow-50 border border-yellow-200 rounded-xl text-center">
                      <p className="text-sm text-yellow-700">Select an interaction type to view results.</p>
                    </div>
                  )}
                </div>
              )}

              {/* Histogram */}
              {experimentData[selectedFolder]?.outputCsv && (!usePbFiltered || (usePbFiltered && experimentData[selectedFolder].outputWithPbCsv)) && shouldShowHistogram(getFilteredDockingData()) && (
                <div className="border border-gray-200 rounded-xl p-6 shadow-lg bg-gradient-to-br from-white to-gray-50">
                  <div className="flex items-center gap-2 mb-4">
                    <BarChart3 className="h-5 w-5 text-blue-600" />
                    <h4 className="text-lg font-semibold text-gray-800">
                      Distribution of Docking Scores ({usePbFiltered && hasPbCsv ? 'PoseBusters Filtered' : 'All Ligands'})
                    </h4>
                  </div>
                  <ResponsiveContainer width="100%" height={350}>
                    <BarChart
                      data={getHistogramData(getFilteredDockingData())}
                      margin={{ top: 20, right: 30, left: 20, bottom: 60 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" opacity={0.7} />
                      <XAxis
                        dataKey="range"
                        label={{
                          value: 'Docking Score (kcal/mol)',
                          position: 'insideBottom',
                          offset: -10,
                          fill: '#1f2937',
                          fontSize: 14,
                          fontWeight: 600,
                        }}
                        tick={{ fontSize: 12, fill: '#6b7280' }}
                        angle={-45}
                        textAnchor="end"
                        height={80}
                      />
                      <YAxis
                        label={{
                          value: 'Count',
                          angle: -90,
                          position: 'insideLeft',
                          fill: '#1f2937',
                          fontSize: 14,
                          fontWeight: 600,
                        }}
                        tick={{ fontSize: 12, fill: '#6b7280' }}
                      />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: '#ffffff',
                          border: '1px solid #e5e7eb',
                          borderRadius: '0.75rem',
                          boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
                          fontSize: '14px',
                        }}
                        labelStyle={{ color: '#1f2937', fontWeight: 600 }}
                      />
                      <Bar
                        dataKey="count"
                        fill="url(#colorGradient)"
                        radius={[6, 6, 0, 0]}
                        stroke="#2563eb"
                        strokeWidth={1}
                      />
                      <defs>
                        <linearGradient id="colorGradient" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor="#3b82f6" stopOpacity={0.9} />
                          <stop offset="100%" stopColor="#60a5fa" stopOpacity={0.7} />
                        </linearGradient>
                      </defs>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}