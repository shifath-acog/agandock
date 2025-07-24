import { NextResponse } from 'next/server';
import { exec } from 'child_process';
import { promisify } from 'util';
import { readdir } from 'fs/promises';
import path from 'path';

const execAsync = promisify(exec);

export async function POST(request: Request) {
  try {
    const { folder_name, lower_range, higher_range, use_pb_filtered_ligands } = await request.json();
    if (!folder_name) {
      return NextResponse.json({ error: 'Folder name is required' }, { status: 400 });
    }

    const baseDir = '/app';
    const folderPath = path.join(baseDir, folder_name);
    const fullFolderPath = folderPath;

    // Find the PDB file
    const files = await readdir(folderPath);
    const pdbFile = files.find((file) => file.endsWith('.pdb'));
    if (!pdbFile) {
      return NextResponse.json({ error: 'No PDB file found in experiment folder' }, { status: 400 });
    }
    const pdbFilePath = path.join(folderPath, pdbFile);

    // Construct CLI command
    let cliCommand = `agandock run_plip "${fullFolderPath}" --pdb_file "${pdbFilePath}"`;
    if (use_pb_filtered_ligands) {
      cliCommand += ' --use_pb_filtered_ligands';
    }
    if (typeof lower_range === 'number' && typeof higher_range === 'number') {
      cliCommand += ` --lower_range ${lower_range} --higher_range ${higher_range}`;
    }
    console.log('Executing run_plip command:', cliCommand);

    // Execute CLI command
    const { stdout, stderr } = await execAsync(cliCommand, { cwd: '/app' });
    console.log('run_plip stdout:', stdout);
    if (stderr) console.error('run_plip stderr:', stderr);

    const outputPlipDir = path.join(folderPath, 'output_plip_files');
    return NextResponse.json({ outputPlipDir });
  } catch (error) {
    console.error('Error in run-plip:', error);
    const errorMessage = error instanceof Error ? error.message : 'Failed to run PLIP analysis';
    return NextResponse.json({ error: errorMessage }, { status: 500 });
  }
}