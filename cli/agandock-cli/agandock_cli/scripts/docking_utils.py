import os
import re
import csv
import sys
import time
import math
import torch
import base64
import random
import shutil
import psutil
import string
import logging
import zipfile
import subprocess
import pandas as pd
import concurrent.futures
import multiprocessing as mp

from glob import glob
from typing import Optional, List
from rdkit import Chem
from rdkit.Chem import AllChem, DataStructs, Draw
from io import BytesIO
from openbabel import openbabel, pybel
from multiprocessing import Pool, cpu_count
from concurrent.futures import ThreadPoolExecutor

try:
    from protonator import protonator
    has_protonator = True
except ImportError:
    protonator, has_protonator = None, False

# Suppress RDKit and OpenBabel warnings
stderr = sys.stderr
sys.stderr = open(os.devnull, 'w')
logging.getLogger('openbabel').setLevel(logging.ERROR)
logging.getLogger('pybel').setLevel(logging.ERROR)
logging.getLogger("rdkit").setLevel(logging.ERROR)
sys.stderr = stderr

# Define script base path using environment variable with fallback
SCRIPT_BASE = os.environ.get("AGANDOCK_SCRIPTS", "/home/shifath/AGANDOCK/main/streamlit/scripts")

def check_availability():
    if "CUDA_VISIBLE_DEVICES" not in os.environ:
        os.environ["CUDA_VISIBLE_DEVICES"] = "0"

    if torch.cuda.is_available():
        device = torch.device("cuda")
        gpu_info = os.popen('nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits').readlines()
        gpu_available = 100 - int(gpu_info[0].strip())
        gpu_result = f"\u001b[1m\u001b[34mGPU availability: \u001b[91m{gpu_available:.2f}%\u001b[0m"
    else:
        device = torch.device("cpu")
        gpu_result = 'GPU is not available, using CPU instead'

    cpu_percentage = psutil.cpu_percent()
    cpu_available = 100 - cpu_percentage
    cpu_result = f"\u001b[1m\u001b[34mCPU availability: \u001b[91m{cpu_available:.2f}%\u001b[0m"

    print(gpu_result)
    print(cpu_result)
    return device

def process_smiles_csv(folder_name, input_csv):
    input_smiles = input_csv if os.path.isabs(input_csv) else os.path.join(folder_name, input_csv)
    if not os.path.exists(input_smiles):
        raise FileNotFoundError(f"File not found: {input_smiles}")

    df = pd.read_csv(input_smiles)
    df_salt = df[df['SMILES'].str.contains('\\.')]
    df_salt.to_csv(f'{folder_name}/salted_compounds.csv', index=False)

    df_no_salt = df[~df['SMILES'].str.contains('\\.')]

    def atom_count(smiles):
        try:
            mol = Chem.MolFromSmiles(smiles)
            return mol.GetNumAtoms() if mol else 0
        except:
            return 0

    df_no_salt = df_no_salt[df_no_salt['SMILES'].apply(atom_count) <= 50]

    return df_no_salt

def get_structure(mol: Chem.Mol, num_conformations: int, index: int) -> Optional[Chem.Mol]:
    try:
        if has_protonator:
            mol = protonator(mol)

        mol = Chem.AddHs(mol)
        new_mol = Chem.Mol(mol)

        conformer_energies = []
        AllChem.EmbedMultipleConfs(mol, numConfs=num_conformations, useExpTorsionAnglePrefs=True, useBasicKnowledge=True)
        conformer_energies = AllChem.MMFFOptimizeMoleculeConfs(mol, maxIters=2000, nonBondedThresh=100.0)

        if index == 0:
            i = conformer_energies.index(min(conformer_energies))
        elif index > 0:
            i = index - 1
        else:
            raise ValueError("index cannot be less than zero.")

        new_mol.AddConformer(mol.GetConformer(i))
        return new_mol
    except ValueError as e:
        print(f"Error processing molecule: {e}")
        return None

def molecule_to_sdf(mol: Chem.Mol, output_filename: str, name: Optional[str] = None):
    if name is not None:
        mol.SetProp("_Name", name)
    writer = Chem.SDWriter(output_filename)
    writer.write(mol)
    writer.close()

