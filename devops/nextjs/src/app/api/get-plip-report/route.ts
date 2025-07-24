 import { NextResponse } from 'next/server';
import { readFile } from 'fs/promises';
import path from 'path';

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const folder = searchParams.get('folder');
  const pdb = searchParams.get('pdb');

  if (!folder || !pdb) {
    return NextResponse.json({ error: 'Folder and PDB parameters are required' }, { status: 400 });
  }

  try {
    const reportPath = path.join('/app', folder, 'plc', `report_${pdb.replace('.pdb', '')}.json`);
    const reportContent = await readFile(reportPath, 'utf-8');
    const report = JSON.parse(reportContent);
    return NextResponse.json({ interactions: report.interactions || [] });
  } catch (error) {
    console.error('Error fetching PLIP report:', error);
    return NextResponse.json({ interactions: [] }, { status: 200 });
  }
}