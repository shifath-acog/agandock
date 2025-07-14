#!/bin/bash

folder_name="$1"
input_pdbqt="$folder_name/pipeline_files/3_pdbqt"

output_smi="$folder_name/pipeline_files/4_smiles"
mkdir -p "$output_smi"

# Convert PDBQT to SMILES in batches of 20000
batch_num=1
batch_size=20000
pdbqt_files=("$input_pdbqt"/*.pdbqt)
total_files="${#pdbqt_files[@]}"
for (( i=0; i<total_files; i+=batch_size )); do
    batch_files=("${pdbqt_files[@]:i:batch_size}")
    obabel "${batch_files[@]}" -ipdbqt -osmi -O "$output_smi"/.smi -m > /dev/null 2>&1
    ((batch_num++))
done


echo -e "\033[1m\033[34mPDBQT to SMILES conversion completed and files saved in folder: \033[91m$output_smi\033[0m" >&1
