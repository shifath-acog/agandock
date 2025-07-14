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
import streamlit as st
import concurrent.futures
import ipywidgets as widgets
import multiprocessing as mp
import streamlit_shadcn_ui as ui

from glob import glob
from typing import Optional, List
from IPython.display import Audio, display
from rdkit import Chem
from rdkit.Chem import AllChem, DataStructs, Draw
from rdkit.Chem.Draw import rdMolDraw2D
from io import BytesIO, StringIO
from scripts.docking_utils import *
from openbabel import openbabel, pybel
from multiprocessing import Pool, cpu_count
from st_aggrid import AgGrid, GridOptionsBuilder
from concurrent.futures import ThreadPoolExecutor
from rdkit.Chem import AllChem, Descriptors, Draw 

try:
    from protonator import protonator
    has_protonator = True
except ImportError:
    protonator, has_protonator = None, False




##############################################################################################################################
""" Check GPU Availability """

def check_availability():
    if "CUDA_VISIBLE_DEVICES" not in os.environ:
        os.environ["CUDA_VISIBLE_DEVICES"] = "0"

    if torch.cuda.is_available():
        device = torch.device("cuda")
        gpu_info = os.popen('nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits').readlines()
        gpu_available = 100 - int(gpu_info[0].strip())
        gpu_result = f"\033[1m\033[34mGPU availability: \033[91m{gpu_available:.2f}%\033[0m"
    else:
        device = torch.device("cpu")
        gpu_result = 'GPU is not available, using CPU instead'

    cpu_percentage = psutil.cpu_percent()
    cpu_available = 100 - cpu_percentage
    cpu_result = f"\033[1m\033[34mCPU availability: \033[91m{cpu_available:.2f}%\033[0m"
    
    print(gpu_result)
    print(cpu_result)
    return device



##############################################################################################################################
""" Remove Salt Compounds """

def process_smiles_csv(folder_name, input_csv):
    input_smiles = input_csv if os.path.isabs(input_csv) else os.path.join(folder_name, input_csv)
    if not os.path.exists(input_smiles):
        raise FileNotFoundError(f"File not found: {input_smiles}")

    df = pd.read_csv(input_smiles)
    # st.markdown(f'<p style="font-size:16px; color:#887b56;">Total compounds loaded: <span style="color: #4973f2; font-size: 20px;"><b>{len(df)}</b></span></p>', unsafe_allow_html=True)

    df_salt = df[df['SMILES'].str.contains('\.')]
    # st.markdown(f'<p style="font-size:16px; color:#887b56;">Salts removed: <span style="color: #4973f2; font-size: 20px;"><b>{len(df_salt)}</b></span></p>', unsafe_allow_html=True)

    df_salt.to_csv(f'{folder_name}/salted_compounds.csv', index=False)

    df_no_salt = df[~df['SMILES'].str.contains('\.')]
    
    def atom_count(smiles):
        try:
            mol = Chem.MolFromSmiles(smiles)
            return mol.GetNumAtoms() if mol else 0
        except:
            return 0

    df_no_salt = df_no_salt[df_no_salt['SMILES'].apply(atom_count) <= 50]
    
    return df_no_salt


##############################################################################################################################
""" Convert SMILES to SDF """

def read_smi_file(filename: str, i_from: int, i_to: int) -> List[Chem.Mol]:
    mol_list = []
    with open(filename, 'r') as smiles_file:
        for i, line in enumerate(smiles_file):
            if i_from <= i < i_to:
                tokens = line.split()
                smiles = tokens[0]
                mol_list.append(Chem.MolFromSmiles(smiles))
    return mol_list


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
        st.write(f"Error processing molecule: {e}")
        return None

def molecules_to_structure(population: List[Chem.Mol], num_conformations: int, index: int, num_cpus: int):
    with mp.Pool(num_cpus) as pool:
        args = [(p, num_conformations, index) for p in population]
        generated_molecules = pool.starmap(get_structure, args)

        names = [''.join(random.choices(string.ascii_uppercase + string.digits, k=6)) for _ in generated_molecules]
        return generated_molecules, names


