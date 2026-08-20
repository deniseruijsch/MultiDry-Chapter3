#!/bin/bash
#Set job requirements
#SBATCH --ntasks=16
#SBATCH --mem=100G
#SBATCH --time=23:00:00
#SBATCH --job-name efolding
#SBATCH --output=/home/druijsch/scripts/2026_06_10_efolding_weighted/job.%j.%N.out
#SBATCH --error=/home/druijsch/scripts/2026_06_10_efolding_weighted/job.%j.%N.err

#Loading modules
module load 2024
module load GCC/13.3.0
module load UDUNITS/2.2.28-GCCcore-13.3.0
module load json-c/0.17-GCCcore-13.3.0
module load OpenMPI/5.0.3-GCC-13.3.0
module load netCDF/4.9.2-gompi-2024a
module load Python/3.12.3-GCCcore-13.3.0

source /home/druijsch/myenv/bin/activate
python -u /home/druijsch/scripts/2026_06_10_efolding_weighted/2026_06_11_calculate_efolding.py