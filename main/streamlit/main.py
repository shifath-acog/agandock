import os
import glob
import pandas as pd
import streamlit as st

from scripts.docking_utils import *
from scripts.streamlit_utils import *
# from scripts.visualize import *


def main():
    setup_header_and_footer()

    with st.sidebar:
        pdb_file, pdbqt_file, config_file, input_type, input_csv, input_smiles = handle_sidebar_inputs()

    tabs = st.tabs(["Molecular Docking", "Docking summary & Filteration", "PLIP Analysis", "Data Visualizations"])
    progress_table_placeholder = st.empty()

    with tabs[0]:
        st.markdown("#### Docking Process")
        st.write("Please configure the inputs using the sidebar and run the docking pipeline.")
    
        button_container = st.container()
        docking_progress_logs = st.container()

        if "run_docking_clicked" not in st.session_state:
            st.session_state.run_docking_clicked = False

        with button_container:
            if st.button("Run Docking Pipeline", key="run_docking_pipeline"):
                st.session_state.run_docking_clicked = True
                st.session_state.data_loaded = {}

        if st.session_state.run_docking_clicked:
            with docking_progress_logs:
                if "docking_results" not in st.session_state:
                    st.session_state.docking_results = run_docking_pipeline(pdb_file, pdbqt_file, config_file, input_type,
                                                                            input_csv, input_smiles, progress_table_placeholder,
                                                                            docking_progress_logs)
                else:
                    st.info("Docking pipeline results are already cached.")


    with tabs[1]:
        st.markdown("#### Visualize Docked Ligands Binding Affinity Scores")
        
        agandock_folders = get_agandock_folders()
        
        if agandock_folders:
            selected_folder = st.selectbox("Select an Experiment to load data", 
                                            agandock_folders,
                                            key="data_analysis_folder",
                                            on_change=lambda: st.session_state.pop('data_loaded', None))
        
            if "data_loaded" not in st.session_state:
                st.session_state.data_loaded = {}
        
            if selected_folder and selected_folder not in st.session_state.data_loaded:
                with st.spinner("Loading experiment data..."):
                    data = load_folder_data(selected_folder)
                    st.session_state.data_loaded[selected_folder] = data
        
            if selected_folder in st.session_state.data_loaded:
                data = st.session_state.data_loaded[selected_folder]
                df_input, df_salt, time_taken, num_pdbqt_in, num_pdbqt_out = data
                display_summary(df_input, df_salt, time_taken, num_pdbqt_in, num_pdbqt_out)
                output_csv_path = os.path.join(selected_folder, "output.csv")
                df = pd.read_csv(output_csv_path)
                create_histogram(df, time_taken)
        
                run_pb = st.radio("Do you want to run PoseBusters filtration?", ("No", "Yes"))
                if run_pb == "Yes":
                    lower_range, higher_range = select_affinity_range(df)
                    if st.button("Run PoseBusters"):
                        handle_posebusters(selected_folder, df, lower_range, higher_range)
        else:
            st.error("No experiments found. Please run the docking process first.")


    with tabs[2]:
        st.markdown("#### Protein-Ligand Interaction Profiler")
        st.write("Easy and fast identification of non-covalent interactions between biological macromolecules and their ligands.")
    
        agandock_folders = get_agandock_folders()
    
        if agandock_folders:
            selected_folder = st.selectbox("Select an Experiment to load data",
                                            agandock_folders,
                                            key="plip_analysis_folder",
                                            on_change=lambda: st.session_state.pop("data_loaded", None))
    
            st.session_state.setdefault("data_loaded", {})
            st.session_state.setdefault("plip_results", {})
    
            if selected_folder and selected_folder not in st.session_state["data_loaded"]:
                with st.spinner("Loading experiment data..."):
                    st.session_state["data_loaded"][selected_folder] = load_folder_data(selected_folder)
    
            if selected_folder in st.session_state["data_loaded"]:
                data = st.session_state["data_loaded"][selected_folder]
    
                run_plip = st.radio("Want to run PLIP analysis on?", ("All ligands", "Posebusters filtered ligands"))
    
                csv_file = "output.csv" if run_plip == "All ligands" else "output_with_pb.csv"
                csv_path = os.path.join(selected_folder, csv_file)
    
                if run_plip == "Posebusters filtered ligands" and not os.path.exists(csv_path):
                    st.warning(f"Posebusters filtration is not done for experiment {selected_folder}."
                                "Please first run the Posebusters filtration using tab 'Docking Summary and Filtration'.")
                else:
                    df = pd.read_csv(csv_path)
                    create_histogram_for_plip(df, time_taken)
                    lower_range, higher_range = select_affinity_range_for_plip(df)
    
                    if st.button(f"Run PLIP on {run_plip.lower()}"):
                        with st.spinner("Running PLIP analysis..."):
                            output_path = handle_plip(selected_folder, df, lower_range, higher_range)
                            st.session_state["plip_results"][selected_folder] = output_path
    
                    if selected_folder in st.session_state["plip_results"]:
                        display_plip_data(selected_folder, st.session_state["plip_results"][selected_folder])
        else:
            st.error("No experiments found. Please run the docking process first.")

    
    with tabs[3]:
        st.markdown("#### Data Visualization")
        st.write("Do PLIP analysis and visualize 3D structures of receptor (PDB) and docked ligand poses (PDBQT).")
    
        agandock_folders = get_agandock_folders()
    
        if agandock_folders:
            selected_folder = st.selectbox("Select an Experiment to load data",
                                            agandock_folders,
                                            key="visualization_tab",
                                            on_change=lambda: st.session_state.pop("data_loaded", None))
    
            st.session_state.setdefault("data_loaded", {})
    
            if selected_folder and selected_folder not in st.session_state["data_loaded"]:
                with st.spinner("Loading experiment data..."):
                    st.session_state["data_loaded"][selected_folder] = load_folder_data(selected_folder)
    
            if selected_folder in st.session_state["data_loaded"]:
                data = st.session_state["data_loaded"][selected_folder]
    
                receptor_pdb_path = get_receptor_pdb_path(selected_folder)
                if not receptor_pdb_path:
                    return
    
                output_plip_path, sdf_out_path = get_plip_and_sdf_paths(selected_folder)
                if not output_plip_path or not sdf_out_path:
                    return
    
                process_and_copy_matching_files(output_plip_path, sdf_out_path)
    
                ligand_files = collect_ligand_files(output_plip_path)
                if ligand_files:
                    select_ligand_and_visualize(output_plip_path, ligand_files, receptor_pdb_path)
    
        else:
            st.error("No Agandock folders found in the current directory.")


if __name__ == "__main__":
    main()