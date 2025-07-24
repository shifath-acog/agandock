import { NextResponse } from 'next/server';
import { readFile } from 'fs/promises';
import path from 'path';

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const filePath = searchParams.get('file');

  if (!filePath) {
    return NextResponse.json({ error: 'File path is required' }, { status: 400 });
  }

  try {
    // Ensure file path is within /app
    const resolvedPath = path.resolve('/app', filePath.replace('/app/', ''));
    if (!resolvedPath.startsWith('/app')) {
      return NextResponse.json({ error: 'Invalid file path' }, { status: 400 });
    }

    const fileContent = await readFile(resolvedPath, 'utf-8');
    return new NextResponse(fileContent, {
      headers: { 'Content-Type': 'text/plain' },
    });
  } catch (error) {
    console.error('Error in get-file:', error);
    return NextResponse.json({ error: 'Failed to fetch file' }, { status: 500 });
  }
}