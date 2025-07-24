export function parseCsv(csvContent: string) {
  const rows = csvContent.trim().split('\n').map((row) => row.split(','));
  const headers = rows[0] || ['Name', 'SMILES', 'Docking score (kcal/mol)', 'Ligand efficiency'];
  const rowData: Record<string, string>[] = rows.slice(1).map((row) =>
    headers.reduce<Record<string, string>>((obj, header, i) => {
      obj[header] = row[i] || '';
      return obj;
    }, {})
  );
  return { headers, rowData };
}

export function getHistogramData(csvContent: string) {
  const { rowData } = parseCsv(csvContent);
  const scores = rowData
    .map((row) => parseFloat(row['Docking score (kcal/mol)']))
    .filter((score) => !isNaN(score));
  
  const minScore = Math.floor(Math.min(...scores));
  const maxScore = Math.ceil(Math.max(...scores));
  const binSize = 2;
  const bins: { range: string; count: number }[] = [];
  
  for (let i = minScore; i < maxScore; i += binSize) {
    const rangeStart = i;
    const rangeEnd = i + binSize;
    const count = scores.filter((score) => score >= rangeStart && score < rangeEnd).length;
    bins.push({ range: `${rangeStart} to ${rangeEnd}`, count });
  }
  
  return bins;
}

export function shouldShowHistogram(csvContent: string) {
  const { rowData } = parseCsv(csvContent);
  return rowData.length > 1;
}