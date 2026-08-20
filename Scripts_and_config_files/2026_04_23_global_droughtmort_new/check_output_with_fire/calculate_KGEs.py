import numpy as np
import xarray as xr
import colormaps as cmaps
import pandas as pd

def calculate_KGE(simulated: xr.DataArray, observed: xr.DataArray) -> xr.DataArray:
    """
    Calculate the Kling-Gupta Efficiency (KGE) for simulated and observed time series
    for each grid cell (lon, lat).
    
    Parameters:
    simulated (xr.DataArray): The simulated time series (model output), with dimensions (time, lat, lon).
    observed (xr.DataArray): The observed time series, with dimensions (time, lat, lon).
    
    Returns:
    xr.DataArray: Kling-Gupta Efficiency (KGE) for each grid cell (lat, lon).
    """
    # Ensure that both arrays have the same shape
    if simulated.shape != observed.shape:
        raise ValueError("Simulated and observed arrays must have the same shape")

    # Calculate Pearson correlation coefficient (r) for each grid cell
    r = xr.corr(simulated, observed, dim='time')

    # Calculate the alpha term (ratio of standard deviations) for each grid cell
    alpha = simulated.std(dim='time') / observed.std(dim='time')

    # Calculate the beta term (ratio of means) for each grid cell
    beta = simulated.mean(dim='time') / observed.mean(dim='time')

    # Calculate the Kling-Gupta Efficiency (KGE) for each grid cell
    kge = 1 - np.sqrt((r - 1)**2 + (alpha - 1)**2 + (beta - 1)**2)

    return kge, r, alpha, beta

GPP_baseline = xr.open_dataset("/projects/prjs2023/chapter3/lpjml_output/2026_01_29_baseline_run/baseline_withfire/output/mgpp.nc").GPP.sel(time = slice('2000-03','2019'))
# Convert CFTimeIndex to pandas datetime
time_as_timestamp = pd.to_datetime(GPP_baseline["time"].values.astype(str))

# Convert to period
time_as_period = time_as_timestamp.to_period("M")
time_as_timestamp = time_as_period.to_timestamp(how="start")

# Update the time coordinate in the DataArray
GPP_baseline = GPP_baseline.assign_coords(time=time_as_timestamp)

GPP_monthlymort = xr.open_dataset("/projects/prjs2023/chapter3/lpjml_output/2026_01_29_baseline_run/monthlybackground_withfire/output/mgpp.nc").GPP.sel(time = slice('2000-03','2019'))
# Convert CFTimeIndex to pandas datetime
time_as_timestamp = pd.to_datetime(GPP_monthlymort["time"].values.astype(str))

# Convert to period
time_as_period = time_as_timestamp.to_period("M")
time_as_timestamp = time_as_period.to_timestamp(how="start")

# Update the time coordinate in the DataArray
GPP_monthlymort = GPP_monthlymort.assign_coords(time=time_as_timestamp)

GPP_droughtmort = xr.open_dataset("/projects/prjs2023/chapter3/lpjml_output/2026_04_23_global_droughtmort_new/withfire/output/mgpp.nc").GPP.sel(time = slice('2000-03','2019'))
# Convert CFTimeIndex to pandas datetime
time_as_timestamp = pd.to_datetime(GPP_droughtmort["time"].values.astype(str))

# Convert to period
time_as_period = time_as_timestamp.to_period("M")
time_as_timestamp = time_as_period.to_timestamp(how="start")

# Update the time coordinate in the DataArray
GPP_droughtmort = GPP_droughtmort.assign_coords(time=time_as_timestamp)


GPP_MODIS = xr.open_dataset("/projects/prjs2023/chapter3/MODIS/GPP_MODIS_landseamask_01deg.nc").sel(time = slice('2000-03','2019')).sel(lat = slice(-55.96,83.66)).Gpp
# Convert CFTimeIndex to pandas datetime
time_as_timestamp = pd.to_datetime(GPP_MODIS["time"].values.astype(str))

# Convert to period
time_as_period = time_as_timestamp.to_period("M")
time_as_timestamp = time_as_period.to_timestamp(how="start")

# Update the time coordinate in the DataArray
GPP_MODIS = GPP_MODIS.assign_coords(time=time_as_timestamp)


GPP_baseline['lon'] = GPP_monthlymort.lon
GPP_baseline['lat'] = GPP_monthlymort.lat
GPP_MODIS['lon'] = GPP_monthlymort.lon
GPP_MODIS['lat'] = GPP_monthlymort.lat
GPP_droughtmort['lon'] = GPP_MODIS.lon
GPP_droughtmort['lat'] = GPP_MODIS.lat




# Create xarray DataArrays (simulated and observed data for demonstration)
simulated_data = GPP_baseline
observed_data = GPP_MODIS

