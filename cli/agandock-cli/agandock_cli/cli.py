import argparse
import os
from agandock_cli.scripts.docking_utils import run_docking_pipeline, handle_posebusters

def main():
    parser = argparse.ArgumentParser(description="CLI for docking and filtration.")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Subparser for docking
    docking_parser = subparsers.add_parser('run_docking', help='Run the docking pipeline')
    docking_parser.add_argument('folder_name', type=str, help='Folder to save results')
    docking_parser.add_argument('--pdb_file', type=str, required=True, help='Path to the PDB file')
    docking_parser.add_argument('--pdbqt_file', type=str, required=True, help='Path to the PDBQT file')
    docking_parser.add_argument('--config_file', type=str, required=True, help='Path to the config file')
    docking_parser.add_argument('--input_type', type=str, required=True, choices=["Multiple SMILES", "Single SMILES"], help='Type of input (e.g., Multiple SMILES, Single SMILES)')
    docking_parser.add_argument('--input_csv', type=str, help='Path to the input CSV file for SMILES (required if input_type is Multiple SMILES)')
    docking_parser.add_argument('--input_smiles', type=str, help='Single SMILES string (required if input_type is Single SMILES)')

    # Subparser for filtering
    filter_parser = subparsers.add_parser('run_filter', help='Run the filtration process')
    filter_parser.add_argument('folder_name', type=str, help='Folder containing results to filter')
    filter_parser.add_argument('lower_range', type=float, help='Lower affinity threshold')
    filter_parser.add_argument('higher_range', type=float, help='Higher affinity threshold')
    filter_parser.add_argument('--pdb_file', type=str, required=True, help='Path to the PDB file (for PoseBusters)')

    args = parser.parse_args()

    if args.command == 'run_docking':
        if args.input_type == "Multiple SMILES" and not args.input_csv:
            parser.error("--input_csv is required when --input_type is Multiple SMILES")
        if args.input_type == "Single SMILES" and not args.input_smiles:
            parser.error("--input_smiles is required when --input_type is Single SMILES")

        # Convert relative paths to absolute paths
        pdb_file = os.path.abspath(args.pdb_file)
        pdbqt_file = os.path.abspath(args.pdbqt_file)
        config_file = os.path.abspath(args.config_file)
        input_csv = os.path.abspath(args.input_csv) if args.input_csv else None
        folder_name = os.path.abspath(args.folder_name)

        print(f"Running docking pipeline for folder: {folder_name}")
        run_docking_pipeline(pdb_file, pdbqt_file, config_file, args.input_type, input_csv, args.input_smiles, folder_name)
        print("Docking pipeline completed.")
    elif args.command == 'run_filter':
        folder_name = os.path.abspath(args.folder_name)
        pdb_file = os.path.abspath(args.pdb_file)
        print(f"Running filtration for folder: {folder_name} with range: {args.lower_range} to {args.higher_range}")
        handle_posebusters(folder_name, args.lower_range, args.higher_range, pdb_file)
        print("Filtration completed.")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()