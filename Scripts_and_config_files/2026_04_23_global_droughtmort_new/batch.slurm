#!/bin/bash
#Set job requirements
#SBATCH -n 256
#SBATCH --ntasks-per-node=64
#SBATCH --time=4-23:00:00
#SBATCH -J lpjml_droughtglobal
#SBATCH --output=/home/druijsch/LPJmL5/dev15oct2025/config_files/2026_04_23_global_droughtmort_new/job.%j.%N.out
#SBATCH --error=/home/druijsch/LPJmL5/dev15oct2025/config_files/2026_04_23_global_droughtmort_new/job.%j.%N.err

#Loading modules
module load 2024
module load GCC/13.3.0
module load UDUNITS/2.2.28-GCCcore-13.3.0
module load json-c/0.17-GCCcore-13.3.0
module load OpenMPI/5.0.3-GCC-13.3.0
module load netCDF/4.9.2-gompi-2024a

export LPJROOT="/home/druijsch/LPJmL5/dev15oct2025"  

mpirun -np 256 $LPJROOT/bin/lpjml /home/druijsch/LPJmL5/dev15oct2025/config_files/2026_04_23_global_droughtmort_new/2026_04_23_global_droughtmort_new_config.cjson
