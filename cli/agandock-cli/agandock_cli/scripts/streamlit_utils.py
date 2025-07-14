import os
from agandock_cli.scripts.docking_utils import run_docking_pipeline
from agandock_cli.scripts.docking_utils import handle_posebusters

def run_docking(folder_name, pdb_file, pdbqt_file, config_file, input_type, input_csv, input_smiles):
    print("Running docking pipeline...")
    results = run_docking_pipeline(pdb_file, pdbqt_file, config_file, input_type, input_csv, input_smiles, folder_name)
    print("Docking pipeline completed.")
    return results

def run_filter(folder_name, lower_range, higher_range, pdb_file):
    print("Running filtration...")
    handle_posebusters(folder_name, lower_range, higher_range, pdb_file)
    print("Filtration completed.")