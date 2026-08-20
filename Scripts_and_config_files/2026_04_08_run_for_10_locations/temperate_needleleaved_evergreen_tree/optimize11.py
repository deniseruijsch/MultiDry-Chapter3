import os
import re
import subprocess
import xarray as xr
import numpy as np
import optuna
import json

# ==============================
# 0. Observed data and slopes
# ==============================
obs_spei = xr.open_dataset(
    "/home/druijsch/data/SPEI/"
    "SPEI12_monthly_1901_2019_0_1_degree_2025_01_06_remapnn.nc"
)["SPEI"]

aridity = xr.open_dataset(
    "/home/druijsch/data/aridity/aridity_mean_0_1_degree.nc"
).__xarray_dataarray_variable__

aridity['lon'] = obs_spei['lon']
aridity['lat'] = obs_spei['lat']

S_obs_mort = -0.46
intercept_mort = -1.96

S_obs_gpp_water = {
    0: 0.14, 1: 0.12, 2: 0.12, 3: 0.17,
    4: 0.18, 5: 0.08, 6: 0.08, 7: 0.10
}

intercept_gpp = {
    0: 0.02, 1: 0.03, 2: 0.02, 3: 0.04, 
    4: 0.04, 5: 0.01, 6: 0.00, 7: 0.01
}

# ==============================
# Calibration period
# ==============================
START_YEAR = 2000 #2000
END_YEAR   = 2019 #2019

# ==============================
# 1. Utilities
# ==============================
def standardized_anomalies(data, start_year=START_YEAR, end_year=END_YEAR):
    data_ref = data.sel(time=slice(f"{start_year}-01-01", f"{end_year}-12-31"))
    clim_mean = data_ref.groupby("time.month").mean("time")
    clim_std = data_ref.groupby("time.month").std("time")
    clim_std = clim_std.where(clim_std != 0)

    return xr.apply_ufunc(
        lambda x, m, s: (x - m) / s if s != 0 else np.nan,
        data.groupby("time.month"),
        clim_mean,
        clim_std,
        vectorize=True
    )

# ==============================
# 2. LPJ parameter modification
# ==============================
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

def get_pft_values(trial):
    vals = {}
    for pft in pfts:
        a = trial.suggest_float(f"alpha_{pft.replace(' ','_')}", 0.01, 0.99)
        b = trial.suggest_float(f"beta_{pft.replace(' ','_')}", 0.01, 25.0)
        vals[pft] = (a, b)
    return vals

def modify_turnover_file(pft_vals):
    fname = "/home/druijsch/LPJmL5/dev15oct2025/src/tree/turnover_daily_tree.c"
    with open(fname) as f:
        txt = f.read()

    block = ""
    for i, (pft, (a, b)) in enumerate(pft_vals.items()):
        cond = "if" if i == 0 else "} else if"
        block += f'{cond}(strcmp(pft->par->name,"{pft}")==0) {{\n'
        block += f"  alpha = {a};\n  beta = {b};\n"
    block += "} else {\n  alpha = 0.2;\n  beta = 1.0;\n}\n"

    txt = re.sub(
        r"// START OPTUNA ALPHA/BETA.*?// END OPTUNA ALPHA/BETA",
        f"// START OPTUNA ALPHA/BETA\n{block}// END OPTUNA ALPHA/BETA",
        txt,
        flags=re.DOTALL
    )

    with open(fname, "w") as f:
        f.write(txt)

# ==============================
# 3. Compile & run LPJ
# ==============================
def compile_lpjml():
    base = "/home/druijsch/LPJmL5/dev15oct2025"
    subprocess.run(["bash", "configure.sh", "-prefix", f"{base}/install"],
                   cwd=base, check=True, stdout=subprocess.DEVNULL)
    subprocess.run(["make"], cwd=base, check=True, stdout=subprocess.DEVNULL)
    subprocess.run(["make", "install"], cwd=base, check=True, stdout=subprocess.DEVNULL)

def make_trial_config(n):
    cfg_template = "/home/druijsch/LPJmL5/dev15oct2025/config_files/2026_01_20_run_for_every_location/temperate_needleleaved_evergreen_tree/temperate_needleleaved_evergreen_tree_config_optuna.cjson"
    trial_dir = f"/projects/prjs2023/chapter3/lpjml_output/2026_01_20_run_for_every_location/temperate_needleleaved_evergreen_tree/run_{n:04d}"
    os.makedirs(f"{trial_dir}/output", exist_ok=True)

    with open(cfg_template) as f:
        txt = f.read().replace("{{outpath}}", f"{trial_dir}/output")

    cfg_file = f"{trial_dir}/config.cjson"
    with open(cfg_file, "w") as f:
        f.write(txt)

    return cfg_file, trial_dir

