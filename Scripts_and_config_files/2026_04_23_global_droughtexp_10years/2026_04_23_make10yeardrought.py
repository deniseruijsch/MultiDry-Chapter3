import xarray as xr
pr = xr.open_dataset("/projects/prjs2023/chapter3/lpjml_input/gswp3-w5e5_obsclim_pr_global_daily_1901_2019_version_2021-09-XX_mm_day.nc").sel(time = slice("1960","2010"))
print("precip loaded")

pr_zeroed = pr.copy()
pr_zeroed['pr'].loc[dict(time=slice("1970", "1979"))] = 0
print("precip zeroed")

pr_zeroed.to_netcdf("/projects/prjs2023/chapter3/lpjml_input/droughtexp_10years/pr_1960_2010_zeroed_1970_1979_global_slurm.nc")
print("file saved")