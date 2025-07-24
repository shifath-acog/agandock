import { NextResponse } from 'next/server';
import { readdir, readFile, access } from 'fs/promises';
import path from 'path';

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const folder = searchParams.get('folder');

  try {
    const baseDir = '/app';
    if (!folder) {
      // List only folders containing output.csv
      const dirs = await readdir(baseDir, { withFileTypes: true });
      const folders = [];
      for (const dir of dirs) {
        if (dir.isDirectory()) {
          const outputCsvPath = path.join(baseDir, dir.name, 'output.csv');
          try {
            await access(outputCsvPath);
            folders.push(dir.name);
          } catch {
            // Skip folders without output.csv
          }
        }
      }
      return NextResponse.json({ folders });
    }

    const folderPath = path.join(baseDir, folder);
    const outputCsvPath = path.join(folderPath, 'output.csv');
    let outputWithPbCsv = '';

    // Check if output_with_pb.csv exists
    try {
      await access(path.join(folderPath, 'output_with_pb.csv'));
      outputWithPbCsv = await readFile(path.join(folderPath, 'output_with_pb.csv'), 'utf-8');
    } catch {
      console.warn(`output_with_pb.csv not found in ${folder}`);
    }

    let outputCsv = '';
    try {
      outputCsv = await readFile(outputCsvPath, 'utf-8');
    } catch {
      return NextResponse.json({ error: `Output CSV not found in ${folder}` }, { status: 404 });
    }

    return NextResponse.json({ outputCsv, outputWithPbCsv });
  } catch (error) {
    console.error('Error in get-experiments:', error);
    return NextResponse.json({ error: 'Failed to fetch experiments' }, { status: 500 });
  }
}