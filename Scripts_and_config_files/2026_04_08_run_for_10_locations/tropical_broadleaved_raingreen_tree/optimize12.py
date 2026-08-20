import os
import re
import subprocess
import xarray as xr
import numpy as np
import optuna
import json
import shutil
from multiprocessing import Pool

# ==============================
# 0. SETTINGS
# ==============================
locations = [
    "patch_1", "patch_2", "patch_3", "patch_4", "patch_5",
    "patch_6", "patch_7", "patch_8", "patch_9", "patch_10"
]

BASE_CONFIG_DIR = "/home/druijsch/LPJmL5/dev15oct2025/config_files/2026_04_08_run_for_10_locations/tropical_broadleaved_raingreen_tree"
LPJ_BIN = "/home/druijsch/LPJmL5/dev15oct2025/install/bin/lpjml"
OUTPUT_DIR = "/projects/prjs2023/chapter3/lpjml_output/2026_04_08_run_for_10_locations/tropical_broadleaved_raingreen_tree"
os.environ["LPJROOT"] = "/home/druijsch/LPJmL5/dev15oct2025"
# TOTAL_CORES = 512

START_YEAR = 2000
END_YEAR   = 2019

pfts = [
    "tropical broadleaved evergreen tree",
    "tropical broadleaved raingreen tree",
    "temperate needleleaved evergreen tree",
    "temperate broadleaved evergreen tree",
    "temperate broadleaved summergreen tree",
    "boreal needleleaved evergreen tree",
    "boreal broadleaved summergreen tree",
    "boreal needleleaved summergreen tree"
]

OBJECTIVE_NAMES = [f"gpp_water_{pft}" for pft in pfts] + [f"mort_{pft}" for pft in pfts]
N_OBJECTIVES = len(OBJECTIVE_NAMES)  # 16

# ==============================
# 1. Observations
# ==============================
obs_spei = xr.open_dataset(
    "/projects/prjs2023/chapter3/SPEI/SPEI12_monthly_1901_2019_0_1_degree_2025_01_06_remapnn.nc"
)["SPEI"]

S_obs_mort = -0.46
intercept_mort = -1.96

S_obs_gpp_water = {0:0.14,1:0.12,2:0.12,3:0.17,4:0.18,5:0.08,6:0.08,7:0.10}
intercept_gpp = {0:0.02,1:0.03,2:0.02,3:0.04,4:0.04,5:0.01,6:0.00,7:0.01}

# ==============================
# 2. Utilities
# ==============================
def standardized_anomalies(data):
    data_ref = data.sel(time=slice(f"{START_YEAR}", f"{END_YEAR}"))
    clim_mean = data_ref.groupby("time.month").mean("time")
    clim_std = data_ref.groupby("time.month").std("time")
    clim_std = clim_std.where(clim_std != 0)

    return xr.apply_ufunc(
        lambda x, m, s: (x - m)/s if s!=0 else np.nan,
        data.groupby("time.month"),
        clim_mean,
        clim_std,
        vectorize=True
    )

# ==============================
# 3. LPJ parameter modification
# ==============================

def get_pft_values(trial):
    vals = {}
    for pft in pfts:
        a = trial.suggest_float(f"alpha_{pft.replace(' ','_')}", 0.01, 0.99)
        b = trial.suggest_float(f"beta_{pft.replace(' ','_')}", 0.01, 25.0)
        vals[pft] = (a,b)
    return vals

def modify_turnover_file(pft_vals):
    fname = "/home/druijsch/LPJmL5/dev15oct2025/src/tree/turnover_daily_tree.c"
    with open(fname) as f:
        txt = f.read()
    
    block = ""
    for i,(pft,(a,b)) in enumerate(pft_vals.items()):
        cond = "if" if i==0 else "} else if"
        block += f'{cond}(strcmp(pft->par->name,"{pft}")==0) {{\n'
        block += f"  alpha = {a};\n  beta = {b};\n"
    block += "} else {\n  alpha = 0.2;\n  beta = 1.0;\n}\n"

    txt = re.sub(
        r"// START OPTUNA ALPHA/BETA.*?// END OPTUNA ALPHA/BETA",
        f"// START OPTUNA ALPHA/BETA\n{block}// END OPTUNA ALPHA/BETA",
        txt,
        flags=re.DOTALL
    )

    with open(fname,"w") as f:
        f.write(txt)

