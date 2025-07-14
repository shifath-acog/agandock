#!/bin/bash

folder_name="$1"
input_pdbqt="$folder_name/pipeline_files/3_pdbqt"

output_smi="$folder_name/pipeline_files/4_smiles"
mkdir -p "$output_smi"

for file in "$input_pdbqt"/*.pdbqt; do
    filename=$(basename -- "$file")
    filename_no_ext="${filename%.*}"
    obabel "$file" -ipdbqt -osmi -O "$output_smi/$filename_no_ext.smi" > /dev/null 2>&1
done

echo -e "\033[1m\033[34mPDBQT to SMILES conversion completed and files saved in folder: \033[91m$output_smi\033[0m" >&1
