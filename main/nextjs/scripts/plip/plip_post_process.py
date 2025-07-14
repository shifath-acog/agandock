import xml.etree.ElementTree as ET
import pandas as pd
import os
import argparse

def get_hydrophobic(root):
    hydrophobic_interactions = []
    for interaction in root.iter('hydrophobic_interaction'):
        ligcoo = interaction.find('ligcoo')
        protcoo = interaction.find('protcoo')
        hydrophobic_interactions.append({
            'resnr': interaction.find('resnr').text,
            'restype': interaction.find('restype').text,
            'reschain': interaction.find('reschain').text,
            'resnr_lig': interaction.find('resnr_lig').text,
            'restype_lig': interaction.find('restype_lig').text,
            'reschain_lig': interaction.find('reschain_lig').text,
            'dist': interaction.find('dist').text,
            'ligcarbonidx': interaction.find('ligcarbonidx').text,
            'protcarbonidx': interaction.find('protcarbonidx').text,
            'ligx': ligcoo.find('x').text,
            'ligy': ligcoo.find('y').text,
            'ligz': ligcoo.find('z').text,
            'protx': protcoo.find('x').text,
            'proty': protcoo.find('y').text,
            'protz': protcoo.find('z').text,
        })
    
    df = pd.DataFrame(hydrophobic_interactions)
    return df
    
def get_hydrogen(root):
    # create an empty list to hold the rows
    rows = []
    
    # loop over each hydrogen_bond tag
    for hbond in root.iter('hydrogen_bond'):
        # extract the relevant information from the tag
        id = int(hbond.get('id'))
        resnr = int(hbond.find('resnr').text)
        restype = hbond.find('restype').text
        reschain = hbond.find('reschain').text
        resnr_lig = int(hbond.find('resnr_lig').text)
        restype_lig = hbond.find('restype_lig').text
        reschain_lig = hbond.find('reschain_lig').text
        sidechain = True if hbond.find('sidechain').text == 'True' else False
        dist_ha = float(hbond.find('dist_h-a').text)
        dist_da = float(hbond.find('dist_d-a').text)
        don_angle = float(hbond.find('don_angle').text)
        protisdon = True if hbond.find('protisdon').text == 'True' else False
        donoridx = int(hbond.find('donoridx').text)
        donortype = hbond.find('donortype').text
        acceptoridx = int(hbond.find('acceptoridx').text)
        acceptortype = hbond.find('acceptortype').text
        ligcoo_x = float(hbond.find('ligcoo/x').text)
        ligcoo_y = float(hbond.find('ligcoo/y').text)
        ligcoo_z = float(hbond.find('ligcoo/z').text)
        protcoo_x = float(hbond.find('protcoo/x').text)
        protcoo_y = float(hbond.find('protcoo/y').text)
        protcoo_z = float(hbond.find('protcoo/z').text)
        
        # append the information as a row to the list
        rows.append([id, resnr, restype, reschain, resnr_lig, restype_lig, reschain_lig, sidechain, dist_ha, dist_da, don_angle, protisdon, donoridx, donortype, acceptoridx, acceptortype, ligcoo_x, ligcoo_y, ligcoo_z, protcoo_x, protcoo_y, protcoo_z])
    
    # create the dataframe
    df = pd.DataFrame(rows, columns=['id', 'resnr', 'restype', 'reschain', 'resnr_lig', 'restype_lig', 'reschain_lig', 'sidechain', 'dist_ha', 'dist_da', 'don_angle', 'protisdon', 'donoridx', 'donortype', 'acceptoridx', 'acceptortype', 'ligcoo_x', 'ligcoo_y', 'ligcoo_z', 'protcoo_x', 'protcoo_y', 'protcoo_z'])
    
    return df
    
    