def process_row(row, output_sdf, num_conformations, idx_conformer):
    smiles, mol_name = row['SMILES'], row['Name']
    mol = Chem.MolFromSmiles(smiles)
    if mol is not None:
        mol = get_structure(mol, num_conformations, idx_conformer)
        if mol is not None:
            sdf_filename = os.path.join(output_sdf, f"{mol_name}.sdf")
            molecule_to_sdf(mol, sdf_filename, name=mol_name)

def convert_smiles_to_sdf_parallel(folder_name, df, num_conformations, idx_conformer=0):
    output_sdf = os.path.join(folder_name, "pipeline_files/1_sdf")
    os.makedirs(os.path.join(folder_name, "pipeline_files", "1_sdf"), exist_ok=True)

    total = len(df)
    max_workers = os.cpu_count()
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(process_row, row, output_sdf, num_conformations, idx_conformer) for _, row in df.iterrows()]

        for future in concurrent.futures.as_completed(futures):
            future.result()

def add_atom_numbers(input_output):
    input_mol2, output_mol2 = input_output
    with open(input_mol2, 'r') as f:
        mol2_content = f.readlines()

    atom_section_index = mol2_content.index('@<TRIPOS>ATOM\n')
    atom_counts = {}

    for i in range(atom_section_index + 1, len(mol2_content)):
        if mol2_content[i].startswith('@<TRIPOS>'):
            break
        else:
            atom_type = mol2_content[i][8:10].strip()
            if len(atom_type) == 2 and not atom_type[1].isdigit():
                atom_type = atom_type.capitalize()
            if atom_type not in atom_counts:
                atom_counts[atom_type] = 1
            else:
                atom_counts[atom_type] += 1

            atom_number = str(atom_counts[atom_type])
            new_atom = f"{atom_type}{atom_number}"
            mol2_content[i] = f"{mol2_content[i][:8]}{new_atom:<4}{mol2_content[i][11:]}"

    with open(output_mol2, 'w') as f:
        f.writelines(mol2_content)

def format_mol2_files(folder_name):
    input_mol2 = os.path.join(folder_name, "pipeline_files/2_mol2")
    output_mol2 = os.path.join(folder_name, "pipeline_files/2_mol2_format")
    os.makedirs(output_mol2, exist_ok=True)

    mol2_files = [file for file in os.listdir(input_mol2) if file.endswith('.mol2')]
    input_output_pairs = [(os.path.join(input_mol2, mol2_file), os.path.join(output_mol2, mol2_file)) for mol2_file in mol2_files]

    with Pool() as pool:
        pool.map(add_atom_numbers, input_output_pairs)

    print(f"\u001b[1m\u001b[34mMOL2 files formatted and saved in folder: \u001b[91m{output_mol2}\u001b[0m")

def process_smiles_files_for_check(input_smiles_files):
    output_file = os.path.join(os.path.dirname(input_smiles_files), "smiles.txt")

    if os.path.exists(output_file):
        os.remove(output_file)

    with open(output_file, 'a') as output:
        for filename in os.listdir(input_smiles_files):
            input_file_path = os.path.join(input_smiles_files, filename)
            if os.path.isfile(input_file_path):
                with open(input_file_path, 'r') as input_file:
                    file_content = input_file.read().strip()
                    output.write(f'{file_content}\n')

    df = pd.read_csv(output_file, header=None, delimiter='\t', names=['obabel_SMILES', 'Name'])
    df = df[['Name', 'obabel_SMILES']]
    return df

def check_pdbqt_files(folder_name, input_csv):
    input_csv_path = os.path.join(folder_name, input_csv)
    df1 = pd.read_csv(input_csv_path)
    df1 = df1.sort_values(by='Name').reset_index(drop=True)

    input_smiles_files = os.path.join(folder_name, "pipeline_files/4_smiles")
    df2 = process_smiles_files_for_check(input_smiles_files)
    df2 = df2.sort_values(by='Name').reset_index(drop=True)

    try:
        df3 = pd.merge(df1, df2, on='Name', how='inner')
    except Exception as e:
        raise

    def process_df_for_check(df3_inner):
        df4 = pd.DataFrame({'Name': df3_inner['Name']})
        df4['similarity_score'] = 0.0

        def calculate_similarity(row):
            try:
                m1 = Chem.MolFromSmiles(row['SMILES'])
                m2 = Chem.MolFromSmiles(row['obabel_SMILES'])

                if m1 is not None and m2 is not None:
                    invgen = AllChem.GetMorganFeatureAtomInvGen()
                    ffpgen = AllChem.GetMorganGenerator(radius=2, atomInvariantsGenerator=invgen)

                    ffp1 = ffpgen.GetSparseCountFingerprint(m1)
                    ffp2 = ffpgen.GetSparseCountFingerprint(m2)

                    similarity_score = DataStructs.DiceSimilarity(ffp1, ffp2)
                    return similarity_score
                else:
                    return None
            except Exception as e:
                return None

        df4['similarity_score'] = df3_inner.apply(calculate_similarity, axis=1)

        df4 = df4[df4['similarity_score'] == 1].drop(['similarity_score'], axis=1)

        file_path = os.path.join(folder_name, "pipeline_files/1_compounds_for_docking.csv")
        df4.to_csv(file_path, index=False)
        return df4

    df4 = process_df_for_check(df3)
    return df4