def molecule_to_sdf(mol: Chem.Mol, output_filename: str, name: Optional[str] = None):
    if name is not None:
        mol.SetProp("_Name", name)
    writer = Chem.SDWriter(output_filename)
    writer.write(mol)
    writer.close()



##############################################################################################################################
""" Convert SMILES to SDF """

def read_smi_file(filename: str, i_from: int, i_to: int) -> List[Chem.Mol]:
    mol_list = []
    with open(filename, 'r') as smiles_file:
        for i, line in enumerate(smiles_file):
            if i_from <= i < i_to:
                tokens = line.split()
                smiles = tokens[0]
                mol_list.append(Chem.MolFromSmiles(smiles))
    return mol_list


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
        st.write(f"Error processing molecule: {e}")
        return None

def molecules_to_structure(population: List[Chem.Mol], num_conformations: int, index: int, num_cpus: int):
    with mp.Pool(num_cpus) as pool:
        args = [(p, num_conformations, index) for p in population]
        generated_molecules = pool.starmap(get_structure, args)

        names = [''.join(random.choices(string.ascii_uppercase + string.digits, k=6)) for _ in generated_molecules]
        return generated_molecules, names


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


##############################################################################################################################
""" Format Mol2 Files """

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
            atom_type = mol2_content[i][8:10].strip()  # Capture up to three characters for atom type
            if len(atom_type) == 2 and not atom_type[1].isdigit():
                atom_type = atom_type.capitalize()  # Ensure standard representation (e.g., Cl, Na)
            if atom_type not in atom_counts:
                atom_counts[atom_type] = 1
            else:
                atom_counts[atom_type] += 1

            atom_number = str(atom_counts[atom_type])
            new_atom = f"{atom_type}{atom_number}"
            mol2_content[i] = f"{mol2_content[i][:8]}{new_atom:<4}{mol2_content[i][11:]}"  # Keep alignment consistent

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

    print(f"\033[1m\033[34mMOL2 files formatted and saved in folder: \033[91m{output_mol2}\033[0m")
    


##############################################################################################################################
""" Pass Correct PDBQT files for Docking """

def check_pdbqt_files(folder_name, input_csv):
    input_smiles = os.path.join(folder_name, input_csv)

    logging.getLogger("rdkit").setLevel(logging.ERROR)

    def process_smiles_files(input_smiles_files):
        output_file = os.path.join(folder_name, "pipeline_files/smiles.txt")
        
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

    df1 = pd.read_csv(input_smiles)
    df1 = df1.sort_values(by='Name').reset_index(drop=True)

    input_smiles_files = os.path.join(folder_name, "pipeline_files/4_smiles")
    df2 = process_smiles_files(input_smiles_files)
    df2 = df2.sort_values(by='Name').reset_index(drop=True)

    try:
        df3 = pd.merge(df1, df2, on='Name', how='inner')
    except Exception as e:
        raise

    def process_df(folder_name, df3):
        df4 = pd.DataFrame({'Name': df3['Name']})
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

        df4['similarity_score'] = df3.apply(calculate_similarity, axis=1)

        df4 = df4[df4['similarity_score'] == 1].drop(['similarity_score'], axis=1)

        file_path = os.path.join(folder_name, "pipeline_files/1_compounds_for_docking.csv")
        df4.to_csv(file_path, index=False)
        return df4

    df4 = process_df(folder_name, df3)


def copy_correct_pdbqt_files(folder_name, input_csv):

    input_smiles = os.path.join(folder_name, input_csv)
    
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


def copy_correct_pdbqt_file(folder_name, input_csv):

    input_smiles = os.path.join(folder_name, input_csv)
    
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
        input_file_path = os.path.join(all_pdbqt_files, "1.pdbqt")
        output_file_path = os.path.join(output_dir, f"{compound_name}.pdbqt")

        if os.path.exists(input_file_path):
            shutil.copy(input_file_path, output_file_path)

    print(f"\033[1m\033[34mCompounds filtered out using Dice Similarity: \033[91m{filtered_out}\033[0m")