def get_water_bridge(root):
    # create a list to store the water bridges
    water_bridges = []
    
    # loop over the water bridges and extract the information
    for bridge in root.iter('water_bridge'):
        bridge_info = {
            'id': bridge.get('id'),
            'resnr': bridge.find('resnr').text,
            'restype': bridge.find('restype').text,
            'reschain': bridge.find('reschain').text,
            'resnr_lig': bridge.find('resnr_lig').text,
            'restype_lig': bridge.find('restype_lig').text,
            'reschain_lig': bridge.find('reschain_lig').text,
            'dist_a-w': bridge.find('dist_a-w').text,
            'dist_d-w': bridge.find('dist_d-w').text,
            'don_angle': bridge.find('don_angle').text,
            'water_angle': bridge.find('water_angle').text,
            'protisdon': bridge.find('protisdon').text,
            'donor_idx': bridge.find('donor_idx').text,
            'donortype': bridge.find('donortype').text,
            'acceptor_idx': bridge.find('acceptor_idx').text,
            'acceptortype': bridge.find('acceptortype').text,
            'water_idx': bridge.find('water_idx').text,
            'ligcoo_x': bridge.find('ligcoo/x').text,
            'ligcoo_y': bridge.find('ligcoo/y').text,
            'ligcoo_z': bridge.find('ligcoo/z').text,
            'protcoo_x': bridge.find('protcoo/x').text,
            'protcoo_y': bridge.find('protcoo/y').text,
            'protcoo_z': bridge.find('protcoo/z').text,
            'watercoo_x': bridge.find('watercoo/x').text,
            'watercoo_y': bridge.find('watercoo/y').text,
            'watercoo_z': bridge.find('watercoo/z').text,
        }
        water_bridges.append(bridge_info)
    
    # create a DataFrame from the list
    df = pd.DataFrame(water_bridges)
    return df

def get_salt_bridge(root):
    salt_bridges = []
    for bridge in root.iter('salt_bridge'):
        prot_idx_list, lig_idx_list = [], []
        for i in bridge.iter('prot_idx_list'):
            ids = i.findall('idx')
            for id in ids:
                prot_idx_list.append(id.text)
        for i in bridge.iter('lig_idx_list'):
            ids = i.findall('idx')
            for id in ids:
                lig_idx_list.append(id.text)
        bridge_info = {
            'id': bridge.get('id'),
            'resnr': bridge.find('resnr').text,
            'restype': bridge.find('restype').text,
            'reschain': bridge.find('reschain').text,
            'resnr_lig': bridge.find('resnr_lig').text,
            'restype_lig': bridge.find('restype_lig').text,
            'reschain_lig': bridge.find('reschain_lig').text,
            'dist': bridge.find('dist').text,
            'protispos': bridge.find('protispos').text,
            'lig_group': bridge.find('lig_group').text,
            'ligx': bridge.find('ligcoo/x').text,
            'ligy': bridge.find('ligcoo/y').text,
            'ligz': bridge.find('ligcoo/z').text,
            'protx': bridge.find('protcoo/x').text,
            'proty': bridge.find('protcoo/y').text,
            'protz': bridge.find('protcoo/z').text,
            'prot_idx_list': prot_idx_list,
            'lig_idx_list': lig_idx_list
        }
        salt_bridges.append(bridge_info)

    df = pd.DataFrame(salt_bridges)
    return df

