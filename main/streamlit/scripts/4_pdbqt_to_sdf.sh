#!/bin/bash

folder_name="$1"
input_pdbqt="$folder_name/pipeline_files/8_pdbqt_out_threshold_m1"

output_mol2="$folder_name/pipeline_files/9_mol2_out"
output_sdf="$folder_name/pipeline_files/9_sdf_out"

mkdir -p "$output_mol2"
mkdir -p "$output_sdf"

for file in "$input_pdbqt"/*.pdbqt; do
    filename=$(basename -- "$file")
    filename_no_ext="${filename%.*}"
    obabel "$file" -ipdbqt -omol2 -O "$output_mol2/$filename_no_ext.mol2" > /dev/null 2>&1
done

for file in "$output_mol2"/*.mol2; do
    filename=$(basename -- "$file")
    filename_no_ext="${filename%.*}"
    obabel "$file" -imol2 -Osdf -O "$output_sdf/$filename_no_ext.sdf" > /dev/null 2>&1
done

echo -e "\033[1m\033[34mPDBQT to SDF conversion completed and files saved in folder: \033[91m$output_sdf\033[0m" >&1