# ==============================
# 4. Compile LPJ
# ==============================
def compile_lpjml():
    base = "/home/druijsch/LPJmL5/dev15oct2025"
    subprocess.run(["make"], cwd=base, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["make","install"], cwd=base, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# ==============================
# 5. Config creation
# ==============================
import os
import re

import os
import re

def make_trial_config(trial_number, num_patches=10):
    """
    Create LPJ config files for all patches in a trial.
    Ensures directories exist and input/restart paths are correct.
    """
    cfg_files = []

    for patch_idx in range(1, num_patches + 1):
        patch_name = f"patch_{patch_idx}"

        # Directories for this trial and patch
        trial_dir = os.path.join(BASE_CONFIG_DIR, f"trial_{trial_number:04d}", patch_name)
        os.makedirs(trial_dir, exist_ok=True)

        # Output directory (LPJ requires this to exist)
        outpath = os.path.join(OUTPUT_DIR, f"trial_{trial_number:04d}", patch_name)
        os.makedirs(outpath, exist_ok=True)
        os.makedirs(os.path.join(outpath, "output"), exist_ok=True)

        cfg_file = os.path.join(trial_dir, "config.cjson")

        # Correct input file name (no underscore before number)
        input_file = os.path.join(
            BASE_CONFIG_DIR,
            "spinup", "configs",
            f"tropical_broadleaved_raingreen_tree_patch{patch_idx}_input.cjson"
        )

        base_cfg = os.path.join(BASE_CONFIG_DIR, "tropical_broadleaved_raingreen_tree_config_optuna.cjson")

        # Restart filename for this patch
        restart_filename = os.path.join(
            "/home/druijsch/LPJmL5/dev15oct2025/restart/2026_04_08_run_for_10_locations/tropical_broadleaved_raingreen_tree",
            patch_name,
            "restart_1960_crop_stdfire.lpj"
        )

        # Read base config
        with open(base_cfg) as f:
            txt = f.read()

        # Replace "input" section
        txt = re.sub(
            r'("input"\s*:\s*#include\s*".*?")',
            f'"input":\n  #include "{input_file}"',
            txt,
            flags=re.DOTALL
        )

        # Replace "outpath"
        txt = re.sub(
            r'("outpath"\s*:\s*".*?")',
            f'"outpath": "{outpath}"',
            txt
        )

        # Replace "restart_filename"
        txt = re.sub(
            r'("restart_filename"\s*:\s*".*?")',
            f'"restart_filename": "{restart_filename}"',
            txt
        )

        # Write updated config
        with open(cfg_file, "w") as f:
            f.write(txt)

        cfg_files.append(cfg_file)

    return cfg_files

# # ==============================
# # 6. Run LPJ in parallel
# # ==============================
# def run_lpj(cfg_file):
#     try:
#         subprocess.run(["mpirun","-np","52","/home/druijsch/LPJmL5/dev15oct2025/install/bin/lpjml",cfg_file], check=True)
#         return cfg_file,"success"
#     except subprocess.CalledProcessError as e:
#         return cfg_file,f"failed: {e}"

# def run_all_lpj_parallel(cfg_files):
#     with Pool(min(len(cfg_files), TOTAL_CORES//10)) as p:
#         return p.map(run_lpj, cfg_files)
    

# ==============================
# 6. Run LPJ sequentially (optimized)
# ==============================
def run_lpj(cfg_file):
    """
    Run LPJ for a single config file using MPI.
    Returns success/failure.
    """
    try:
        # Run LPJ with 63 MPI processes (adjust if needed)
        subprocess.run(
            ["mpirun", "-np", "63", "/home/druijsch/LPJmL5/dev15oct2025/install/bin/lpjml", cfg_file],
            check=True,
        )
        return cfg_file, "success"
    except subprocess.CalledProcessError as e:
        return cfg_file, f"failed: {e}"

def run_all_lpj_sequential(cfg_files):
    """
    Run all patches sequentially, each using MPI.
    Avoids oversubscription of cores.
    """
    results = []
    for cfg_file in cfg_files:
        cfg, status = run_lpj(cfg_file)
        results.append((cfg, status))
        if status != "success":
            print(f"Warning: {cfg} failed")
    return results

# ==============================
# 7. Load and calculate objectives
# ==============================

def compute_gpp_objectives(trial_number):
    trial_base = os.path.join(OUTPUT_DIR, f"trial_{trial_number:04d}")

    gpp_vals = {pft: [] for pft in range(8)}
    spei_vals = {pft: [] for pft in range(8)}

    # Prepare SPEI once
    spei_local = obs_spei.sel(
        time=slice(f"{START_YEAR}", f"{END_YEAR}")
    )#.resample(time='MS').mean()

    for loc in locations:
        out = os.path.join(trial_base, loc, "output")

        gpp = xr.open_dataset(os.path.join(out, "pft_gpp.nc")).GPP \
            .convert_calendar("standard") \
            .sel(time=slice(f"{START_YEAR}", f"{END_YEAR}")) \
            .resample(time='MS').mean()

        fpc = xr.open_dataset(os.path.join(out, "fpc.nc")).FPC[:, 1:] \
            .convert_calendar("standard") \
            .sel(time=slice(f"{START_YEAR}", f"{END_YEAR}")) \
            .resample(time='MS').mean()

        fpc['pft'] = fpc.pft - 1

        fpc_safe = fpc.where(fpc > 1e-5)
        gpp_per_fpc = gpp / fpc_safe

        gpp_std = standardized_anomalies(gpp_per_fpc)

        spei_loc = spei_local.sel(lat=gpp.lat, lon=gpp.lon, method="nearest")

        spei_flat = spei_loc.values.flatten()

        for pft_idx in range(8):
            gpp_flat = gpp_std.isel(pft=pft_idx).values.flatten()

            mask = np.isfinite(gpp_flat) & np.isfinite(spei_flat)

            gpp_vals[pft_idx].append(gpp_flat[mask])
            spei_vals[pft_idx].append(spei_flat[mask])

    # ==============================
    # Compute slopes
    # ==============================
    slopes = {}
    objectives = []

    for pft_idx in range(8):
        gpp_all = np.concatenate(gpp_vals[pft_idx])
        spei_all = np.concatenate(spei_vals[pft_idx])

        mask = np.isfinite(gpp_all) & np.isfinite(spei_all)

        if mask.sum() > 10:
            S_fit, b_fit = np.polyfit(spei_all[mask], gpp_all[mask], 1)

            slopes[pft_idx] = {"slope": S_fit, "intercept": b_fit}

            y_model = S_fit * spei_all[mask] + b_fit
            y_obs = (
                S_obs_gpp_water[pft_idx] * spei_all[mask]
                + intercept_gpp[pft_idx]
            )

            rmse = np.sqrt(np.mean((y_model - y_obs) ** 2))
            objectives.append(rmse)

        else:
            slopes[pft_idx] = {"slope": np.nan, "intercept": np.nan}
            objectives.append(1e6)

    return slopes, objectives



def compute_mortality_objectives(trial_number):
    trial_base = os.path.join(OUTPUT_DIR, f"trial_{trial_number:04d}")

    mort_vals = {pft: [] for pft in range(8)}
    spei_vals = {pft: [] for pft in range(8)}

    spei_local = obs_spei.sel(
        time=slice(f"{START_YEAR}", f"{END_YEAR}")
    ).resample(time='YS').mean()

    for loc in locations:
        out = os.path.join(trial_base, loc, "output")

        mort = xr.open_dataset(os.path.join(out, "pft_mort.nc")).mortality \
            .convert_calendar("standard") \
            .sel(time=slice(f"{START_YEAR}", f"{END_YEAR}")) \
            .resample(time="YS").sum()

        spei_loc = spei_local.sel(lat=mort.lat, lon=mort.lon, method="nearest")

        spei_flat = spei_loc.values.flatten()

        for pft_idx in range(8):
            mort_flat = mort.isel(pft=pft_idx).values.flatten()

            # log transform
            mort_flat = np.log10(mort_flat)

            mask = np.isfinite(mort_flat) & np.isfinite(spei_flat)

            mort_vals[pft_idx].append(mort_flat[mask])
            spei_vals[pft_idx].append(spei_flat[mask])

    # ==============================
    # Compute slopes
    # ==============================
    slopes = {}
    objectives = []

    for pft_idx in range(8):
        mort_all = np.concatenate(mort_vals[pft_idx])
        spei_all = np.concatenate(spei_vals[pft_idx])

        mask = np.isfinite(mort_all) & np.isfinite(spei_all)

        if mask.sum() > 10:
            S_fit, b_fit = np.polyfit(spei_all[mask], mort_all[mask], 1)

            slopes[pft_idx] = {"slope": S_fit, "intercept": b_fit}

            y_model = S_fit * spei_all[mask] + b_fit
            y_obs = S_obs_mort * spei_all[mask] + intercept_mort

            rmse = np.sqrt(np.mean((y_model - y_obs) ** 2))
            objectives.append(rmse)

        else:
            slopes[pft_idx] = {"slope": np.nan, "intercept": np.nan}
            objectives.append(1e6)

    return slopes, objectives


# ==============================
# 8. Objective (with slopes in JSON)
# ==============================
def objective(trial):
    # 1. Update parameters + compile
    modify_turnover_file(get_pft_values(trial))
    compile_lpjml()

    # 2. Run LPJ sequentially
    cfg_files = make_trial_config(trial.number)
    run_all_lpj_sequential(cfg_files)

    # 3. Compute objectives
    gpp_slopes, gpp_obj = compute_gpp_objectives(trial.number)
    mort_slopes, mort_obj = compute_mortality_objectives(trial.number)

    # 4. Prepare JSON-friendly dict
    gpp_loss_water = {pft_name: gpp_obj[i] for i, pft_name in enumerate(pfts)}
    mort_loss_per_pft = {pft_name: mort_obj[i] for i, pft_name in enumerate(pfts)}

    # include slopes/intercepts in the JSON
    gpp_slopes_json = {pft_name: gpp_slopes[i] for i, pft_name in enumerate(pfts)}
    mort_slopes_json = {pft_name: mort_slopes[i] for i, pft_name in enumerate(pfts)}

    loss_record = {
        "params": dict(trial.params),
        "gpp_loss_water": gpp_loss_water,
        "mort_loss_per_pft": mort_loss_per_pft,
        "gpp_slopes": gpp_slopes_json,
        "mort_slopes": mort_slopes_json
    }

    # 5. Save to JSON
    loss_file = os.path.join(BASE_CONFIG_DIR, "loss_per_trial.json")
    os.makedirs(BASE_CONFIG_DIR, exist_ok=True)

    if os.path.exists(loss_file) and os.path.getsize(loss_file) > 0:
        try:
            with open(loss_file, "r") as f:
                all_trials = json.load(f)
        except json.JSONDecodeError:
            all_trials = {}
    else:
        all_trials = {}

    all_trials[str(trial.number)] = loss_record
    with open(loss_file, "w") as f:
        json.dump(all_trials, f, indent=2)

    # 6. Return 16 objectives for Optuna (8 GPP + 8 mortality)
    return tuple(gpp_obj + mort_obj)

# ==============================
# 9. Run Optuna
# ==============================
if __name__=="__main__":
    study = optuna.create_study(directions=["minimize"]*N_OBJECTIVES)
    study.optimize(objective,n_trials=100)
    
    print("Pareto-optimal solutions:")
    for t in study.best_trials:
        print(dict(zip(OBJECTIVE_NAMES, t.values)))
        print("params:", t.params)
        print("-" * 80)