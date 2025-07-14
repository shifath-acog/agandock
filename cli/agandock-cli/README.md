# filepath: /home/scripts/cli_app.py

import argparse
import os
from scripts.docking_utils import run_docking_pipeline, process_uploaded_files

def run_docking(folder_name, input_csv):
    # Implement the logic to run the docking pipeline
    # This function should call the run_docking_pipeline function from docking_utils
    print(f"Running docking pipeline with input CSV: {input_csv} in folder: {folder_name}")
    # Here you would gather the necessary parameters and call the function
    # Example:
    # pdb_file, pdbqt_file, config_file, input_type, input_csv, input_smiles = process_uploaded_files(...)
    # run_docking_pipeline(pdb_file, pdbqt_file, config_file, input_type, input_csv, input_smiles)

def run_filter(folder_name, threshold):
    # Implement the logic to run the filtering process
    print(f"Running filter with threshold: {threshold} in folder: {folder_name}")
    # Here you would call the appropriate filtering function from docking_utils
    # Example:
    # extraction_based_on_threshold(folder_name, threshold)

def main():
    parser = argparse.ArgumentParser(description="CLI for docking and filtering operations.")
    subparsers = parser.add_subparsers(dest='command')

    # Subparser for docking
    docking_parser = subparsers.add_parser('run_docking_pipeline', help='Run the docking pipeline')
    docking_parser.add_argument('folder_name', type=str, help='Folder containing input files')
    docking_parser.add_argument('input_csv', type=str, help='CSV file with input data')

    # Subparser for filtering
    filter_parser = subparsers.add_parser('run_filter', help='Run the filtering process')
    filter_parser.add_argument('folder_name', type=str, help='Folder containing input files')
    filter_parser.add_argument('threshold', type=float, help='Threshold for filtering')

    args = parser.parse_args()

    if args.command == 'run_docking_pipeline':
        run_docking(args.folder_name, args.input_csv)
    elif args.command == 'run_filter':
        run_filter(args.folder_name, args.threshold)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()