def get_halogen(root):
    # Create an empty list to store the data
    data = []
    
    # Loop through each halogen_bond tag
    for hb in root.iter('halogen_bond'):
        # Extract the data from the tag
        id = hb.get('id')
        resnr = hb.find('resnr').text
        restype = hb.find('restype').text
        reschain = hb.find('reschain').text
        resnr_lig = hb.find('resnr_lig').text
        restype_lig = hb.find('restype_lig').text
        reschain_lig = hb.find('reschain_lig').text
        sidechain = hb.find('sidechain').text
        dist = hb.find('dist').text
        don_angle = hb.find('don_angle').text
        acc_angle = hb.find('acc_angle').text
        don_idx = hb.find('don_idx').text
        donortype = hb.find('donortype').text
        acc_idx = hb.find('acc_idx').text
        acceptortype = hb.find('acceptortype').text
        ligcoo = hb.find('ligcoo')
        lig_x = ligcoo.find('x').text
        lig_y = ligcoo.find('y').text
        lig_z = ligcoo.find('z').text
        protcoo = hb.find('protcoo')
        prot_x = protcoo.find('x').text
        prot_y = protcoo.find('y').text
        prot_z = protcoo.find('z').text
        
        # Append the data to the list
        data.append([id, resnr, restype, reschain, resnr_lig, restype_lig, reschain_lig,
                     sidechain, dist, don_angle, acc_angle, don_idx, donortype, acc_idx,
                     acceptortype, lig_x, lig_y, lig_z, prot_x, prot_y, prot_z])
        
    # Convert the data to a DataFrame
    df = pd.DataFrame(data, columns=['id', 'resnr', 'restype', 'reschain', 'resnr_lig', 'restype_lig',
                                     'reschain_lig', 'sidechain', 'dist', 'don_angle', 'acc_angle',
                                     'don_idx', 'donortype', 'acc_idx', 'acceptortype', 'lig_x',
                                     'lig_y', 'lig_z', 'prot_x', 'prot_y', 'prot_z'])
    return df

def get_pi_stacks(root):
    pi_stacks = []
    
    for i in root.iter('pi_stack'):
        prot_idx_list, lig_idx_list = [], []
        for j in i.iter('prot_idx_list'):
            ids = j.findall('idx')
            for id in ids:
                prot_idx_list.append(id.text)
        for j in i.iter('lig_idx_list'):
            ids = j.findall('idx')
            for id in ids:
                lig_idx_list.append(id.text)
        info = {
            'id': i.get('id'),
            'resnr': i.find('resnr').text,
            'restype': i.find('restype').text,
            'prot_idx_list': prot_idx_list,
            'lig_idx_list': lig_idx_list
        }
        pi_stacks.append(info)

    df = pd.DataFrame(pi_stacks)
    return df

def get_pi_cation_interactions(root):
    pi_cation_interactions = []

    for i in root.iter('pi_cation_interaction'):
        prot_idx_list, lig_idx_list = [], []
        for j in i.iter('prot_idx_list'):
            ids = j.findall('idx')
            for id in ids:
                prot_idx_list.append(id.text)
        for j in i.iter('lig_idx_list'):
            ids = j.findall('idx')
            for id in ids:
                lig_idx_list.append(id.text)
        info = {
            'id': i.get('id'),
            'resnr': i.find('resnr').text,
            'restype': i.find('restype').text,
            'prot_idx_list': prot_idx_list,
            'lig_idx_list': lig_idx_list
        }
        pi_cation_interactions.append(info)

    df = pd.DataFrame(pi_cation_interactions)
    return df

def get_halogen_bonds(root):
    halogen_bonds = []

    for i in root.iter('halogen_bond'):
        info = {
            'id': i.get('id'),
            'resnr': i.find('resnr').text,
            'restype': i.find('restype').text,
            'acc_idx': i.find('acc_idx').text,
            'don_idx': i.find('don_idx').text
        }
        halogen_bonds.append(info)

    df = pd.DataFrame(halogen_bonds)
    return df

def get_metal_complexes(root):
    metal_complexes = []

    for i in root.iter('metal_complex'):
        info = {
            'id': i.get('id'),
            'resnr': i.find('resnr').text,
            'restype': i.find('restype').text,
            'metal_idx': i.find('metal_idx').text,
            'target_idx': i.find('target_idx').text
        }
        metal_complexes.append(info)

    df = pd.DataFrame(metal_complexes)
    return df