# Calculate KGE
kge_baseline, r_baseline, alpha_baseline, beta_baseline = calculate_KGE(simulated_data, observed_data)


# Create xarray DataArrays (simulated and observed data for demonstration)
simulated_data = GPP_monthlymort
observed_data = GPP_MODIS

# Calculate KGE
kge_monthlymort, r_monthlymort, alpha_monthlymort, beta_monthlymort = calculate_KGE(simulated_data, observed_data)


# Create xarray DataArrays (simulated and observed data for demonstration)
simulated_data = GPP_droughtmort
observed_data = GPP_MODIS

# Calculate KGE
kge_droughtmort, r_droughtmort, alpha_droughtmort, beta_droughtmort = calculate_KGE(simulated_data, observed_data)



# Combine the KGE metrics into a single Dataset
kge_ds = xr.Dataset(
    {
        "kge_baseline": kge_baseline,
        "r_baseline": r_baseline,
        "alpha_baseline": alpha_baseline,
        "beta_baseline": beta_baseline,
        "kge_monthlymort": kge_monthlymort,
        "r_monthlymort": r_monthlymort,
        "alpha_monthlymort": alpha_monthlymort,
        "beta_monthlymort": beta_monthlymort,
        "kge_droughtmort": kge_droughtmort,
        "r_droughtmort": r_droughtmort,
        "alpha_droughtmort": alpha_droughtmort,
        "beta_droughtmort": beta_droughtmort,
    },
    coords={
        "lat": GPP_baseline.lat,
        "lon": GPP_baseline.lon
    }
)

# Save to NetCDF
output_path = "/home/druijsch/LPJmL5/dev15oct2025/config_files/2026_04_23_global_droughtmort_new/check_output_with_fire/kgemetrics.nc"
kge_ds.to_netcdf(output_path)

print(f"KGE metrics saved to {output_path}")


import xarray as xr
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import cartopy.crs as ccrs
import cartopy.feature as cfeature

kge_ds = xr.open_dataset("/home/druijsch/LPJmL5/dev15oct2025/config_files/2026_04_23_global_droughtmort_new/check_output_with_fire/kgemetrics.nc")

kge_baseline = kge_ds["kge_baseline"]
kge_monthlymort = kge_ds["kge_monthlymort"]
kge_droughtmort = kge_ds["kge_droughtmort"]

r_baseline = kge_ds["r_baseline"]
r_monthlymort = kge_ds["r_monthlymort"]
r_droughtmort = kge_ds["r_droughtmort"]

alpha_baseline = kge_ds["alpha_baseline"]
alpha_monthlymort = kge_ds["alpha_monthlymort"]
alpha_droughtmort = kge_ds["alpha_droughtmort"]

beta_baseline = kge_ds["beta_baseline"]
beta_monthlymort = kge_ds["beta_monthlymort"]
beta_droughtmort = kge_ds["beta_droughtmort"]

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import cartopy.crs as ccrs
import cartopy.feature as cfeature

cmap = matplotlib.colors.LinearSegmentedColormap.from_list("", ["darkcyan","lemonchiffon","mediumorchid"])

def add_map(ax, data, cmap, vmin, vmax, cbar_label, extend, subplot_label, fontsize):
    im = data.plot(
        ax=ax,
        transform=ccrs.PlateCarree(),
        cmap=cmap,
        vmin=vmin,
        vmax=vmax,
        add_colorbar=False
    )
    ax.add_feature(cfeature.COASTLINE, linewidth=0.5)
    ax.add_feature(cfeature.LAND, facecolor='lightgray')
    ax.axis('off')

    ax.text(0.01, 0.99, subplot_label, transform=ax.transAxes,
            fontsize=fontsize, fontweight='bold', va='top', ha='left',
            bbox=dict(facecolor='white', alpha=0.6, edgecolor='none'))
    
    return im  # Return the image so we can create a shared colorbar



