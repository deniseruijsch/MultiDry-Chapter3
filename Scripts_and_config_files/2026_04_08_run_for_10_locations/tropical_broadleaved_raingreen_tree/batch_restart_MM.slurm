#!/bin/bash
#SBATCH -n 50
#SBATCH --time=4-23:00:00
#SBATCH -J lpjml_temp_patches

#SBATCH --array=0-9%2   # run 2 at a time (important!)

#SBATCH --output=/home/druijsch/LPJmL5/dev15oct2025/config_files/2026_04_08_run_for_10_locations/tropical_broadleaved_raingreen_tree/job.%A_%a.%N.out
#SBATCH --error=/home/druijsch/LPJmL5/dev15oct2025/config_files/2026_04_08_run_for_10_locations/tropical_broadleaved_raingreen_tree/job.%A_%a.%N.err

# ----------------------------
# LOAD MODULES (unchanged)
# ----------------------------
module load 2024
module load GCC/13.3.0
module load UDUNITS/2.2.28-GCCcore-13.3.0
module load json-c/0.17-GCCcore-13.3.0
module load OpenMPI/5.0.3-GCC-13.3.0
module load netCDF/4.9.2-gompi-2024a

export LPJROOT="/home/druijsch/LPJmL5/dev15oct2025"

# ----------------------------
# GET CONFIG FILE
# ----------------------------
CONFIG_LIST="/home/druijsch/LPJmL5/dev15oct2025/config_files/2026_04_08_run_for_10_locations/tropical_broadleaved_raingreen_tree/config_list_restart_MM.txt"

CONFIG=$(sed -n "$((SLURM_ARRAY_TASK_ID+1))p" $CONFIG_LIST)

echo "--------------------------------------"
echo "Running config: $CONFIG"
echo "SLURM task ID: $SLURM_ARRAY_TASK_ID"
echo "Node: $(hostname)"
echo "--------------------------------------"

# ----------------------------
# RUN MODEL
# ----------------------------
mpirun -np 50 $LPJROOT/bin/lpjml "$CONFIG"