import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from matplotlib.path import Path
from matplotlib.patches import PathPatch
import matplotlib
import colormaps as cmaps
from matplotlib.colors import ListedColormap
import pandas as pd

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



def standardized_anomalies(data):
    climatology_mean = data.groupby('time.month').mean('time')
    climatology_std = data.groupby('time.month').std('time')
    
    # Check if climatology_std is not zero
    climatology_std_nonzero = climatology_std.where(climatology_std != 0)
    
    # Calculate standardized anomalies only where climatology_std is not zero
    stand_anomalies = xr.apply_ufunc(lambda x, m, s: (x - m) / s if s != 0 else np.nan, 
                                      data.groupby('time.month'), climatology_mean, climatology_std_nonzero,
                                      dask='allowed', vectorize=True)
    print('anomalies done')
    return stand_anomalies



GPP_baseline_stan = standardized_anomalies(GPP_baseline)
# Convert the time coordinate to the start of the month using pandas
time_as_period = pd.to_datetime(GPP_baseline_stan["time"].values).to_period("M")
time_as_timestamp = time_as_period.to_timestamp(how="start")

# Update the time coordinate in the DataArray
GPP_baseline_stan = GPP_baseline_stan.assign_coords(time=time_as_timestamp)
GPP_baseline_stan.to_netcdf('/home/druijsch/LPJmL5/dev15oct2025/config_files/2026_03_27_global_droughtmort/check_output_with_fire/GPP_baseline_stan.nc')


# GPP_monthlymort_stan = standardized_anomalies(GPP_monthlymort)
# # Convert the time coordinate to the start of the month using pandas
# time_as_period = pd.to_datetime(GPP_monthlymort_stan["time"].values).to_period("M")
# time_as_timestamp = time_as_period.to_timestamp(how="start")

# # Update the time coordinate in the DataArray
# GPP_monthlymort_stan = GPP_monthlymort_stan.assign_coords(time=time_as_timestamp)
# GPP_monthlymort_stan.to_netcdf('/home/druijsch/LPJmL5/dev15oct2025/config_files/2026_03_27_global_droughtmort/check_output_with_fire/GPP_monthlymort_stan.nc')


GPP_droughtmort_stan = standardized_anomalies(GPP_droughtmort)
# Convert the time coordinate to the start of the month using pandas
time_as_period = pd.to_datetime(GPP_droughtmort_stan["time"].values).to_period("M")
time_as_timestamp = time_as_period.to_timestamp(how="start")

# Update the time coordinate in the DataArray
GPP_droughtmort_stan = GPP_droughtmort_stan.assign_coords(time=time_as_timestamp)
GPP_droughtmort_stan.to_netcdf('/home/druijsch/LPJmL5/dev15oct2025/config_files/2026_04_23_global_droughtmort_new/check_output_with_fire/GPP_droughtmort_stan.nc')




GPP_baseline_stan = xr.open_dataset("/home/druijsch/LPJmL5/dev15oct2025/config_files/2026_03_27_global_droughtmort/check_output_with_fire/GPP_baseline_stan.nc").GPP
GPP_monthlymort_stan = xr.open_dataset("/home/druijsch/LPJmL5/dev15oct2025/config_files/2026_03_27_global_droughtmort/check_output_with_fire/GPP_monthlymort_stan.nc").GPP
GPP_droughtmort_stan = xr.open_dataset('/home/druijsch/LPJmL5/dev15oct2025/config_files/2026_04_23_global_droughtmort_new/check_output_with_fire/GPP_droughtmort_stan.nc').GPP


def GPP_MYDs_timemean(GPP_st_an, SPEI_grid_MYD):
    GPP_st_an_MYD = GPP_st_an.where(SPEI_grid_MYD.notnull())
    GPP_st_an_MYD_mean = GPP_st_an_MYD.mean("time")
    return GPP_st_an_MYD, GPP_st_an_MYD_mean

SPEI_grid01_MYDs_W5E5 = xr.open_dataset("/projects/prjs2023/chapter3/SPEI/SPEI_12_MYDS_1901_2019_01deg_remapnn.nc").SPEI.sel(time = slice('2000-03','2019')).sel(lat = slice(-56.0,83.7))
SPEI_grid01_MYDs_W5E5['lat'] = GPP_droughtmort_stan.lat
SPEI_grid01_MYDs_W5E5['lon'] = GPP_droughtmort_stan.lon


# GPP_st_an_W5E5_MYD_2000_2019_LPJML, GPP_st_an_W5E5_MYD_mean_2000_2019_LPJML = GPP_MYDs_timemean(GPP_baseline_stan, SPEI_grid01_MYDs_W5E5)
# GPP_st_an_W5E5_MYD_mean_2000_2019_LPJML.to_netcdf('/home/druijsch/LPJmL5/dev15oct2025/config_files/2026_03_27_global_droughtmort/check_output_with_fire/GPP_LPJML_baseline_01deg_MYD_mean.nc')

# GPP_st_an_W5E5_MYD_2000_2019_LPJML, GPP_st_an_W5E5_MYD_mean_2000_2019_LPJML = GPP_MYDs_timemean(GPP_monthlymort_stan, SPEI_grid01_MYDs_W5E5)
# GPP_st_an_W5E5_MYD_mean_2000_2019_LPJML.to_netcdf('/home/druijsch/LPJmL5/dev15oct2025/config_files/2026_03_27_global_droughtmort/check_output_with_fire/GPP_LPJML_monthlymort_01deg_MYD_mean.nc')

GPP_st_an_W5E5_MYD_2000_2019_LPJML, GPP_st_an_W5E5_MYD_mean_2000_2019_LPJML = GPP_MYDs_timemean(GPP_droughtmort_stan, SPEI_grid01_MYDs_W5E5)
GPP_st_an_W5E5_MYD_mean_2000_2019_LPJML.to_netcdf('/home/druijsch/LPJmL5/dev15oct2025/config_files/2026_04_23_global_droughtmort_new/check_output_with_fire/GPP_LPJML_droughtmort_01deg_MYD_mean.nc')