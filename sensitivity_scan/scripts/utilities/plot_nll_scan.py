import ROOT
import matplotlib.pyplot as plt
import numpy as np
import mplhep as hep
import argparse 

parser = argparse.ArgumentParser(description="Plot NLL scan results from ROOT files.")
parser.add_argument("--signal", action="store_true", help="Plot signal-only NLL scan")
args = parser.parse_args()

hep.style.use("CMS")

if args.signal:
    keys = ["envelope", "dCB", "gaussian"]
else:
    keys = ["envelope", "idx0", "idx1", "idx2"]
    # keys = ["envelope", "idx0", "idx1"]
    # keys = ["idx2"]

files = {}
trees = {}

for key in keys:
    suffix = "" if key == "envelope" else f"_{key}Only" if args.signal else f"_{key}"
    filepath = f"higgsCombine.nll_scan_{'signal' if args.signal else 'bkg'}Envelope{suffix}.MultiDimFit.mH120.root"
    files[key] = ROOT.TFile.Open(filepath)
    trees[key] = files[key].Get("limit")

# retrieve r values and 2*(deltaNLL+nll+nll0)
r_values = {}
delta_nll_values = {}
nll_values = {}
nll0_values = {}

for key, tree in trees.items():
    r_values[key] = []
    delta_nll_values[key] = []
    nll_values[key] = []
    nll0_values[key] = []

    for idx, entry in enumerate(tree):
        if idx == 0:
            continue
        # if entry.r < -5 or entry.r > 5:
        #     continue
        # if entry is ~-0.9, skip it
        if -0.91 < entry.r < -0.89 and key == "idx2":
            continue
        r_values[key].append(entry.r)
        delta_nll_values[key].append(2 * (entry.deltaNLL + entry.nll + entry.nll0))
        nll_values[key].append(entry.nll)
        nll0_values[key].append(entry.nll0)

# sort values by r for better plotting
for key in keys:
    sorted_indices = np.argsort(r_values[key])
    r_values[key] = np.array(r_values[key])[sorted_indices]
    delta_nll_values[key] = np.array(delta_nll_values[key])[sorted_indices]
    nll_values[key] = np.array(nll_values[key])[sorted_indices]
    nll0_values[key] = np.array(nll0_values[key])[sorted_indices]

# Plot r vs 2*(deltaNLL+nll+nll0), overlapped for the three keys
fig, ax = plt.subplots(figsize=(10, 6))
for key in keys:
    kwargs = {}
    if key == "envelope":
        kwargs["color"] = "black"
        kwargs["markerfacecolor"] = "None"
        kwargs["markersize"] = 10
    ax.plot(r_values[key], delta_nll_values[key], label=key, marker='o', linestyle='-', alpha=0.9, **kwargs)
ax.set_xlabel("r")
ax.set_ylabel("2*(deltaNLL + nll + nll0)")
ax.set_title("NLL Scan for Different Models")
ax.legend()
plt.grid()
plt.savefig(f"nll_scan_comparison{'_signal' if args.signal else '_bkg'}.png")