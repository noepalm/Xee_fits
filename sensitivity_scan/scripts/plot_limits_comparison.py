import ROOT
import numpy as np
import matplotlib.pyplot as plt
import os
import mplhep as hep
import argparse
import pickle

plt.style.use(hep.style.CMS)

parser = argparse.ArgumentParser()
# take as input list of input folders to process
parser.add_argument('-i', '--input_folders', type=str, nargs='+', required=True, help='Input folders containing limits_results.pkl to compare')
parser.add_argument('-f', '--fit_tags', type=str, nargs='*', default=[], help='Fit tags to identify input files')
parser.add_argument('-l', '--labels', type=str, nargs='*', default=[], help='Labels for legend (defaults to category, i.e. last subfolder)')
parser.add_argument('-o', '--output_folder', type=str, default='plots', help='Output folder')
parser.add_argument('-r', '--region', type=str, nargs='+', default=['region1'], choices=["region0", "region1", "region2"], help='Mass region(s) (for labeling purposes)')
parser.add_argument('-m', '--mu', action="store_true", help="Plot limits on mu rather than model-independent ones")
parser.add_argument('--overlap', action="store_true", help="Load combined region file (limits_results_region0_region1_...) instead of separate files")
parser.add_argument('--tag', type=str, default='', help='Tag to append to output folder name')

args = parser.parse_args()
tag = f"_{args.tag}" if args.tag else ""
fit_tags = args.fit_tags
labels = args.labels
regions = args.region if isinstance(args.region, list) else [args.region]
base_folder = "/eos/home-n/npalmeri/www/DiElectron/sensitivity"

# PROCESSING INPUT FILE TAGS
if len(fit_tags) > 0 and len(fit_tags) != len(args.input_folders):
    raise ValueError("If fit_tags are provided, their number must match the number of input_folders (use '' for no tag)")

if len(fit_tags) == 0:
    fit_tags = [''] * len(args.input_folders)

# PROCESSING LEGEND LABELS
label_map = {
    "inclusive": "Inclusive",
    "etaCombination": "$\eta$ combination",
    "dRCombination": "$\Delta R$ combination",
}

if len(labels) > 0 and len(labels) != len(args.input_folders):
    raise ValueError("If labels are provided, their number must match the number of input_folders")

if len(labels) == 0:
    labels = [os.path.basename(os.path.normpath(folder)) for folder in args.input_folders]

labels = [label_map.get(label, label) for label in labels]

# If multiple regions are requested, first try to use the combined file for all inputs.
if len(regions) > 1:
    combined_region = "_".join(regions)
    combined_exists_for_all = True
    for folder, fit_tag in zip(args.input_folders, fit_tags):
        fit_tag_label = "" if fit_tag == "" else f"_{fit_tag}"
        combined_path = os.path.join(base_folder, folder, f"limits_results_{combined_region}{fit_tag_label}.pkl")
        if not os.path.exists(combined_path):
            combined_exists_for_all = False
            break

    use_combined = args.overlap or combined_exists_for_all

    if use_combined:
        input_folders = args.input_folders
        regions_expanded = [combined_region] * len(input_folders)
        if args.overlap and not combined_exists_for_all:
            print("WARNING: --overlap requested but at least one combined file is missing.")
            print("Falling back to per-region files.")
            use_combined = False

    if not use_combined:
        # Fallback behavior: plot each region separately on the same canvas.
        labels = [f"{label} ({region})" for label in labels for region in regions]
        input_folders = [folder for folder in args.input_folders for _ in regions]
        fit_tags = [fit_tag for fit_tag in fit_tags for _ in regions]
        regions_expanded = [region for _ in args.input_folders for region in regions]
else:
    input_folders = args.input_folders
    regions_expanded = regions * len(input_folders)

outfolder = args.output_folder
os.makedirs(outfolder, exist_ok=True)

# Create output filename based on regions
region_suffix = "_".join(args.region) if len(args.region) > 1 else args.region[0]
overlap_suffix = "_overlap" if args.overlap else ""

branch_specs = [
    (
        "expected_50_indep_accept",
        r"$\sigma(pp \to X) \cdot \mathrm{BR}(X \to ee) \cdot A \cdot \epsilon$ [pb]",
        "indep_accept",
    ),
    (
        "expected_50_indep",
        r"$\sigma(pp \to X) \cdot \mathrm{BR}(X \to ee) \cdot A$ [pb]",
        "indep",
    ),
    (
        "expected_50",
        r"$\mu$",
        "mu",
    ),
]

for branch, y_label, branch_suffix in branch_specs:
    fig, ax = plt.subplots(figsize=(15 if len(regions) > 1 else 10, 10))

    # Build 68% expected band keys matching the current branch variant.
    branch_low = branch.replace("expected_50", "expected_16", 1)
    branch_high = branch.replace("expected_50", "expected_84", 1)

    for fit_tag, folder, label, region in zip(fit_tags, input_folders, labels, regions_expanded):
        fit_tag_label = "" if fit_tag == "" else f"_{fit_tag}"
        with open(os.path.join(base_folder, folder, f'limits_results_{region}{fit_tag_label}.pkl'), 'rb') as f:
            r_values = pickle.load(f)

        sorted_keys = sorted(r_values.keys(), key=float)
        # # only plot in range 1.3 - 10
        sorted_keys = [mass for mass in sorted_keys if 0.6 <= float(mass) <= 10]
        # # also take only every other point to avoid overcrowding the plot
        # sorted_keys = sorted_keys[::2]
        # # finally, exclude 4.1 and 4.2
        # sorted_keys = [mass for mass in sorted_keys if float(mass) != 4.1 and float(mass) != 4.3 and float(mass) != 8.5]
        masses = np.array([float(mass) for mass in sorted_keys])
        expected_50 = np.array([float(r_values[mass][branch]) for mass in sorted_keys])
        expected_16 = np.array([float(r_values[mass][branch_low]) for mass in sorted_keys])
        expected_84 = np.array([float(r_values[mass][branch_high]) for mass in sorted_keys])

        (line,) = ax.plot(masses, expected_50, label=label, marker='o')
        ax.fill_between(
            masses,
            expected_16,
            expected_84,
            alpha=0.22,
            color=line.get_color(),
            linewidth=0,
        )

    ax.set_yscale('log')
    ax.set_xlabel('M(X) [GeV]')
    ax.set_ylabel(y_label)
    hep.cms.label(
        "Preliminary",
        loc=0,
        ax=ax,
        com=13.6,
        data=np.any(["data" in folder for folder in input_folders]),
        lumi="6.68",
    )
    ax.legend()

    for ext in ['png', 'pdf']:
        plt.savefig(os.path.join(outfolder, f'limits_comparison_{branch_suffix}_{region_suffix}{overlap_suffix}{tag}.{ext}'))
    plt.close(fig)