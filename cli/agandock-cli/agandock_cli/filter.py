import os
from agandock_cli.scripts.docking_utils import run_docking_pipeline, handle_posebusters

def run_docking(folder_name, input_csv):
    print(f"Running docking pipeline for folder: {folder_name} with input CSV: {input_csv}")
    results = run_docking_pipeline(folder_name, input_csv)
    print("Docking pipeline completed.")
    return results

def run_filter(folder_name, lower_range, higher_range):
    print(f"Running filtration for folder: {folder_name} with range: {lower_range} to {higher_range}")
    handle_posebusters(folder_name, lower_range, higher_range)
    print("Filtration completed.")