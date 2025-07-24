import { NextResponse } from 'next/server';
import { exec } from 'child_process';
import { promisify } from 'util';
import { readFile, writeFile, mkdir, unlink } from 'fs/promises';
import path from 'path';

// Promisify exec for async/await
const execAsync = promisify(exec);

// Function to sanitize filenames (replace invalid characters with underscores)
function sanitizeFilename(filename: string): string {
  return filename.replace(/[^a-zA-Z0-9._-]/g, '_');
}

export async function POST(request: Request) {
  const outputDirBase = '/app';
  let command: string = '';
  let folderName: string | null = null;
  const filesToDelete: string[] = [];

  try {
    // Parse form data
    const formData = await request.formData();
    folderName = formData.get('folderName') as string | null;
    const pdbFile = formData.get('pdbFile') as File | null;
    const pdbqtFile = formData.get('pdbqtFile') as File | null;
    const configFile = formData.get('configFile') as File | null;
    const inputType = formData.get('inputType') as 'csv' | 'smiles';
    let inputSmiles = formData.get('inputSmiles') as string | null;
    const inputCsv = formData.get('inputCsv') as File | null;

    // Validate inputs
    if (!folderName || !folderName.match(/^[a-zA-Z0-9_-]+$/)) {
      return NextResponse.json(
        { success: false, error: 'Invalid or missing folderName (must contain only letters, numbers, underscores, or hyphens)' },
        { status: 400 }
      );
    }
    if (!pdbFile || !pdbqtFile || !configFile) {
      return NextResponse.json(
        { success: false, error: 'Missing required files (pdbFile, pdbqtFile, configFile)' },
        { status: 400 }
      );
    }
    if (inputType === 'csv' && !inputCsv) {
      return NextResponse.json(
        { success: false, error: 'Missing inputCsv for csv input type' },
        { status: 400 }
      );
    }
    if (inputType === 'smiles' && (!inputSmiles || inputSmiles.trim() === '')) {
      return NextResponse.json(
        { success: false, error: 'Missing or empty inputSmiles for smiles input type' },
        { status: 400 }
      );
    }

    // Sanitize SMILES string
    if (inputType === 'smiles') {
      inputSmiles = inputSmiles!.trim().replace(/\n/g, '');
      if (!inputSmiles.match(/^[A-Za-z0-9@+\-\[\]\(\)\\\/=]+$/)) {
        return NextResponse.json(
          { success: false, error: 'Invalid SMILES string (use letters, numbers, and valid SMILES characters)' },
          { status: 400 }
        );
      }
    }

    // Construct output directory
    const outputDir = path.join(outputDirBase, folderName);
    await mkdir(outputDir, { recursive: true });

    // Sanitize and save uploaded files with original names
    const pdbFilename = sanitizeFilename(pdbFile.name);
    const pdbqtFilename = sanitizeFilename(pdbqtFile.name);
    const configFilename = sanitizeFilename(configFile.name);
    const pdbPath = path.join(outputDir, pdbFilename);
    const pdbqtPath = path.join(outputDir, pdbqtFilename);
    const configPath = path.join(outputDir, configFilename);
    await writeFile(pdbPath, Buffer.from(await pdbFile.arrayBuffer()));
    await writeFile(pdbqtPath, Buffer.from(await pdbqtFile.arrayBuffer()));
    await writeFile(configPath, Buffer.from(await configFile.arrayBuffer()));
    filesToDelete.push(pdbPath, pdbqtPath, configPath);

    // Handle input type
    let inputArg: string;
    if (inputType === 'csv') {
      const csvFilename = sanitizeFilename(inputCsv!.name);
      const csvPath = path.join(outputDir, csvFilename);
      await writeFile(csvPath, Buffer.from(await inputCsv!.arrayBuffer()));
      inputArg = `--input_csv ${csvPath}`;
      filesToDelete.push(csvPath);
    } else {
      inputArg = `--input_smiles "${inputSmiles!.replace(/"/g, '\\"')}"`;
    }

    // Build and execute CLI command
    command =
      `agandock run_docking ${outputDir} ` +
      `--pdb_file ${pdbPath} ` +
      `--pdbqt_file ${pdbqtPath} ` +
      `--config_file ${configPath} ` +
      `--input_type "${inputType === 'csv' ? 'Multiple SMILES' : 'Single SMILES'}" ` +
      inputArg;

    console.log('Executing command:', command);

    const { stdout, stderr } = await execAsync(command);
    console.log('Docking stdout:', stdout);
    if (stderr) console.error('Docking stderr:', stderr);

    // Read output CSV
    const outputPath = path.join(outputDir, 'output.csv');
    const csvContentOutput = await readFile(outputPath, 'utf-8');

    // Clean up uploaded files (optional, depending on AGandock CLI behavior)
    // await Promise.all(filesToDelete.map((file) => unlink(file).catch(() => null)));

    return NextResponse.json({
      success: true,
      command,
      output: csvContentOutput,
      stderr,
    });
  } catch (error) {
    console.error('Docking error:', error);
    // Clean up files in case of error
    await Promise.all(filesToDelete.map((file) => unlink(file).catch(() => null)));

    return NextResponse.json(
      { success: false, error: error instanceof Error ? error.message : 'Failed to run docking', command },
      { status: 500 }
    );
  }
}