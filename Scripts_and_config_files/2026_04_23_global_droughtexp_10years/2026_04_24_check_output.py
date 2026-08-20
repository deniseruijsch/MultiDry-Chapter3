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
    return data.sel(pft=slice(0, 7)).convert_calendar("standard").sel(time=slice("1969", "1979"))

# process all scenarios
fpc_proc = {name: process_fpc_per_pft(ds) for name, ds in fpc.items()}

import numpy as np
import xarray as xr

FPC = fpc_proc['baseline'].where(fpc_proc['baseline'] > 1e-3)

def fit_tau(y):
    y = np.asarray(y)

    mask = np.isfinite(y) & (y > 0)
    if mask.sum() < 3:
        return np.nan

    t = np.arange(y.shape[0])

    slope, _ = np.polyfit(t[mask], np.log(y[mask]), 1)
    return -1 / slope

tau_base = xr.apply_ufunc(
    fit_tau,
    FPC,
    input_core_dims=[['time']],
    vectorize=True,
    dask='parallelized',
    output_dtypes=[float]
)
tau_base.to_netcdf("/home/druijsch/scripts/2026_05_20_efolding_time_maps/tau_baseline_v4.nc")



import numpy as np
import xarray as xr

DM = fpc_proc['DM'].where(fpc_proc['DM'] > 1e-3)

def fit_tau(y):
    y = np.asarray(y)

    mask = np.isfinite(y) & (y > 0)
    if mask.sum() < 3:
        return np.nan

    t = np.arange(y.shape[0])

    slope, _ = np.polyfit(t[mask], np.log(y[mask]), 1)
    return -1 / slope

tau_dm = xr.apply_ufunc(
    fit_tau,
    DM,
    input_core_dims=[['time']],
    vectorize=True,
    dask='parallelized',
    output_dtypes=[float]
)
tau_dm.to_netcdf("/home/druijsch/scripts/2026_05_20_efolding_time_maps/tau_dm_v4.nc")

import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature

pfts = tau_base['pft'].values

nrows = 2
ncols = len(pfts)

vmin = 0
vmax = 24

fig, axes = plt.subplots(
    nrows=nrows,
    ncols=ncols,
    figsize=(3*ncols, 6),
    subplot_kw={'projection': ccrs.PlateCarree()}
)

axes = np.atleast_2d(axes)

# ---------------------------
# TOP ROW: FPC (tau_base)
# ---------------------------
for i, p in enumerate(pfts):

    ax = axes[0, i]

    data = tau_base.sel(pft=p)

    im = ax.pcolormesh(
        tau_base['lon'],
        tau_base['lat'],
        data,
        transform=ccrs.PlateCarree(),
        shading='auto',
        vmin=vmin,
        vmax=vmax
    )

    ax.coastlines()
    ax.add_feature(cfeature.BORDERS, linewidth=0.3)

    ax.set_title(f'FPC τ — PFT {p}')

# ---------------------------
# BOTTOM ROW: DM
# ---------------------------
for i, p in enumerate(pfts):

    ax = axes[1, i]

    data = tau_dm.sel(pft=p)

    im = ax.pcolormesh(
        tau_dm['lon'],
        tau_dm['lat'],
        data,
        transform=ccrs.PlateCarree(),
        shading='auto',
        vmin=vmin,
        vmax=vmax
    )

    ax.coastlines()
    ax.add_feature(cfeature.BORDERS, linewidth=0.3)

    ax.set_title(f'DM τ — PFT {p}')

# ---------------------------
# shared colorbar
# ---------------------------
cbar = fig.colorbar(
    im,
    ax=axes,
    orientation='horizontal',
    fraction=0.03,
    pad=0.05
)

cbar.set_label('E-folding time (months)')
cbar.set_ticks([0, 6, 12, 18, 24])

plt.tight_layout()
plt.savefig("/home/druijsch/LPJmL5/dev15oct2025/config_files/2026_04_23_global_droughtexp_10years/tau_map_vs.png", dpi = 300)
plt.show()





# import xarray as xr
# import numpy as np
# import xarray as xr
# from pathlib import Path

# BASE_PATH = Path("/projects/prjs2023/chapter3/lpjml_output/2026_04_23_global_droughtexp_10years")

# def load_all_runs(file_name, var_name):
#     paths = {
#         "baseline": BASE_PATH / "baseline/output" / f"{file_name}.nc",
#         "MM": BASE_PATH / "MM/output" / f"{file_name}.nc",
#         "DM": BASE_PATH / "DM/output" / f"{file_name}.nc",
#     }
    
#     data = {
#         key: xr.open_dataset(path)[var_name]
#         for key, path in paths.items()
#     }
    
#     return data
# fpc = load_all_runs("fpc", "FPC")
# # process function: skip total PFT (first), spatial mean
# def process_fpc_per_pft(data):
#     return data.sel(pft=slice(2, 9)).convert_calendar("standard").sel(time=slice("1970", "1979"))