def parse_xml_file(filepath):
    """return processed dataframe from a xml file."""
    # Parse the XML file
    print(filepath)
    tree = ET.parse(filepath)
    root = tree.getroot()
    for i in root.iter('bindingsite'):
        if i.find('.//longname').text=='UNL':
            print("Found UNL")
            root = i
        elif i.find('.//longname').text=='UNK':
            print("Found UNK")
            root = i

    df_hydrophobic = get_hydrophobic(root)
    df_hydrogen = get_hydrogen(root)
    df_water_bridge = get_water_bridge(root)
    df_salt_bridge = get_salt_bridge(root)
    df_halogen = get_halogen(root)
    df_pi_stacks = get_pi_stacks(root)
    df_pi_cation_interactions = get_pi_cation_interactions(root)
    df_halogen_bonds = get_halogen_bonds(root)
    df_metal_complexes = get_metal_complexes(root)

    data = dict()
    data['Name'] = filepath.split('/')[4]

    smiles_to_pdb_map = root.find('.//smiles_to_pdb').text 
    data['smiles_to_pdb_map'] = smiles_to_pdb_map
    
    all_rsnr = []
    atom_ids = []
    data['SMILES'] = root.find('.//smiles').text
    if len(df_hydrophobic) != 0:
        data['num_hydrophobic_interactions'] = len(df_hydrophobic)
        data['rsnr_hydrophobic'] = df_hydrophobic['resnr'].values.tolist()
        data['restype_hydrophobic'] = df_hydrophobic['restype'].values.tolist()
        data['ligcarbonidx_hydrophobic'] = df_hydrophobic['ligcarbonidx'].values.tolist()
        data['protcarbonidx_hydrophobic'] = df_hydrophobic['protcarbonidx'].values.tolist()
    else:
        data['num_hydrophobic_interactions'] = 0
        data['rsnr_hydrophobic'] = []
        data['restype_hydrophobic'] = []
        data['ligcarbonidx_hydrophobic'] = []
        data['protcarbonidx_hydrophobic'] = []
    all_rsnr = all_rsnr + data['rsnr_hydrophobic']
    atom_ids = atom_ids + data['ligcarbonidx_hydrophobic'] + data['protcarbonidx_hydrophobic']

    if len(df_hydrogen) != 0:
        data['num_hydrogen_bonding_interactions'] = len(df_hydrogen)
        data['rsnr_hydrogen'] = df_hydrogen['resnr'].values.tolist()
        data['restype_hydrogen'] = df_hydrogen['restype'].values.tolist()
        data['strong_hydrogen_bonds'] = len(df_hydrogen[(df_hydrogen['dist_da'] < 2.5)])
        data['moderate_hydrogen_bonds'] = len(df_hydrogen[(df_hydrogen['dist_da'] >= 2.5) & (df_hydrogen['dist_da'] <= 3.2)])
        data['weak_hydrogen_bonds'] = len(df_hydrogen[(df_hydrogen['dist_da'] > 3.2)])
        data['acceptoridx_hydrogen_bonds'] = df_hydrogen['acceptoridx'].values.tolist()
        data['donoridx_hydrogen_bonds'] = df_hydrogen['donoridx'].values.tolist()
    else:
        data['num_hydrogen_bonding_interactions'] = 0
        data['rsnr_hydrogen'] = []
        data['restype_hydrogen'] = []
        data['strong_hydrogen_bonds'] = 0
        data['moderate_hydrogen_bonds'] = 0
        data['weak_hydrogen_bonds'] = 0
        data['acceptoridx_hydrogen_bonds'] = []
        data['donoridx_hydrogen_bonds'] = []
    all_rsnr = all_rsnr + data['rsnr_hydrogen']
    atom_ids = atom_ids + data['acceptoridx_hydrogen_bonds'] + data['donoridx_hydrogen_bonds']

    if len(df_water_bridge) != 0:
        data['num_water_bridges'] = len(df_water_bridge)
        data['rsnr_water_bridge'] = df_water_bridge['resnr'].values.tolist()
        data['restype_water_bridge'] = df_water_bridge['restype'].values.tolist()
        data['water_idx'] = df_water_bridge['water_idx'].values.tolist()
        data['acceptor_idx_water_bridge'] = df_water_bridge['acceptor_idx'].values.tolist()
        data['donor_idx_water_bridge'] = df_water_bridge['donor_idx'].values.tolist()
    else:
        data['num_water_bridges'] = 0
        data['rsnr_water_bridge'] = []
        data['restype_water_bridge'] = []
        data['water_idx'] = []
        data['acceptor_idx_water_bridge'] = []
        data['donor_idx_water_bridge'] = []
    all_rsnr = all_rsnr + data['rsnr_water_bridge']
    atom_ids = atom_ids + data['acceptor_idx_water_bridge'] + data['donor_idx_water_bridge']

    if len(df_salt_bridge) != 0:
        data['num_salt_bridges'] = len(df_salt_bridge)
        data['rsnr_salt_bridge'] = df_salt_bridge['resnr'].values.tolist()
        data['restype_salt_bridge'] = df_salt_bridge['restype'].values.tolist()
        data['prot_idx_list_salt_bridge'] = [element for nestedlist in df_salt_bridge['prot_idx_list'].values.tolist() for element in nestedlist]
        data['lig_idx_list_salt_bridge'] = [element for nestedlist in df_salt_bridge['lig_idx_list'].values.tolist() for element in nestedlist]
    else:
        data['num_salt_bridges'] = 0
        data['rsnr_salt_bridge'] = []
        data['restype_salt_bridge'] = []
        data['prot_idx_list_salt_bridge'] = []
        data['lig_idx_list_salt_bridge'] = []
    all_rsnr = all_rsnr + data['rsnr_salt_bridge']
    atom_ids = atom_ids + data['prot_idx_list_salt_bridge'] + data['lig_idx_list_salt_bridge']

    if len(df_halogen) != 0:    
        data['num_halogen'] = len(df_halogen)
        data['rsnr_halogen'] = df_halogen['resnr'].values.tolist()
        data['restype_halogen'] = df_halogen['restype'].values.tolist()
        data['acc_idx_halogen'] = df_halogen['acc_idx'].values.tolist()
        data['don_idx_halogen'] = df_halogen['don_idx'].values.tolist()
    else:
        data['num_halogen'] = 0
        data['rsnr_halogen'] = []
        data['restype_halogen'] = []
        data['acc_idx_halogen'] = []
        data['don_idx_halogen'] = []
    all_rsnr = all_rsnr + data['rsnr_halogen']
    atom_ids = atom_ids + data['acc_idx_halogen'] + data['don_idx_halogen']

    if len(df_pi_stacks) != 0:
        data['num_pi_stacks'] = len(df_pi_stacks)
        data['rsnr_pi_stacks'] = df_pi_stacks['resnr'].values.tolist()
        data['restype_pi_stacks'] = df_pi_stacks['restype'].values.tolist()
        data['prot_idx_list_pi_stacks'] = [element for nestedlist in df_pi_stacks['prot_idx_list'].values.tolist() for element in nestedlist]
        data['lig_idx_list_pi_stacks'] = [element for nestedlist in df_pi_stacks['lig_idx_list'].values.tolist() for element in nestedlist]
    else:
        data['num_pi_stacks'] = 0
        data['rsnr_pi_stacks'] = []
        data['restype_pi_stacks'] = []
        data['prot_idx_list_pi_stacks'] = []
        data['lig_idx_list_pi_stacks'] = []
    all_rsnr = all_rsnr + data['rsnr_pi_stacks']
    atom_ids = atom_ids + data['prot_idx_list_pi_stacks'] + data['lig_idx_list_pi_stacks']

    if len(df_pi_cation_interactions) != 0:
        data['num_pi_cation_interactions'] = len(df_pi_cation_interactions)
        data['rsnr_pi_cation_interactions'] = df_pi_cation_interactions['resnr'].values.tolist()
        data['restype_pi_cation_interactions'] = df_pi_cation_interactions['restype'].values.tolist()
        data['prot_idx_list_pi_cation_interactions'] = [element for nestedlist in df_pi_cation_interactions['prot_idx_list'].values.tolist() for element in nestedlist]
        data['lig_idx_list_pi_cation_interactions'] = [element for nestedlist in df_pi_cation_interactions['lig_idx_list'].values.tolist() for element in nestedlist]
    else:
        data['num_pi_cation_interactions'] = 0
        data['rsnr_pi_cation_interactions'] = []
        data['restype_pi_cation_interactions'] = []
        data['prot_idx_list_pi_cation_interactions'] = []
        data['lig_idx_list_pi_cation_interactions'] = []
    all_rsnr = all_rsnr + data['rsnr_pi_cation_interactions']
    atom_ids = atom_ids + data['prot_idx_list_pi_cation_interactions'] + data['lig_idx_list_pi_cation_interactions']

    if len(df_halogen_bonds) != 0:
        data['num_halogen_bonds'] = len(df_halogen_bonds)
        data['rsnr_halogen_bonds'] = df_halogen_bonds['resnr'].values.tolist()
        data['restype_halogen_bonds'] = df_halogen_bonds['restype'].values.tolist()
        data['acc_idx_halogen_bonds'] = df_halogen_bonds['acc_idx'].values.tolist()
        data['don_idx_halogen_bonds'] = df_halogen_bonds['don_idx'].values.tolist()
    else:
        data['num_halogen_bonds'] = 0
        data['rsnr_halogen_bonds'] = []
        data['restype_halogen_bonds'] = []
        data['acc_idx_halogen_bonds'] = []
        data['don_idx_halogen_bonds'] = []
    all_rsnr = all_rsnr + data['rsnr_halogen_bonds']
    atom_ids = atom_ids + data['acc_idx_halogen_bonds'] + data['don_idx_halogen_bonds']

    if len(df_metal_complexes) != 0:
        data['num_metal_complexes'] = len(df_metal_complexes)
        data['rsnr_metal_complexes'] = df_metal_complexes['resnr'].values.tolist()
        data['restype_metal_complexes'] = df_metal_complexes['restype'].values.tolist()
        data['metal_idx_metal_complexes'] = df_metal_complexes['metal_idx'].values.tolist()
        data['target_idx_metal_complexes'] = df_metal_complexes['target_idx'].values.tolist()
    else:
        data['num_metal_complexes'] = 0
        data['rsnr_metal_complexes'] = []
        data['restype_metal_complexes'] = []
        data['metal_idx_metal_complexes'] = []
        data['target_idx_metal_complexes'] = []
    all_rsnr = all_rsnr + data['rsnr_metal_complexes']
    atom_ids = atom_ids + data['metal_idx_metal_complexes'] + data['target_idx_metal_complexes']

    all_rsnr = [int(i) for i in all_rsnr]
    data['all_rsnr'] = sorted(set(all_rsnr))
    
    return data
    

