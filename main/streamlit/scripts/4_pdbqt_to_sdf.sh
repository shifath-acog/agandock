#!/bin/bash

folder_name="$1"
input_pdbqt="$folder_name/pipeline_files/8_pdbqt_out_threshold_m1"

output_mol2="$folder_name/pipeline_files/9_mol2_out"
output_sdf="$folder_name/pipeline_files/9_sdf_out"

mkdir -p "$output_mol2"
mkdir -p "$output_sdf"

# Convert PDBQT to MOL2 in batches of 20000
batch_num=1
batch_size=20000
pdbqt_files=("$input_pdbqt"/*.pdbqt)
total_files="${#pdbqt_files[@]}"
for (( i=0; i<total_files; i+=batch_size )); do
    batch_files=("${pdbqt_files[@]:i:batch_size}")
    obabel "${batch_files[@]}" -ipdbqt -omol2 -O "$output_mol2"/.mol2 -m > /dev/null 2>&1
    ((batch_num++))
done

# Convert MOL2 to SDF in batches of 20000
batch_num=1
mol2_files=("$output_mol2"/*.mol2)
total_files="${#mol2_files[@]}"
for (( i=0; i<total_files; i+=batch_size )); do
    batch_files=("${mol2_files[@]:i:batch_size}")
    obabel "${batch_files[@]}" -imol2 -Osdf -O "$output_sdf"/.sdf -m > /dev/null 2>&1
    ((batch_num++))
done


echo -e "\033[1m\033[34mPDBQT to SDF conversion completed and files saved in folder: \033[91m$output_sdf\033[0m" >&1
