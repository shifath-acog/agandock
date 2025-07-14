from py3Dmol import view
import streamlit as st

def visualize_3d_structures(receptor_pdb_path, ligand_file_path):
    try:
        with open(receptor_pdb_path, "r") as protein_file:
            receptor_data = protein_file.read()

        with open(ligand_file_path, "r") as ligand_file:
            ligand_data = ligand_file.read()

        viewer = view(width=1100, height=600)
        viewer.addModel(receptor_data, 'pdb')
        viewer.setStyle({'model': 0}, {'cartoon': {'color': 'lightblue', 'opacity': 0.8}})  
        
        viewer.addModel(ligand_data, 'sdf')
        viewer.setStyle({'model': 1}, {'stick': {'colorscheme': 'greenCarbon'}})
        viewer.setBackgroundColor('white')
        viewer.zoomTo()
        viewer_html = viewer._make_html()
        st.components.v1.html(viewer_html, height=600, width=1100)
        
    except Exception as e:
        st.error(f"An error occurred while visualizing 3D structures: {e}")