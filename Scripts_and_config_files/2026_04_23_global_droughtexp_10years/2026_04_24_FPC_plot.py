import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from pathlib import Path


BASE_PATH = Path("/projects/prjs2023/chapter3/lpjml_output/2026_04_23_global_droughtexp_10years")


def plot_fpc_timeseries(lon, lat, save_path=None, dpi=300):
    # ----------------------------
    # Load data
    # ----------------------------
    def load_all_runs(file_name, var_name):
        paths = {
            "baseline": BASE_PATH / "baseline/output" / f"{file_name}.nc",
            "MM": BASE_PATH / "MM/output" / f"{file_name}.nc",
            "DM": BASE_PATH / "DM/output" / f"{file_name}.nc",
        }

        return {
            key: xr.open_dataset(path)[var_name].sel(
                lon=lon, lat=lat, method="nearest"
            )
            for key, path in paths.items()
        }

    fpc = load_all_runs("fpc", "FPC")

    # ----------------------------
    # Process data
    # ----------------------------
    def process_fpc_per_pft(data):
        return data.sel(pft=slice(2, 12)).convert_calendar("standard")

    fpc_proc = {name: process_fpc_per_pft(ds) for name, ds in fpc.items()}

    # ----------------------------
    # Determine valid PFTs
    # ----------------------------
    valid_pfts = []
    for pft in list(fpc_proc.values())[0].pft.values:
        combined = np.concatenate(
            [fpc_proc[name].sel(pft=pft).values for name in fpc_proc]
        )
        if not (np.all(np.isnan(combined)) or np.all(np.isclose(combined, 0))):
            valid_pfts.append(pft)

    # ----------------------------
    # Labels
    # ----------------------------
    pft_names = [
        'tropical broadleaved evergreen tree',
        'tropical broadleaved raingreen tree',
        'temperate needleleaved evergreen tree',
        'temperate broadleaved evergreen tree',
        'temperate broadleaved summergreen tree',
        'boreal needleleaved evergreen tree',
        'boreal broadleaved summergreen tree',
        'boreal needleleaved summergreen tree',
        'Tropical C4 grass',
        'Temperate C3 grass',
        'Polar C3 grass'
    ]

    all_pfts = fpc_proc[list(fpc_proc.keys())[0]].pft.values

    pft_labels = {
        pft: pft_names[int(pft) - 2]
        for pft in all_pfts
    }

    # ----------------------------
    # Colors
    # ----------------------------
    tropical = [2, 3]
    temperate = [4, 5, 6]
    boreal = [7, 8, 9]
    grass = [10, 11, 12]

    pft_colors = {}

    greens = cm.Greens(np.linspace(0.5, 0.9, len(tropical)))
    oranges = cm.Oranges(np.linspace(0.5, 0.9, len(temperate)))
    blues = cm.Blues(np.linspace(0.5, 0.9, len(boreal)))
    purples = cm.Purples(np.linspace(0.4, 0.8, len(grass)))

    for i, p in enumerate(tropical):
        pft_colors[p] = greens[i]

    for i, p in enumerate(temperate):
        pft_colors[p] = oranges[i]

    for i, p in enumerate(boreal):
        pft_colors[p] = blues[i]

    for i, p in enumerate(grass):
        pft_colors[p] = purples[i]

    # ----------------------------
    # Plot
    # ----------------------------
    runs = list(fpc_proc.keys())
    fig, axes = plt.subplots(len(runs), 1, figsize=(14, 10), sharex=True)

    for ax, run in zip(axes, runs):
        data = fpc_proc[run]
        years = data.time.values

        stack_data = []
        labels = []
        colors = []

        for pft in valid_pfts:
            vals = data.sel(pft=pft).values
            stack_data.append(vals)
            labels.append(pft_labels[pft])
            colors.append(pft_colors[pft])

        ax.stackplot(years, stack_data, labels=labels, colors=colors)
        ax.set_title(f"{run} (lon={lon}, lat={lat})", loc="left")
        ax.set_ylabel("FPC")
        ax.grid(alpha=0.3)

    axes[-1].set_xlabel("Year")

    # legend once
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="center right")

    plt.tight_layout(rect=[0, 0, 0.85, 1])

    # ----------------------------
    # Save figure (NEW)
    # ----------------------------
    if save_path is not None:
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)

        plt.savefig(
            save_path,
            dpi=dpi,
            bbox_inches="tight",
            transparent=True
        )

    plt.show()
    
plot_fpc_timeseries(-116, 40, save_path="/home/druijsch/LPJmL5/dev15oct2025/config_files/2026_04_23_global_droughtexp_10years/fpc_lon-116_lat40.png")
print("first done")
plot_fpc_timeseries(-59, -36, save_path="/home/druijsch/LPJmL5/dev15oct2025/config_files/2026_04_23_global_droughtexp_10years/fpc_lon-59_lat-36.png")
print("second done")