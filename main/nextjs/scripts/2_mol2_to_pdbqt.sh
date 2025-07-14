#!/bin/bash

folder_name="$1"
input_mol2="$folder_name/pipeline_files/2_mol2_format"

output_pdbqt="$folder_name/pipeline_files/3_pdbqt"

mkdir -p "$output_pdbqt"

for file in "$input_mol2"/*.mol2; do
    filename=$(basename -- "$file")
    filename_no_ext="${filename%.*}"
    obabel "$file" -opdbqt -O "$output_pdbqt/$filename_no_ext.pdbqt" > /dev/null 2>&1
done

echo -e "\033[1m\033[34mMOL2 to PDBQT conversion completed and files saved in folder: \033[91m$output_pdbqt\033[0m" >&1
