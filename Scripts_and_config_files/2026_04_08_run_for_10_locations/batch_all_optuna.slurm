#!/bin/bash

# Submit the first job
job1=$(sbatch /home/druijsch/LPJmL5/dev15oct2025/config_files/2026_04_08_run_for_10_locations/boreal_broadleaved_summergreen_tree/batch_optuna.slurm | awk '{print $4}')

# Chain the rest using dependencies
job2=$(sbatch --dependency=afterany:$job1 /home/druijsch/LPJmL5/dev15oct2025/config_files/2026_04_08_run_for_10_locations/boreal_needleleaved_evergreen_tree/batch_optuna.slurm | awk '{print $4}')

job3=$(sbatch --dependency=afterany:$job2 /home/druijsch/LPJmL5/dev15oct2025/config_files/2026_04_08_run_for_10_locations/boreal_needleleaved_summergreen_tree/batch_optuna.slurm | awk '{print $4}')

job4=$(sbatch --dependency=afterany:$job3 /home/druijsch/LPJmL5/dev15oct2025/config_files/2026_04_08_run_for_10_locations/temperate_broadleaved_evergreen_tree/batch_optuna.slurm | awk '{print $4}')

job5=$(sbatch --dependency=afterany:$job4 /home/druijsch/LPJmL5/dev15oct2025/config_files/2026_04_08_run_for_10_locations/temperate_broadleaved_summergreen_tree/batch_optuna.slurm | awk '{print $4}')

job6=$(sbatch --dependency=afterany:$job5 /home/druijsch/LPJmL5/dev15oct2025/config_files/2026_04_08_run_for_10_locations/temperate_needleleaved_evergreen_tree/batch_optuna.slurm | awk '{print $4}')

job7=$(sbatch --dependency=afterany:$job6 /home/druijsch/LPJmL5/dev15oct2025/config_files/2026_04_08_run_for_10_locations/tropical_broadleaved_evergreen_tree/batch_optuna.slurm | awk '{print $4}')

job8=$(sbatch --dependency=afterany:$job7 /home/druijsch/LPJmL5/dev15oct2025/config_files/2026_04_08_run_for_10_locations/tropical_broadleaved_raingreen_tree/batch_optuna.slurm | awk '{print $4}')

echo "Submitted jobs in sequence:"
echo "$job1 -> $job2 -> $job3 -> $job4 -> $job5 -> $job6 -> $job7 -> $job8"