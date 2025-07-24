import { NextResponse } from 'next/server';
import { readdir, readFile } from 'fs/promises';
import path from 'path';

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const folder_name = searchParams.get('folder');
  const csv_file = searchParams.get('csv_file');

  if (!folder_name) {
    return NextResponse.json({ error: 'Folder name is required' }, { status: 400 });
  }

  try {
    const outputPlipDir = path.join('/app', folder_name, 'output_plip_files');
    const files = await readdir(outputPlipDir);
    const csvFiles = files.filter((file) => file.endsWith('.csv')).map((file) => ({
      name: file,
      displayName: file
        .replace('.csv', '')
        .replace(/_/g, ' ')
        .replace(/\b\w/g, (c) => c.toUpperCase()),
    }));

    if (csv_file) {
      const csvPath = path.join(outputPlipDir, csv_file);
      const csvContent = await readFile(csvPath, 'utf-8');
      return NextResponse.json({ csvContent });
    }

    return NextResponse.json({ csvFiles });
  } catch (error) {
    console.error('Error in get-plip-results:', error);
    return NextResponse.json({ error: 'Failed to fetch PLIP results' }, { status: 500 });
  }
}