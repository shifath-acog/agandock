#!/bin/bash

folder_name="$1"
input_sdf_dir="$folder_name/pipeline_files/1_sdf"
output_mol2_dir="$folder_name/pipeline_files/2_mol2"

mkdir -p "$output_mol2_dir"

sdf_files=("$input_sdf_dir"/*.sdf)
if [ ! -e "${sdf_files[0]}" ]; then
    echo "Error: No SDF files found in $input_sdf_dir to process." >&2
    exit 1
fi

# Change to the output directory before running obabel
cd "$output_mol2_dir" || { echo "Error: Could not change to directory $output_mol2_dir"; exit 1; }

# Run obabel on all input files, writing output to the current directory
obabel "$input_sdf_dir"/*.sdf -omol2 -m

mol2_file_count=$(find . -maxdepth 1 -type f -name "*.mol2" 2>/dev/null | wc -l)
echo "Found $mol2_file_count generated MOL2 files."

if [ "$mol2_file_count" -eq 0 ]; then
    echo "CRITICAL ERROR: obabel command failed to generate any .mol2 files." >&2
    exit 1
fi

echo -e "\033[1m\033[34mSDF to MOL2 conversion completed and files saved in folder: \033[91m$output_mol2_dir\033[0m" >&1
