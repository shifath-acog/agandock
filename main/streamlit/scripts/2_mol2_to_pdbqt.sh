#!/bin/bash

folder_name="$1"
input_mol2="$folder_name/pipeline_files/2_mol2_format"

output_pdbqt="$folder_name/pipeline_files/3_pdbqt"

mkdir -p "$output_pdbqt"


# Convert to PDBQT in batches of 20000
batch_num=1
batch_size=20000
mol2_files=("$input_mol2"/*.mol2)
total_files="${#mol2_files[@]}"
for (( i=0; i<total_files; i+=batch_size )); do
    batch_files=("${mol2_files[@]:i:batch_size}")
    obabel "${batch_files[@]}" -opdbqt -O "$output_pdbqt"/.pdbqt -m > /dev/null 2>&1
    ((batch_num++))
done


echo -e "\033[1m\033[34mMOL2 to PDBQT conversion completed and files saved in folder: \033[91m$output_pdbqt\033[0m" >&1