# # process all scenarios
# fpc_proc = {name: process_fpc_per_pft(ds) for name, ds in fpc.items()}

# import numpy as np
# import xarray as xr

# def compute_efolding(FPC):
#     # avoid log(0)
#     FPC = FPC.where(FPC > 0)

#     logFPC = np.log(FPC)

#     # convert time to numeric (years)
#     t = xr.DataArray(
#         (FPC['time'].dt.year + FPC['time'].dt.dayofyear / 365.0),
#         dims="time"
#     )

#     # subtract first time to avoid big numbers
#     t = t - t.isel(time=0)

#     # linear regression: slope = -k
#     slope = xr.apply_ufunc(
#         lambda x, y: np.polyfit(x, y, 1)[0],
#         t, logFPC,
#         input_core_dims=[["time"], ["time"]],
#         vectorize=True,
#         dask="parallelized",
#         output_dtypes=[float]
#     )

#     k = -slope
#     tau = 1 / k   # e-folding time

#     return tau
# tau_base = compute_efolding(fpc_proc['baseline'])
# tau_base.to_netcdf("/home/druijsch/LPJmL5/dev15oct2025/config_files/2026_04_23_global_droughtexp_10years/tau_baseline.nc")
# print("tau_base done")
# tau_DM   = compute_efolding(fpc_proc['DM'])
# tau_DM.to_netcdf("/home/druijsch/LPJmL5/dev15oct2025/config_files/2026_04_23_global_droughtexp_10years/tau_DM.nc")
# print("tau_DM done")

# valid_pfts = [
#     "tropical broadleaved evergreen tree",
#     "tropical broadleaved raingreen tree",
#     "temperate needleleaved evergreen tree",
#     "temperate broadleaved evergreen tree",
#     "temperate broadleaved summergreen tree",
#     "boreal needleleaved evergreen tree",
#     "boreal broadleaved summergreen tree",
#     "boreal needleleaved summergreen tree",
# ]
# import matplotlib.pyplot as plt
# import cartopy.crs as ccrs
# import numpy as np

# def plot_pft_comparison_autoscale(tau_base, tau_DM, valid_pfts):
#     n = len(valid_pfts)
#     ncols = min(4, n)
#     nrows = int(np.ceil(n / ncols))

#     fig = plt.figure(figsize=(6*ncols, 8*nrows))

#     for i, pft in enumerate(valid_pfts):
#         row = i // ncols
#         col = i % ncols

#         base = tau_base.sel(pft=pft)
#         dm   = tau_DM.sel(pft=pft)

#         # --- compute shared vmin/vmax for THIS PFT ---
#         combined = np.concatenate([
#             base.values.flatten(),
#             dm.values.flatten()
#         ])

#         combined = combined[np.isfinite(combined)]

#         if len(combined) == 0:
#             continue

#         # robust scaling (avoids outliers blowing up colorbar)
#         vmin = np.percentile(combined, 5)
#         vmax = np.percentile(combined, 95)

#         # --- TOP: baseline ---
#         ax_top = plt.subplot(
#             2*nrows, ncols, 2*row*ncols + col + 1,
#             projection=ccrs.PlateCarree()
#         )

#         im = base.plot(
#             ax=ax_top,
#             transform=ccrs.PlateCarree(),
#             cmap="YlOrRd_r",
#             vmin=vmin, vmax=vmax,
#             add_colorbar=False
#         )

#         ax_top.coastlines()
#         ax_top.set_title(f"PFT {pft} (Baseline)")
#         ax_top.set_xticks([])
#         ax_top.set_yticks([])

#         # --- BOTTOM: drought ---
#         ax_bot = plt.subplot(
#             2*nrows, ncols, (2*row+1)*ncols + col + 1,
#             projection=ccrs.PlateCarree()
#         )

#         dm.plot(
#             ax=ax_bot,
#             transform=ccrs.PlateCarree(),
#             cmap="YlOrRd_r",
#             vmin=vmin, vmax=vmax,
#             add_colorbar=False
#         )

#         ax_bot.coastlines()
#         ax_bot.set_title(f"PFT {pft} (Drought)")
#         ax_bot.set_xticks([])
#         ax_bot.set_yticks([])

#         # --- shared colorbar per PFT ---
#         cbar = fig.colorbar(
#             im,
#             ax=[ax_top, ax_bot],
#             orientation="vertical",
#             fraction=0.046,
#             pad=0.04
#         )
#         cbar.set_label("E-folding time (years)")

#     #plt.tight_layout()
#     plt.savefig("/home/druijsch/LPJmL5/dev15oct2025/config_files/2026_04_23_global_droughtexp_10years/tau_comparison.png", dpi = 300)
#     plt.show()
    
# plot_pft_comparison_autoscale(tau_base, tau_DM, valid_pfts)
# print("done")