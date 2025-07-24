'use client';

import { useState, useEffect, useRef } from 'react';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Loader2, FileText, Info } from 'lucide-react';
import { Button } from '@/components/ui/button';
import * as NGL from 'ngl';

interface VisualizationTabProps {
  // Add props if needed
}

interface PlcData {
  pdbFiles: string[];
  plcExists: boolean;
  receptorPdb: string | null;
}

export function VisualizationTab({}: VisualizationTabProps) {
  const [experimentFolders, setExperimentFolders] = useState<string[]>([]);
  const [selectedFolder, setSelectedFolder] = useState<string | null>(null);
  const [plcData, setPlcData] = useState<Record<string, PlcData>>({});
  const [selectedPdb, setSelectedPdb] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [viewerLoading, setViewerLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const stageRef = useRef<NGL.Stage | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

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

  // Fetch PLC files and receptor PDB when folder is selected
  useEffect(() => {
    async function fetchPlcFiles() {
      if (!selectedFolder || selectedFolder in plcData) return;
      setLoading(true);
      setError(null);
      setSelectedPdb('');
      try {
        const response = await fetch(`/api/get-plc-files?folder=${encodeURIComponent(selectedFolder)}`);
        if (!response.ok) throw new Error(`Failed to load PLC files for ${selectedFolder}`);
        const data: PlcData = await response.json();
        setPlcData((prev) => ({
          ...prev,
          [selectedFolder]: data,
        }));
        if (data.pdbFiles.length > 0) {
          setSelectedPdb(data.pdbFiles[0]);
        }
      } catch (err) {
        setError(`Error loading PLC files for ${selectedFolder}. Please try again.`);
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    fetchPlcFiles();
  }, [selectedFolder, plcData]);

  // Function to initialize NGL viewer and load PDB files
  const showDockedPose = async () => {
    if (!containerRef.current || !selectedFolder || !plcData[selectedFolder]?.receptorPdb || !selectedPdb) return;

    setViewerLoading(true);
    setError(null);

    try {
      // Destroy existing stage if any
      if (stageRef.current) {
        stageRef.current.dispose();
        stageRef.current = null;
      }

      // Initialize new NGL stage
      stageRef.current = new NGL.Stage(containerRef.current, {
        backgroundColor: 'white',
      });

      // Load receptor PDB
      const receptorUrl = `/api/get-file?file=${encodeURIComponent(plcData[selectedFolder].receptorPdb)}`;
      const receptorComponent = await stageRef.current.loadFile(receptorUrl, { ext: 'pdb' });
      if (receptorComponent instanceof NGL.StructureComponent) {
        receptorComponent.addRepresentation('cartoon', { colorScheme: 'residueindex' });
      } else {
        console.warn('Receptor file loaded but not a StructureComponent:', receptorComponent);
      }

      // Load ligand PDB
      const ligandUrl = `/api/get-file?file=${encodeURIComponent(`/app/${selectedFolder}/plc/${selectedPdb}`)}`;
      const ligandComponent = await stageRef.current.loadFile(ligandUrl, { ext: 'pdb' });
      if (ligandComponent instanceof NGL.StructureComponent) {
        ligandComponent.addRepresentation('licorice', { colorScheme: 'element' });
      } else {
        console.warn('Ligand file loaded but not a StructureComponent:', ligandComponent);
      }

      // Auto-view the entire scene once
      if (stageRef.current) {
        stageRef.current.autoView();
      }
    } catch (err) {
      setError('Error initializing 3D viewer. Please try again.');
      console.error(err);
    } finally {
      setViewerLoading(false);
    }
  };

  // Cleanup stage on unmount
  useEffect(() => {
    return () => {
      if (stageRef.current) {
        stageRef.current.dispose();
        stageRef.current = null;
      }
    };
  }, []);

  return (
    <div className="space-y-6 border border-gray-200 shadow-md hover:shadow-lg transition-shadow duration-200 bg-white rounded-xl px-6 py-4">
      <div className="border-b border-gray-200 pb-4">
        <div className="flex items-center gap-2">
          <FileText className="h-5 w-5 text-blue-600" />
          <h3 className="text-xl font-semibold text-gray-800">Docked Pose Visualization</h3>
        </div>
        <p className="text-sm text-gray-600 mt-2">
          Visualize protein-ligand interactions for docking results
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
              setSelectedPdb('');
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

          {selectedFolder && plcData[selectedFolder] && (
            <div className="space-y-6">
              {!plcData[selectedFolder].plcExists ? (
                <div className="p-6 bg-yellow-50 border border-yellow-200 rounded-xl text-center">
                  <p className="text-sm text-yellow-700">
                    Please first run PLIP for a given experiment.
                  </p>
                </div>
              ) : plcData[selectedFolder].pdbFiles.length === 0 ? (
                <div className="p-6 bg-yellow-50 border border-yellow-200 rounded-xl text-center">
                  <p className="text-sm text-yellow-700">
                    No PDB files found in the PLC folder. Please run PLIP analysis.
                  </p>
                </div>
              ) : (
                <>
                  <div className="flex items-center gap-4">
                    <Select
                      value={selectedPdb}
                      onValueChange={setSelectedPdb}
                    >
                      <SelectTrigger className="w-full max-w-md h-12 border-gray-300 rounded-xl shadow-sm focus:ring-2 focus:ring-blue-200 focus:border-blue-500">
                        <SelectValue placeholder="Select a ligand PDB file" />
                      </SelectTrigger>
                      <SelectContent>
                        {plcData[selectedFolder].pdbFiles.map((pdb) => (
                          <SelectItem key={pdb} value={pdb}>
                            {pdb}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <Button
                      onClick={showDockedPose}
                      disabled={!selectedPdb || !plcData[selectedFolder].receptorPdb || viewerLoading}
                      className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white text-sm disabled:bg-gray-400"
                    >
                      {viewerLoading ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <FileText className="h-4 w-4" />
                      )}
                      Show Docked Pose
                    </Button>
                  </div>

                  {selectedPdb && plcData[selectedFolder].receptorPdb ? (
                    <div className="border border-gray-200 rounded-xl shadow-lg overflow-hidden">
                      <div
                        ref={containerRef}
                        style={{ width: '100%', height: '600px', position: 'relative' }}
                      />
                    </div>
                  ) : (
                    <div className="p-6 bg-yellow-50 border border-yellow-200 rounded-xl text-center">
                      <div className="flex items-center justify-center gap-2">
                        <Info className="h-5 w-5 text-yellow-700" />
                        <p className="text-sm text-yellow-700">
                          {selectedPdb
                            ? 'Receptor PDB file not found. Please ensure the experiment folder contains a receptor PDB.'
                            : 'Select a ligand PDB file to visualize.'}
                        </p>
                      </div>
                    </div>
                  )}
                </>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}