def copy_correct_pdbqt_files(folder_name, input_csv):
    all_pdbqt_files = os.path.join(folder_name, "pipeline_files/3_pdbqt")
    compounds_to_be_dock = os.path.join(folder_name, "pipeline_files/1_compounds_for_docking.csv")
    output_dir = os.path.join(folder_name, "pipeline_files/5_pdbqt_for_docking")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    smiles_folder = os.path.join(folder_name, "pipeline_files/4_smiles")
    smiles_count = sum(1 for _ in os.scandir(smiles_folder) if _.is_file())

    df1 = pd.read_csv(compounds_to_be_dock)

    filtered_out = smiles_count - len(df1)

    for compound_name in df1['Name']:
        input_file_path = os.path.join(all_pdbqt_files, f"{compound_name}.pdbqt")
        output_file_path = os.path.join(output_dir, f"{compound_name}.pdbqt")

        if os.path.exists(input_file_path):
            shutil.copy(input_file_path, output_file_path)

    print(f"\033[1m\033[34mCompounds filtered out using Dice Similarity: \033[91m{filtered_out}\033[0m")

def create_ligands_path_batchwise(folder_name, batch_size=10):
    output_pdbqt = os.path.join(folder_name, "pipeline_files/5_pdbqt_for_docking")

    def chunk_list(input_list, chunk_size):
        return [input_list[i:i + chunk_size] for i in range(0, len(input_list), chunk_size)]

    def get_pdbqt_files(input_path):
        return [file for file in os.listdir(input_path) if file.endswith(".pdbqt")]

    pdbqt_files = get_pdbqt_files(output_pdbqt)

    ligand_batches = chunk_list(pdbqt_files, batch_size)

    for i, ligand_batch in enumerate(ligand_batches):
        batch_ligands_path = os.path.join(output_pdbqt, "..", f"unidock_pdbqt_batch_{i+1}.txt")
        with open(batch_ligands_path, "w") as batch_file:
            batch_file.write('\n'.join(os.path.join(output_pdbqt, file) for file in ligand_batch))

    batch_files = [f"ligands_batch_{i}.txt" for i in range(len(ligand_batches))]
    return len(batch_files)

def affinity_from_pdbqt_files(folder_name):
    ligands_pdbqt_out = os.path.join(folder_name, "pipeline_files/6_pdbqt_out")
    results = []
    pdbqt_files = [f for f in os.listdir(ligands_pdbqt_out) if f.endswith(".pdbqt")]
    print(f"\u001b[1m\u001b[34mFound {len(pdbqt_files)} PDBQT files in {ligands_pdbqt_out}: {pdbqt_files}\u001b[0m")
    for filename in pdbqt_files:
        file_path = os.path.join(ligands_pdbqt_out, filename)
        with open(file_path, 'r') as file:
            lines = file.readlines()
            if len(lines) < 2:
                print(f"\u001b[1m\u001b[91mWarning: {filename} is empty or has insufficient lines\u001b[0m")
                continue
            affinity_line = lines[1]
            try:
                affinity_value = float(affinity_line.split()[3])
                name = filename.replace('_out.pdbqt', '')
                results.append({'Name': name, 'Affinity': affinity_value})
            except (IndexError, ValueError) as e:
                print(f"\u001b[1m\u001b[91mError processing {filename}: {e}\u001b[0m")
                continue
    if not results:
        print(f"\u001b[1m\u001b[91mNo valid affinity values extracted in {ligands_pdbqt_out}\u001b[0m")
    output_file = os.path.join(folder_name, 'pipeline_files/2_extract_affinity_from_pdbqt.csv')
    with open(output_file, 'w', newline='') as csv_file:
        fieldnames = ['Name', 'Affinity']
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    print(f"\u001b[1m\u001b[34mAffinity values extracted and saved in folder: \u001b[91m{output_file}\u001b[0m")

