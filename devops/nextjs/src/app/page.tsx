'use client';
import { useState } from 'react';

export default function Home() {
  const [result, setResult] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    const data = Object.fromEntries(formData.entries());

    try {
      const response = await fetch('/api/docking', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });

      const res = await response.json();

      if (response.ok) {
        setResult(res.output);
        setError('');
      } else {
        setError(res.error);
        setResult('');
      }
    } catch (err) {
      setError('An unexpected error occurred.');
      setResult('');
    }
  };

  return (
    <main className="flex min-h-screen flex-col items-center justify-between p-24">
      <div className="z-10 w-full max-w-5xl items-center justify-between font-mono text-sm lg:flex">
        <h1 className="text-4xl font-bold text-center">AGANDOCK</h1>
      </div>

      <form onSubmit={handleSubmit} className="w-full max-w-lg">
        <div className="flex flex-wrap -mx-3 mb-6">
          <div className="w-full px-3">
            <label className="block uppercase tracking-wide text-gray-700 text-xs font-bold mb-2" htmlFor="folder_name">
              Folder Name
            </label>
            <input className="appearance-none block w-full bg-gray-200 text-gray-700 border rounded py-3 px-4 mb-3 leading-tight focus:outline-none focus:bg-white" id="folder_name" name="folder_name" type="text" placeholder="agandock_run" />
          </div>
        </div>

        <div className="flex flex-wrap -mx-3 mb-6">
          <div className="w-full px-3">
            <label className="block uppercase tracking-wide text-gray-700 text-xs font-bold mb-2" htmlFor="pdb_file">
              PDB File
            </label>
            <input className="appearance-none block w-full bg-gray-200 text-gray-700 border rounded py-3 px-4 mb-3 leading-tight focus:outline-none focus:bg-white" id="pdb_file" name="pdb_file" type="text" placeholder="/path/to/protein.pdb" />
          </div>
        </div>

        <div className="flex flex-wrap -mx-3 mb-6">
          <div className="w-full px-3">
            <label className="block uppercase tracking-wide text-gray-700 text-xs font-bold mb-2" htmlFor="pdbqt_file">
              PDBQT File
            </label>
            <input className="appearance-none block w-full bg-gray-200 text-gray-700 border rounded py-3 px-4 mb-3 leading-tight focus:outline-none focus:bg-white" id="pdbqt_file" name="pdbqt_file" type="text" placeholder="/path/to/protein.pdbqt" />
          </div>
        </div>

        <div className="flex flex-wrap -mx-3 mb-6">
          <div className="w-full px-3">
            <label className="block uppercase tracking-wide text-gray-700 text-xs font-bold mb-2" htmlFor="config_file">
              Config File test
            </label>
            <input className="appearance-none block w-full bg-gray-200 text-gray-700 border rounded py-3 px-4 mb-3 leading-tight focus:outline-none focus:bg-white" id="config_file" name="config_file" type="text" placeholder="/path/to/config.txt" />
          </div>
        </div>

        <div className="flex flex-wrap -mx-3 mb-6">
          <div className="w-full px-3">
            <label className="block uppercase tracking-wide text-gray-700 text-xs font-bold mb-2" htmlFor="input_type">
              Input Type
            </label>
            <select className="appearance-none block w-full bg-gray-200 text-gray-700 border rounded py-3 px-4 mb-3 leading-tight focus:outline-none focus:bg-white" id="input_type" name="input_type">
              <option>Single SMILES</option>
              <option>Multiple SMILES</option>
            </select>
          </div>
        </div>

        <div className="flex flex-wrap -mx-3 mb-6">
          <div className="w-full px-3">
            <label className="block uppercase tracking-wide text-gray-700 text-xs font-bold mb-2" htmlFor="input_smiles">
              SMILES
            </label>
            <input className="appearance-none block w-full bg-gray-200 text-gray-700 border rounded py-3 px-4 mb-3 leading-tight focus:outline-none focus:bg-white" id="input_smiles" name="input_smiles" type="text" placeholder="CCO" />
          </div>
        </div>

        <div className="flex flex-wrap -mx-3 mb-6">
          <div className="w-full px-3">
            <label className="block uppercase tracking-wide text-gray-700 text-xs font-bold mb-2" htmlFor="input_csv">
              CSV File
            </label>
            <input className="appearance-none block w-full bg-gray-200 text-gray-700 border rounded py-3 px-4 mb-3 leading-tight focus:outline-none focus:bg-white" id="input_csv" name="input_csv" type="text" placeholder="/path/to/ligands.csv" />
          </div>
        </div>

        <div className="flex items-center justify-between">
          <button className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline" type="submit">
            Run Docking
          </button>
        </div>
      </form>

      {result && (
        <div className="w-full max-w-5xl mt-8">
          <h2 className="text-2xl font-bold mb-4">Results</h2>
          <pre className="bg-gray-100 p-4 rounded-lg">{result}</pre>
        </div>
      )}

      {error && (
        <div className="w-full max-w-5xl mt-8">
          <h2 className="text-2xl font-bold mb-4 text-red-500">Error</h2>
          <pre className="bg-red-100 p-4 rounded-lg text-red-700">{error}</pre>
        </div>
      )}
    </main>
  );
}