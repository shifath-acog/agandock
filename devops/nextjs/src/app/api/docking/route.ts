import { NextRequest, NextResponse } from 'next/server';
import { exec } from 'child_process';

export async function POST(req: NextRequest) {
  const { folder_name, pdb_file, pdbqt_file, config_file, input_type, input_smiles, input_csv } = await req.json();

  let command = `/miniconda/bin/agandock run_docking ${folder_name}`;

  if (pdb_file) command += ` --pdb_file ${pdb_file}`;
  if (pdbqt_file) command += ` --pdbqt_file ${pdbqt_file}`;
  if (config_file) command += ` --config_file ${config_file}`;
  if (input_type) command += ` --input_type "${input_type}"`;
  if (input_smiles) command += ` --input_smiles ${input_smiles}`;
  if (input_csv) command += ` --input_csv ${input_csv}`;

  return new Promise((resolve) => {
    exec(command, (error, stdout, stderr) => {
      if (error) {
        console.error(`exec error: ${error}`);
        resolve(NextResponse.json({ error: stderr }, { status: 500 }));
        return;
      }
      resolve(NextResponse.json({ output: stdout }));
    });
  });
}