def parse_all_files():
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--dir", help="Root directory containing subdirectories of XML files", required=True)
    args = parser.parse_args()

    result_list = []
    for root, dirs, files in os.walk(args.dir):
        for f in files:
            if f == "report.xml":
                xml_file = os.path.join(root, f)
                data = parse_xml_file(xml_file)
                result_list.append(data)
    
    df_result = pd.DataFrame(result_list)
    df_result.to_csv(os.path.join(args.dir, "plip_result.csv"), index=False)

    df = df_result
    df = df.loc[:, ~df.columns.str.contains('idx')]

    patterns = {'hydrogen': 'hydrogen_bonds.csv',
                'halogen': 'halogen_bonds.csv',
                'hydrophobic': 'hydrophobic.csv',
                'water': 'water_bridges.csv',
                'pi_stack': 'pi_stacking.csv',
                'pi_cation': 'pi_cation.csv',
                'salt': 'salt_bridges.csv',
                'metal': 'metal_complexes.csv'}

    for pattern, filename in patterns.items():
        selected_columns = df.loc[:, df.columns.str.contains(pattern)]
        selected_columns_with_pdb = pd.concat([df[['Name']], selected_columns], axis=1)
        selected_columns_with_pdb.to_csv(os.path.join(args.dir, filename), index=False)



if __name__ == "__main__":
    parse_all_files()
