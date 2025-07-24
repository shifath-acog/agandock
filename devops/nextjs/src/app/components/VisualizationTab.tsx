'use client';

import { useState, useEffect, useRef } from 'react';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Loader2, FileText, Info, Eye, EyeOff, ZoomIn, Download } from 'lucide-react';
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
  const [showReceptor, setShowReceptor] = useState<boolean>(true);
  const [showLigand, setShowLigand] = useState<boolean>(true);
  const stageRef = useRef<NGL.Stage | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const receptorReprRef = useRef<NGL.RepresentationElement | null>(null);
  const ligandReprRef = useRef<NGL.RepresentationElement | null>(null);

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
      // Initialize NGL stage if it doesn't exist
      if (!stageRef.current) {
        stageRef.current = new NGL.Stage(containerRef.current, {
          backgroundColor: 'white',
        });
      } else {
        // Clear existing components if stage already exists
        stageRef.current.removeAllComponents();
      }

      // Load receptor PDB
      const receptorUrl = `/api/get-file?file=${encodeURIComponent(plcData[selectedFolder].receptorPdb)}`;
      const receptorComponent = await stageRef.current.loadFile(receptorUrl, { ext: 'pdb' });
      if (receptorComponent instanceof NGL.StructureComponent) {
        receptorReprRef.current = receptorComponent.addRepresentation('cartoon', {
          colorScheme: 'residueindex',
          visible: showReceptor,
        });
      } else {
        console.warn('Receptor file loaded but not a StructureComponent:', receptorComponent);
      }

      // Load ligand PDB
      const ligandUrl = `/api/get-file?file=${encodeURIComponent(`/app/${selectedFolder}/plc/${selectedPdb}`)}`;
      const ligandComponent = await stageRef.current.loadFile(ligandUrl, { ext: 'pdb' });
      if (ligandComponent instanceof NGL.StructureComponent) {
        ligandReprRef.current = ligandComponent.addRepresentation('licorice', {
          colorScheme: 'element',
          visible: showLigand,
        });
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

  // Toggle receptor visibility
  const toggleReceptor = () => {
    if (receptorReprRef.current) {
      receptorReprRef.current.setVisibility(!showReceptor);
      setShowReceptor(!showReceptor);
    }
  };

  // Toggle ligand visibility
  const toggleLigand = () => {
    if (ligandReprRef.current) {
      ligandReprRef.current.setVisibility(!showLigand);
      setShowLigand(!showLigand);
    }
  };

  // Zoom to binding site
  const zoomToBindingSite = () => {
    if (stageRef.current && ligandReprRef.current) {
      const selection = new NGL.Selection('within 5 of :A');
    }
  };

  // Export PNG snapshot
  const exportPng = () => {
    if (stageRef.current) {
      stageRef.current.viewer.makeImage({
        antialias: true,
        trim: false,
        transparent: false,
      }).then((blob: Blob) => {
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `docked_pose_${selectedPdb}.png`;
        link.click();
        URL.revokeObjectURL(url);
      });
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
          <div className="flex items-center gap-4 flex-wrap">
            <Select
              value={selectedFolder ?? undefined}
              onValueChange={(value) => {
                setSelectedFolder(value);
                setError(null);
                setSelectedPdb('');
                setShowReceptor(true);
                setShowLigand(true);
              }}
            >
              <SelectTrigger className="w-full max-w-xs h-12 border-gray-300 rounded-xl shadow-sm focus:ring-2 focus:ring-blue-200 focus:border-blue-500">
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
              <Select
                value={selectedPdb}
                onValueChange={(value) => {
                  setSelectedPdb(value);
                  setShowReceptor(true);
                  setShowLigand(true);
                }}
              >
                <SelectTrigger className="w-full max-w-xs h-12 border-gray-300 rounded-xl shadow-sm focus:ring-2 focus:ring-blue-200 focus:border-blue-500">
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
            )}

            <Button
              onClick={showDockedPose}
              disabled={!selectedPdb || !selectedFolder || !plcData[selectedFolder]?.receptorPdb || viewerLoading}
              className="flex items-center gap-2 bg-black hover:bg-gray-900 text-white text-sm disabled:bg-gray-400"
            >
              {viewerLoading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <FileText className="h-4 w-4" />
              )}
              Show Docked Pose
            </Button>
          </div>

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
                  {selectedPdb && plcData[selectedFolder].receptorPdb && (
                    <div className="flex flex-wrap gap-4">
                      <Button
                        onClick={toggleReceptor}
                        className="flex items-center gap-2 bg-gray-600 hover:bg-gray-700 text-white text-sm"
                      >
                        {showReceptor ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                        {showReceptor ? 'Hide Receptor' : 'Show Receptor'}
                      </Button>
                      <Button
                        onClick={toggleLigand}
                        className="flex items-center gap-2 bg-gray-600 hover:bg-gray-700 text-white text-sm"
                      >
                        {showLigand ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                        {showLigand ? 'Hide Ligand' : 'Show Ligand'}
                      </Button>
                      {/* <Button
                        onClick={zoomToBindingSite}
                        className="flex items-center gap-2 bg-gray-600 hover:bg-gray-700 text-white text-sm"
                      >
                        <ZoomIn className="h-4 w-4" />
                        Zoom to Binding Site
                      </Button> */}
                      <Button
                        onClick={exportPng}
                        className="flex items-center gap-2 bg-gray-600 hover:bg-gray-700 text-white text-sm"
                      >
                        <Download className="h-4 w-4" />
                        Export PNG
                      </Button>
                    </div>
                  )}

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