def plot_triple_KGE_maps(kge1, r1, beta1, alpha1,
                        kge2, r2, beta2, alpha2,
                        kge3, r3, beta3, alpha3,
                        savedir):

    fig = plt.figure(figsize=(18, 18))
    gs = gridspec.GridSpec(4, 3, hspace=0.25, wspace=0.05)

    # === Row 1: KGE ===
    ax1 = fig.add_subplot(gs[0, 0], projection=ccrs.PlateCarree(central_longitude=11))
    im1 = add_map(ax1, kge1, cmaps.ice_r, -0.41, 1, "", 'min', 'a)', fontsize=14)

    ax2 = fig.add_subplot(gs[0, 1], projection=ccrs.PlateCarree(central_longitude=11))
    add_map(ax2, kge2, cmaps.ice_r, -0.41, 1, "", 'min', 'b)', fontsize=14)

    ax3 = fig.add_subplot(gs[0, 2], projection=ccrs.PlateCarree(central_longitude=11))
    add_map(ax3, kge3, cmaps.ice_r, -0.41, 1, "", 'min', 'c)', fontsize=14)

    cax1 = fig.add_axes([0.2, 0.71, 0.6, 0.015])
    cbar1 = plt.colorbar(im1, cax=cax1, orientation='horizontal', extend='min')
    cbar1.set_label("Kling-Gupta Efficiency", fontsize=14)
    cbar1.ax.tick_params(labelsize=12)

    # === Row 2: Correlation ===
    ax4 = fig.add_subplot(gs[1, 0], projection=ccrs.PlateCarree(central_longitude=11))
    im2 = add_map(ax4, r1, cmaps.cmp_b2r_r, -1, 1, "", 'neither', 'd)', fontsize=12)

    ax5 = fig.add_subplot(gs[1, 1], projection=ccrs.PlateCarree(central_longitude=11))
    add_map(ax5, r2, cmaps.cmp_b2r_r, -1, 1, "", 'neither', 'e)', fontsize=12)

    ax6 = fig.add_subplot(gs[1, 2], projection=ccrs.PlateCarree(central_longitude=11))
    add_map(ax6, r3, cmaps.cmp_b2r_r, -1, 1, "", 'neither', 'f)', fontsize=12)

    cax2 = fig.add_axes([0.2, 0.51, 0.6, 0.015])
    cbar2 = plt.colorbar(im2, cax=cax2, orientation='horizontal')
    cbar2.set_label("Correlation", fontsize=14)
    cbar2.ax.tick_params(labelsize=12)

    # === Row 3: Bias Ratio ===
    ax7 = fig.add_subplot(gs[2, 0], projection=ccrs.PlateCarree(central_longitude=11))
    im3 = add_map(ax7, beta1, cmap, 0, 2, "", 'max', 'g)', fontsize=12)

    ax8 = fig.add_subplot(gs[2, 1], projection=ccrs.PlateCarree(central_longitude=11))
    add_map(ax8, beta2, cmap, 0, 2, "", 'max', 'h)', fontsize=12)

    ax9 = fig.add_subplot(gs[2, 2], projection=ccrs.PlateCarree(central_longitude=11))
    add_map(ax9, beta3, cmap, 0, 2, "", 'max', 'i)', fontsize=12)

    cax3 = fig.add_axes([0.2, 0.31, 0.6, 0.015])
    cbar3 = plt.colorbar(im3, cax=cax3, orientation='horizontal', extend='max')
    cbar3.set_label("Bias Ratio", fontsize=14)
    cbar3.ax.tick_params(labelsize=12)

    # === Row 4: Variability Ratio ===
    ax10 = fig.add_subplot(gs[3, 0], projection=ccrs.PlateCarree(central_longitude=11))
    im4 = add_map(ax10, alpha1, cmap, 0, 2, "", 'max', 'j)', fontsize=12)

    ax11 = fig.add_subplot(gs[3, 1], projection=ccrs.PlateCarree(central_longitude=11))
    add_map(ax11, alpha2, cmap, 0, 2, "", 'max', 'k)', fontsize=12)

    ax12 = fig.add_subplot(gs[3, 2], projection=ccrs.PlateCarree(central_longitude=11))
    add_map(ax12, alpha3, cmap, 0, 2, "", 'max', 'l)', fontsize=12)

    cax4 = fig.add_axes([0.2, 0.11, 0.6, 0.015])
    cbar4 = plt.colorbar(im4, cax=cax4, orientation='horizontal', extend='max')
    cbar4.set_label("Variability Ratio", fontsize=14)
    cbar4.ax.tick_params(labelsize=12)

    # === Column headers ===
    fig.text(0.2, 0.88, 'Baseline', fontsize=16, fontweight='bold', ha='center')
    fig.text(0.5, 0.88, 'Monthly mortality', fontsize=16, fontweight='bold', ha='center')
    fig.text(0.8, 0.88, 'Drought mortality', fontsize=16, fontweight='bold', ha='center')

    # === Horizontal separators ===
    for y in [0.67, 0.47, 0.27]:
        fig.lines.append(plt.Line2D([0.05, 0.95], [y, y],
                                   transform=fig.transFigure,
                                   color='gray', linewidth=0.8, linestyle='--'))

    plt.savefig(savedir, dpi=1200, bbox_inches='tight')
    plt.show()

plot_triple_KGE_maps(kge_baseline, r_baseline, beta_baseline, alpha_baseline,
                    kge_monthlymort, r_monthlymort, beta_monthlymort, alpha_monthlymort,
                    kge_droughtmort, r_droughtmort, beta_droughtmort, alpha_droughtmort,
                    savedir='/home/druijsch/LPJmL5/dev15oct2025/config_files/2026_04_23_global_droughtmort_new/check_output_with_fire/kge_comparison.png')