##############################################################################################################################
""" Create a ligands paths text file """

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




##############################################################################################################################
""" Extract Affinity Values """

def affinity_from_pdbqt_files(folder_name):
    ligands_pdbqt_out = os.path.join(folder_name, "pipeline_files/6_pdbqt_out")
    results = []
    for filename in os.listdir(ligands_pdbqt_out):
        file_path = os.path.join(ligands_pdbqt_out, filename)

        if os.path.isfile(file_path) and filename.endswith(".pdbqt"):
            with open(file_path, 'r') as file:
                lines = file.readlines()
                affinity_line = lines[1]
                affinity_value = float(affinity_line.split()[3])
                name = filename.replace('_out.pdbqt', '')
                results.append({'Name': name, 'Affinity': affinity_value})

    output_file = os.path.join(folder_name, 'pipeline_files/2_extract_affinity_from_pdbqt.csv')
    with open(output_file, 'w', newline='') as csv_file:
        fieldnames = ['Name', 'Affinity']
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"\033[1m\033[34mAffnity values extracted and saved in folder: \033[91m{output_file}\033[0m")




#############################################################################################################################
""" Extract Compounds Based on Affinity threshold """

def extraction_based_on_threshold(folder_name, threshold, factor):
    source_dir = os.path.join(folder_name, "pipeline_files/6_pdbqt_out")
    affinity_score_path = os.path.join(folder_name, "pipeline_files/2_extract_affinity_from_pdbqt.csv")

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

    print("\033[1m\033[34mCompounds Extracted based on threshold value\033[0m".format(output_file_path))



#############################################################################################################################
""" Extracted Model 1 content """

def copy_content(file_path, output_folder):
    with open(file_path, 'r') as file:
        content = file.read()
        endmdl_index = content.find("ENDMDL")
        endmdl_content = content[:endmdl_index + len("ENDMDL")]
        output_file_path = os.path.join(output_folder, os.path.basename(file_path))
        with open(output_file_path, 'w') as output_file:
            output_file.write(endmdl_content)
        

def extract_model1(folder_name):
    # input_folder = os.path.join(folder_name, "pipeline_files/7_pdbqt_out_threshold")
    input_folder = os.path.join(folder_name, "pipeline_files/6_pdbqt_out")
    output_folder = os.path.join(folder_name, "pipeline_files/8_pdbqt_out_threshold_m1")
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for file_name in os.listdir(input_folder):
        file_path = os.path.join(input_folder, file_name)
        if os.path.isfile(file_path) and file_name.endswith(".pdbqt"):
            copy_content(file_path, output_folder)

    print(f"\033[1m\033[34mExtracted Model_1 content and saved in folder: \033[91m{output_folder}\033[0m")



##############################################################################################################################
""" Process PoseBusters Output file """

def process_pb_csv(folder_name):
    pb_result = os.path.join(folder_name, 'pipeline_files', '4_pb_out.csv')
    pb = pd.read_csv(pb_result)
    pb = pb.drop('file', axis=1)
    pb = pb.drop(pb.index[1::2])
    pb = pb.rename(columns={'molecule': 'Name'})
    pb['passes'] = pb.iloc[:, 1:].eq('True').sum(axis=1)
    pb.to_csv(os.path.join(folder_name, 'pipeline_files', '5_pb_out.csv'), index=False)


# def final_output(folder_name, input_csv, passes):

#     def show_step_completed(message):
#         """Displays a step completed indicator."""
#         st.markdown(
#             f"""
#             <div style="display: flex; align-items: center; margin-top: 10px;">
#                 <div style="width: 20px; height: 20px; background-color: green; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-right: 10px;">
#                     <span style="color: white; font-size: 16px;">✓</span>
#                 </div>
#                 <span>{message}</span>
#             </div>
#             """, unsafe_allow_html=True
#         )

#     input_smiles = os.path.join(folder_name, input_csv)
    
#     posebusters_path = os.path.join(folder_name, 'pipeline_files', '5_pb_out.csv')
#     df = pd.read_csv(posebusters_path)
    
#     df1 = df[df['passes'] >= passes]

