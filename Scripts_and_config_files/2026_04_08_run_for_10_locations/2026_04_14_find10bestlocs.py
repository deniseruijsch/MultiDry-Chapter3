import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
import os

dynamic_lc = xr.open_dataset("/projects/prjs2023/chapter3/lpjml_output/2026_01_29_baseline_run/monthlybackground/output/fpc.nc").FPC.sel(time = "1960-01")[0,1:]

aridity = xr.open_dataset(
    "/projects/prjs2023/chapter3/aridity/aridity_mean_0_1_degree.nc"
).__xarray_dataarray_variable__.sel(lat = slice(-55.9,83.75))

aridity['lon'] = dynamic_lc['lon']
aridity['lat'] = dynamic_lc['lat']

pft_names_main = [
    "tropical broadleaved evergreen tree",
    "tropical broadleaved raingreen tree",
    "temperate needleleaved evergreen tree",
    "temperate broadleaved evergreen tree",
    "temperate broadleaved summergreen tree",
    "boreal needleleaved evergreen tree",
    "boreal broadleaved summergreen tree",
    "boreal needleleaved summergreen tree"
]
import numpy as np
import xarray as xr
import os

# ----------------------------
# PARAMETERS
# ----------------------------
patch_height = 8
patch_width  = 8
buffer_deg   = 1.0
aridity_thr  = 1.0
top_n        = 10
min_dist_cells = 20

# ----------------------------
# FUNCTION: find distinct hotspots
# ----------------------------
def find_top_n_hotspots_dist(patch_sum, n=10, min_dist_cells=20):
    data = patch_sum.values
    flat = data.flatten()

    valid_idx = np.where(~np.isnan(flat))[0]
    sorted_idx = valid_idx[np.argsort(flat[valid_idx])[::-1]]

    hotspots = []

    for idx in sorted_idx:
        i, j = np.unravel_index(idx, data.shape)

        too_close = False
        for (ii, jj, _) in hotspots:
            if abs(i - ii) < min_dist_cells and abs(j - jj) < min_dist_cells:
                too_close = True
                break

        if not too_close:
            hotspots.append((i, j, data[i, j]))

        if len(hotspots) == n:
            break

    return hotspots


# ----------------------------
# CLIMATE FILES
# ----------------------------
climate_data = {
    "wind":  { "var": "sfcwind", "file": "/projects/prjs2023/chapter3/lpjml_input/gswp3-w5e5_obsclim_sfcwind_global_daily_1901_2019_version_2021-09-XX.nc" },
    "temp":  { "var": "tas",     "file": "/projects/prjs2023/chapter3/lpjml_input/gswp3-w5e5_obsclim_tas_global_daily_1901_2019_version_2021-09-XX_degreesC.nc" },
    "prec":  { "var": "pr",      "file": "/projects/prjs2023/chapter3/lpjml_input/gswp3-w5e5_obsclim_pr_global_daily_1901_2019_version_2021-09-XX_mm_day.nc" },
    "lwdown":{ "var": "rlds",    "file": "/projects/prjs2023/chapter3/lpjml_input/gswp3-w5e5_obsclim_rlds_global_daily_1901_2019_version_2021-09-XX.nc" },
    "swdown":{ "var": "rsds",    "file": "/projects/prjs2023/chapter3/lpjml_input/gswp3-w5e5_obsclim_rsds_global_daily_1901_2019_version_2021-09-XX.nc" },
    "vpd":   { "var": "VPD",     "file": "/projects/prjs2023/chapter3/lpjml_input/VPD_W5E5_daily_05deg_1901_2019.nc" },
    "soil":  { "var": "soilcode","file": "/projects/prjs2023/chapter3/lpjml_input/regridded_global_usda_soilmap.nc" }
}

base_out = "/projects/prjs2023/chapter3/lpjml_input/run_for_10_locations"


# ----------------------------
# MAIN LOOP OVER PFTs
# ----------------------------
for i, pft_name in enumerate(pft_names_main):

    print(f"\n🌱 Processing: {pft_name}")

    fpc_da = dynamic_lc.isel(pft=i)
    fpc_wl = fpc_da.where(aridity < aridity_thr)

    # Moving-window sum
    patch_sum = fpc_wl.rolling(
        lat=patch_height,
        lon=patch_width,
        center=True
    ).construct({"lat": "lat_patch", "lon": "lon_patch"}).sum(dim=("lat_patch", "lon_patch"))

    if np.all(np.isnan(patch_sum)):
        print("⚠️ No valid data")
        continue

    # ----------------------------
    # 🔥 GET TOP 10 HOTSPOTS
    # ----------------------------
    hotspots = find_top_n_hotspots_dist(
        patch_sum,
        n=top_n,
        min_dist_cells=min_dist_cells
    )

    print(f"Top {len(hotspots)} hotspots:")

    for k, (ii, jj, val) in enumerate(hotspots, start=1):

        lat_center = patch_sum.lat[ii].item()
        lon_center = patch_sum.lon[jj].item()

        print(f"{k}: value={val:.3f}, lat={lat_center:.2f}, lon={lon_center:.2f}")

        # ----------------------------
        # DEFINE PATCH BOUNDS
        # ----------------------------
        lat_res = fpc_da.lat[1] - fpc_da.lat[0]
        lon_res = fpc_da.lon[1] - fpc_da.lon[0]

        lat0 = lat_center - (patch_height / 2) * lat_res
        lat1 = lat_center + (patch_height / 2) * lat_res
        lon0 = lon_center - (patch_width / 2) * lon_res
        lon1 = lon_center + (patch_width / 2) * lon_res

        # buffer
        latb0 = max(lat0 - buffer_deg, fpc_da.lat.min().item())
        latb1 = min(lat1 + buffer_deg, fpc_da.lat.max().item())
        lonb0 = max(lon0 - buffer_deg, fpc_da.lon.min().item())
        lonb1 = min(lon1 + buffer_deg, fpc_da.lon.max().item())

        # ----------------------------
        # CREATE OUTPUT FOLDER
        # ----------------------------
        patch_folder = os.path.join(
            base_out,
            pft_name.replace(" ", "_"),
            f"patch_{k}"
        )
        os.makedirs(patch_folder, exist_ok=True)

        # ----------------------------
        # SAVE CLIMATE DATA
        # ----------------------------
        for var_name, details in climate_data.items():

            ds = xr.open_dataset(details["file"])
            ds_var = ds[details["var"]]

            # soil = core, others = buffered
            if var_name == "soil":
                lat_min, lat_max = lat0, lat1
                lon_min, lon_max = lon0, lon1
            else:
                lat_min, lat_max = latb0, latb1
                lon_min, lon_max = lonb0, lonb1

            # Handle lat direction
            if ds_var.lat.values[0] < ds_var.lat.values[-1]:
                ds_sub = ds_var.sel(lat=slice(lat_min, lat_max), lon=slice(lon_min, lon_max))
            else:
                ds_sub = ds_var.sel(lat=slice(lat_max, lat_min), lon=slice(lon_min, lon_max))

            if ds_sub.lat.size == 0 or ds_sub.lon.size == 0:
                print(f"❌ Empty slice for {var_name} (patch {k})")
                ds.close()
                continue

            out_file = os.path.join(patch_folder, f"{var_name}.nc")
            ds_sub.to_netcdf(out_file)
            ds.close()

        print(f"✅ Saved patch {k}")