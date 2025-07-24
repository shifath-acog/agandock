import { NextResponse } from 'next/server';
import { exec } from 'child_process';
import { promisify } from 'util';
import { readFile, readdir } from 'fs/promises';
import path from 'path';

const execAsync = promisify(exec);

export async function POST(request: Request) {
  try {
    const { folder_name, lower_range, higher_range } = await request.json();
    if (!folder_name || typeof lower_range !== 'number' || typeof higher_range !== 'number') {
      return NextResponse.json({ error: 'Invalid input parameters' }, { status: 400 });
    }

    const baseDir = '/app';
    const folderPath = path.join(baseDir, folder_name);
    const fullFolderPath = folderPath;

    // Find the PDB file in the experiment folder
    const files = await readdir(folderPath);
    const pdbFile = files.find((file) => file.endsWith('.pdb'));
    if (!pdbFile) {
      return NextResponse.json({ error: 'No PDB file found in experiment folder' }, { status: 400 });
    }
    const pdbFilePath = path.join(folderPath, pdbFile);
    const outputWithPbCsvPath = path.join(folderPath, 'output_with_pb.csv');
    const outputWithoutPbCsvPath = path.join(folderPath, 'output_without_pb.csv');

    // Construct CLI command
    const cliCommand = `agandock run_filter "${fullFolderPath}" ${lower_range} ${higher_range} --pdb_file "${pdbFilePath}"`;
    console.log('Executing run_filter command:', cliCommand);

    // Execute CLI command
    const { stdout, stderr } = await execAsync(cliCommand, { cwd: '/app' });
    console.log('run_filter stdout:', stdout);
    if (stderr) console.error('run_filter stderr:', stderr);

    // Read filtered outputs
    const outputWithPbCsv = await readFile(outputWithPbCsvPath, 'utf-8');
    let outputWithoutPbCsv = '';
    try {
      outputWithoutPbCsv = await readFile(outputWithoutPbCsvPath, 'utf-8');
    } catch (err) {
      console.warn('output_without_pb.csv not found or empty:', err);
      outputWithoutPbCsv = 'Name,SMILES,Docking score (kcal/mol),Ligand efficiency\n'; // Empty CSV header
    }

    return NextResponse.json({ outputWithPbCsv, outputWithoutPbCsv });
  } catch (error) {
    console.error('Error in run-filter:', error);
    const errorMessage = error instanceof Error ? error.message : 'Failed to run filter';
    return NextResponse.json({ error: errorMessage }, { status: 500 });
  }
}