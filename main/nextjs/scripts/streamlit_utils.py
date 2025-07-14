import io
import os
import time
import pytz
import base64
import subprocess
import pandas as pd
import numpy as np
import altair as alt
import seaborn as sns
import streamlit as st
import matplotlib.pyplot as plt
import streamlit.components.v1 as components
import scripts.docking_setup as setup

from io import BytesIO
from py3Dmol import view
from datetime import datetime
from matplotlib.patches import FancyBboxPatch
from scripts.docking_utils import *
from scripts.visualize import *


def add_custom_header_and_footer(header_and_footer_color, logo_image_path, header_background_path, background_image, title, subtitle, more_info_url):
    """Adds custom header with animated subtitle, GitHub link button, and footer to the app."""
    with open(logo_image_path, "rb") as image_file:
        logo_image = base64.b64encode(image_file.read()).decode("utf-8")

    with open(header_background_path, "rb") as image_file:
        header_background = base64.b64encode(image_file.read()).decode()

    with open(background_image, "rb") as image_file:
        background_image = base64.b64encode(image_file.read()).decode()

    st.markdown(
        f"""
        <style>
            .stApp {{
                background: linear-gradient(rgba(255, 255, 255, 0.8), rgba(255, 255, 255, 0.8)), 
                            url(data:image/jpeg;base64,{background_image});
                background-size: cover;
                background-repeat: no-repeat;
                background-attachment: fixed;
                background-blend-mode: lighten; /* Optional: Adjust blend mode */
            }}
        </style>
        """,
        unsafe_allow_html=True
    )

    header_css = f'''
    <style>
        [data-testid="stAppViewContainer"] {{
            padding: 0;
        }}
        [data-testid="stHeader"] {{
            display: none; /* Remove default Streamlit header */
        }}
        @keyframes popIn {{
            0% {{ opacity: 0; transform: scale(0.5); }}
            100% {{ opacity: 1; transform: scale(1); }}
        }}
        
        .custom-header {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            background: linear-gradient(to right, rgba(255, 255, 255, 0.95), rgba(255, 255, 255, 0.9), rgba(255, 255, 255, 0.0)),
                        url(data:image/jpeg;base64,{header_background}) no-repeat center;
            background-size: cover;
            box-shadow: 0px 4px 15px rgba(0, 0, 0, 0.2);
            padding: 5px 10px;
            z-index: 1000;
            display: flex;
            align-items: center;
            height: 80px; /* Height for the header */
        }}

        .custom-header .center-content {{
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            flex: 1;
            text-align: center;
        }}

        .custom-header .title {{
            font-family: "Times New Roman", serif;
            font-size: 25px;
            font-weight: bold;
            color: {header_and_footer_color};
            margin: 0;
        }}
        
        .custom-header .subtitle {{
            font-family: "Times New Roman", serif;
            font-size: 16px;
            color: {header_and_footer_color};
            margin: 0;
            display: flex;
            gap: 5px;
        }}

        .custom-header img {{
            height: 40px;
            margin-left: 9px;
        }}


        .custom-footer {{
            position: fixed;
            bottom: 0;
            left: 0;
            width: 100%;
            background: {header_and_footer_color};
            color: white;
            text-align: center;
            padding: 8px 0;
            font-size: 14px;
            z-index: 1000;
        }}
    </style>
    <div class="custom-header">
        <img src="data:image/svg+xml;base64,{logo_image}" alt="Logo" />
        <div class="center-content">
            <div class="title">{title}</div>
            <div class="subtitle">{subtitle}</div>
        </div>
        <div class="moreinfo-button">
            <a href="{more_info_url}" target="_blank"
               style="background-color: {header_and_footer_color}; color: white; text-decoration: none; 
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


def add_custom_css():
    """Add consolidated custom CSS for the application."""
    st.markdown(
        """
        <style>
            /* Sidebar styling */
            [data-testid="stSidebar"] {
                width: 260px !important;
                position: fixed !important;
                left: 15px;
                top: 0 !important;
                height: 80vh !important;
                overflow: auto !important;
                background: #dac4b3;
                z-index: 10;
                margin-top: 100px;
                color: #31473A;
                border: 0px solid #31473A;
                box-shadow: 0px 4px 15px rgba(0, 0, 0, 0.2);
                backdrop-filter: blur(5px);
                border-radius: 15px;
                padding: 10px;
            }

            [data-testid="stSidebar"] > div:first-child {
                margin-top: -80px !important;
            }

            [data-testid="stAppViewContainer"] {
                margin-left: 260px !important;
                padding: 1rem;
                width: calc(100% - 260px) !important;
            }

            [data-testid="stSidebar"] {
                overflow-x: hidden !important;
            }

            [data-testid="stSidebar"] {
                overflow-y: hidden !important;
            }

            .block-container {
                padding: 2.5rem 2rem;
                max-width: 100% !important;
            }
    
            div[data-testid="stTabs"] hr {
                display: none !important; /* Hide horizontal line if present */
            }
    
            /* Default styling for all tabs */
            div[data-testid="stTabs"] button {
                background-color: #d4d7dc; /* Tab background color */
                color: black; /* Tab text color */
                font-size: 22px; /* Increase font size */
                padding: 10px 15px; /* Add padding for better appearance */
                border: none; /* Remove default border */
                border-radius: 15px 15px 0px 0px; /* Round top corners only */
                transition: background-color 0.3s ease; /* Smooth transition */
            }
    
            /* Styling for hovered tabs */
            div[data-testid="stTabs"] button:hover {
                background-color: #d4d7dc; /* Background color on hover */
                color: black; /* Hover text color */
            }
    
            /* Styling for the active (selected) tab */
            div[data-testid="stTabs"] button[aria-selected="true"] {
                background-color: #6a8f6b !important; /* Active tab background color */
                color: white !important; /* Active tab text color */
            }
    
            /* Ensure container styling remains consistent */
            div[data-testid="stTabs"] {
                margin-top: 12px !important;
                margin-left: 0 !important;
                margin-right: 0 !important;
                width: 100% !important;
            }

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

            /* File uploader styling */
            div[data-testid="stFileUploader"] {
                div div {display: none !important;}
                label {color: blue !important;}
                margin-top: 0rem !important;
            }


            
            /* Radio button adjustments */
            div[data-baseweb="radio"] > div {
                gap: 0.5rem !important;
            }

            div[data-testid="stRadio"] > label {
                color: blue !important;
                font-size: 1rem !important;
                margin-top: 1rem !important;
                margin-bottom: 0.0rem !important;
            }

            /* SMILES input styling */
            div[data-testid="stTextInput"] {
                margin-top: -1.6rem !important; /* Reduce gap for SMILES input */
                width: 100% !important; /* Reduce width of the text input container */
            }

            input[type="text"] {
                width: 100% !important;
            }

            /* Button styling */
            div.stButton > button {
                background-color: #dac4b3 !important;
                color: black !important;
                padding: 8px 20px !important;
                border-radius: 10px !important;
                font-size: 18px !important;
                border: 0px solid #282d56 !important;
                box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.2) !important;
                cursor: pointer !important;
                transition: all 0.2s ease-in-out;
            }

            div.stButton > button:hover {
                background-color: #d8a788 !important;
                color: black !important;
                box-shadow: 0px 6px 8px rgba(0, 0, 0, 0.3) !important;
            }

            /* Custom CSS for the download button */
            .download-button {
                background-color: #dac4b3; 
                color: black; 
                text-decoration: none; 
                padding: 10px 20px; 
                border-radius: 5px; 
                font-size: 14px; 
                transition: background-color 0.3s ease;
            }
            .download-button:visited {
                color: black; /* Ensure visited links stay black */
            }
            .download-button:hover {
                background-color: #d8a788; 
                color: white; 
                text-decoration: none; /* Prevent underline on hover */
            }

            /* Custom container to reduce spacing */
            div[data-testid="stNumberInput"] {
                margin-top: -10px !important; /* Negative margin to reduce space above input */
                margin-bottom: 0 !important; /* Remove extra space below input */
                padding: 0 !important; /* Remove default padding */
            }
    
            /* Style the label directly */
            .custom-label {
                font-size: 14px;
                color: #8e5572;
                margin-left: 3px !important;
                margin-bottom: -25px !important; /* Negative margin to pull label closer to input */
            }
    
            /* Style the number input box */
            div[data-testid="stNumberInput"] input[type="number"] {
                width: 80px !important; /* Compact width for the input field */
                margin: 0 !important; /* Remove extra margins */
            }

        </style>
        """,
        unsafe_allow_html=True,
    )
    

def setup_header_and_footer():
    """Set up the custom header, footer, and styles for the app."""
    header_and_footer_color = "#3f4022"
    logo_image_path = "scripts/aganitha-logo.svg"
    header_background_path = "scripts/header_background.png"
    background_image = "scripts/back_ground.jpg"
    title = "AganDock"
    subtitle = "A virtual screening pipeline for ultra-large chemical libraries"
    more_info_url = "https://www.aganitha.ai/solutions/virtual-screening/"

    add_custom_header_and_footer(
        header_and_footer_color, logo_image_path, header_background_path,
        background_image, title, subtitle, more_info_url
    )
    add_custom_css()


def handle_sidebar_inputs():
    # Upload target protein
    uploaded_files = st.sidebar.file_uploader(
        "Upload target protein",
        type=["pdb", "pdbqt"],
        accept_multiple_files=True,
        help="Upload PDB and PDBQT files."
    )

    # Take user inputs for config values
    st.sidebar.markdown(
        '<span style="color: blue; font-size: 0.85rem;">Set pocket center</span>', 
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.sidebar.columns(3)
    center_x = col1.number_input("X-coord", value=126.73, format="%.2f", step=0.01)
    center_y = col2.number_input("Y-coord", value=115.92, format="%.2f", step=0.01)
    center_z = col3.number_input("Z-coord", value=136.18, format="%.2f", step=0.01)

    st.sidebar.markdown(
        '<span style="color: blue; font-size: 0.85rem;">Set box size</span>', 
        unsafe_allow_html=True
    )
    
    col4, col5, col6 = st.sidebar.columns(3)
    size_x = col4.number_input("X-len", value=30.09, format="%.2f", step=0.01)
    size_y = col5.number_input("Y-len", value=23.36, format="%.2f", step=0.01)
    size_z = col6.number_input("Z-len", value=27.08, format="%.2f", step=0.01)

    # Check if all values are provided
    config_ready = all(val is not None for val in [center_x, center_y, center_z, size_x, size_y, size_z])

    config_content = None
    if config_ready:
        config_content = generate_config_file_content(center_x, center_y, center_z, size_x, size_y, size_z)

    pdb_file, pdbqt_file, config_file, statuses = process_uploaded_files(uploaded_files, config_content, config_ready)
    display_upload_summary(statuses)

    # Select ligand input type
    input_type = st.radio(
        "Upload ligands",
        options=["Multiple SMILES", "Single SMILES"],
        help="Provide a CSV file containing SMILES data with a column named 'SMILES,' or enter a single SMILES string."
    )

    input_csv, input_smiles = None, None
    upload_status = {"csv_file": False, "smiles_input": False}

    # Handle file upload or text input
    if input_type == "Multiple SMILES":
        input_csv = st.file_uploader("", type=["csv"], label_visibility="collapsed")
        if input_csv:
            upload_status["csv_file"] = True
            st.markdown('<p style="font-size:14px; color:green;">CSV file uploaded ✅</p>', unsafe_allow_html=True)

    elif input_type == "Single SMILES":
        input_smiles = st.text_input("")
        if input_smiles:
            upload_status["smiles_input"] = True
            st.markdown('<p style="font-size:14px; color:green;">SMILES entered ✅</p>', unsafe_allow_html=True)

    return pdb_file, pdbqt_file, config_file, input_type, input_csv, input_smiles



def generate_config_file_content(center_x, center_y, center_z, size_x, size_y, size_z):
    """Generate config file content from user inputs."""
    return f"""
center_x = {center_x}
center_y = {center_y}
center_z = {center_z}
size_x = {size_x}
size_y = {size_y}
size_z = {size_z}

energy_range = 3
exhaustiveness = 8
num_modes = 9
    """.strip()


def process_uploaded_files(uploaded_files, config_content, config_ready):
    """Process uploaded files and return their statuses."""
    statuses = {
        "pdb_file": False,
        "pdbqt_file": False,
        "config_file": config_ready,  # Only mark as True if all values are provided
    }

    pdb_file, pdbqt_file = None, None
    
    for file in uploaded_files:
        if file.name.endswith(".pdb"):
            pdb_file = file
            statuses["pdb_file"] = True
        elif file.name.endswith(".pdbqt"):
            pdbqt_file = file
            statuses["pdbqt_file"] = True
    
    # Convert config_content to bytes only if all values are provided
    config_file = None
    if config_ready and config_content:
        config_file = io.BytesIO(config_content.encode("utf-8"))
        config_file.name = "config.txt"

    return pdb_file, pdbqt_file, config_file, statuses
    

def display_upload_summary(statuses):
    upload_summary = f"""
        <div style='font-size: 14px; line-height: 1.4;'>
            {'PDB file uploaded ✅' if statuses['pdb_file'] else 'PDB file not uploaded ❌'}<br>
        </div>
    """
    st.markdown(upload_summary, unsafe_allow_html=True)



def display_csv_upload_status(input_csv):
    """Display CSV upload status for Multiple SMILES."""
    csv_status = "CSV File Uploaded ✅" if input_csv else "CSV file not uploaded ❌"
    st.markdown(f"""
        <style>
            .upload-status {{
                font-size: 14px;
                line-height: 1.4;
                margin-bottom: 0px;
            }}
        </style>
        <div class="upload-status">
            {csv_status}
        </div>
    """, unsafe_allow_html=True)

def display_smiles_upload_status(input_smiles):
    """Display CSV upload status for Multiple SMILES."""
    smiles_status = "Single SMILES entered ✅" if input_smiles else "Single SMILES not entered ❌"
    st.markdown(f"""
        <style>
            .upload-status {{
                font-size: 14px;
                line-height: 1.4;
                margin-bottom: 0px;
            }}
        </style>
        <div class="upload-status">
            {smiles_status}
        </div>
    """, unsafe_allow_html=True)


##############################################################################################################################
""" Tab 0: Docking code """

# Function to handle molecular docking
def molecular_docking(pdb_file, pdbqt_file, config_file, input_type, input_csv, input_smiles):
    st.markdown("### Docking Process")
    st.write("Please configure the inputs using the sidebar and run the docking pipeline.")

    steps = [
        "Preprocess Input",
        "Convert SMILES to SDF",
        "Convert SDF to PDBQT",
        "Verify PDBQT Files",
        "Perform Docking",
    ]

    if st.button("Run Docking Pipeline", key="run_docking_pipeline"):
        st.success("Docking pipeline started!")
        # Example function call (replace with actual implementation)
        run_docking_pipeline(pdb_file, pdbqt_file, config_file, input_type, input_csv, input_smiles)

# Function to handle data visualization
def data_visualization():
    st.markdown("### Data Visualization")
    receptor_pdb_file = st.file_uploader("Upload Receptor PDB File", type=["pdb"])

    if receptor_pdb_file and st.button("Show Visualization"):
        st.info("Visualization would be displayed here.")
        # Call visualize_3d_structures() as required

def preprocess_csv(input_csv):
    """Preprocess the uploaded CSV file."""
    csv_data = pd.read_csv(input_csv)
    csv_data = csv_data.dropna()
    if "SMILES" not in csv_data.columns:
        st.error("CSV file must contain a 'SMILES' column.")
        st.stop()
    if "Name" not in csv_data.columns:
        csv_data["Name"] = [f"agan{i+1}" for i in range(len(csv_data))]
    return csv_data[["Name", "SMILES"]]



def generate_progress_table(steps, current_step):
    """Generates HTML for a horizontal progress bar with steps."""
    completed_color = "#4CAF50"  # Green
    pending_color = "#B0B0B0"  # Grey

    circles_html = ""
    labels_html = ""
    for i, step in enumerate(steps):
        color = completed_color if i <= current_step else pending_color
        check_mark = "✓" if i <= current_step else ""

        # Circles for progress
        circles_html += f"""
        <div style="flex: 1; text-align: center;">
            <div style="width: 30px; height: 30px; background-color: {color}; border-radius: 50%; 
                        display: flex; align-items: center; justify-content: center; margin: 0 auto;">
                <span style="color: white; font-size: 16px;">{check_mark}</span>
            </div>
        </div>
        """

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
    <div style="display: flex; align-items: center; justify-content: space-between; margin-top: 20px;">
        {circles_html}
    </div>
    {progress_line}
    <div style="display: flex; align-items: center; justify-content: space-between; margin-top: 5px;">
        {labels_html}
    </div>
    """


def save_uploaded_file(folder, file):
    """Save an uploaded file to a specified folder."""
    file_path = os.path.abspath(os.path.join(folder, file.name))
    with open(file_path, "wb") as f:
        f.write(file.read())
    return file_path

def run_docking_pipeline(pdb_file,
                         pdbqt_file,
                         config_file,
                         input_type,
                         input_csv,
                         input_smiles,
                         progress_table_placeholder,
                         docking_progress_container):
    
    start_time = time.time()
    india_tz = pytz.timezone("Asia/Kolkata")
    current_time = datetime.now(india_tz)
    folder_name = current_time.strftime("agandock_%Y%m%d_%H%M%S")
    os.makedirs(folder_name, exist_ok=True)

    st.markdown("""
        <style>
            #progress-bar {
                position: sticky;
                top: 0; /* Stick to the top of the page */
                background: #f9f9f9; /* Background for the sticky bar */
                padding: 10px 0; /* Add padding for spacing */
                z-index: 1000; /* Ensure it stays on top */
            }
        </style>
    """, unsafe_allow_html=True)

    steps = ["Preprocess Input", "Convert SMILES to SDF", "Convert SDF to PDBQT", "Verify PDBQT Files", "Perform Docking"]
    progress_table_placeholder = st.empty()

    def update_progress(step_index):
        """Updates the progress table dynamically."""
        html_table = generate_progress_table(steps, step_index)
    
        # Clear and update the placeholder with the new HTML
        progress_table_placeholder.empty()  # Clears the placeholder's content
        with progress_table_placeholder:
            components.html(f"""
                <div id="progress-bar">
                    {html_table}
                </div>
            """, height=120, scrolling=True)

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

                    num_rows = pd.read_csv(input_csv_path).shape[0]
                    update_progress(step_index)

                elif step_index == 1:
                    # Step 2: Convert SMILES to SDF
                    df_no_salt = process_smiles_csv(folder_name, input_csv_path)
                    convert_smiles_to_sdf_parallel(folder_name, df_no_salt, num_conformations=10)
                    update_progress(step_index)

                elif step_index == 2:
                    # Step 3: Convert SDF to PDBQT
                    subprocess.run(["/bin/bash", "scripts/1_sdf_to_mol2.sh", folder_name],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                    format_mol2_files(folder_name)
                    subprocess.run(["/bin/bash", "scripts/2_mol2_to_pdbqt.sh", folder_name],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                    update_progress(step_index)

                elif step_index == 3:
                    # Step 4: Verify PDBQT Files
                    subprocess.run(["/bin/bash", "scripts/3_pdbqt_to_smiles.sh", folder_name],
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

                    affinity_from_pdbqt_files(folder_name)
                    extract_model1(folder_name)
                    subprocess.run(["/bin/bash", "scripts/4_pdbqt_to_sdf.sh", folder_name],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                    update_progress(step_index)

                    end_time = time.time()
                    elapsed_time_seconds = round((end_time - start_time), 2)
                    os.makedirs(os.path.join(folder_name, "pipeline_files", "execution_time"), exist_ok=True)
                    file_path = os.path.join(folder_name, "pipeline_files/execution_time/total_execution_time.txt")
                    with open(file_path, "w") as file:
                        file.write(f"{elapsed_time_seconds}")
                    
                    final_output_without_pb(folder_name, input_csv_path, elapsed_time_seconds)

                    final_csv = os.path.join(folder_name, 'output.csv')
                    form_protein_ligands_complexes(folder_name, final_csv)

                    st.markdown(f'<p style="font-size:16px; color:#887b56; margin-top:20px;">Results are saved in <span style="color: #4973f2; font-size: 18px;"><b>{folder_name}</b></span></p>', unsafe_allow_html=True)

    st.write("")
    st.write("")
    st.write("")
    



##############################################################################################################################
""" Tab 1: Data Analysis code """

def load_folder_data(selected_folder):
    """Load data for the selected folder."""
    input_csv_path = os.path.join(selected_folder, "input_smiles.csv")
    df_input = pd.read_csv(input_csv_path)

    salts_csv_path = os.path.join(selected_folder, "salted_compounds.csv")
    df_salt = pd.read_csv(salts_csv_path)

    time_taken_path = os.path.join(selected_folder, "pipeline_files/execution_time/total_execution_time.txt")
    with open(time_taken_path, "r") as file:
        time_taken = file.read().strip()

    pdbqt_in = os.path.join(selected_folder, "pipeline_files/3_pdbqt")
    pdbqt_out = os.path.join(selected_folder, "pipeline_files/5_pdbqt_for_docking")
    num_pdbqt_in = len([f for f in os.listdir(pdbqt_in) if os.path.isfile(os.path.join(pdbqt_in, f))])
    num_pdbqt_out = len([f for f in os.listdir(pdbqt_out) if os.path.isfile(os.path.join(pdbqt_out, f))])

    return df_input, df_salt, time_taken, num_pdbqt_in, num_pdbqt_out


def display_summary(df_input, df_salt, time_taken, num_pdbqt_in, num_pdbqt_out):
    """Display summary of loaded data."""
    st.markdown(f"""
        <p style="font-size:16px; color:#887b56;">Total compounds loaded: <span style="color: #4973f2; font-size: 20px;"><b>{len(df_input)}</b></span></p>
        <p style="font-size:16px; color:#887b56;">Salts removed: <span style="color: #4973f2; font-size: 20px;"><b>{len(df_salt)}</b></span></p>
        <p style="font-size:16px; color:#887b56;">No. of compounds removed in PDBQT verification: <span style="color: #4973f2; font-size: 20px;"><b>{num_pdbqt_in - num_pdbqt_out}</b></span></p>
    """, unsafe_allow_html=True)


def create_histogram(df, time_taken):
    """Create and display a histogram of docking scores."""
    st.markdown(f"""
        <p style="font-size:16px; color:#887b56; margin-top:0px;">Docking process for
        <span style="color: #4973f2; font-size: 20px;"><b>{len(df)}</b></span> compounds completed successfully in
        <span style="color: #4973f2; font-size: 20px;"><b>{time_taken}</b></span> seconds.</p>
        <p style="font-size:18px; color:#593c22; font-weight:bold;">Histogram of Docking Scores</p>
    """, unsafe_allow_html=True)

    docking_scores = df["Docking score (kcal/mol)"]
    bin_edges = list(range(int(docking_scores.min()) - 1, int(docking_scores.max()) + 2))
    bins = pd.cut(docking_scores, bins=bin_edges, right=False, include_lowest=True)
    bin_counts = bins.value_counts().sort_index()

    histogram_data = pd.DataFrame({
        "Range": [f"{int(interval.left)} to {int(interval.right)}" for interval in bin_counts.index],
        "Left": [interval.left for interval in bin_counts.index],
        "Right": [interval.right for interval in bin_counts.index],
        "Count": bin_counts.values
    })

    histogram_data = histogram_data.query("Count > 0").sort_values(by=["Left"]).drop(columns=["Left", "Right"])

    range_order = histogram_data["Range"].tolist()
    max_count = histogram_data["Count"].max()

    bar_width = 30
    chart_width = (len(histogram_data) * bar_width) + 400

    main_chart = alt.Chart(histogram_data).mark_bar(
        size=bar_width, color='#3f4022', cornerRadiusEnd=5
    ).encode(
        x=alt.X("Range:N", title="Docking Score Range", sort=range_order,
                axis=alt.Axis(labelAngle=0, labelFontSize=14, titleFontSize=16)),
        y=alt.Y("Count:Q", title="Count", scale=alt.Scale(domain=[0, max_count * 1.1]),
                axis=alt.Axis(tickCount=max_count, format='d', labelFontSize=14, titleFontSize=16)),
        tooltip=["Range", "Count"]
    ).properties(width=chart_width, height=400)

    text_labels = alt.Chart(histogram_data).mark_text(
        align='center', baseline='bottom', fontSize=14, color='black', dy=-5
    ).encode(
        x=alt.X("Range:N", sort=range_order),
        y=alt.Y("Count:Q"),
        text=alt.Text("Count:Q")
    )

    spacer_chart = alt.Chart(pd.DataFrame({"x": [0]})).mark_bar().encode(
        x=alt.X('x:Q', axis=None), y=alt.Y('x:Q', axis=None)
    ).properties(width= 150, height=400)

    combined_chart = alt.hconcat(spacer_chart, main_chart + text_labels).configure_view(
        strokeOpacity=0
    ).properties(background="transparent")

    st.altair_chart(combined_chart, use_container_width=False)


def select_affinity_range(df):
    """Select affinity range for PoseBusters."""

    st.markdown('<p style="margin-bottom: 10px; margin-left: 0px; font-size: 20px; font-weight: bold; color: #593c22;">Select the Docking Score range to run Posebusters</p>', unsafe_allow_html=True)
    
    min_affinity, max_affinity = df['Docking score (kcal/mol)'].min(), df['Docking score (kcal/mol)'].max()
    col1, _, col2, _ = st.columns([0.12, 0.1, 0.12, 0.66])
    
    with col1:
        st.markdown('<p class="custom-label">Lower threshold</p>', unsafe_allow_html=True)
        lower_range = st.number_input(
            "",
            min_value=min_affinity,
            max_value=max_affinity,
            value=min_affinity,
            step=0.01,
            format="%.2f",
            key="lower_affinity_input"
        )
    with col2:
        st.markdown('<p class="custom-label">Higher threshold</p>', unsafe_allow_html=True)
        higher_range = st.number_input(
            "",
            min_value=min_affinity,
            max_value=max_affinity,
            value=max_affinity,
            step=0.01,
            format="%.2f",
            key="higher_affinity_input"
        )
    
    if lower_range < min_affinity or higher_range > max_affinity:
        st.warning(f"Affinity range must be between {min_affinity} and {max_affinity}.")
        return None, None
    elif lower_range >= higher_range:
        st.warning("Lower range must be less than higher range.")
        return None, None


    df_selected = df[(df['Docking score (kcal/mol)'] >= lower_range) & 
                     (df['Docking score (kcal/mol)'] <= higher_range)]
    selected_count = len(df_selected)

    st.markdown(f"""<p style="margin-top: -10px; font-size:16px; color:#887b56;
                     ">Total compounds selected for PoseBusters filtration: <span style="color: #4973f2;  
                      font-size: 20px;"><b>{selected_count}</b></span></p>""", unsafe_allow_html=True)

    return lower_range, higher_range


def handle_posebusters(selected_folder, df, lower_range, higher_range):
    """Run PoseBusters filtration and process results."""
    with st.spinner(f"Running PoseBusters filtration on selected compounds..."):
        extraction_based_on_threshold_for_pb(selected_folder, lower_range, higher_range)
        script_path = os.path.join("scripts", "5_posebusters_filter.sh")
        pdb_file_path = next((os.path.join(selected_folder, file_name) 
                              for file_name in os.listdir(selected_folder) 
                              if file_name.endswith(".pdb")), None)
        subprocess.run(["/bin/bash", script_path, selected_folder, pdb_file_path],
                       text=True)
        process_pb_csv(selected_folder)
        final_output_with_pb(selected_folder, passes=19)
        st.success("PoseBusters filtration completed successfully.")




##############################################################################################################################
""" Tab 2: PLIP Analysis code """

def create_histogram_for_plip(df, time_taken):
    """Create and display a histogram of docking scores."""
    st.markdown(f"""
        <p style="font-size:18px; color:#006064; font-weight:bold;">Histogram of Docking Scores</p>
    """, unsafe_allow_html=True)

    docking_scores = df["Docking score (kcal/mol)"]
    bin_edges = list(range(int(docking_scores.min()) - 1, int(docking_scores.max()) + 2))
    bins = pd.cut(docking_scores, bins=bin_edges, right=False, include_lowest=True)
    bin_counts = bins.value_counts().sort_index()

    histogram_data = pd.DataFrame({
        "Range": [f"{int(interval.left)} to {int(interval.right)}" for interval in bin_counts.index],
        "Left": [interval.left for interval in bin_counts.index],
        "Right": [interval.right for interval in bin_counts.index],
        "Count": bin_counts.values
    })

    histogram_data = histogram_data.query("Count > 0").sort_values(by=["Left"]).drop(columns=["Left", "Right"])

    range_order = histogram_data["Range"].tolist()
    max_count = histogram_data["Count"].max()

    bar_width = 30
    chart_width = (len(histogram_data) * bar_width) + 400

    main_chart = alt.Chart(histogram_data).mark_bar(
        size=bar_width, color='#006064', cornerRadiusEnd=5
    ).encode(
        x=alt.X("Range:N", title="Docking Score Range", sort=range_order,
                axis=alt.Axis(labelAngle=0, labelFontSize=14, titleFontSize=16)),
        y=alt.Y("Count:Q", title="Count", scale=alt.Scale(domain=[0, max_count * 1.1]),
                axis=alt.Axis(tickCount=max_count, format='d', labelFontSize=14, titleFontSize=16)),
        tooltip=["Range", "Count"]
    ).properties(width=chart_width, height=400)

    text_labels = alt.Chart(histogram_data).mark_text(
        align='center', baseline='bottom', fontSize=14, color='black', dy=-5
    ).encode(
        x=alt.X("Range:N", sort=range_order),
        y=alt.Y("Count:Q"),
        text=alt.Text("Count:Q")
    )

    spacer_chart = alt.Chart(pd.DataFrame({"x": [0]})).mark_bar().encode(
        x=alt.X('x:Q', axis=None), y=alt.Y('x:Q', axis=None)
    ).properties(width= 150, height=400)

    combined_chart = alt.hconcat(spacer_chart, main_chart + text_labels).configure_view(
        strokeOpacity=0
    ).properties(background="transparent")

    st.altair_chart(combined_chart, use_container_width=False)


def select_affinity_range_for_plip(df):
    """Select affinity range for PoseBusters."""

    st.markdown('<p style="margin-bottom: 10px; margin-left: 0px; font-size: 20px; font-weight: bold; color: #006064;">Select the Docking Score range to run PLIP</p>', unsafe_allow_html=True)
    
    min_affinity, max_affinity = df['Docking score (kcal/mol)'].min(), df['Docking score (kcal/mol)'].max()
    col1, _, col2, _ = st.columns([0.12, 0.1, 0.12, 0.66])
    
    with col1:
        st.markdown('<p style="font-size: 16px; color: #a67b56; margin-bottom: -30px;">Lower threshold</p>', unsafe_allow_html=True)
        lower_range = st.number_input(
            "",
            min_value=min_affinity,
            max_value=max_affinity,
            value=min_affinity,
            step=0.01,
            format="%.2f",
            key="lower_affinity_input_plip"
        )
    with col2:
        st.markdown('<p style="font-size: 16px; color: #a67b56; margin-bottom: -30px;">Higher threshold</p>', unsafe_allow_html=True)
        higher_range = st.number_input(
            "",
            min_value=min_affinity,
            max_value=max_affinity,
            value=max_affinity,
            step=0.01,
            format="%.2f",
            key="higher_affinity_input_plip"
        )
    
    if lower_range < min_affinity or higher_range > max_affinity:
        st.warning(f"Affinity range must be between {min_affinity} and {max_affinity}.")
        return None, None
    elif lower_range >= higher_range:
        st.warning("Lower range must be less than higher range.")
        return None, None

    df_selected = df[(df['Docking score (kcal/mol)'] >= lower_range) & 
                     (df['Docking score (kcal/mol)'] <= higher_range)]
    selected_count = len(df_selected)

    st.markdown(f"""<p style="margin-top: -10px; font-size:16px; color:#887b56;
                     ">Total compounds selected for PLIP analysis: <span style="color: #4973f2;  
                      font-size: 20px;"><b>{selected_count}</b></span></p>""", unsafe_allow_html=True)

    return lower_range, higher_range



def extraction_based_on_threshold_for_plip(selected_folder, df, lower_range, higher_range):
    protein_ligand_complexes_folder = os.path.join(selected_folder, "plc")
    plc_all_ligands_folder = os.path.join(selected_folder, "plc_all_ligands")

    if os.path.exists(plc_all_ligands_folder):
        shutil.rmtree(plc_all_ligands_folder)
    
    os.makedirs(plc_all_ligands_folder)

    df_output = df

    df_filtered = df_output[(df_output['Docking score (kcal/mol)'] >= lower_range) &
                            (df_output['Docking score (kcal/mol)'] <= higher_range)]
    
    selected_ligands = df_filtered['Name'].tolist()
    
    for ligand in selected_ligands:
        pdb_file_name = f"{ligand}.pdb"
        pdb_source_path = os.path.join(protein_ligand_complexes_folder, pdb_file_name)
        
        if os.path.exists(pdb_source_path):
            pdb_destination_path = os.path.join(plc_all_ligands_folder, pdb_file_name)
            shutil.copy(pdb_source_path, pdb_destination_path)
            print(f"Copied {pdb_file_name} to {plc_all_ligands_folder}")
        else:
            print(f"Warning: {pdb_file_name} not found in {protein_ligand_complexes_folder}")
    
    return plc_all_ligands_folder  


def run_plip(selected_folder, plc_all_ligands):
    
    plip_path = os.path.abspath("scripts/plip") 
    pdb_path = os.path.abspath(f"{selected_folder}/plc_all_ligands") 
    output_path = os.path.abspath(f"{selected_folder}/output_plip_files")

    if os.path.exists(output_path):
        shutil.rmtree(output_path)
        
    os.makedirs(output_path, exist_ok=True)
    os.environ["PYTHONPATH"] = plip_path

    pdb_files = [f for f in os.listdir(pdb_path) if f.endswith(".pdb")]
    for pdb_file in pdb_files:
        input_file = os.path.join(pdb_path, pdb_file)
        pdb_output_dir = os.path.join(output_path, os.path.splitext(pdb_file)[0])
        os.makedirs(pdb_output_dir, exist_ok=True)

        plip_cmd_path = os.path.join(plip_path, "plipcmd.py")
        command = ["python3", plip_cmd_path, "-f", input_file, "-yvxt", "-o", pdb_output_dir]
        result = subprocess.run(command, cwd=pdb_path, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    post_process_command = ["python3", os.path.join(plip_path, "plip_post_process.py"), "-d", output_path]
    subprocess.run(post_process_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    return output_path 


def generate_plip_tables_html(filtered_df):
    colgroup_html = ''.join(
        f'<col>' for _ in filtered_df.columns
    )

    table_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/tablesort/5.2.1/tablesort.min.js"></script>
        <style>
            th {{
                cursor: pointer;
                background-color: #006064;
                color: white;
                padding: 8px;
                position: sticky;
                top: 0;
                z-index: 10; 
                font-weight: normal; 
            }}
            td {{
                padding: 8px;
                text-align: center;
                word-wrap: break-word;
                overflow-wrap: break-word;
            }}
            table {{
                border-collapse: collapse;
                width: 100%;
                table-layout: auto;
                background-color: #FFFFFF;
            }}
            th, td {{
                border: 1px solid #ddd;
            }}
            /* Sticky headers for the first two columns */
            th.sticky-left, td.sticky-left {{
                position: sticky;
                left: 0;
                z-index: 5; 
                background-color: #f3f3f3;
            }}
            th.sticky-left:nth-child(2), td.sticky-left:nth-child(2) {{
                left: calc(15px + 10px); 
            }}
            th.sticky-top-left {{
                z-index: 15; 
            }}
            th.sticky-top-left:nth-child(2) {{
                z-index: 14;
            }}
        </style>
    </head>
    <body>
        <div class="table-container">
            <table id="sortable-table">
                <colgroup>
                    {colgroup_html}
                </colgroup>
                <thead>
                    <tr>
                        <th class="sticky-left sticky-top-left" style="background-color: #006064;">#</th>
                        <th class="sticky-left sticky-top-left" style="background-color: #006064;">Name</th>
                        {''.join(f'<th style="background-color: #006064;">{col}</th>' for col in filtered_df.columns[1:])}
                    </tr>
                </thead>
                <tbody>
                    {''.join(
                        f'<tr><td class="sticky-left">{i}</td>'
                        f'<td class="sticky-left">{row[0]}</td>'
                        + ''.join(f'<td>{val}</td>' for val in row[1:])
                        + '</tr>'
                        for i, row in enumerate(filtered_df.values, start=0)
                    )}
                </tbody>
            </table>
        </div>
        <script>
            new Tablesort(document.getElementById('sortable-table'));
        </script>
    </body>
    </html>
    """
    return table_html


def plot_heatmap(df):
    data = df.set_index('Name')
    
    fig_width = 10
    fig_height = max(len(data.index) * 0.5, 5)
    
    plt.figure(figsize=(fig_width, fig_height))
    ax = sns.heatmap(data, 
                     cmap=["#e0f7fa", "#b2ebf2", "#80deea", "#4dd0e1", "#26c6da", "#00bcd4", 
                          "#00acc1", "#0097a7", "#00838f", "#006064"],
                     annot=True, fmt=".0f", linewidths=0.1, linecolor='white', 
                     square=False, cbar=False, xticklabels=data.columns, yticklabels=data.index)
    
    ax.xaxis.set_ticks_position('top')
    plt.xticks(rotation=45, ha='left')
    plt.yticks(rotation=0, ha='right')
    plt.ylabel('Entities', fontsize=14)
    plt.tight_layout()
    plt.gcf().patch.set_alpha(0)
    st.pyplot(plt)

    

def display_plip_data(selected_folder, output_path):
    st.write("##### PLIP Results")
    csv_files = []
    for root, dirs, files in os.walk(output_path):
        for file in files:
            if file.endswith(".csv"):
                csv_files.append(os.path.join(root, file))

    if not csv_files:
        st.write("No CSV files found in the output directory.")
        return

    csv_dict = {os.path.splitext(os.path.basename(file))[0]: file for file in csv_files}
    ordered_csv_files = ['plip_result'] + [file for file in csv_dict.keys() if file != 'plip_result']
    selected_file_name = st.selectbox("Select type of Protein-ligand interaction to analyze:", ordered_csv_files, index=0)

    if selected_file_name:
        selected_file_path = csv_dict[selected_file_name]
        if selected_file_name == "plip_result":
            df = pd.read_csv(selected_file_path)
            num_columns = [col for col in df.columns if col.startswith('num_')]
            if 'Name' in df.columns:
                columns_to_show = ['Name'] + num_columns
            else:
                columns_to_show = num_columns 
            df = df[columns_to_show]
        else:
            df = pd.read_csv(selected_file_path)

        scrollable_table_html = generate_plip_tables_html(df)
        st.components.v1.html(scrollable_table_html, height=300, scrolling=True)

        original_csv_data = pd.read_csv(selected_file_path).to_csv(index=False).encode('utf-8')
        b64 = base64.b64encode(original_csv_data).decode()

        st.markdown(
            f"<div style='text-align: left; margin-top: 10px; margin-bottom: 20px;'>"
            f"<a href='data:file/csv;base64,{b64}' download='plip_result.csv' "
            f"style='background-color: #006064; color: white; text-decoration: none; padding: 10px 20px; border-radius: 5px; font-size: 14px;'>"
            f"Download PLIP result</a>"
            f"</div>",
            unsafe_allow_html=True)

        if selected_file_name == "plip_result":
            plot_heatmap(df)


def handle_plip(selected_folder, df, lower_range, higher_range):
    st.write("")
    st.write("")
    st.write("")
    plc_all_ligands = extraction_based_on_threshold_for_plip(selected_folder, df, lower_range, higher_range)
    output_path = run_plip(selected_folder, plc_all_ligands)
    return output_path




# def create_histogram(df, time_taken):
#     # Generate the histogram plot
#     docking_scores = df["Docking score (kcal/mol)"]
#     bin_edges = list(range(int(docking_scores.min()) - 1, int(docking_scores.max()) + 2))
#     bin_counts, _ = np.histogram(docking_scores, bins=bin_edges)

#     bin_centers = [(bin_edges[i] + bin_edges[i+1]) / 2 for i in range(len(bin_edges) - 1)]
#     bar_width = 0.1  # Slimmer bars for compactness

#     # Adjust figure size based on the number of bins
#     fig_width = len(bin_centers) * 0.3 + 2  # Smaller width proportional to bins
#     fig_height = 1.8  # Reduced height for compactness
#     fig, ax = plt.subplots(figsize=(fig_width, fig_height), dpi=300, facecolor='none')
#     # fig, ax = plt.subplots(figsize=(28, 1.8), dpi=300, facecolor='none')

#     for x, y in zip(bin_centers, bin_counts):
#         rect = FancyBboxPatch(
#             (x - bar_width / 2, 0),  # Lower-left corner
#             bar_width,  # Slimmer width
#             y,  # Height
#             boxstyle="round,pad=0.1,rounding_size=0.05",  # Rounded top edges
#             facecolor="#4973f2",  # Bar color
#             linewidth=0  # No border
#         )
#         ax.add_patch(rect)

#     max_count = max(bin_counts)
#     padding = max_count * 0.05  # Small padding above bars
#     ax.set_xlim(bin_edges[0] - bar_width, bin_edges[-1] + bar_width)
#     ax.set_ylim(0, max_count + padding)
#     ax.set_xticks(bin_centers)
#     ax.set_xticklabels(
#         [f"{int(bin_edges[i])} to {int(bin_edges[i+1])}" for i in range(len(bin_edges) - 1)],
#         rotation=45, ha="right", fontsize=6  # Very small text
#     )
#     ax.set_title("Docking Scores", fontsize=8, weight='bold')  # Compact title
#     ax.set_xlabel("Score Range", fontsize=6)  # Compact x-axis label
#     ax.set_ylabel("Frequency", fontsize=6)  # Compact y-axis label
#     ax.tick_params(axis='both', labelsize=5)  # Compact tick labels
#     plt.tight_layout(pad=0.2)  # Minimal padding for compact layout

#     # Wrap the plot in a custom div to control its width
#     st.markdown(
#         """
#         <div style="max-width: 600px; margin: 0 auto; text-align: center;">
#         """,
#         unsafe_allow_html=True,
#     )

#     # Embed the figure into Streamlit
#     st.pyplot(fig, clear_figure=True)

#     # Close the wrapping div
#     st.markdown("</div>", unsafe_allow_html=True)

#     # Save the plot to a buffer for download
#     buffer = BytesIO()
#     plt.savefig(buffer, format="png", dpi=300, transparent=True)
#     buffer.seek(0)

#     st.download_button(
#         label="Download Histogram",
#         data=buffer,
#         file_name="docking_score_histogram.png",
#         mime="image/png"
#     )
#     plt.close(fig)


# import streamlit as st
# import pandas as pd
# import plotly.graph_objects as go
# import numpy as np

# def create_histogram(df, time_taken):
#     docking_scores = df["Docking score (kcal/mol)"]
#     bin_edges = list(range(int(docking_scores.min()) - 1, int(docking_scores.max()) + 2))
#     bin_counts, _ = np.histogram(docking_scores, bins=bin_edges)

#     bin_centers = [(bin_edges[i] + bin_edges[i+1]) / 2 for i in range(len(bin_edges) - 1)]
#     bar_width = 0.2  # Fixed width for bars
#     gap = 0.05  # Gap between bars

#     # Create the figure with rounded corner bars
#     fig = go.Figure()

#     for x, y in zip(bin_centers, bin_counts):
#         fig.add_trace(
#             go.Bar(
#                 x=[x],
#                 y=[y],
#                 width=bar_width - gap,  # Adjusted width for gaps
#                 marker=dict(
#                     color="#4973f2",
#                     line=dict(width=0),
#                     opacity=1
#                 ),
#                 hoverinfo="x+y",  # Show x and y values on hover
#                 texttemplate='%{y}',  # Show frequency above bars
#                 textposition='outside',
#             )
#         )

#     # Update layout for rounded corners and improved readability
#     fig.update_traces(marker=dict(line_color="#4973f2", line_width=0.5))
#     fig.update_layout(
#         title=dict(
#             text="Docking Scores",
#             font=dict(size=14, family="Arial", color="black"),
#             x=0.5,
#         ),
#         xaxis=dict(
#             title="Score Range",
#             tickvals=bin_centers,
#             ticktext=[
#                 f"{int(bin_edges[i])} to {int(bin_edges[i+1])}"
#                 for i in range(len(bin_edges) - 1)
#             ],
#             showline=True,
#             linecolor="gray",
#             mirror=True,
#         ),
#         yaxis=dict(
#             title="Frequency",
#             showline=True,
#             linecolor="gray",
#             mirror=True,
#             zeroline=True,
#             zerolinecolor="lightgray",
#         ),
#         barmode="relative",
#         bargap=gap*0.1/bar_width,  # Adjust gap between bars
#         margin=dict(l=40, r=40, t=60, b=40),
#         plot_bgcolor="white",
#         height=400,
#     )

#     # Add gridlines for better readability
#     fig.update_xaxes(showgrid=False)
#     fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor="lightgray")

#     # Render the chart in Streamlit
#     st.plotly_chart(fig, use_container_width=True)






##############################################################################################################################
""" Tab 2: Protein-Ligand Interaction code """


import py3Dmol
from py3Dmol import view
from IPython.display import display, HTML


def get_agandock_folders(base_path="."):
    """Retrieve Agandock experiment folders."""
    return [f for f in os.listdir(base_path) if os.path.isdir(f) and f.startswith("agandock")]


def get_receptor_pdb_path(selected_folder):
    pdb_files = [f for f in os.listdir(selected_folder) if f.endswith('.pdb')]
    if not pdb_files:
        st.error("No PDB file found in the selected folder.")
        return None
    return os.path.join(selected_folder, pdb_files[0])

def get_plip_and_sdf_paths(selected_folder):
    output_plip_path = os.path.join(selected_folder, "output_plip_files")
    sdf_out_path = os.path.join(selected_folder, "pipeline_files", "9_sdf_out")
    if not os.path.exists(output_plip_path) or not os.path.exists(sdf_out_path):
        st.error("Please first run PLIP for a given experiment.")
        return None, None
    return output_plip_path, sdf_out_path

def process_and_copy_matching_files(output_plip_path, sdf_out_path):
    plip_folders = [f for f in os.listdir(output_plip_path) if os.path.isdir(os.path.join(output_plip_path, f))]
    sdf_files = [f for f in os.listdir(sdf_out_path) if f.endswith('_out.sdf')]
    
    for folder_name in plip_folders:
        matching_sdf = [sdf for sdf in sdf_files if sdf.startswith(folder_name + "_")]
        if matching_sdf:
            source_sdf_path = os.path.join(sdf_out_path, matching_sdf[0])
            destination_folder = os.path.join(output_plip_path, folder_name)
            destination_sdf_path = os.path.join(destination_folder, matching_sdf[0])

            os.makedirs(destination_folder, exist_ok=True)
            shutil.copy(source_sdf_path, destination_sdf_path)

def collect_ligand_files(output_plip_path):
    ligand_files = [
        os.path.join(root, file)
        for root, _, files in os.walk(output_plip_path)
        for file in files if file.endswith('.sdf')
    ]
    if not ligand_files:
        st.error("No SDF files found in output_plip_files.")
    return ligand_files

def select_ligand_and_visualize(output_plip_path, ligand_files, receptor_pdb_path):
    selected_ligand_file_display_names = [os.path.basename(file).replace('_out.sdf', '') for file in ligand_files]
    selected_ligand_display_map = dict(zip(selected_ligand_file_display_names, ligand_files))

    selected_ligand_file_display_name = st.selectbox(
        "Select a Docked Ligand",
        selected_ligand_file_display_names,
        key="ligand_file_selector",
        index=0
    )

    if selected_ligand_file_display_name in selected_ligand_display_map:
        ligand_path = selected_ligand_display_map[selected_ligand_file_display_name]
        visualize_data(output_plip_path, receptor_pdb_path, os.path.dirname(ligand_path), os.path.basename(ligand_path))
    else:
        st.error(f"Ligand file '{selected_ligand_file_display_name}' not found.")


import random
import py3Dmol
import pandas as pd
import streamlit as st

def generate_unique_colors(num_colors):
    """Generate a list of distinct colors."""
    colors = []
    for _ in range(num_colors):
        # Generate random colors in hexadecimal format
        color = "#{:02x}{:02x}{:02x}".format(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        colors.append(color)
    return colors

import random
import py3Dmol
import pandas as pd
import streamlit as st

import colorsys

def generate_unique_colors(num_colors):
    colors = []
    hue_step = 1.0 / num_colors
    for i in range(num_colors):
        hue = (i * hue_step) % 1.0
        saturation = 0.8
        value = 0.9
        rgb = colorsys.hsv_to_rgb(hue, saturation, value)
        hex_color = "#{:02x}{:02x}{:02x}".format(int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255))
        colors.append(hex_color)
    return colors


def visualize_3d_structures(output_plip_path, receptor_pdb_path, ligand_file_path):
    try:
        plip_result_file = os.path.join(output_plip_path, "plip_result.csv")
        plip_results = pd.read_csv(plip_result_file)
        df_all_residues = plip_results[['Name', 'all_rsnr']]

        ligand_name = os.path.basename(ligand_file_path).replace('_out.sdf', '')
        selected_residues = df_all_residues[df_all_residues['Name'] == ligand_name]['all_rsnr'].values

        if selected_residues.size == 0:
            st.error(f"No residues found for the selected ligand {ligand_name}.")
            return
        
        residues_to_highlight = eval(selected_residues[0])  
        residue_colors = generate_unique_colors(len(residues_to_highlight))
        residues_color_map = dict(zip(residues_to_highlight, residue_colors))

        col1, col2 = st.columns([0.85, 0.15])

        with col1:
            viewer = py3Dmol.view(width=940, height=600)

            with open(receptor_pdb_path, 'r') as protein_file:
                receptor_data = protein_file.read()
            viewer.addModel(receptor_data, 'pdb')

            viewer.setStyle({'model': 0}, {'cartoon': {'color': 'lightgrey'}})

            for res, color in residues_color_map.items():
                viewer.setStyle({'resi': res}, {'stick': {'color': color}})

            with open(ligand_file_path, 'r') as ligand_file:
                ligand_data = ligand_file.read()
            viewer.addModel(ligand_data, 'sdf')

            viewer.setStyle({'model': 1}, {'stick': {'colorscheme': 'greenCarbon'}})

            viewer.setBackgroundColor('white')
            viewer.zoomTo()

            viewer_html = viewer._make_html()

            st.components.v1.html(viewer_html, height=600, width=940)

        with col2:
            label_html = "<div style='font-family:sans-serif; margin-top:20px;'>"
            label_html += "<h9> </h9><ul style='list-style-type:none; padding:0;'>"

            for res, color in residues_color_map.items():
                label_html += f"<li style='margin-top:0px; margin-bottom:5px;'><span style='display:inline-block; width:15px; height:15px; background-color:{color}; margin-right:10px;'></span>Residue {res}</li>"

            label_html += "</ul></div>"

            st.markdown(label_html, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"An error occurred while visualizing 3D structures: {e}")





def visualize_data(output_plip_path, receptor_pdb_path, ligand_folder_path, selected_ligand_file):
    """Prepare and show visualization for the selected receptor and ligand files."""
    ligand_file_path = os.path.join(ligand_folder_path, selected_ligand_file)
    if receptor_pdb_path and st.button("Show Visualization", key="visualization_button"):
        with st.spinner("Preparing visualization..."):
            visualize_3d_structures(output_plip_path, receptor_pdb_path, ligand_file_path)
    elif not receptor_pdb_path:
        st.error("Please upload the receptor PDB file to visualize the structure.")


# def get_ligand_files(ligand_folder_path):
#     """Retrieve ligand SDF files from the specified folder."""
#     if os.path.exists(ligand_folder_path):
#         return [f for f in os.listdir(ligand_folder_path) if f.endswith(".sdf")]
#     return []



# def visualize_3d_structures(output_plip_path, receptor_pdb_path, ligand_file_path):
#     try:
#         plip_result_file = os.path.join(output_plip_path, "plip_result.csv")
#         plip_results = pd.read_csv(plip_result_file)
#         df_all_residues = plip_results[['all_rsnr']]
#         st.dataframe(df_all_residues)
        
#         # Load and visualize 3D structures
#         with open(receptor_pdb_path, "r") as protein_file:
#             receptor_data = protein_file.read()

#         with open(ligand_file_path, "r") as ligand_file:
#             ligand_data = ligand_file.read()

#         # Initialize the 3D viewer
#         viewer = view(width=1100, height=600)
#         viewer.addModel(receptor_data, 'pdb')
#         viewer.setStyle({'model': 0}, {'cartoon': {'color': 'lightblue', 'opacity': 0.8}})  
        
#         viewer.addModel(ligand_data, 'sdf')
#         viewer.setStyle({'model': 1}, {'stick': {'colorscheme': 'greenCarbon'}})
#         viewer.setBackgroundColor('white')
#         viewer.zoomTo()

#         # Render the viewer in Streamlit
#         viewer_html = viewer._make_html()
#         st.components.v1.html(viewer_html, height=600, width=1100)
        
#     except Exception as e:
#         st.error(f"An error occurred while visualizing 3D structures: {e}")

        

