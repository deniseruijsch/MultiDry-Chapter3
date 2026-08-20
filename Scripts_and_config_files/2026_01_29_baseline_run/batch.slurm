#!/bin/bash
#SBATCH --ntasks=60
#SBATCH --ntasks-per-node=12
#SBATCH --threads-per-core=1
#SBATCH --time=14-23:00:00
#SBATCH --partition=allq
#SBATCH --dependency=afterany:260546
#SBATCH -o /eejit/home/ruiij001/dev15oct2025/config_files/2026_01_29_baseline_run/job.%j.%N.out  # STDOUT
#SBATCH -e /eejit/home/ruiij001/dev15oct2025/config_files/2026_01_29_baseline_run/job.%j.%N.err  # STDERR
#SBATCH --job-name lpjml
#SBATCH --exclusive

#SBATCH --mail-type=BEGIN,END,FAIL
#SBATCH --mail-user=d.ruijsch@uu.nl

# Set the LPJROOT environment variable
export LPJROOT="/eejit/home/ruiij001/dev15oct2025"  

mpirun -np 60 "$LPJROOT/bin/lpjml" /eejit/home/ruiij001/dev15oct2025/config_files/2026_01_29_baseline_run/2026_01_29_baseline_run_withfire_config.cjson