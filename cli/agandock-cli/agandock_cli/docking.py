import os
from agandock_cli.scripts.docking_utils import run_docking_pipeline, handle_posebusters

def run_docking(folder_name, pdb_file, pdbqt_file, config_file, input_type, input_csv, input_smiles):
    print(f"Running docking pipeline for folder: {folder_name}")
    run_docking_pipeline(pdb_file, pdbqt_file, config_file, input_type, input_csv, input_smiles, folder_name)

def run_filter(folder_name, lower_range, higher_range, pdb_file):
    print(f"Running filter for folder: {folder_name} with range: {lower_range} to {higher_range}")
    handle_posebusters(folder_name, lower_range, higher_range, pdb_file)