#     affinity_path = os.path.join(folder_name, 'pipeline_files', '2_extract_affinity_from_pdbqt.csv')
#     df2 = pd.read_csv(affinity_path)
#     df2 = df2.sort_values(by='Affinity').reset_index(drop=True)

#     df_temp = pd.merge(df1, df2, on='Name', how='left')

#     df3 = pd.read_csv(input_smiles)

#     df4 = pd.merge(df_temp, df3, on='Name', how='left')
#     df4 = df4[['Name', 'SMILES', 'Affinity']]
#     df4 = df4.sort_values(by='Affinity').reset_index(drop=True)

#     def count_all_heavy_atoms(smiles):
#         mol = Chem.MolFromSmiles(smiles)
#         if mol is None:
#             return None
#         return sum(1 for atom in mol.GetAtoms() if atom.GetAtomicNum() != 1)

#     df4['HeavyAtoms'] = df4['SMILES'].apply(count_all_heavy_atoms)
#     df4['Efficiency'] = df4['Affinity'] / df4['HeavyAtoms']
#     df4['Efficiency'] = df4['Efficiency'].round(3)
#     df4 = df4.drop(columns=['HeavyAtoms'])
    
#     output_csv_path = os.path.join(folder_name, "output.csv")
#     df4.to_csv(output_csv_path, index=False)
#     if os.path.exists(output_csv_path):
#         output_df = pd.read_csv(output_csv_path)
#         ui.table(data=output_df, maxHeight=300)

#         csv_data = output_df.to_csv(index=False).replace('\n', '%0A').replace(',', '%2C')
#         st.markdown(f"""
#             <div style="text-align: left; margin-top: -10px; margin-bottom: 15px;">
#                 <a href="data:text/csv;charset=utf-8,{csv_data}" download="docking_result.csv" 
#                    style="background-color: #f28e8c; color: white; text-decoration: none; padding: 10px 15px; border-radius: 10px; font-size: 14px;">
#                     Download CSV
#                 </a>
#             </div>
#         """, unsafe_allow_html=True)
#     else:
#         st.warning("The output.csv file could not be found.")

#     filtered_count = len(df) - len(df1)
#     print(f"\033[1m\033[34mCompounds filtered out by PoseBusters: \033[91m{filtered_count}\033[0m")

def generate_structure_image(smiles):
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    img = Draw.MolToImage(mol, size=(200, 100))
    buffered = BytesIO()
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

# def generate_scrollable_html_table(filtered_df):
#     """
#     Generates an HTML scrollable table for displaying in Streamlit with custom styling.
#     """
#     styled_df = filtered_df.style \
#                            .set_table_styles([
#                                {'selector': 'thead th', 
#                                 'props': [('background-color', '#6a8f6b'),  
#                                           ('color', '#FFFFFF'), 
#                                           ('font-size', '14px'), 
#                                           ('text-align', 'center')]}
#                            ]) \
#                            .apply(lambda row: ['background-color: #FFFFFF; color: black;'  # Light color for all rows
#                                                 for _ in row], axis=1) \
#                            .set_properties(**{'font-size': '14px', 'text-align': 'center', 'background-color': '#FFFFFF', 'color': 'black'})

