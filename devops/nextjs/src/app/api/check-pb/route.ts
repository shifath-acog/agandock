import { NextResponse } from 'next/server';
import { access } from 'fs/promises';
import path from 'path';

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const folder = searchParams.get('folder');

  if (!folder) {
    return NextResponse.json({ error: 'Folder name is required' }, { status: 400 });
  }

  try {
    const csvPath = path.join('/app', folder, 'output_with_pb.csv');
    await access(csvPath);
    return NextResponse.json({ exists: true });
  } catch (error) {
    return NextResponse.json({ exists: false });
  }
}