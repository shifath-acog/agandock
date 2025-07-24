import { NextResponse } from 'next/server';
import { readdir, access } from 'fs/promises';
import path from 'path';

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const folder = searchParams.get('folder');

  if (!folder) {
    return NextResponse.json({ error: 'Folder parameter is required' }, { status: 400 });
  }

  try {
    const plcDir = path.join('/app', folder, 'plc');
    // Check if plc folder exists
    let plcExists = false;
    let pdbFiles: string[] = [];
    try {
      await access(plcDir);
      plcExists = true;
      // List .pdb files in plc folder
      const files = await readdir(plcDir, { withFileTypes: true });
      pdbFiles = files
        .filter((file) => file.isFile() && file.name.endsWith('.pdb'))
        .map((file) => file.name);
    } catch {
      // plc folder doesn't exist
    }

    // Get receptor PDB path from experiment folder
    const experimentDir = path.join('/app', folder);
    const experimentFiles = await readdir(experimentDir, { withFileTypes: true });
    const receptorPdb = experimentFiles.find(
      (file) =>
        file.isFile() &&
        file.name.endsWith('.pdb') &&
        !file.name.match(/pdb_\d+_[a-f0-9-]+\.pdb/) // Exclude temporary files like pdb_<timestamp>_<uuid>.pdb
    )?.name;

    return NextResponse.json({
      pdbFiles,
      plcExists,
      receptorPdb: receptorPdb ? path.join('/app', folder, receptorPdb) : null,
    });
  } catch (error) {
    console.error('Error in get-plc-files:', error);
    return NextResponse.json({ error: 'Failed to fetch PLC files' }, { status: 500 });
  }
}