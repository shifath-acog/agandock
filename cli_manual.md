
# Overview of the `agandock` CLI

The CLI, executed via:

```bash
docker exec agandock_cli_app agandock [COMMAND]
```

uses:

- **Uni-Dock** for docking (GPU-accelerated, leveraging `cudatoolkit=11.5` from `nextjs.yaml`)
- **PoseBusters** for pose validation
- **PLIP** for interaction analysis

It relies on dependencies like `rdkit`, `openbabel-wheel`, and `psutil` (from `requirements.txt`) for SMILES parsing, molecular conversions, and resource monitoring. The CLI is designed for both single-molecule and high-throughput docking, with outputs suitable for further analysis or visualization (e.g., in the Streamlit app via `streamlit_env`).

---

## Commands, Inputs, and Outputs

### 1. `agandock run_docking`

**Purpose**: Docks ligands to a protein target using Uni-Dock, producing docking scores and pose files.

#### Inputs

- **Positional Argument**:
  - `folder_name`: Absolute path to the output directory  
    e.g., `/app/agandock_test_run` for single SMILES, `/app/agandock_test_run_multi` for multiple SMILES.

- **Options**:
  - `--pdb_file <path>`: Path to the protein structure PDB file  
    e.g., `/app/cli/agandock-cli/agandock_cli/inputs/minD_APO_C1.pdb`
  - `--pdbqt_file <path>`: Path to the protein structure PDBQT file
  - `--config_file <path>`: Path to the Uni-Dock configuration file (defines the docking search space)
  - `--input_type {Multiple SMILES,Single SMILES}`: Specifies the input type
  - `--input_smiles <SMILES>`: A single SMILES string (required for Single SMILES)
  - `--input_csv <path>`: Path to CSV with SMILES (required for Multiple SMILES)

#### Example Commands

**Single SMILES**:

```bash
docker exec agandock_cli_app agandock run_docking /app/agandock_test_run \
  --pdb_file /app/cli/agandock-cli/agandock_cli/inputs/minD_APO_C1.pdb \
  --pdbqt_file /app/cli/agandock-cli/agandock_cli/inputs/minD_APO_C1.pdbqt \
  --config_file /app/cli/agandock-cli/agandock_cli/inputs/minD_APO_C1_conf.txt \
  --input_type "Single SMILES" \
  --input_smiles CCO
```

**Multiple SMILES**:

```bash
docker exec agandock_cli_app agandock run_docking /app/agandock_test_run_multi \
  --pdb_file /app/cli/agandock-cli/agandock_cli/inputs/minD_APO_C1.pdb \
  --pdbqt_file /app/cli/agandock-cli/agandock_cli/inputs/minD_APO_C1.pdbqt \
  --config_file /app/cli/agandock-cli/agandock_cli/inputs/minD_APO_C1_conf.txt \
  --input_type "Multiple SMILES" \
  --input_csv /app/cli/agandock-cli/agandock_cli/inputs/ligands.csv
```

#### Outputs

**Single SMILES**:

- **Directory**: `/app/agandock_test_run`
- **Files**:
  - `output.csv`: Docking results
  - `pipeline_files/`: Intermediate files (SDF, MOL2, PDBQT)

**Example `output.csv`**:

```csv
Name,SMILES,Docking score (kcal/mol),Ligand efficiency
agan1,CCO,-2.55,-0.85
```

---

**Multiple SMILES**:

- **Directory**: `/app/agandock_test_run_multi`
- **Files**:
  - `output.csv`: Results for all ligands
  - `pipeline_files/`: Individual pose files

**Example `output.csv`**:

```csv
Name,SMILES,Docking score (kcal/mol),Ligand efficiency
ligand1,CCO,-2.55,-0.85
ligand2,CNC,-3.10,-0.77
```

---

### 2. `agandock run_filter`

**Purpose**: Filters docking results based on affinity score and runs PoseBusters analysis.

#### Inputs

