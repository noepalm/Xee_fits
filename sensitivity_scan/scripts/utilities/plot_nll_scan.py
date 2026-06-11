import ROOT
import matplotlib.pyplot as plt
import numpy as np
import mplhep as hep
import argparse 

parser = argparse.ArgumentParser(description="Plot NLL scan results from ROOT files.")
parser.add_argument("--signal", action="store_true", help="Plot signal-only NLL scan")
parser.add_argument("-o", "--output", type=str, default="nll_scan_comparison.png", help="Output filename for the plot")
parser.add_argument("-i", "--input", type=str, default=None, help="Input ROOT file containing the NLL scan trees")
parser.add_argument("--deltaNLL", action="store_true", help="Plot 2*deltaNLL instead of envelope formula")
parser.add_argument("--year", type=str, default="", help="Year to process")
parser.add_argument("--title", type=str, default="NLL Scan for Different Models", help="Title for the plot")
parser.add_argument("--poi", type=str, default="r", help="Name of the parameter of interest (POI) to plot on the x-axis")
parser.add_argument("--tag", type=str, default="", help="Additional tag for file naming")
args = parser.parse_args()

hep.style.use("CMS")

if args.signal:
    keys = ["envelope", "dCB", "gaussian"]
else:
    # keys = ["envelope", "idx0", "idx1", "idx2"]
    # keys = ["envelope", "idx0", "idx1"]
    keys = ["envelope"]
    # keys = ["idx0"]

files = {}
trees = {}

for key in keys:
    suffix = "" if key == "envelope" else f"_{key}Only" if args.signal else f"_{key}"
    suffix = suffix + f"_{args.year}" if args.year else suffix
    suffix = suffix + f"_{args.tag}" if args.tag else suffix
    if args.input:
        filepath = args.input
    else:
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
        # if entry.r < -4 or entry.r > 4:
        #     continue
        r_values[key].append(getattr(entry, args.poi))
        if args.deltaNLL:
            delta_nll_values[key].append(2 * entry.deltaNLL)
        else:
            delta_nll_values[key].append(2 * (entry.deltaNLL + entry.nll + entry.nll0))
            # nll_values[key].append(entry.nll)
            # nll0_values[key].append(entry.nll0)

# sort values by r for better plotting
for key in keys:
    sorted_indices = np.argsort(r_values[key])
    r_values[key] = np.array(r_values[key])[sorted_indices]
    delta_nll_values[key] = np.array(delta_nll_values[key])[sorted_indices]
    # if not args.deltaNLL:
    #     nll_values[key] = np.array(nll_values[key])[sorted_indices]
    #     nll0_values[key] = np.array(nll0_values[key])[sorted_indices]

# Plot r vs 2*(deltaNLL+nll+nll0), overlapped for the three keys
fig, ax = plt.subplots(figsize=(10, 8))
for key in keys:
    kwargs = {}
    if key == "envelope":
        kwargs["color"] = "black"
        kwargs["markerfacecolor"] = "None"
        kwargs["markersize"] = 10
    ax.plot(r_values[key], delta_nll_values[key], label=key, marker='o', linestyle='-', alpha=0.9, **kwargs)
ax.set_xlabel(args.poi)
if args.deltaNLL:
    ax.set_ylabel(r"-2$\Delta$lnL")
else:
    ax.set_ylabel("2*(deltaNLL + nll + nll0)")

if args.deltaNLL:
    ax.axhline(0.5, color="red", linestyle="--", label="1$\sigma$ (deltaNLL=0.5)")

ax.set_title(args.title)
ax.legend()
plt.grid()
plt.tight_layout()
plt.savefig(args.output)
# plt.savefig(f"nll_scan{'_signal' if args.signal else '_bkg'}.png")