def extraction_based_on_threshold(folder_name, threshold, factor):
    source_dir = os.path.join(folder_name, "pipeline_files/6_pdbqt_out")
    affinity_score_path = os.path.join(folder_name, 'pipeline_files', '2_extract_affinity_from_pdbqt.csv')

    df = pd.read_csv(affinity_score_path)

    destination_dir = os.path.join(folder_name, "pipeline_files/7_pdbqt_out_threshold")
    os.makedirs(destination_dir, exist_ok=True)

    output_file_path = os.path.join(folder_name, "pipeline_files/3_compounds_for_posebusters.csv")

    if threshold == 'dynamic':
        dynamic_threshold = df['Affinity'].mean() - factor * df['Affinity'].std()
        dynamic = df[df['Affinity'] < dynamic_threshold]
        dynamic.to_csv(output_file_path, index=False)

        for index, row in dynamic.iterrows():
            compound_name = row['Name'].split('_out')[0]
            source_file = os.path.join(source_dir, f"{compound_name}_out.pdbqt")
            destination_file = os.path.join(destination_dir, f"{compound_name}_out.pdbqt")
            shutil.copy(source_file, destination_file)

    elif isinstance(threshold, (float, int)):
        static = df[df['Affinity'] < threshold]
        static.to_csv(output_file_path, index=False)

        for index, row in static.iterrows():
            compound_name = row['Name'].split('_out')[0]
            source_file = os.path.join(source_dir, f"{compound_name}_out.pdbqt")
            destination_file = os.path.join(destination_dir, f"{compound_name}_out.pdbqt")
            shutil.copy(source_file, destination_file)

    print("Compounds Extracted based on threshold value")

def copy_content(file_path, output_folder):
    with open(file_path, 'r') as file:
        content = file.read()
        endmdl_index = content.find("ENDMDL")
        endmdl_content = content[:endmdl_index + len("ENDMDL")]
        output_file_path = os.path.join(output_folder, os.path.basename(file_path))
        with open(output_file_path, 'w') as output_file:
            output_file.write(endmdl_content)

def extract_model1(folder_name):
    input_folder = os.path.join(folder_name, "pipeline_files/6_pdbqt_out")
    output_folder = os.path.join(folder_name, "pipeline_files/8_pdbqt_out_threshold_m1")
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for file_name in os.listdir(input_folder):
        file_path = os.path.join(input_folder, file_name)
        if os.path.isfile(file_path) and file_name.endswith(".pdbqt"):
            copy_content(file_path, output_folder)

    print(f"\u001b[1m\u001b[34mExtracted Model_1 content and saved in folder: \u001b[91m{output_folder}\u001b[0m")

def process_pb_csv(folder_name):
    pb_result = os.path.join(folder_name, 'pipeline_files', '4_pb_out.csv')
    pb = pd.read_csv(pb_result)
    pb = pb.drop('file', axis=1)
    pb = pb.drop(pb.index[1::2])
    pb = pb.rename(columns={'molecule': 'Name'})
    pb['passes'] = pb.iloc[:, 1:].eq('True').sum(axis=1)
    pb.to_csv(os.path.join(folder_name, 'pipeline_files', '5_pb_out.csv'), index=False)

def generate_structure_image(smiles):
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    buffered = BytesIO()
    img = Draw.MolToImage(mol, size=(200, 100))
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return f'<img src="data:image/png;base64,{img_str}"/>'

def add_chemical_structure_column(results):
    results['Chemical structure'] = results['SMILES'].apply(generate_structure_image)
    return results

def count_all_heavy_atoms(smiles):
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    return sum(1 for atom in mol.GetAtoms() if atom.GetAtomicNum() != 1)

