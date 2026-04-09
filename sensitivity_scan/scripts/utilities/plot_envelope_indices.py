import ROOT
import matplotlib.pyplot as plt
import argparse
from pathlib import Path
import glob
import mplhep as hep

hep.style.use("CMS")

region_ranges = {
    "region0": {"min": 0.3, "min_limit": 0.5, "max": 2.4, "max_limit": 2.2},
    "region1": {"min": 1.6, "min_limit": 1.8, "max": 5.3, "max_limit": 4.9},
    "region2": {"min": 4.5, "min_limit": 4.9, "max": 10.5, "max_limit": 10},
}

template = "cards/260327/cards_{region}_data_envelope_withScaleSyst_withMeanNuisance_IDSF_triggerSF_finerBinning_tighterCuts_biasTests_bySubera_binned/ee"
parser = argparse.ArgumentParser(description='Plot envelope indices from ROOT files.')
parser.add_argument("--input_folder_template", "-i", default=template, help='Template for input folder, e.g., output_{era}')
parser.add_argument("--output_dir", '-o', default='plots', help='Directory to save the output')
parser.add_argument("--regions", nargs='+', help='Regions to plot, e.g., region0 region1 region2')
parser.add_argument("--eras", nargs='+', default = ["2022", "2022EE", "2023", "2023BPix"], help='Eras to plot')

args = parser.parse_args()

regions = ["region0", "region1", "region2"]
eras = ["2022", "2022EE", "2023", "2023BPix"]

results = {}

#1. fetch pdf_index result for each era and each region
for region in regions:
    # fetch all subfolders in input_folder
    input_folder = args.input_folder_template.format(region=region)
    subfolders = glob.glob(input_folder + "/*/")
    # extract mass value from folder (folder name already is a float)
    for subfolder in subfolders:
        # if folder name is not a float number, skip
        if not subfolder.split("/")[-2].replace(".", "", 1).isdigit():
            print("Skipping folder: ", subfolder)
            continue
        mass = float(subfolder.split("/")[-2])
        if mass < region_ranges[region]["max_limit"] and mass > region_ranges[region]["min_limit"]:
            for era in eras:
                file = ROOT.TFile(f"{subfolder}/higgsCombine_inclusive_{era}_SB.MultiDimFit.mH120.root")
                tree = file.Get("limit")
                tree.GetEntry(0)
                index = getattr(tree,f"pdf_index_{era}_envelope")
                if era not in results:
                    results[era] = {}
                results[era][mass] = index

# 2. plot all results overlapped (by era)
plt.figure(figsize=(12, 6))
for era in eras:
    masses = sorted(results[era].keys())
    indices = [results[era][mass] for mass in masses]
    plt.plot(masses, indices, label=era, markersize=3, marker='o', linestyle='-')
plt.xlabel("Mass (GeV)")
plt.ylabel("PDF Index")
plt.title("Envelope PDF Index vs Mass", pad = 30)
plt.legend()
plt.grid()
plt.tight_layout()

# add vertical lines at region boundaries
for region in regions:
    plt.axvline(region_ranges[region]["min_limit"], color='gray', linestyle='--', label=f'{region} min', alpha=0.5)
    plt.axvline(region_ranges[region]["max_limit"], color='gray', linestyle='--', label=f'{region} max', alpha=0.5)

# indices are either 0 (chebyshev), 1 (bernstein) or 2 (polyexp); change y-axis labels accordingly
plt.yticks([0, 1, 2], ["Chebyshev", "Bernstein", "PolyExp"], rotation=60)

# save plot
output_dir = Path(args.output_dir)
output_dir.mkdir(parents=True, exist_ok=True)
plt.savefig(output_dir / "envelope_indices.png")