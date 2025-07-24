import { NextResponse } from 'next/server';
import { readdir } from 'fs/promises';
import path from 'path';

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const folder_name = searchParams.get('folder');
    if (!folder_name) {
      return NextResponse.json({ error: 'Folder name is required' }, { status: 400 });
    }

    const folderPath = path.join('/app', folder_name);
    const files = await readdir(folderPath);
    const pdbFile = files.find((file) => file.endsWith('.pdb'));
    if (!pdbFile) {
      return NextResponse.json({ error: 'No PDB file found' }, { status: 400 });
    }

    return NextResponse.json({ pdbFile });
  } catch (error) {
    console.error('Error in check-pdb:', error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Failed to check PDB file' },
      { status: 500 }
    );
  }
}