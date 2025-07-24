'use client';

import { useState, useEffect } from 'react';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Loader2, FileText, Download, BarChart3, Filter, RefreshCw, Info } from 'lucide-react';
import { AgGridReact } from 'ag-grid-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import type { ColDef, GridApi } from 'ag-grid-community';
import Slider from 'rc-slider';
import 'rc-slider/assets/index.css';
import { Button } from '@/components/ui/button';
import * as Tabs from '@radix-ui/react-tabs';

interface ExperimentData {
  outputCsv: string; // Content of output.csv (pre-PoseBusters)
  outputWithPbCsv: string; // Content of output_with_pb.csv (PoseBusters passed)
  outputWithoutPbCsv: string; // Content of output_without_pb.csv (PoseBusters failed)
  isPoseBustersFiltered: boolean; // Tracks if PoseBusters was applied
}

interface FiltrationTabProps {
  // Add props if needed
}

export function FiltrationTab({}: FiltrationTabProps) {
  const [experimentFolders, setExperimentFolders] = useState<string[]>([]);
  const [selectedFolder, setSelectedFolder] = useState<string | null>(null);
  const [experimentData, setExperimentData] = useState<Record<string, ExperimentData>>({});
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [gridApi, setGridApi] = useState<GridApi | null>(null);
  const [scoreRange, setScoreRange] = useState<[number, number]>([-10, 0]);
  const [filteredData, setFilteredData] = useState<Record<string, string>[] | null>(null);
  const [poseBustersLoading, setPoseBustersLoading] = useState<boolean>(false);
  const [hasPdbFile, setHasPdbFile] = useState<boolean>(true);
  const [activeTab, setActiveTab] = useState<'passed' | 'failed'>('passed');

  // Fetch experiment folders on mount
  useEffect(() => {
    async function fetchExperiments() {
      setLoading(true);
      try {
        const response = await fetch('/api/get-experiments');
        if (!response.ok) {
          throw new Error('Failed to fetch experiment folders');
        }
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

  // Fetch data and check PDB file for selected folder
  useEffect(() => {
    async function fetchExperimentData() {
      if (!selectedFolder || selectedFolder in experimentData) return;
      setLoading(true);
      setError(null);
      setFilteredData(null);
      try {
        // Fetch experiment data
        const response = await fetch(`/api/get-experiments?folder=${encodeURIComponent(selectedFolder)}`);
        if (!response.ok) {
          throw new Error(`Failed to load data for ${selectedFolder}`);
        }
        const data = await response.json();
        setExperimentData((prev) => ({
          ...prev,
          [selectedFolder]: {
            outputCsv: data.outputCsv,
            outputWithPbCsv: '',
            outputWithoutPbCsv: '',
            isPoseBustersFiltered: false,
          },
        }));

        // Check for PDB file
        const pdbResponse = await fetch(`/api/check-pdb?folder=${encodeURIComponent(selectedFolder)}`);
        if (!pdbResponse.ok) {
          setHasPdbFile(false);
          setError('No PDB file found in experiment folder. PoseBusters filtering is disabled.');
        } else {
          setHasPdbFile(true);
        }
      } catch (err) {
        setError(`Error loading data for ${selectedFolder}. Please try again.`);
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    fetchExperimentData();
  }, [selectedFolder, experimentData]);

  // Parse CSV content
  const parseCsv = (csvContent: string) => {
    const rows = csvContent.trim().split('\n').map((row) => row.split(','));
    const headers = rows[0] || ['Name', 'SMILES', 'Docking score (kcal/mol)', 'Ligand efficiency'];
    const rowData: Record<string, string>[] = rows.slice(1).map((row) =>
      headers.reduce<Record<string, string>>((obj, header, i) => {
        obj[header] = row[i] || '';
        return obj;
      }, {})
    );
    return { headers, rowData };
  };

  // Filter data by docking score range
  const filterByScoreRange = (rowData: Record<string, string>[]) => {
    return rowData.filter((row) => {
      const score = parseFloat(row['Docking score (kcal/mol)']);
      return !isNaN(score) && score >= scoreRange[0] && score <= scoreRange[1];
    });
  };

  // Prepare data for histogram
  const getHistogramData = (rowData: Record<string, string>[]) => {
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
  const shouldShowHistogram = (rowData: Record<string, string>[]) => {
    return rowData.length > 1;
  };

  // Custom cell renderer for numeric values
  const numericCellRenderer = (params: any) => {
    const value = parseFloat(params.value);
    if (isNaN(value)) return params.value;
    return value.toFixed(2);
  };

  // Custom cell renderer for docking scores with color coding
  const dockingScoreCellRenderer = (params: any) => {
    const value = parseFloat(params.value);
    if (isNaN(value)) return params.value;
    let colorClass = '';
    if (value <= -10) colorClass = 'text-green-700 bg-green-50 font-semibold';
    else if (value <= -8) colorClass = 'text-green-600 bg-green-25 font-medium';
    else if (value <= -6) colorClass = 'text-yellow-700 bg-yellow-50 font-medium';
    else if (value <= -4) colorClass = 'text-orange-700 bg-orange-50';
    else colorClass = 'text-red-700 bg-red-50';
    return (
      <span className={`px-2 py-1 rounded-md text-sm ${colorClass}`}>
        {value.toFixed(2)}
      </span>
    );
  };

  // Column definitions
  const columnDefs = (headers: string[]): ColDef[] =>
    headers.map((header) => {
      const baseConfig: ColDef = {
        headerName: header,
        field: header,
        sortable: true,
        filter: true,
        resizable: true,
        minWidth: 120,
        headerClass: 'custom-header',
        cellClass: 'custom-cell',
      };
      if (header === 'Docking score (kcal/mol)') {
        return {
          ...baseConfig,
          cellRenderer: dockingScoreCellRenderer,
          sort: 'asc',
          minWidth: 180,
          comparator: (valueA: string, valueB: string) => parseFloat(valueA) - parseFloat(valueB),
        };
      } else if (header === 'Ligand efficiency') {
        return { ...baseConfig, cellRenderer: numericCellRenderer, minWidth: 150, flex: 1 };
      } else if (header === 'SMILES') {
        return { ...baseConfig, minWidth: 200, flex: 7, cellClass: 'font-mono text-xs custom-cell' };
      } else if (header === 'Name') {
        return { ...baseConfig, minWidth: 80, cellClass: 'font-medium custom-cell', pinned: 'left' };
      }
      return baseConfig;
    });

  // Export filtered data
  const exportData = () => {
    if (gridApi) {
      const suffix = activeTab === 'passed' ? 'posebusters_passed' : 'posebusters_failed';
      gridApi.exportDataAsCsv({
        fileName: `${selectedFolder}_${suffix}_results.csv`,
      });
    }
  };

  // Reset filters
  const resetFilters = () => {
    setFilteredData(null);
    setScoreRange(getScoreBounds() as [number, number]);
    setError(null);
    setActiveTab('passed');
    if (selectedFolder && experimentData[selectedFolder]) {
      setExperimentData((prev) => ({
        ...prev,
        [selectedFolder]: {
          ...prev[selectedFolder],
          isPoseBustersFiltered: false,
        },
      }));
    }
  };

  // Run PoseBusters filter
  const runPoseBusters = async () => {
    if (!selectedFolder || !hasPdbFile) return;
    setPoseBustersLoading(true);
    setError(null);
    try {
      const response = await fetch('/api/run-filter', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          folder_name: selectedFolder,
          lower_range: scoreRange[0],
          higher_range: scoreRange[1],
        }),
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to run PoseBusters filter');
      }
      const data = await response.json();
      setExperimentData((prev) => ({
        ...prev,
        [selectedFolder]: {
          ...prev[selectedFolder],
          outputWithPbCsv: data.outputWithPbCsv,
          outputWithoutPbCsv: data.outputWithoutPbCsv,
          isPoseBustersFiltered: true,
        },
      }));
      setFilteredData(null); // Reset client-side filter
      setActiveTab('passed'); // Default to passed tab after filtering
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Error running PoseBusters filter. Please try again.';
      setError(errorMessage);
      console.error('PoseBusters error:', err);
    } finally {
      setPoseBustersLoading(false);
    }
  };

  // Get filtered row data based on active tab
  const getFilteredRowData = () => {
    if (!selectedFolder || !experimentData[selectedFolder]) return [];
    const csvContent = experimentData[selectedFolder].isPoseBustersFiltered
      ? activeTab === 'passed'
        ? experimentData[selectedFolder].outputWithPbCsv
        : experimentData[selectedFolder].outputWithoutPbCsv
      : experimentData[selectedFolder].outputCsv;
    const { rowData } = parseCsv(csvContent);
    return filteredData || filterByScoreRange(rowData);
  };

  // Get score range bounds based on active tab
  const getScoreBounds = () => {
    if (!selectedFolder || !experimentData[selectedFolder]) return [-10, 0];
    const csvContent = experimentData[selectedFolder].isPoseBustersFiltered
      ? activeTab === 'passed'
        ? experimentData[selectedFolder].outputWithPbCsv
        : experimentData[selectedFolder].outputWithoutPbCsv
      : experimentData[selectedFolder].outputCsv;
    const { rowData } = parseCsv(csvContent);
    const scores = rowData
      .map((row) => parseFloat(row['Docking score (kcal/mol)']))
      .filter((score) => !isNaN(score));
    return [Math.floor(Math.min(...scores, -10)), Math.ceil(Math.max(...scores, 0))];
  };

  // Check if output_without_pb.csv is empty
  const isOutputWithoutPbEmpty = () => {
    if (!selectedFolder || !experimentData[selectedFolder] || !experimentData[selectedFolder].isPoseBustersFiltered) {
      return false;
    }
    const { rowData } = parseCsv(experimentData[selectedFolder].outputWithoutPbCsv);
    return rowData.length === 0;
  };

  return (
    <div className="space-y-6 border border-gray-200 shadow-md hover:shadow-lg transition-shadow duration-200 bg-white rounded-xl px-6 py-4">
      <div className="border-b border-gray-200 pb-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <FileText className="h-5 w-5 text-blue-600" />
            <h3 className="text-xl font-semibold text-gray-800">Filtration</h3>
          </div>
          {selectedFolder && experimentData[selectedFolder] && (
            <Button
              onClick={exportData}
              className="flex items-center gap-2 bg-gray-800 text-white rounded-lg hover:bg-gray-700 text-sm font-medium shadow-sm"
            >
              <Download className="h-4 w-4" />
              Export {activeTab === 'passed' ? 'Passed' : 'Failed'} CSV
            </Button>
          )}
        </div>
        <p className="text-sm text-gray-600 mt-2">
          Filter docking results by score range or apply PoseBusters
          {selectedFolder && experimentData[selectedFolder]?.isPoseBustersFiltered
            ? ` (Showing ${activeTab === 'passed' ? 'passed' : 'failed'} PoseBusters results)`
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
            value={selectedFolder || undefined}
            onValueChange={(value) => {
              setSelectedFolder(value);
              setError(null);
              setFilteredData(null);
              setScoreRange([-10, 0]);
              setActiveTab('passed');
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
              {/* Data Summary */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-white border border-gray-200 rounded-lg p-4 flex flex-col items-center">
                  <div className="text-2xl font-semibold text-blue-600">
                    {getFilteredRowData().length}
                  </div>
                  <div className="text-xs text-gray-500 font-normal mt-1">Total Compounds</div>
                </div>
                <div className="bg-white border border-gray-200 rounded-lg p-4 flex flex-col items-center">
                  <div className="text-2xl font-semibold text-green-600">
                    {(() => {
                      const scores = getFilteredRowData()
                        .map((row) => parseFloat(row['Docking score (kcal/mol)']))
                        .filter((score) => !isNaN(score));
                      return scores.length > 0 ? Math.min(...scores).toFixed(1) : 'N/A';
                    })()}
                  </div>
                  <div className="text-xs text-gray-500 font-normal mt-1">Best Score (kcal/mol)</div>
                </div>
                <div className="bg-white border border-gray-200 rounded-lg p-4 flex flex-col items-center">
                  <div className="text-2xl font-semibold text-purple-600">
                    {(() => {
                      const scores = getFilteredRowData()
                        .map((row) => parseFloat(row['Docking score (kcal/mol)']))
                        .filter((score) => !isNaN(score));
                      return scores.length > 0 ? (scores.reduce((a, b) => a + b, 0) / scores.length).toFixed(1) : 'N/A';
                    })()}
                  </div>
                  <div className="text-xs text-gray-500 font-normal mt-1">Average Score (kcal/mol)</div>
                </div>
              </div>

              {/* Score Range Filter */}
              <div className="border border-gray-200 rounded-xl p-6 shadow-lg bg-gradient-to-br from-white to-gray-50">
                {/* Header */}
                <div className="flex items-center justify-between mb-6">
                  <div className="flex items-center gap-3">
                    <Filter className="h-6 w-6 text-blue-600" />
                    <h4 className="text-xl font-semibold text-gray-800">Docking Score Filter</h4>
                  </div>
                  <Button
                    onClick={resetFilters}
                    className="flex items-center gap-2 bg-gray-100 hover:bg-gray-200 text-gray-700 text-sm font-medium border border-gray-300 rounded-lg shadow-none"
                  >
                    <RefreshCw className="h-4 w-4" />
                    Reset
                  </Button>
                </div>

                {/* Range and Apply */}
                <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-4">
                  <div>
                    <span className="block text-xs text-gray-500 uppercase tracking-wide mb-1">Current Range</span>
                    <span className="text-lg font-mono text-blue-700">
                      {scoreRange[0].toFixed(1)} <span className="text-gray-400">to</span> {scoreRange[1].toFixed(1)} <span className="text-gray-500 text-base">kcal/mol</span>
                    </span>
                  </div>
                  {/* <Button
                    onClick={() =>
                      setFilteredData(
                        filterByScoreRange(
                          parseCsv(
                            experimentData[selectedFolder][
                              activeTab === 'passed' ? 'outputWithPbCsv' : 'outputWithoutPbCsv'
                            ] || experimentData[selectedFolder].outputCsv
                          ).rowData
                        )
                      )
                    }
                    className="bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold px-6 py-2 rounded-lg shadow"
                  >
                    Apply Filter
                  </Button> */}
                </div>

                {/* Slider */}
                <div className="pt-2 pb-1">
                  <Slider
                    range
                    min={getScoreBounds()[0]}
                    max={getScoreBounds()[1]}
                    value={scoreRange}
                    onChange={(value) => setScoreRange(value as [number, number])}
                    allowCross={false}
                    step={0.1}
                    classNames={{
                      rail: 'bg-gray-200 h-2 rounded-full',
                      track: 'bg-blue-500 h-2 rounded-full',
                      handle: 'border-2 border-blue-500 bg-white h-5 w-5 -mt-1.5',
                    }}
                  />
                </div>
              </div>

              {/* PoseBusters Filter */}
              <div className="flex justify-end">
                <Button
                  onClick={runPoseBusters}
                  disabled={poseBustersLoading || !selectedFolder || !hasPdbFile}
                  className={`
                    group relative flex items-center gap-3 px-6 py-3
                    text-sm font-semibold tracking-wide
                    bg-gradient-to-r from-emerald-500 to-green-500
                    hover:from-emerald-600 hover:to-green-600
                    disabled:from-gray-300 disabled:to-gray-400
                    text-white shadow-lg
                    hover:shadow-xl hover:scale-[1.02]
                    disabled:hover:scale-100
                    rounded-xl
                    transition-all duration-200 ease-in-out
                    ring-2 ring-emerald-500/50 ring-offset-2
                    hover:ring-emerald-600/50
                    disabled:ring-gray-300/50
                    ${poseBustersLoading ? 'animate-pulse' : ''}
                  `}
                >
                  <span className="relative flex items-center gap-2">
                    {poseBustersLoading ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Filter className="h-4 w-4 transition-transform group-hover:scale-110" />
                    )}
                    <span className="relative">
                      Run PoseBusters
                      <span className="absolute bottom-0 left-0 h-[2px] w-0 bg-white/40 
                        group-hover:w-full transition-all duration-300"></span>
                    </span>
                  </span>
                  {!poseBustersLoading && (
                    <span className="absolute inset-0 rounded-xl bg-gradient-to-r from-emerald-500/20 to-green-500/20 
                      blur-xl group-hover:blur-2xl transition-all duration-300 opacity-0 group-hover:opacity-100" />
                  )}
                </Button>
              </div>

              {/* Tabs for Passed/Failed Results */}
              {experimentData[selectedFolder]?.isPoseBustersFiltered && (
                <Tabs.Root
                  value={activeTab}
                  onValueChange={(value) => setActiveTab(value as 'passed' | 'failed')}
                  className="space-y-4"
                >
                  <Tabs.List className="flex space-x-1 bg-gray-100 p-1 rounded-lg">
                    <Tabs.Trigger
                      value="passed"
                      className={`flex-1 py-2 px-4 text-sm font-medium rounded-md text-gray-700 transition-all ${
                        activeTab === 'passed' ? 'bg-white shadow-sm' : 'hover:bg-gray-200'
                      }`}
                    >
                      Passed PoseBusters
                    </Tabs.Trigger>
                    <Tabs.Trigger
                      value="failed"
                      className={`flex-1 py-2 px-4 text-sm font-medium rounded-md text-gray-700 transition-all ${
                        activeTab === 'failed' ? 'bg-white shadow-sm' : 'hover:bg-gray-200'
                      }`}
                    >
                      Failed PoseBusters
                    </Tabs.Trigger>
                  </Tabs.List>

                  <Tabs.Content value="passed">
                    {getFilteredRowData().length === 0 ? (
                      <div className="p-6 bg-yellow-50 border border-yellow-200 rounded-xl text-center">
                        <p className="text-sm text-yellow-700">No compounds passed the PoseBusters check.</p>
                      </div>
                    ) : (
                      <>
                        {/* Histogram */}
                        {shouldShowHistogram(getFilteredRowData()) && (
                          <div className="border border-gray-200 rounded-xl p-6 shadow-lg bg-gradient-to-br from-white to-gray-50">
                            <div className="flex items-center gap-2 mb-4">
                              <BarChart3 className="h-5 w-5 text-blue-600" />
                              <h4 className="text-lg font-semibold text-gray-800">
                                Distribution of Passed PoseBusters Docking Scores
                              </h4>
                            </div>
                            <ResponsiveContainer width="100%" height={350}>
                              <BarChart
                                data={getHistogramData(getFilteredRowData())}
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

                        {/* AG Grid Table */}
                        <div className="border border-gray-200 rounded-xl shadow-lg overflow-hidden">
                          <div className="ag-theme-alpine-custom">
                            <AgGridReact
                              columnDefs={columnDefs(parseCsv(experimentData[selectedFolder].outputWithPbCsv).headers)}
                              rowData={getFilteredRowData()}
                              defaultColDef={{
                                flex: 1,
                                minWidth: 100,
                                filter: true,
                                sortable: true,
                                resizable: true,
                                cellClass: 'custom-cell',
                              }}
                              pagination={true}
                              paginationPageSize={20}
                              domLayout="autoHeight"
                              headerHeight={48}
                              rowHeight={42}
                              animateRows={true}
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
                      </>
                    )}
                  </Tabs.Content>

                  <Tabs.Content value="failed">
                    {isOutputWithoutPbEmpty() ? (
                      <div className="p-6 bg-green-50 border border-green-200 rounded-xl text-center">
                        <div className="flex items-center justify-center gap-2">
                          <Info className="h-5 w-5 text-green-600" />
                          <p className="text-sm text-green-700">All compounds passed the PoseBusters check.</p>
                        </div>
                      </div>
                    ) : (
                      <>
                        {/* Histogram */}
                        {shouldShowHistogram(getFilteredRowData()) && (
                          <div className="border border-gray-200 rounded-xl p-6 shadow-lg bg-gradient-to-br from-white to-gray-50">
                            <div className="flex items-center gap-2 mb-4">
                              <BarChart3 className="h-5 w-5 text-blue-600" />
                              <h4 className="text-lg font-semibold text-gray-800">
                                Distribution of Failed PoseBusters Docking Scores
                              </h4>
                            </div>
                            <ResponsiveContainer width="100%" height={350}>
                              <BarChart
                                data={getHistogramData(getFilteredRowData())}
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
                                  fill="url(#colorGradientFailed)"
                                  radius={[6, 6, 0, 0]}
                                  stroke="#b91c1c"
                                  strokeWidth={1}
                                />
                                <defs>
                                  <linearGradient id="colorGradientFailed" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="0%" stopColor="#ef4444" stopOpacity={0.9} />
                                    <stop offset="100%" stopColor="#f87171" stopOpacity={0.7} />
                                  </linearGradient>
                                </defs>
                              </BarChart>
                            </ResponsiveContainer>
                          </div>
                        )}

                        {/* AG Grid Table */}
                        <div className="border border-gray-200 rounded-xl shadow-lg overflow-hidden">
                          <div className="ag-theme-alpine-custom">
                            <AgGridReact
                              columnDefs={columnDefs(parseCsv(experimentData[selectedFolder].outputWithoutPbCsv).headers)}
                              rowData={getFilteredRowData()}
                              defaultColDef={{
                                flex: 1,
                                minWidth: 100,
                                filter: true,
                                sortable: true,
                                resizable: true,
                                cellClass: 'custom-cell',
                              }}
                              pagination={true}
                              paginationPageSize={20}
                              domLayout="autoHeight"
                              headerHeight={48}
                              rowHeight={42}
                              animateRows={true}
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
                      </>
                    )}
                  </Tabs.Content>
                </Tabs.Root>
              )}

              {/* Default View (Before PoseBusters) */}
              {!experimentData[selectedFolder]?.isPoseBustersFiltered && (
                <>
                  {/* Histogram */}
                  {shouldShowHistogram(getFilteredRowData()) && (
                    <div className="border border-gray-200 rounded-xl p-6 shadow-lg bg-gradient-to-br from-white to-gray-50">
                      <div className="flex items-center gap-2 mb-4">
                        <BarChart3 className="h-5 w-5 text-blue-600" />
                        <h4 className="text-lg font-semibold text-gray-800">
                          Distribution of Docking Scores
                        </h4>
                      </div>
                      <ResponsiveContainer width="100%" height={350}>
                        <BarChart
                          data={getHistogramData(getFilteredRowData())}
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

                  {/* AG Grid Table */}
                  <div className="border border-gray-200 rounded-xl shadow-lg overflow-hidden">
                    <div className="ag-theme-alpine-custom">
                      <AgGridReact
                        columnDefs={columnDefs(parseCsv(experimentData[selectedFolder].outputCsv).headers)}
                        rowData={getFilteredRowData()}
                        defaultColDef={{
                          flex: 1,
                          minWidth: 100,
                          filter: true,
                          sortable: true,
                          resizable: true,
                          cellClass: 'custom-cell',
                        }}
                        pagination={true}
                        paginationPageSize={20}
                        domLayout="autoHeight"
                        headerHeight={48}
                        rowHeight={42}
                        animateRows={true}
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
                </>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}