def generate_table_html(filtered_df):
    column_widths = {
        "Index": "35px",
        "Name": "100px",
        "SMILES": "300px",
        "Chemical structure": "200px",
        "Docking score": "100px",
        "Ligand efficiency": "100px",
    }

    colgroup_html = f'<col style="width: {column_widths.get("Index", "100px")};">'
    colgroup_html += ''.join(
        f'<col style="width: {column_widths.get(col, "100px")};">' for col in filtered_df.columns
    )

    table_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/tablesort/5.2.1/tablesort.min.js"></script>
        <style>
            th {{
                cursor: pointer;
                background-color: #6a8f6b;
                color: white;
                padding: 8px;
                position: sticky;
                top: 0;
                z-index: 2;
            }}
            td {{
                padding: 8px;
                text-align: center;
                word-wrap: break-word;
                overflow-wrap: break-word;
            }}
            table {{
                border-collapse: collapse;
                width: 100%;
                table-layout: fixed;
                background-color: #FFFFFF;
            }}
            th, td {{
                border: 1px solid #ddd;
            }}
            td:first-child {{
                position: sticky;
                left: 0;
                background-color: #f4f4f4;
                z-index: 1;
            }}
            .table-container {{
                max-height: 500px;
                overflow-y: auto;
            }}
        </style>
    </head>
    <body>
        <div class="table-container">
            <table id="sortable-table">
                <colgroup>
                    {colgroup_html}
                </colgroup>
                <thead>
                    <tr>
                        <th>#</th>
                        {''.join(f'<th>{col}</th>' for col in filtered_df.columns)}
                    </tr>
                </thead>
                <tbody>
                    {''.join(
                        f'<tr><td>{i}</td>' + ''.join(f'<td>{val}</td>' for val in row) + '</tr>'
                        for i, row in enumerate(filtered_df.values, start=1)
                    )}
                </tbody>
            </table>
        </div>
        <script>
            new Tablesort(document.getElementById('sortable-table'));
        </script>
    </body>
    </html>
    """
    return table_html

def final_output_without_pb(folder_name, input_csv, elapsed_time_seconds):
    input_smiles = os.path.join(folder_name, input_csv) if not os.path.isabs(input_csv) else input_csv
    affinity_path = os.path.join(folder_name, 'pipeline_files', '2_extract_affinity_from_pdbqt.csv')

    df1 = pd.read_csv(affinity_path)
    df1 = df1.sort_values(by='Affinity').reset_index(drop=True)

    df2 = pd.read_csv(input_smiles)

    df3 = pd.merge(df1, df2, on='Name', how='left')
    df3 = df3[['Name', 'SMILES', 'Affinity']]
    df3 = df3.sort_values(by='Affinity').reset_index(drop=True)
    df3['HeavyAtoms'] = df3['SMILES'].apply(count_all_heavy_atoms)
    df3['Efficiency'] = df3['Affinity'] / df3['HeavyAtoms']
    df3 = df3.drop(columns=['HeavyAtoms'])
    numeric_columns = df3.select_dtypes(include='float').columns
    df3[numeric_columns] = df3[numeric_columns].apply(lambda s: s.map('{:.2f}'.format))
    df3 = df3.rename(columns={'Affinity': 'Docking score (kcal/mol)', 'Efficiency': 'Ligand efficiency'})

    # Print results to console as a clean table
    print("\n--- Docking Results ---")
    print(df3.to_string(index=False))
    print("---------------------")

    # Save the final CSV file
    output_csv_path = os.path.join(folder_name, 'output.csv')
    df3.to_csv(output_csv_path, index=False)
    print(f"\nResults successfully saved to: {output_csv_path}")

def extraction_based_on_threshold_for_pb(folder_name, lower_range, higher_range):
    print("")
    print("")
    print("")
    source_dir = os.path.join(folder_name, "pipeline_files/9_sdf_out")
    affinity_score_path = os.path.join(folder_name, 'pipeline_files', '2_extract_affinity_from_pdbqt.csv')

    df = pd.read_csv(affinity_score_path)

    destination_dir = os.path.join(folder_name, "pipeline_files/9_sdf_out_threshold")
    if os.path.exists(destination_dir):
        shutil.rmtree(destination_dir)
    os.makedirs(destination_dir)

    output_file_path = os.path.join(folder_name, "pipeline_files/3_compounds_for_posebusters.csv")

    df_range = df[(df['Affinity'] >= lower_range) & (df['Affinity'] <= higher_range)]
    df_range.to_csv(output_file_path, index=False)

    for _, row in df_range.iterrows():
        compound_name = row['Name'].split('_out')[0]
        source_file = os.path.join(source_dir, f"{compound_name}_out.sdf")
        destination_file = os.path.join(destination_dir, f"{compound_name}_out.sdf")
        shutil.copy(source_file, destination_file)

def final_output_with_pb(folder_name, passes):
    posebusters_path = os.path.join(folder_name, 'pipeline_files', '5_pb_out.csv')
    df1 = pd.read_csv(posebusters_path).query('passes >= @passes')

    df2 = pd.read_csv(os.path.join(folder_name, "output.csv"))
    df3 = pd.merge(df1, df2, on='Name', how='left')[['Name', 'SMILES', 'Docking score (kcal/mol)', 'Ligand efficiency']]
    
    output_with_pb_path = os.path.join(folder_name, 'output_with_pb.csv')
    df3.to_csv(output_with_pb_path, index=False)

    df4 = pd.read_csv(os.path.join(folder_name, "pipeline_files/3_compounds_for_posebusters.csv"))

    df5 = pd.merge(df4[['Name']], df1[['Name']], on='Name', how='inner')
    df5 = pd.merge(df5, df2, on='Name', how='left')[['Name', 'SMILES', 'Docking score (kcal/mol)', 'Ligand efficiency']]

    df6 = pd.merge(df4[['Name']], df2, on='Name', how='left')
    df6 = df6[~df6['Name'].isin(df5['Name'])][['Name', 'SMILES', 'Docking score (kcal/mol)', 'Ligand efficiency']]
    df6 = df6.reset_index(drop=True)
    output_without_pb_path = os.path.join(folder_name, 'output_without_pb.csv')
    df6.to_csv(output_without_pb_path, index=False)

    # Format numeric columns
    numeric_cols = df3.select_dtypes(include='float').columns
    df3[numeric_cols] = df3[numeric_cols].apply(lambda s: s.map('{:.2f}'.format))
    numeric_cols_df6 = df6.select_dtypes(include='float').columns
    df6[numeric_cols_df6] = df6[numeric_cols_df6].apply(lambda s: s.map('{:.2f}'.format))

    print(f"\n--- PoseBusters Filtered Results ---")
    print(f"Compounds that PASSED PoseBusters: ({len(df3)})")
    print(df3.to_string(index=False))
    print(f"\nResults saved to: {output_with_pb_path}")
    print("--------------------------------------")

    print(f"\nCompounds that FAILED PoseBusters: ({len(df6)})")
    print(df6.to_string(index=False))
    print(f"\nFailed results saved to: {output_without_pb_path}")
    print("-------------------------------------")

def convert_pdbqt_to_pdb(input_file_path, output_file_path):
    mol = next(pybel.readfile("pdbqt", input_file_path))
    mol.write("pdb", output_file_path, overwrite=True)

def form_protein_ligands_complexes(folder_name, csv_path):
    pdb_file = next(f for f in os.listdir(folder_name) if f.endswith(".pdb"))
    protein_path = os.path.join(folder_name, pdb_file)

    with open(protein_path, 'r') as protein_file:
        atom_lines = [line.strip() for line in protein_file if line.startswith("ATOM")]

    all_pdbqt_files_dir = os.path.join(folder_name, "pipeline_files/8_pdbqt_out_threshold_m1")
    selective_pdbqt_files_dir = os.path.join(folder_name, "plc")
    if not os.path.exists(selective_pdbqt_files_dir):
        os.makedirs(selective_pdbqt_files_dir)

    final_output = pd.read_csv(csv_path)

    for compound_name in final_output['Name']:
        input_file_path = os.path.join(all_pdbqt_files_dir, f"{compound_name}_out.pdbqt")
        output_file_path = os.path.join(selective_pdbqt_files_dir, f"{compound_name}.pdb")

        if os.path.exists(input_file_path):
            convert_pdbqt_to_pdb(input_file_path, output_file_path)

            with open(output_file_path, 'r') as output_file:
                pdb_content = output_file.readlines()
            pdb_atom_lines = [line.replace("ATOM  ", "HETATM", 1) for line in pdb_content if line.startswith("ATOM")]

            with open(output_file_path, 'w') as output_file:
                output_file.write('\n'.join(atom_lines) + '\n')
                output_file.write(''.join(pdb_atom_lines))

def run_script(script_name, folder_name):
    script_path = os.path.join(SCRIPT_BASE, script_name)
    if not os.path.isfile(script_path):
        raise FileNotFoundError(f"Script {script_path} not found")
    print(f"Running script: {script_path} with folder: {folder_name}")
    result = subprocess.run(["/bin/bash", script_path, folder_name],
                            capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error running {script_name}:")
        print(f"STDOUT: {result.stdout}")
        print(f"STDERR: {result.stderr}")
        raise RuntimeError(f"{script_name} failed")
    print(f"{script_name} completed successfully.")

def run_docking_pipeline(pdb_file_path, pdbqt_file_path, config_file_path, input_type, input_csv_path, input_smiles, folder_name):
    os.makedirs(folder_name, exist_ok=True)
    pdb_file_destination = os.path.join(folder_name, os.path.basename(pdb_file_path))
    if not os.path.exists(pdb_file_destination):
        shutil.copy(pdb_file_path, pdb_file_destination)

    if input_type == "Multiple SMILES" and input_csv_path:
        csv_data = pd.read_csv(input_csv_path)
        csv_data = csv_data.dropna()
        if "SMILES" not in csv_data.columns:
            raise ValueError("CSV file must contain a 'SMILES' column.")
        if "Name" not in csv_data.columns:
            csv_data["Name"] = [f"agan{i+1}" for i in range(len(csv_data))]
        input_df = csv_data[["Name", "SMILES"]]
    elif input_type == "Single SMILES" and input_smiles:
        input_df = pd.DataFrame({"Name": ["agan1"], "SMILES": [input_smiles]})
    else:
        raise ValueError("Please provide valid input for either Multiple SMILES or Single SMILES.")

    input_df.to_csv(os.path.join(folder_name, "input_smiles.csv"), index=False)

    df_no_salt = process_smiles_csv(folder_name, "input_smiles.csv")
    convert_smiles_to_sdf_parallel(folder_name, df_no_salt, num_conformations=10)

    run_script("1_sdf_to_mol2.sh", folder_name)
    format_mol2_files(folder_name)
    run_script("2_mol2_to_pdbqt.sh", folder_name)
    run_script("3_pdbqt_to_smiles.sh", folder_name)

    check_pdbqt_files(folder_name, "input_smiles.csv")
    if input_type == "Multiple SMILES":
        copy_correct_pdbqt_files(folder_name, "input_smiles.csv")
    else:
        copy_correct_pdbqt_files(folder_name, "input_smiles.csv")

    num_batches = create_ligands_path_batchwise(folder_name)
    ligand_batches = [f"unidock_pdbqt_batch_{i+1}.txt" for i in range(num_batches)]
    output_result_base = os.path.abspath(os.path.join(folder_name, "pipeline_files", "6_pdbqt_out"))
    os.makedirs(output_result_base, exist_ok=True)
    for i, ligands_batch_file in enumerate(ligand_batches):
        ligands_path = os.path.join(folder_name, "pipeline_files", ligands_batch_file)
        batch_output_logs = os.path.abspath(os.path.join(folder_name, "pipeline_files", f"unidock_output_batch_{i+1}.txt"))
        open(batch_output_logs, 'w').close()
        unidock_command = (
            f"unidock "
            f"--receptor {pdbqt_file_path} "
            f"--gpu_batch $(cat {ligands_path}) "
            f"--search_mode detail "
            f"--scoring vina "
            f"--config {config_file_path} "
            f"--dir {output_result_base} "
            f">> {batch_output_logs} 2>&1"
        )
        print(f"\u001b[1m\u001b[34mExecuting unidock command: {unidock_command}\u001b[0m")
        exit_status = os.system(unidock_command)
        if exit_status != 0:
            print(f"\u001b[1m\u001b[91mError: unidock command failed with exit status {exit_status}. Check {batch_output_logs} for details.\u001b[0m")

    affinity_from_pdbqt_files(folder_name)
    extract_model1(folder_name)
    run_script("4_pdbqt_to_sdf.sh", folder_name)

    final_output_without_pb(folder_name, "input_smiles.csv", 0)

    final_csv = os.path.join(folder_name, 'output.csv')
    form_protein_ligands_complexes(folder_name, final_csv)

def handle_posebusters(folder_name, lower_range, higher_range, pdb_file_path):
    run_script("4_pdbqt_to_sdf.sh", folder_name)
    extraction_based_on_threshold_for_pb(folder_name, lower_range, higher_range)
    script_path = os.path.join(SCRIPT_BASE, "5_posebusters_filter.sh")
    if not os.path.isfile(script_path):
        raise FileNotFoundError(f"Script {script_path} not found")
    subprocess.run(["/bin/bash", script_path, folder_name, pdb_file_path], text=True)
    process_pb_csv(folder_name)
    final_output_with_pb(folder_name, passes=19)  # Assuming a default pass threshold