def run_lpj(cfg_file):
    subprocess.run(
        ["mpirun", "-np", "40",
         "/home/druijsch/LPJmL5/dev15oct2025/install/bin/lpjml",
         cfg_file],
        check=True
    )

# ==============================
# 4. Load outputs
# ==============================
def load_outputs(trial_dir):
    out = f"{trial_dir}/output"
    gpp = xr.open_dataset(f"{out}/pft_gpp.nc")["GPP"].convert_calendar("standard")
    mort = xr.open_dataset(f"{out}/pft_mort.nc")["mortality"].convert_calendar("standard")
    fpc = xr.open_dataset(f"{out}/fpc.nc")["FPC"][:,1:].convert_calendar("standard")
    fpc['pft'] = fpc.pft - 1
    return (
        gpp.sel(time=slice(f"{START_YEAR}", f"{END_YEAR}")).resample(time = 'MS').mean(),
        mort.sel(time=slice(f"{START_YEAR}", f"{END_YEAR}")).resample(time = 'MS').mean(),
        fpc.sel(time=slice(f"{START_YEAR}", f"{END_YEAR}")).resample(time = 'MS').mean()
    )

def objective(trial):
    # ---- Modify LPJ parameters
    modify_turnover_file(get_pft_values(trial))
    # mort_div = trial.suggest_float("mort_divisor", 1, 12)
    # modify_mortality_file(mort_div)

    gpp_loss_water = {pft: None for pft in pfts}
    mort_loss_per_pft = {pft: None for pft in pfts}

    status = "success"
    error_msg = None
    obj = None

    try:
        # ---- Compile and run LPJ
        compile_lpjml()
        cfg_file, trial_dir = make_trial_config(trial.number)
        run_lpj(cfg_file)
        mod_gpp, mort_da, fpc_da = load_outputs(trial_dir)
        
        # Mask very small FPC
        fpc_safe = fpc_da.where(fpc_da > 1e-5)

        # Compute per-cover GPP and standardized anomalies
        gpp_per_fpc = (mod_gpp / fpc_safe).convert_calendar("standard").sel(
            time=slice(f"{START_YEAR}", f"{END_YEAR}")
        )
        mod_gpp_std = standardized_anomalies(gpp_per_fpc)

        # Subset aridity and SPEI to model domain
        arid = aridity.sel(
            lat=slice(mod_gpp.lat.min(), mod_gpp.lat.max()),
            lon=slice(mod_gpp.lon.min(), mod_gpp.lon.max())
        )
        obs_spei_sub = obs_spei.sel(
            lat=slice(mod_gpp.lat.min(), mod_gpp.lat.max()),
            lon=slice(mod_gpp.lon.min(), mod_gpp.lon.max()),
            time=slice(f"{START_YEAR}", f"{END_YEAR}")
        ).resample(time='MS').mean()

        # Safety check: time alignment
        assert np.all(mod_gpp.time.values == obs_spei_sub.time.values), "GPP and SPEI not time-aligned!"
        spei_flat = obs_spei_sub.values.flatten()

        # ---- Monthly aggregation for GPP & SPEI
        for pft_idx in range(8):
            pft_name = pfts[pft_idx]
            gpp_pft = mod_gpp_std.isel(pft=pft_idx)
            arid_3d = arid.broadcast_like(gpp_pft)

            gpp_w = gpp_pft.where(arid_3d < 1).values.flatten()
            spei_w = spei_flat[:gpp_w.size]
            mask = np.isfinite(gpp_w) & np.isfinite(spei_w)

            if mask.sum() > 10:
                # gpp_target = S_obs_gpp_water[pft_idx] * spei_w[mask] + intercept_gpp[pft_idx]
                # gpp_loss_water[pft_name] = np.sqrt(np.mean((gpp_w[mask] - gpp_target)**2))
                
                # Fit a line through the model data
                S_fit, b_fit = np.polyfit(spei_w[mask], gpp_w[mask], 1)

                # Evaluate the fitted line at the same SPEI values
                y_line_model = S_fit * spei_w[mask] + b_fit
                y_line_obs   = S_obs_gpp_water[pft_idx] * spei_w[mask] + intercept_gpp[pft_idx]

                # Compute RMSE between lines
                gpp_loss_water[pft_name] = np.sqrt(np.mean((y_line_model - y_line_obs)**2))
            else:
                gpp_loss_water[pft_name] = None

        # ---- YEARLY aggregation for mortality & SPEI
        mort_y = mort_da.resample(time="YS").sum()          # yearly SUM mortality
        spei_y = obs_spei_sub.resample(time="YS").mean()   # yearly MEAN SPEI-12
        assert np.all(mort_y.time.values == spei_y.time.values), "Yearly mortality and SPEI are not aligned!"

        # ---- Per-PFT mortality check
        for pft_idx in range(8):
            pft_name = pfts[pft_idx]
            mort_pft_y = mort_y.isel(pft=pft_idx)

            if (mort_pft_y > 0.25).any():  # fail if any year exceeds 25%
                print(f"[FAIL] Trial {trial.number}: {pft_name} mortality exceeded 25% in at least one year")
                mort_loss_per_pft[pft_name] = None
            else:
                mort_flat = np.log10(mort_pft_y.values.flatten())
                spei_flat_y = spei_y.values.flatten()
                mask = np.isfinite(mort_flat) & np.isfinite(spei_flat_y)

                if mask.sum() > 10:
                    # mort_target = S_obs_mort * spei_flat_y[mask] + intercept_mort
                    # mort_loss_per_pft[pft_name] = np.sqrt(np.mean((mort_flat[mask] - mort_target)**2))
                    
                    # Fit a line through the model mortality data
                    S_fit, b_fit = np.polyfit(spei_flat_y[mask], mort_flat[mask], 1)

                    # Evaluate both lines at the same SPEI values
                    y_line_model = S_fit * spei_flat_y[mask] + b_fit
                    y_line_obs   = S_obs_mort * spei_flat_y[mask] + intercept_mort

                    # Compute RMSE between lines
                    mort_loss_per_pft[pft_name] = np.sqrt(np.mean((y_line_model - y_line_obs)**2))
                else:
                    mort_loss_per_pft[pft_name] = None

        # ---- Build final objective vector (16 values)
        obj = []
        for pft in pfts:
            obj.append(gpp_loss_water[pft] if gpp_loss_water[pft] is not None else 1e6)
        for pft in pfts:
            obj.append(mort_loss_per_pft[pft] if mort_loss_per_pft[pft] is not None else 1e6)

    except Exception as e:
        status = "failed"
        error_msg = str(e)
        print(f"[FAIL] Trial {trial.number}: {error_msg}")
        obj = [1e6] * N_OBJECTIVES

    print(f"[INFO] Trial {trial.number}: calibrating period {START_YEAR}-{END_YEAR}")

    # ---- ALWAYS SAVE
    folder = "/home/druijsch/LPJmL5/dev15oct2025/config_files/2026_01_20_run_for_every_location/temperate_needleleaved_evergreen_tree"
    os.makedirs(folder, exist_ok=True)
    loss_file = os.path.join(folder, "loss_per_pft_all_trials.json")

    if os.path.exists(loss_file) and os.path.getsize(loss_file) > 0:
        try:
            with open(loss_file, "r") as f:
                all_trials = json.load(f)
        except json.JSONDecodeError:
            all_trials = {}
    else:
        all_trials = {}

    all_trials[str(trial.number)] = {
        "status": status,
        "error": error_msg,
        "params": dict(trial.params),
        "gpp_loss_water": gpp_loss_water,
        "mort_loss_per_pft": mort_loss_per_pft
    }

    with open(loss_file, "w") as f:
        json.dump(all_trials, f, indent=2)

    if status == "success":
        print(f"[SUCCESS] Trial {trial.number}")

    return tuple(obj)




# ==============================
# 6. Run Optuna study
# ==============================
if __name__ == "__main__":
    folder = "/home/druijsch/LPJmL5/dev15oct2025/config_files/2026_01_20_run_for_every_location/temperate_needleleaved_evergreen_tree"
    os.makedirs(folder, exist_ok=True)

    db_file = os.path.join(folder, "lpj_multiobjective.db")
    if os.path.exists(db_file):
        os.remove(db_file)

    # sampler = optuna.samplers.TPESampler(
    #     n_startup_trials=30,
    #     multivariate=True
    # )

    study = optuna.create_study(
        directions=["minimize"] * N_OBJECTIVES,
        #sampler=sampler,
        storage=f"sqlite:///{db_file}",
        study_name="lpj_multiobjective_pftwise",
        load_if_exists=False
    )

    study.optimize(objective, n_trials=500)

    df = study.trials_dataframe()
    df.to_csv(os.path.join(folder, "optuna_multiobjective_results.csv"), index=False)

    print("Pareto-optimal solutions:")
    for t in study.best_trials:
        print(dict(zip(OBJECTIVE_NAMES, t.values)))
        print("params:", t.params)
        print("-" * 80)
