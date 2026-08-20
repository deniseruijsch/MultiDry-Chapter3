import xarray as xr
import numpy as np
import colormaps as cmaps
import xarray as xr
import numpy as np
import xarray as xr
from pathlib import Path

BASE_PATH = Path("/projects/prjs2023/chapter3/lpjml_output/2026_04_23_global_droughtexp_10years")

def load_all_runs(file_name, var_name):
    paths = {
        "baseline": BASE_PATH / "baseline/output" / f"{file_name}.nc",
        "MM": BASE_PATH / "MM/output" / f"{file_name}.nc",
        "DM": BASE_PATH / "DM/output" / f"{file_name}.nc",
    }
    
    data = {
        key: xr.open_dataset(path)[var_name]
        for key, path in paths.items()
    }
    
    return data
fpc = load_all_runs("fpc", "FPC")
# process function: skip total PFT (first), spatial mean
def process_fpc_per_pft(data):
    data['pft'] = data['pft'] - 2
    return data.sel(pft=slice(0, 7)).convert_calendar("standard").sel(time=slice("1970", "1979"))

# process all scenarios
fpc_proc = {name: process_fpc_per_pft(ds) for name, ds in fpc.items()}
fpc_proc



import numpy as np
import xarray as xr

def time_to_efold(y):
    y = np.asarray(y)

    if not np.isfinite(y[0]) or y[0] <= 0:
        return np.nan

    threshold = y[0] / np.e

    crossed = np.where(y <= threshold)[0]

    if len(crossed) == 0:
        return np.nan

    return crossed[0]  # months since start

tau_baseline = xr.apply_ufunc(
    time_to_efold,
    fpc_proc['baseline'],
    input_core_dims=[["time"]],
    vectorize=True,
    dask="parallelized",
    output_dtypes=[float],
)

tau_baseline.to_netcdf("/home/druijsch/scripts/2026_06_10_efolding_weighted/tau_baseline.nc")

tau_DM = xr.apply_ufunc(
    time_to_efold,
    fpc_proc['DM'],
    input_core_dims=[["time"]],
    vectorize=True,
    dask="parallelized",
    output_dtypes=[float],
)

tau_DM.to_netcdf("/home/druijsch/scripts/2026_06_10_efolding_weighted/tau_DM.nc")
