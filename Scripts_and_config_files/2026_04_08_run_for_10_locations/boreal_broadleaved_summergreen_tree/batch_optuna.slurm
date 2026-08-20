#!/bin/bash
#Set job requirements
#SBATCH --ntasks=64
#SBATCH --time=4-23:00:00
#SBATCH --job-name lpjml_optuna
#SBATCH --output=/home/druijsch/LPJmL5/dev15oct2025/config_files/2026_04_08_run_for_10_locations/boreal_broadleaved_summergreen_tree/job_optuna.%j.%N.out
#SBATCH --error=/home/druijsch/LPJmL5/dev15oct2025/config_files/2026_04_08_run_for_10_locations/boreal_broadleaved_summergreen_tree/job_optuna.%j.%N.err

#Loading modules
module load 2024
module load GCC/13.3.0
module load UDUNITS/2.2.28-GCCcore-13.3.0
module load json-c/0.17-GCCcore-13.3.0
module load OpenMPI/5.0.3-GCC-13.3.0
module load netCDF/4.9.2-gompi-2024a
module load Python/3.12.3-GCCcore-13.3.0

source /home/druijsch/myenv/bin/activate
python -u /home/druijsch/LPJmL5/dev15oct2025/config_files/2026_04_08_run_for_10_locations/boreal_broadleaved_summergreen_tree/optimize12.py