#     # Convert the styled DataFrame to HTML with scrollable table
#     styled_df_html = styled_df.to_html(index=False, escape=False)
#     scrollable_table_html = (
#         f"<div style='display: flex; justify-content: center; margin-top: 0px; margin-bottom: 0px;'>"
#         f"<div style='max-height: 500px; overflow-y: scroll; width: auto; border: 0px solid #6a8f6b; margin: 0; padding: 0; box-sizing: border-box;'>"
#         f"<table style='border-collapse: collapse; width: 100%; table-layout: fixed; background-color: #FFFFFF; margin: 0; padding: 0;'>"
#         f"<style>"
#         f"  .col0 {{ text-align: center; }}"
#         f"  .col1 {{ text-align: left; }}"
#         f"  .col2 {{ text-align: center; }}"
#         f"  .col3 {{ text-align: center; }}"
#         f"  .col4 {{ text-align: center; }}"
#         f"  .col5 {{ text-align: center; }}"
#         f"  table {{ margin: 0; padding: 0; }}"
#         f"  tbody {{ margin: 0; padding: 0; box-sizing: border-box; }}"
#         f"  tr, td {{ margin: 0; padding: 0; border: none; }}"
#         f"</style>"
#         f"<colgroup>"
#         f"  <col style='width: 35px;'> <!-- Fix index column width -->"
#         f"  <col style='width: 100px;'> <!-- Fix Name column width -->"
#         f"  <col style='width: 300px;'> <!-- Fix SMILES column width -->"
#         f"  <col style='width: 200px;'> <!-- Fix Chemical structure column width -->"
#         f"  <col style='width: 100px;'> <!-- Fix Docking score column width -->"
#         f"  <col style='width: 100px;'> <!-- Fix Ligand efficiency column width -->"
#         f"</colgroup>"
#         f"<thead style='position: sticky; top: 0; background-color: #6a8f6b; color: white; text-align: center; z-index: 1;'>"
#         f"{styled_df_html.split('<thead>', 1)[1].split('</thead>', 1)[0]}"
#         f"</thead>"
#         f"<tbody style='background-color: #FFFFFF; word-wrap: break-word; margin: 0; padding: 0; box-sizing: border-box;'>"
#         f"{styled_df_html.split('<tbody>', 1)[1]}</tbody>"
#         f"</table>"
#         f"</div>"
#         f"</div>"
#     )
#     return scrollable_table_html

