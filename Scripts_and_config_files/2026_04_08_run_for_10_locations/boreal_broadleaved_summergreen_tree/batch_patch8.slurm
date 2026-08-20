#!/bin/bash
#SBATCH -n 50
#SBATCH --time=4-23:00:00
#SBATCH -J lpjml_temp_patches

#SBATCH --output=/home/druijsch/LPJmL5/dev15oct2025/config_files/2026_04_08_run_for_10_locations/boreal_broadleaved_summergreen_tree/job.%A_%a.%N.out
#SBATCH --error=/home/druijsch/LPJmL5/dev15oct2025/config_files/2026_04_08_run_for_10_locations/boreal_broadleaved_summergreen_tree/job.%A_%a.%N.err

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
# RUN MODEL
# ----------------------------
mpirun -np 50 $LPJROOT/bin/lpjml /home/druijsch/LPJmL5/dev15oct2025/config_files/2026_04_08_run_for_10_locations/boreal_broadleaved_summergreen_tree/spinup/configs/boreal_broadleaved_summergreen_tree_patch8_config_restart_MM.cjson