'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Loader2, FileText, Download, BarChart3 } from 'lucide-react';
import { AgGridReact } from 'ag-grid-react';
import { ModuleRegistry, AllCommunityModule } from 'ag-grid-community';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import type { ColDef, GridApi } from 'ag-grid-community';
import { FiltrationTab } from './FiltrationTab';
import { PlipAnalysisTab } from './PlipAnalysisTab';
import { VisualizationTab } from './VisualizationTab';

// Register AG Grid modules
ModuleRegistry.registerModules([AllCommunityModule]);

interface ExperimentData {
  outputCsv: string; // Content of output.csv
}

interface ResultsTabsProps {
  // Add props if needed for future tabs
}

export function ResultsTabs({}: ResultsTabsProps) {
  const [experimentFolders, setExperimentFolders] = useState<string[]>([]);
  const [selectedFolder, setSelectedFolder] = useState<string | null>(null);
  const [experimentData, setExperimentData] = useState<Record<string, ExperimentData>>({});
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [gridApi, setGridApi] = useState<GridApi | null>(null);

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

  // Fetch data for selected folder
  useEffect(() => {
    async function fetchExperimentData() {
      if (!selectedFolder || selectedFolder in experimentData) return;
      setLoading(true);
      try {
        const response = await fetch(`/api/get-experiments?folder=${encodeURIComponent(selectedFolder)}`);
        if (!response.ok) {
          throw new Error(`Failed to load data for ${selectedFolder}`);
        }
        const data = await response.json();
        setExperimentData((prev) => ({
          ...prev,
          [selectedFolder]: {
            outputCsv: data.outputCsv,
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
  }, [selectedFolder, experimentData]);

  // Parse CSV content into rows for AGGrid
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

  // Prepare data for histogram
  const getHistogramData = (csvContent: string) => {
    const { rowData } = parseCsv(csvContent);
    const scores = rowData
      .map((row) => parseFloat(row['Docking score (kcal/mol)']))
      .filter((score) => !isNaN(score));
    
    // Bin scores into ranges (e.g., -10 to -8, -8 to -6, etc.)
    const minScore = Math.floor(Math.min(...scores));
    const maxScore = Math.ceil(Math.max(...scores));
    const binSize = 2; // 2 kcal/mol per bin
    const bins: { range: string; count: number }[] = [];
    
    for (let i = minScore; i < maxScore; i += binSize) {
      const rangeStart = i;
      const rangeEnd = i + binSize;
      const count = scores.filter((score) => score >= rangeStart && score < rangeEnd).length;
      bins.push({ range: `${rangeStart} to ${rangeEnd}`, count });
    }
    
    return bins;
  };

  // Check if histogram should be displayed (more than one row)
  const shouldShowHistogram = (csvContent: string) => {
    const { rowData } = parseCsv(csvContent);
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
    
    // Color code based on docking score (better scores are more negative)
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

  // AGGrid column definitions with enhanced styling
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

      // Special configuration for specific columns
      if (header === 'Docking score (kcal/mol)') {
        return {
          ...baseConfig,
          cellRenderer: dockingScoreCellRenderer,
          sort: 'asc', // Default sort ascending (best scores first)
          minWidth: 180,
          comparator: (valueA: string, valueB: string) => {
            return parseFloat(valueA) - parseFloat(valueB);
          },
        };
      } else if (header === 'Ligand efficiency') {
        return {
          ...baseConfig,
          cellRenderer: numericCellRenderer,
          minWidth: 150,
          flex: 1,
        };
      } else if (header === 'SMILES') {
        return {
          ...baseConfig,
          minWidth: 200,
          flex: 7, // Take 70% of the available width (if total flex is 10)
          cellClass: 'font-mono text-xs custom-cell',
        };
      } else if (header === 'Name') {
        return {
          ...baseConfig,
          minWidth: 80,
          cellClass: 'font-medium custom-cell',
          pinned: 'left',
        };
      }
      return baseConfig;
    });

  // Export data functionality
  const exportData = () => {
    if (gridApi) {
      gridApi.exportDataAsCsv({
        fileName: `${selectedFolder}_results.csv`,
      });
    }
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-6xl mt-5">
      <Card className="border-0 shadow-xl shadow-[0_-4px_16px_-4px_rgba(0,0,0,0.10)] hover:shadow-2xl hover:shadow-[0_-8px_24px_-6px_rgba(0,0,0,0.13)] transition-shadow duration-300 bg-white rounded-2xl overflow-hidden">
        <CardContent className="px-8 py-10">
          <Tabs defaultValue="docking-results" className="w-full">
            <TabsList className="grid w-full grid-cols-4 h-14 p-1 bg-gray-100 rounded-xl shadow-sm">
              <TabsTrigger
                value="docking-results"
                className="h-12 text-sm font-semibold data-[state=active]:bg-white data-[state=active]:shadow-md data-[state=active]:text-blue-600 transition-all duration-200 hover:bg-gray-200 rounded-lg"
              >
                Docking Results
              </TabsTrigger>
              <TabsTrigger
                value="filtration"
                className="h-12 text-sm font-semibold data-[state=active]:bg-white data-[state=active]:shadow-md data-[state=active]:text-blue-600 transition-all duration-200 hover:bg-gray-200 rounded-lg"
              >
                Filtration
              </TabsTrigger>
              <TabsTrigger
                value="plip-analysis"
                className="h-12 text-sm font-semibold data-[state=active]:bg-white data-[state=active]:shadow-md data-[state=active]:text-blue-600 transition-all duration-200 hover:bg-gray-200 rounded-lg"
              >
                PLIP Analysis
              </TabsTrigger>
              <TabsTrigger
                value="visualization"
                className="h-12 text-sm font-semibold data-[state=active]:bg-white data-[state=active]:shadow-md data-[state=active]:text-blue-600 transition-all duration-200 hover:bg-gray-200 rounded-lg"
              >
                Visualization
              </TabsTrigger>
            </TabsList>

            <TabsContent value="docking-results" className="mt-8">
              <div className="space-y-6 border border-gray-200 shadow-md hover:shadow-lg transition-shadow duration-200 bg-white rounded-xl px-6 py-4">
                <div className="border-b border-gray-200 pb-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <FileText className="h-5 w-5 text-blue-600" />
                      <h3 className="text-xl font-semibold text-gray-800">Docking Results</h3>
                    </div>
                    {selectedFolder && experimentData[selectedFolder] && (
                      <button
                        onClick={exportData}
                        className="flex items-center gap-2 px-4 py-2 bg-gray-800 text-white rounded-lg hover:bg-gray-700 transition-colors duration-200 text-sm font-medium shadow-sm"
                      >
                        <Download className="h-4 w-4" />
                        Export CSV
                      </button>
                    )}
                  </div>
                  <p className="text-sm text-gray-600 mt-2">View the results and docking score distribution of your experiments</p>
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
                              {parseCsv(experimentData[selectedFolder].outputCsv).rowData.length}
                            </div>
                            <div className="text-xs text-gray-500 font-normal mt-1">Total Compounds</div>
                          </div>
                          <div className="bg-white border border-gray-200 rounded-lg p-4 flex flex-col items-center">
                            <div className="text-2xl font-semibold text-green-600">
                              {(() => {
                                const { rowData } = parseCsv(experimentData[selectedFolder].outputCsv);
                                const scores = rowData
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
                                const { rowData } = parseCsv(experimentData[selectedFolder].outputCsv);
                                const scores = rowData
                                  .map((row) => parseFloat(row['Docking score (kcal/mol)']))
                                  .filter((score) => !isNaN(score));
                                return scores.length > 0 ? (scores.reduce((a, b) => a + b, 0) / scores.length).toFixed(1) : 'N/A';
                              })()}
                            </div>
                            <div className="text-xs text-gray-500 font-normal mt-1">Average Score (kcal/mol)</div>
                          </div>
                        </div>

                        {/* Histogram */}
                        {shouldShowHistogram(experimentData[selectedFolder].outputCsv) && (
                          <div className="border border-gray-200 rounded-xl p-6 shadow-lg bg-gradient-to-br from-white to-gray-50">
                            <div className="flex items-center gap-2 mb-4">
                              <BarChart3 className="h-5 w-5 text-blue-600" />
                              <h4 className="text-lg font-semibold text-gray-800">
                                Distribution of Docking Scores
                              </h4>
                            </div>
                            <ResponsiveContainer width="100%" height={350}>
                              <BarChart
                                data={getHistogramData(experimentData[selectedFolder].outputCsv)}
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

                        {/* AGGrid Table */}
                        <div className="border border-gray-200 rounded-xl shadow-lg overflow-hidden">
                          <div className="ag-theme-alpine-custom">
                            <AgGridReact
                              columnDefs={columnDefs(parseCsv(experimentData[selectedFolder].outputCsv).headers)}
                              rowData={parseCsv(experimentData[selectedFolder].outputCsv).rowData}
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
                      </div>
                    )}
                  </div>
                )}
              </div>
            </TabsContent>

            <TabsContent value="filtration" className="mt-8">
              <FiltrationTab />
            </TabsContent>

            <TabsContent value="plip-analysis" className="mt-8">
                <PlipAnalysisTab />
            </TabsContent>

            <TabsContent value="visualization" className="mt-8">
              <VisualizationTab />
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>

      {/* Custom Styles for AG Grid */}
      <style jsx global>{`
        .ag-theme-alpine-custom {
          --ag-foreground-color: #1f2937;
          --ag-background-color: #ffffff;
          --ag-header-background-color: #f8fafc;
          --ag-header-foreground-color: #1e293b;
          --ag-row-hover-background-color: #f0f9ff;
          --ag-selected-row-background-color: #dbeafe;
          --ag-border-color: #e2e8f0;
          --ag-header-height: 48px;
          --ag-row-height: 42px;
          --ag-font-size: 14px;
          --ag-font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
          --ag-cell-horizontal-padding: 16px;
          --ag-grid-size: 8px;
          --ag-row-border-color: #f1f5f9;
        }

        .ag-theme-alpine-custom .ag-header-cell {
          background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
          border-bottom: 2px solid #e2e8f0;
          font-weight: 600;
          color: #1e293b;
          padding: 0 16px;
          display: flex;
          align-items: center;
        }

        .ag-theme-alpine-custom .ag-header-cell:hover {
          background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
        }

        .ag-theme-alpine-custom .custom-header {
          border-right: 1px solid #e2e8f0;
        }

        .ag-theme-alpine-custom .ag-cell {
          padding: 8px 16px;
          line-height: 26px;
          border-bottom: 1px solid #f1f5f9;
          border-right: 1px solid #f8fafc;
          display: flex;
          align-items: center;
        }

        .ag-theme-alpine-custom .custom-cell {
          transition: all 0.2s ease;
        }

        .ag-theme-alpine-custom .ag-row {
          transition: all 0.2s ease;
        }

        .ag-theme-alpine-custom .ag-row:hover {
          background-color: #f0f9ff;
          box-shadow: 0 1px 3px rgba(59, 130, 246, 0.1);
        }

        .ag-theme-alpine-custom .ag-row-selected {
          background-color: #dbeafe !important;
          border-left: 3px solid #3b82f6;
        }

        /* Enhanced AG Grid Pagination Styling */
        .ag-theme-alpine-custom .ag-paging-panel {
          padding: 32px 32px 32px 32px;
          background: linear-gradient(90deg, #f0f9ff 0%, #e0e7ef 100%);
          border-top: 2px solid #e2e8f0;
          border-radius: 0 0 1rem 1rem;
          box-shadow: 0 -2px 8px 0 rgba(59,130,246,0.04);
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 16px;
        }

        .ag-theme-alpine-custom .ag-paging-button {
          color: #2563eb;
          background: #f8fafc;
          border-radius: 9999px;
          padding: 0.75rem 1.25rem;
          margin: 0 6px;
          font-weight: 700;
          font-size: 1.15rem;
          box-shadow: 0 2px 8px rgba(59,130,246,0.08);
          border: 2px solid #e0e7ef;
          transition: all 0.18s cubic-bezier(.4,0,.2,1);
          outline: none;
          display: flex;
          align-items: center;
          gap: 0.5rem;
        }

        .ag-theme-alpine-custom .ag-paging-button svg {
          width: 1.25em;
          height: 1.25em;
          stroke-width: 2.5;
          color: #2563eb;
          transition: color 0.2s;
        }

        .ag-theme-alpine-custom .ag-paging-button:hover:not(.ag-disabled),
        .ag-theme-alpine-custom .ag-paging-button:focus:not(.ag-disabled) {
          background: #dbeafe;
          color: #1d4ed8;
          border-color: #93c5fd;
          box-shadow: 0 4px 16px 0 rgba(59,130,246,0.13);
          transform: translateY(-2px) scale(1.06);
        }

        .ag-theme-alpine-custom .ag-paging-button:hover:not(.ag-disabled) svg,
        .ag-theme-alpine-custom .ag-paging-button:focus:not(.ag-disabled) svg {
          color: #1d4ed8;
        }

        .ag-theme-alpine-custom .ag-paging-button.ag-disabled {
          opacity: 0.5;
          cursor: not-allowed;
          background: #f1f5f9;
          color: #94a3b8;
          border-color: #e0e7ef;
          box-shadow: none;
        }

        .ag-theme-alpine-custom .ag-paging-number {
          color: #1e293b;
          font-weight: 700;
          font-size: 1.1rem;
          margin: 0 10px;
          background: #e0e7ef;
          border-radius: 0.5rem;
          padding: 10px 18px;
          box-shadow: 0 1px 2px rgba(59,130,246,0.04);
          transition: background 0.2s, color 0.2s;
        }

        .ag-theme-alpine-custom .ag-paging-number.ag-paging-number-current {
          background: #2563eb;
          color: #fff;
          box-shadow: 0 2px 8px 0 rgba(59,130,246,0.12);
          border: 2px solid #2563eb;
          transform: scale(1.10);
        }

        /* Pinned column styling */
        .ag-theme-alpine-custom .ag-pinned-left-header,
        .ag-theme-alpine-custom .ag-pinned-left-cols-container {
          border-right: 2px solid #e2e8f0;
          box-shadow: 2px 0 4px rgba(0, 0, 0, 0.05);
        }

        .ag-theme-alpine-custom .ag-pinned-left-header {
          background: linear-gradient(135deg, #fafbfc 0%, #f3f4f6 100%);
        }

        /* Custom scrollbar */
        .ag-theme-alpine-custom .ag-body-horizontal-scroll-viewport::-webkit-scrollbar,
        .ag-theme-alpine-custom .ag-body-vertical-scroll-viewport::-webkit-scrollbar {
          width: 8px;
          height: 8px;
        }

        .ag-theme-alpine-custom .ag-body-horizontal-scroll-viewport::-webkit-scrollbar-track,
        .ag-theme-alpine-custom .ag-body-vertical-scroll-viewport::-webkit-scrollbar-track {
          background: #f1f5f9;
          border-radius: 4px;
        }

        .ag-theme-alpine-custom .ag-body-horizontal-scroll-viewport::-webkit-scrollbar-thumb,
        .ag-theme-alpine-custom .ag-body-vertical-scroll-viewport::-webkit-scrollbar-thumb {
          background: #cbd5e1;
          border-radius: 4px;
          transition: background-color 0.2s ease;
        }

        .ag-theme-alpine-custom .ag-body-horizontal-scroll-viewport::-webkit-scrollbar-thumb:hover,
        .ag-theme-alpine-custom .ag-body-vertical-scroll-viewport::-webkit-scrollbar-thumb:hover {
          background: #94a3b8;
        }

        /* Loading overlay */
        .ag-theme-alpine-custom .ag-overlay-loading-wrapper {
          background: rgba(255, 255, 255, 0.9);
          border-radius: 0.75rem;
        }

        /* Selection checkbox styling */
        .ag-theme-alpine-custom .ag-checkbox-input-wrapper {
          border-radius: 0.25rem;
        }

        .ag-theme-alpine-custom .ag-checkbox-input-wrapper.ag-checked {
          background-color: #3b82f6;
          border-color: #3b82f6;
        }
      `}</style>
    </div>
  );
}