def generate_table_html(filtered_df):
    """
    Generate HTML for a sortable table with customizable columns and specified widths.
    """
    column_widths = {
        "Index": "35px",
        "Name": "100px",        
        "SMILES": "300px",
        "Chemical structure": "200px",
        "Docking score": "100px",
        "Ligand efficiency": "100px",
    }

    colgroup_html = (
        f'<col style="width: {column_widths.get("Index", "100px")};">'
        + ''.join(
            f'<col style="width: {column_widths.get(col, "100px")};">' for col in filtered_df
        )
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
                        {''.join(f'<th>{col}</th>' for col in filtered_df)}
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
    # File paths
    input_smiles = os.path.join(folder_name, input_csv)
    affinity_path = os.path.join(folder_name, 'pipeline_files', '2_extract_affinity_from_pdbqt.csv')

    # Data processing
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
    df3[numeric_columns] = df3[numeric_columns].applymap(lambda x: f'{x:.2f}')
    df3 = add_chemical_structure_column(df3)
    df3 = df3[['Name', 'SMILES', 'Chemical structure', 'Affinity', 'Efficiency']]
    df3 = df3.rename(columns={'Affinity': 'Docking score (kcal/mol)', 'Efficiency': 'Ligand efficiency'})

    # Generate the scrollable HTML table and display it
    # scrollable_table_html = generate_scrollable_html_table(df3)
    # st.markdown(scrollable_table_html, unsafe_allow_html=True)
    scrollable_table_html = generate_table_html(df3)
    st.components.v1.html(scrollable_table_html, height=500, scrolling=True)

    # Prepare CSV for download
    download_csv = df3[['Name', 'SMILES', 'Docking score (kcal/mol)', 'Ligand efficiency']]
    download_csv.to_csv(os.path.join(folder_name, 'output.csv'), index=False)
    csv_data = download_csv.to_csv(index=False).encode('utf-8')
    b64 = base64.b64encode(csv_data).decode()
    st.markdown(
        f"<div style='text-align: left; margin-top: 20px; margin-buttom: 20px;'>"
        f"<a href='data:file/csv;base64,{b64}' download='docking_score.csv' "
        f"style='background-color: #d8a788; color: black; text-decoration: none; padding: 10px 20px; border-radius: 5px; font-size: 14px;'>"
        f"Download (.csv)</a>"
        f"</div>",
        unsafe_allow_html=True,
    )



def extraction_based_on_threshold_for_pb(folder_name, lower_range, higher_range):
    st.write("")
    st.write("")
    st.write("")
    source_dir = os.path.join(folder_name, "pipeline_files/9_sdf_out")
    affinity_score_path = os.path.join(folder_name, "pipeline_files/2_extract_affinity_from_pdbqt.csv")

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
        

import os
import pandas as pd
import base64
import streamlit as st

def final_output_with_pb(folder_name, passes):
    # Load PoseBusters data
    posebusters_path = os.path.join(folder_name, 'pipeline_files', '5_pb_out.csv')
    df1 = pd.read_csv(posebusters_path).query('passes >= @passes')

    df2 = pd.read_csv(os.path.join(folder_name, "output.csv"))
    df3 = pd.merge(df1, df2, on='Name', how='left')[['Name', 'SMILES', 'Docking score (kcal/mol)', 'Ligand efficiency']]
    df3.to_csv(os.path.join(folder_name, 'output_with_pb.csv'), index=False)

    df4 = pd.read_csv(os.path.join(folder_name, "pipeline_files/3_compounds_for_posebusters.csv"))

    df5 = pd.merge(df4[['Name']], df1[['Name']], on='Name', how='inner')
    df5 = pd.merge(df5, df2, on='Name', how='left')[['Name', 'SMILES', 'Docking score (kcal/mol)', 'Ligand efficiency']]

    df6 = pd.merge(df4[['Name']], df2, on='Name', how='left')
    df6 = df6[~df6['Name'].isin(df5['Name'])][['Name', 'SMILES', 'Docking score (kcal/mol)', 'Ligand efficiency']]
    df6 = df6.reset_index(drop=True)
    df6.to_csv(os.path.join(folder_name, 'output_without_pb.csv'), index=False)

    df6_count = len(df6)
    st.markdown(f"""<p style="margin-top: 0px; font-size:16px; color:#887b56;
                             ">Compounds filtered out by Posebusters: <span style="color: #4973f2;  
                              font-size: 20px;"><b>{df6_count}</b></span></p>""", unsafe_allow_html=True)

    st.markdown('<p style="margin-bottom: 10px; margin-left: 0px; font-size: 15px; font-weight: bold; color: #593c22;">Compounds which pass PoseBusters filtration.</p>', unsafe_allow_html=True)

    df3.index += 1
    df3 = add_chemical_structure_column(df3)
    numeric_columns = df3.select_dtypes(include='float').columns
    df3[numeric_columns] = df3[numeric_columns].applymap(lambda x: f'{x:.2f}')
    df3 = df3[['Name', 'SMILES', 'Chemical structure', 'Docking score (kcal/mol)', 'Ligand efficiency']]
    
    scrollable_table_html = generate_table_html(df3)
    st.components.v1.html(scrollable_table_html, height=300, scrolling=True)

    # Prepare download link for CSV
    csv_data = df3.to_csv(index=False).encode('utf-8')
    b64 = base64.b64encode(csv_data).decode()
    st.markdown(
        f"<div style='text-align: left; margin-top: 20px; margin-bottom: 20px;'>"
        f"<a href='data:file/csv;base64,{b64}' download='output_with_pb.csv' "
        f"style='background-color: #d8a788; color: black; text-decoration: none; padding: 10px 20px; border-radius: 5px; font-size: 14px;'>"
        f"Download (.csv)</a>"
        f"</div>",
        unsafe_allow_html=True,
    )

    # Create an expander for the compounds that failed PoseBusters filtration
    with st.expander("Analysis of compounds which failed PoseBusters"):
        st.markdown('<p style="margin-bottom: 10px; margin-left: 0px; font-size: 15px; font-weight: bold; color: #593c22;">Compounds which fail PoseBusters filtration.</p>', unsafe_allow_html=True)
        
        df6.index += 1
        df6 = add_chemical_structure_column(df6)
        numeric_columns = df6.select_dtypes(include='float').columns
        df6[numeric_columns] = df6[numeric_columns].applymap(lambda x: f'{x:.2f}')
        df6 = df6[['Name', 'SMILES', 'Chemical structure', 'Docking score (kcal/mol)', 'Ligand efficiency']]
        
        # scrollable_table_html = generate_scrollable_html_table(df6)
        # st.markdown(scrollable_table_html, unsafe_allow_html=True)
        scrollable_table_html = generate_table_html(df6)
        st.components.v1.html(scrollable_table_html, height=200, scrolling=True)

        csv_data = df6.to_csv(index=False).encode('utf-8')
        b64 = base64.b64encode(csv_data).decode()
        st.markdown(
            f"<div style='text-align: left; margin-top: 20px; margin-bottom: 20px;'>"
            f"<a href='data:file/csv;base64,{b64}' download='output_with_pb.csv' "
            f"style='background-color: #d8a788; color: black; text-decoration: none; padding: 10px 20px; border-radius: 5px; font-size: 14px;'>"
            f"Download (.csv)</a>"
            f"</div>",
            unsafe_allow_html=True,
        )




# def final_output_with_pb(folder_name, passes):
#     posebusters_path = os.path.join(folder_name, 'pipeline_files', '5_pb_out.csv')
#     df1 = pd.read_csv(posebusters_path).query('passes >= @passes')

#     df2 = pd.read_csv(os.path.join(folder_name, "output.csv"))
#     df3 = pd.merge(df1, df2, on='Name', how='left')[['Name', 'SMILES', 'Docking score (kcal/mol)', 'Ligand efficiency']]
#     output_with_pb_path = os.path.join(folder_name, 'output_with_pb.csv')
#     df3.to_csv(output_with_pb_path, index=False)

#     df4 = pd.read_csv(os.path.join(folder_name, "pipeline_files/3_compounds_for_posebusters.csv"))
#     df5 = pd.merge(df4, df2, on='Name', how='left')[['Name', 'SMILES', 'Docking score (kcal/mol)', 'Ligand efficiency']]
#     output_without_pb_path = os.path.join(folder_name, 'output_without_pb.csv')
#     df5.to_csv(output_without_pb_path, index=False)

#     st.write(f"Compounds filtered out by PB are: {len(df5) - len(df1)}")

#     col1, col2 = st.columns(2)

#     with col1:
#         st.markdown("### Compounds which pass PoseBusters filtration")
#         st.dataframe(df3)
#         st.download_button(
#             label="Download CSV",
#             data=df3.to_csv(index=False).encode('utf-8'),
#             file_name="output_with_pb.csv",
#             mime="text/csv"
#         )

#     with col2:
#         st.markdown("### Compounds which fail PoseBusters filtration")
#         st.dataframe(df_without_pb)
#         st.download_button(
#             label="Download CSV",
#             data=df_without_pb.to_csv(index=False).encode('utf-8'),
#             file_name="output_without_pb.csv",
#             mime="text/csv"
#         )


##############################################################################################################################
""" Form Protein ligand complexes for PLIP analysis """

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

    # zip_file_name = f'{os.path.basename(folder_name)}_protein_ligands_pdb_files.zip'
    # zip_file_path = os.path.join(folder_name, zip_file_name)
    # with zipfile.ZipFile(zip_file_path, 'w') as zip_ref:
    #     for root, _, files in os.walk(selective_pdbqt_files_dir):
    #         for file in files:
    #             file_path = os.path.join(root, file)
    #             zip_ref.write(file_path, os.path.relpath(file_path, selective_pdbqt_files_dir))
                
    # shutil.rmtree(selective_pdbqt_files_dir)
    # print(f"\033[1m\033[34m Protein_Ligands PDB files zipped to: \033[91m{zip_file_path}\033[0m")




##############################################################################################################################
""" Process SDF file """

def process_sdf_file(sdf_file_path):
    supplier = Chem.SDMolSupplier(sdf_file_path)

    for mol in supplier:
        if mol is not None:
            if mol.GetNumConformers() > 0:
                conf = mol.GetConformer()
                for atom in mol.GetAtoms():
                    pos = conf.GetAtomPosition(atom.GetIdx())
                    print(f"Atom {atom.GetIdx()}: {pos.x}, {pos.y}, {pos.z}")

                img_size = (500, 500)  
                img = Draw.MolToImage(mol, size=img_size)
                img.show()
