# AGANDOCK CLI Manual

This document provides detailed instructions on how to clone the AGANDOCK repository, set up the environment using Docker, and run the command-line interface (CLI) for molecular docking and filtering.

## Prerequisites

Before you begin, ensure you have the following software installed on your system:
- **Git:** For cloning the repository.
- **Docker:** For building and running the containerized application environment.
- **NVIDIA GPU Drivers:** Required for running Uni-Dock with GPU acceleration.

---

## 1. Clone the Repository

First, clone the AGANDOCK repository to your local machine using the following command:

```bash
git clone https://github.com/shifath-acog/agandock.git
cd agandock
```

---

## 2. Set Up the Docker Environment

The CLI runs inside a Docker container that includes all necessary dependencies, such as Uni-Dock, Open Babel, and PoseBusters.

### a. Build the Docker Image

Navigate to the project's root directory and run the following command to build the Docker image. This may take some time as it downloads and installs all dependencies.

```bash
docker build -t agandock-env .
```

### b. Run the Docker Container

Once the image is built, run a container from it. This command starts the container in detached mode, grants it access to all available GPUs, and mounts the local project directory into the container.

```bash
docker run -dit --gpus all --name agandock_cli_app -v "$(pwd)":/app agandock-env
```
- `--gpus all`: Provides the container with access to the host's GPUs.
- `--name agandock_cli_app`: Assigns a memorable name to the container.
- `-v "$(pwd)":/app`: Mounts your current project directory into the container, allowing the CLI to read inputs and write outputs directly to your project folder.

---

## 3. Install the CLI Package

With the container running, install the `agandock-cli` package inside the container's Python environment. This makes the `agandock` command available.

```bash
docker exec agandock_cli_app pip install -e /app/cli/agandock-cli
```
- `pip install -e`: Installs the package in "editable" mode, which means any changes you make to the local source code will be immediately reflected inside the container without needing to reinstall.

---

## 4. Running the CLI

All commands are executed via `docker exec` on the running container.

### Command Structure

The basic structure for running a command is:
`docker exec agandock_cli_app agandock [COMMAND] [ARGUMENTS...]`

### a. Run Docking (Single SMILES)

This command runs a docking pipeline for a single molecule provided as a SMILES string.

**Example:**
```bash
docker exec agandock_cli_app agandock run_docking \
  /app/agandock_test_run \
  --pdb_file /app/cli/agandock-cli/agandock_cli/inputs/minD_APO_C1.pdb \
  --pdbqt_file /app/cli/agandock-cli/agandock_cli/inputs/minD_APO_C1.pdbqt \
  --config_file /app/cli/agandock-cli/agandock_cli/inputs/minD_APO_C1_conf.txt \
  --input_type "Single SMILES" \
  --input_smiles CCO
```

### b. Run Docking (Multiple SMILES)

This command runs a docking pipeline for multiple molecules provided in a CSV file.

**Example:**
```bash
docker exec agandock_cli_app agandock run_docking \
  /app/agandock_test_run_multi \
  --pdb_file /app/cli/agandock-cli/agandock_cli/inputs/minD_APO_C1.pdb \
  --pdbqt_file /app/cli/agandock-cli/agandock_cli/inputs/minD_APO_C1.pdbqt \
  --config_file /app/cli/agandock-cli/agandock_cli/inputs/minD_APO_C1_conf.txt \
  --input_type "Multiple SMILES" \
  --input_csv /app/cli/agandock-cli/agandock_cli/inputs/ligands.csv
```

### c. Run Filter

This command filters the results of a previous docking run based on an affinity score range and runs PoseBusters analysis.

**Example:**
```bash
docker exec agandock_cli_app agandock run_filter \
  /app/agandock_test_run_multi \
  -5.0 0.0 \
  --pdb_file /app/cli/agandock-cli/agandock_cli/inputs/minD_APO_C1.pdb
```

---

## 5. Input Files

- **`folder_name` (Positional Argument):** The first argument for both `run_docking` and `run_filter`. This is the name of the directory where all output files for that specific run will be saved. **All paths must be absolute paths within the container's filesystem.**
- **`--pdb_file`:** The absolute path to the receptor's PDB file.
- **`--pdbqt_file`:** The absolute path to the receptor's PDBQT file.
- **`--config_file`:** The absolute path to the Uni-Dock configuration file (e.g., `minD_APO_C1_conf.txt`), which specifies the docking search space.
- **`--input_csv`:** (For multiple SMILES) The absolute path to a CSV file containing molecule information. It must have a "SMILES" column and an optional "Name" column.
- **`--input_smiles`:** (For single SMILES) The SMILES string of the molecule to dock.

---

## 6. Output Files

All output is saved in the `folder_name` directory you provide.

- **`output.csv`**: The main results file, containing docking scores and ligand efficiency for all successfully docked compounds.
- **`output_with_pb.csv`**: (Filter command) Results for compounds that passed the PoseBusters check.
- **`output_without_pb.csv`**: (Filter command) Results for compounds that failed the PoseBusters check.
- **`pipeline_files/`**: A subdirectory containing all intermediate files generated during the process (SDF, MOL2, PDBQT, etc.). This is useful for debugging.
- **`plc/`**: A subdirectory containing the final protein-ligand complexes in PDB format.

---

## 7. Stopping and Removing the Container

When you are finished, you can stop and remove the Docker container to free up system resources.

```bash
# Stop the container
docker stop agandock_cli_app

# Remove the container
docker rm agandock_cli_app
```