- **Positional Arguments**:
  - `folder_name`: Path to the docking results directory
  - `lower_range <float>`: Minimum docking score (e.g., `-5.0`)
  - `higher_range <float>`: Maximum docking score (e.g., `0.0`)

- **Options**:
  - `--pdb_file <path>`: Protein PDB path

#### Example Command

```bash
docker exec agandock_cli_app agandock run_filter /app/agandock_test_run_multi -5.0 0.0 \
  --pdb_file /app/cli/agandock-cli/agandock_cli/inputs/minD_APO_C1.pdb
```

#### Outputs

- **Directory**: `/app/agandock_test_run_multi`
- **Files**:
  - `output_with_pb.csv`: Valid poses
  - `output_without_pb.csv`: Failed poses
  - `pipeline_files/`: Updated with PoseBusters output

**Example `output_with_pb.csv`**:

```csv
Name,SMILES,Docking score (kcal/mol),Ligand efficiency
ligand1,CCO,-2.55,-0.85
```

**Example `output_without_pb.csv`**:

```csv
Name,SMILES,Docking score (kcal/mol),Ligand efficiency
ligand2,CNC,-3.10,-0.77
```

---

### 3. `agandock run_plip`

**Purpose**: Performs PLIP analysis to identify protein-ligand interactions.

#### Inputs

- **Positional Argument**:
  - `folder_name`: Path to docking results directory

- **Options**:
  - `--pdb_file <path>`: Protein PDB path
  - `--lower_range <float>`: Minimum score filter (optional)
  - `--higher_range <float>`: Maximum score filter (optional)
  - `--use_pb_filtered_ligands`: Flag to use `output_with_pb.csv` only

#### Example Commands

**Analyze All Ligands**:

```bash
docker exec agandock_cli_app agandock run_plip /app/agandock_test_run_multi \
  --pdb_file /app/cli/agandock-cli/agandock_cli/inputs/minD_APO_C1.pdb
```

**Analyze PoseBusters-Filtered Ligands**:

```bash
docker exec agandock_cli_app agandock run_plip /app/agandock_test_run_multi \
  --pdb_file /app/cli/agandock-cli/agandock_cli/inputs/minD_APO_C1.pdb \
  --lower_range -5.0 \
  --higher_range 0.0 \
  --use_pb_filtered_ligands
```

#### Outputs

- **Directory**: `/app/agandock_test_run_multi/plc`
- **Files**:
  - PLIP report files (e.g., `ligand1_plip_report.xml`)
  - Complex PDBs (e.g., `ligand1_complex.pdb`)

---

## Key Notes

### Single vs. Multiple SMILES

| Mode            | Description                                                                 |
|-----------------|-----------------------------------------------------------------------------|
| Single SMILES   | One ligand (e.g., CCO), one row in `output.csv`, one pose file              |
| Multiple SMILES | Many ligands from a CSV, multi-row output, individual pose files            |

### Command Usage

- `run_filter` and `run_plip` operate on `run_docking` outputs
- `run_filter` is often used with Multiple SMILES for screening

### Dependencies

- `rdkit`, `openbabel-wheel`: Molecular format parsing/conversion
- `posebusters`: Validates poses
- `psutil`: Resource monitoring
- `Uni-Dock`: GPU docking via `cudatoolkit=11.5` in `nextjs.yaml`

### GPU Usage

- Uses `nvidia/cuda:12.2.0-devel-ubuntu22.04` base image
- No `pytorch` in `requirements.txt`, so GPU used mainly for Uni-Dock


---

## Example Workflow

1. **Dock Ligands**  
   Use `run_docking` with SMILES  
   → Output: `output.csv`, `pipeline_files/`

2. **Filter Results**  
   Use `run_filter` with score range  
   → Output: `output_with_pb.csv`, `output_without_pb.csv`

3. **Analyze Interactions**  
   Use `run_plip`, optionally filtered  
   → Output: `plc/` with PLIP reports and complexes
