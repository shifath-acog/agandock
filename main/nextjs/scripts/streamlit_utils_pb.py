import os
import time
import pytz
import base64
import subprocess
import pandas as pd
import streamlit as st
import z_docking_files.docking_setup as setup

from io import BytesIO
from datetime import datetime
from z_docking_files.docking_utils import *

def get_logo_base64(logo_path):
    """Encode logo as base64 for embedding in HTML."""
    with open(logo_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def add_header_and_footer(logo_base64):
    """Adds custom header with animated subtitle, GitHub link button, and footer to the app."""
    header_css = f'''
    <style>
        [data-testid="stAppViewContainer"] {{
            padding: 0;
        }}
        [data-testid="stHeader"] {{
            display: none; /* Remove default Streamlit header */
        }}
        @keyframes popIn {{
            0% {{
                opacity: 0;
                transform: scale(0.5);
            }}
            100% {{
                opacity: 1;
                transform: scale(1);
            }}
        }}
        .custom-header {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            background: linear-gradient(to right, #EDF4F2 100%, #EDF4F2 0%);
            padding: 5px 10px;
            z-index: 1000;
            display: flex;
            align-items: center;
            height: 80px; /* Increased height for subtitle */
        }}
        .custom-header img {{
            height: 40px;
            margin-left: 10px;
        }}
        .custom-header .title {{
            font-family: "Times New Roman", serif;
            font-size: 20px;
            font-weight: bold;
            color: #8a1111;
            position: absolute;
            left: 680px; /* Adjust position of title */
            margin: 0;
            margin-top: -10px;
        }}
        .custom-header .subtitle {{
            font-family: "Times New Roman", serif; /* Consistent font */
            font-size: 14px; /* Smaller font size */
            color: #005f8e; /* Subtitle in gray for contrast */
            position: absolute;
            left: 550px; /* Adjust position of subtitle */
            margin: 0;
            margin-top: 35px;
            display: flex; /* Flex for word-by-word animation */
            gap: 5px; /* Space between words */
        }}
        .custom-header .subtitle span {{
            opacity: 0; /* Initially invisible */
            animation: popIn 0.5s ease-out forwards; /* Animation for each word */
        }}
        .custom-header .github-button {{
            position: absolute;
            top: 25px;
            right: 20px;
            z-index: 1100;
        }}
        /* Assign incremental delays to ensure sequential animation */
        .custom-header .subtitle span:nth-child(1) {{
            animation-delay: 0s;
        }}
        .custom-header .subtitle span:nth-child(2) {{
            animation-delay: 0.1s;
        }}
        .custom-header .subtitle span:nth-child(3) {{
            animation-delay: 0.2s;
        }}
        .custom-header .subtitle span:nth-child(4) {{
            animation-delay: 0.3s;
        }}
        .custom-header .subtitle span:nth-child(5) {{
            animation-delay: 0.4s;
        }}
        .custom-header .subtitle span:nth-child(6) {{
            animation-delay: 0.5s;
        }}
        .custom-header .subtitle span:nth-child(7) {{
            animation-delay: 0.6s;
        }}
        .custom-header .subtitle span:nth-child(8) {{
            animation-delay: 0.7s;
        }}
        .custom-footer {{
            position: fixed;
            bottom: 0;
            left: 0;
            width: 100%;
            background: linear-gradient(to right, #31473A, #31473A); /* Blue footer background */
            color: white;
            text-align: center;
            padding: 8px 0;
            font-size: 14px;
            z-index: 1000;
        }}
    </style>
    <div class="custom-header">
        <img src="data:image/svg+xml;base64,{logo_base64}" alt="Logo" />
        <div class="title">AganDock</div>
        <div class="subtitle">
            <span>A</span>
            <span>virtual</span>
            <span>screening</span>
            <span>pipeline</span>
            <span>for</span>
            <span>ultra-large</span>
            <span>chemical</span>
            <span>libraries</span>
        </div>
        <div class="github-button">
            <a href="https://www.aganitha.ai/solutions/virtual-screening/" target="_blank"
               style="background-color: #31473A; color: white; text-decoration: none; 
                      border: none; border-radius: 10px; padding: 8px 10px; font-size: 14px;">
                More information
            </a>
        </div>
    </div>
    <div class="custom-footer">
        Confidential and Proprietary. Copyright © 2017-24 Aganitha
    </div>
    '''
    st.markdown(header_css, unsafe_allow_html=True)



def add_file_uploader_css():
    """Applies custom styling for the file uploader."""
    css = '''
    <style>
        [data-testid='stFileUploader'] {
            width: max-content;
        }
        [data-testid='stFileUploader'] section {
            padding: 0;
            float: left;
        }
        [data-testid='stFileUploader'] section > input + div {
            display: none;
        }
        [data-testid='stFileUploader'] section + div {
            float: right;
            padding-top: 0;
        }
    </style>
    '''
    st.markdown(css, unsafe_allow_html=True)

def preprocess_csv(input_csv):
    """Preprocess the uploaded CSV file."""
    csv_data = pd.read_csv(input_csv)
    if "SMILES" not in csv_data.columns:
        st.error("CSV file must contain a 'SMILES' column.")
        st.stop()
    if "Name" not in csv_data.columns:
        csv_data["Name"] = [f"agan{i+1}" for i in range(len(csv_data))]
    return csv_data[["Name", "SMILES"]]

# --------------------------------------
# Docking Pipeline Function
# --------------------------------------

import streamlit as st
import streamlit.components.v1 as components
import time
import os
from datetime import datetime
import pytz


# def generate_progress_table(steps, current_step, apply_posebusters=True):
def generate_progress_table(steps, current_step, apply_posebusters=True):
    if not apply_posebusters:
        steps = steps[:-1]
        
    completed_color = "#4CAF50"  # Green
    pending_color = "#B0B0B0"  # Grey

    circles_html = ""
    labels_html = ""
    for i, step in enumerate(steps):
        color = completed_color if i <= current_step else pending_color
        check_mark = "✓" if i <= current_step else ""

        # Labels for steps
        labels_html += f"""
        <div style="flex: 1; text-align: center; font-size: 12px; color: {'black' if i <= current_step else '#B0B0B0'}; margin-top: 5px;">
            {step}
        </div>
        """

    # Horizontal progress line
    progress_line = f"""
    <div style="position: relative; height: 5px; background-color: {pending_color}; margin: 10px 0; width: 100%;">
        <div style="height: 100%; width: {int((current_step + 1) / len(steps) * 100)}%; background-color: {completed_color};"></div>
    </div>
    """

    return f"""
    {progress_line}
    <div style="display: flex; align-items: center; justify-content: space-between; margin-top: 5px;">
        {labels_html}
    </div>
    """



def run_docking_pipeline(
    pdb_file,
    pdbqt_file,
    config_file,
    input_type,
    input_csv,
    input_smiles,
    threshold,
    factor,
    progress_table_placeholder,
    docking_progress_container,
    steps,
    apply_posebusters,
):
    """Executes the docking pipeline with horizontal progress and step indicators."""
    start_time = time.time()
    india_tz = pytz.timezone("Asia/Kolkata")
    current_time = datetime.now(india_tz)
    folder_name = current_time.strftime("agandock_%Y%m%d_%H%M%S")
    os.makedirs(folder_name, exist_ok=True)

    def update_progress(step_index):
        """Updates the progress table dynamically."""
        html_table = generate_progress_table(steps, step_index, apply_posebusters)
        with progress_table_placeholder:
            components.html(html_table, height=300, scrolling=False)

    # Save uploaded files to local paths
    pdb_file_path = save_uploaded_file(folder_name, pdb_file)
    pdbqt_file_path = save_uploaded_file(folder_name, pdbqt_file)
    config_file_path = save_uploaded_file(folder_name, config_file)

    # Steps for the docking pipeline
    for step_index, step_name in enumerate(steps):
        with docking_progress_container:
            # Show the spinner for each step
            with st.spinner(f"Executing: {step_name}"):
                if step_index == 0:
                    # Step 1: Preprocess Input
                    if input_type == "Multiple SMILES" and input_csv:
                        csv_data = preprocess_csv(input_csv)
                        input_csv_path = os.path.abspath(os.path.join(folder_name, "input_smiles.csv"))
                        csv_data.to_csv(input_csv_path, index=False)
                    elif input_type == "Single SMILES" and input_smiles:
                        input_csv_path = os.path.abspath(os.path.join(folder_name, "input_smiles.csv"))
                        pd.DataFrame({"Name": ["agan1"], "SMILES": [input_smiles]}).to_csv(input_csv_path, index=False)
                    else:
                        st.error("Please provide valid input for either Multiple SMILES or Single SMILES.")
                        st.stop()

                    # After processing input, update the progress table
                    update_progress(step_index)

                elif step_index == 1:
                    # Step 2: Convert SMILES to SDF
                    df_no_salt = process_smiles_csv(folder_name, input_csv_path)
                    convert_smiles_to_sdf_parallel(folder_name, df_no_salt, num_conformations=10)
                    update_progress(step_index)

                elif step_index == 2:
                    # Step 3: Convert SDF to PDBQT
                    subprocess.run(["/bin/bash", "z_docking_files/1_sdf_to_mol2.sh", folder_name],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                    format_mol2_files(folder_name)
                    subprocess.run(["/bin/bash", "z_docking_files/2_mol2_to_pdbqt.sh", folder_name],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                    update_progress(step_index)

                elif step_index == 3:
                    # Step 4: Verify PDBQT Files
                    subprocess.run(["/bin/bash", "z_docking_files/3_pdbqt_to_smiles.sh", folder_name],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                    check_pdbqt_files(folder_name, input_csv_path)
                    if input_type == "Multiple SMILES":
                        copy_correct_pdbqt_files(folder_name, input_csv_path)
                    else:
                        copy_correct_pdbqt_file(folder_name, input_csv_path)
                    update_progress(step_index)

                elif step_index == 4:
                    # Step 5: Perform Docking
                    num_batches = create_ligands_path_batchwise(folder_name)
                    ligand_batches = [f"unidock_pdbqt_batch_{i+1}.txt" for i in range(num_batches)]
                    output_result_base = os.path.abspath(os.path.join(folder_name, "pipeline_files", "6_pdbqt_out"))
                    os.makedirs(output_result_base, exist_ok=True)
                    for i, ligands_batch_file in enumerate(ligand_batches):
                        ligands_path = os.path.join(folder_name, "pipeline_files", ligands_batch_file)
                        batch_output_logs = os.path.abspath(os.path.join(folder_name, "pipeline_files", f"unidock_output_batch_{i+1}.txt"))
                        open(batch_output_logs, 'w').close()
                        unidock_command = (
                            f"unidock "
                            f"--receptor {pdbqt_file_path} "
                            f"--gpu_batch $(cat {ligands_path}) "
                            f"--search_mode detail "
                            f"--scoring vina "
                            f"--config {config_file_path} "
                            f"--dir {output_result_base} "
                            f">> {batch_output_logs} 2>&1"
                        )
                        os.system(unidock_command)

                    # After Docking, continue to next steps
                    affinity_from_pdbqt_files(folder_name)
                    extraction_based_on_threshold(folder_name, threshold, factor)
                    extract_model1(folder_name)
                    subprocess.run(["/bin/bash", "z_docking_files/4_pdbqt_to_sdf.sh", folder_name],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

                    update_progress(step_index)

                elif step_index == 5:
                    st.write("Evaluating step_index 5...")
                    # If PoseBusters is NOT applied, finalize output without PoseBusters
                    if not apply_posebusters:
                        st.write("PoseBusters not applied. Generating final output without PoseBusters.")
                        if input_csv:
                            final_output_without_pb(folder_name, input_csv_path)
                        elif input_smiles:
                            final_output_without_pb(folder_name, input_csv_path)

                        # Update the progress table at this step
                        update_progress(step_index)
                        st.write("step_index 5 executed")
                    else:
                        st.write("Skipping step 5 as PoseBusters is enabled.")

                elif step_index == 6:
                    st.write(f"Step 6 triggered. Apply PoseBusters: {apply_posebusters}")
                    # Step 6: Run PoseBusters Filter (only if selected)
                    if apply_posebusters:
                        st.write("PoseBusters applied. Running PoseBusters step...")
                        
                        # Debugging: Check if script exists
                        script_path = os.path.join("z_docking_files", "5_posebusters_filter.sh")
                        if not os.path.exists(script_path):
                            st.error(f"PoseBusters script not found at: {script_path}")
                            return  # Exit early if script is missing

                        try:
                            # Run PoseBusters script
                            st.write(f"Running PoseBusters script: {script_path}")
                            result = subprocess.run(
                                ["/bin/bash", script_path, folder_name, pdb_file_path],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
                            )
                            if result.returncode != 0:
                                st.error(f"PoseBusters script failed: {result.stderr}")
                                return  # Exit early on failure
                            else:
                                st.write(f"PoseBusters script completed successfully:\n{result.stdout}")
                        except Exception as e:
                            st.error(f"Exception occurred while running PoseBusters: {str(e)}")
                            return  # Exit early on exception

                        # Process PoseBusters CSV
                        st.write("Processing PoseBusters CSV...")
                        process_pb_csv(folder_name)

                        # Generate final output
                        try:
                            if input_csv:
                                st.write("Generating final output with PoseBusters.")
                                final_output(folder_name, input_csv_path, passes=19)
                            elif input_smiles:
                                st.write("Generating final output with PoseBusters.")
                                final_output(folder_name, input_csv_path, passes=0)
                        except Exception as e:
                            st.error(f"Error generating final output: {str(e)}")
                            return  # Exit early on failure

                        # Update the progress table after PoseBusters step
                        update_progress(step_index)
                        st.write("step_index 6 executed")
                    else:
                        st.write("PoseBusters not applied. Skipping step 6.")



    end_time = time.time()
    elapsed_time_minutes = round((end_time - start_time) / 60, 1)

    # Show final success message after pipeline completion
    st.success(f"Docking process completed successfully in {elapsed_time_minutes} minutes.")


def save_uploaded_file(folder, file):
    """Save an uploaded file to a specified folder."""
    file_path = os.path.abspath(os.path.join(folder, file.name))
    with open(file_path, "wb") as f:
        f.write(file.read())
    return file_path