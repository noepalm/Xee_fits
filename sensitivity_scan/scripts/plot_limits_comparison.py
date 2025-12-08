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
parser.add_argument('-r', '--region', type=str, default='region1', choices=["region0", "region1", "region2"], help='Mass region (for labeling purposes)')
parser.add_argument('-m', '--mu', action="store_true", help="Plot limits on mu rather than model-independent ones")
parser.add_argument('--tag', type=str, default='', help='Tag to append to output folder name')

args = parser.parse_args()
tag = f"_{args.tag}" if args.tag else ""
fit_tags = args.fit_tags
labels = args.labels

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

for label in labels:
    if label in label_map:
        labels[labels.index(label)] = label_map[label]

input_folders = args.input_folders
outfolder = args.output_folder
os.makedirs(outfolder, exist_ok=True)

base_folder = "/eos/home-n/npalmeri/www/DiElectron/sensitivity"

fig, ax = plt.subplots(figsize=(10, 10))


for fit_tag, folder, label in zip(fit_tags, input_folders, labels):
    fit_tag_label = "" if fit_tag == "" else f"_{fit_tag}"
    with open(os.path.join(base_folder, folder, f'limits_results_{args.region}{fit_tag_label}.pkl'), 'rb') as f:
        r_values = pickle.load(f)
    
    masses = np.array(sorted([float(mass) for mass in r_values.keys()]))
    branch = "expected_50_indep_accept" if not args.mu else "expected_50"
    expected_50 = np.array([float(r_values[mass][branch]) for mass in sorted(r_values.keys(), key=float)])

    plt.plot(masses, expected_50, label=label, marker='o')

plt.yscale('log')
plt.xlabel('M(X) [GeV]')
plt.ylabel(r"$\sigma(pp \to X) \cdot \text{BR}(X \to ee) \cdot A $ [pb]" if not args.mu else "$\mu$")
hep.cms.label("Preliminary", loc=0, ax=ax, com = 13.6)

plt.legend()

for ext in ['png', 'pdf']:
    plt.savefig(os.path.join(outfolder, f'limits_comparison_{args.region}{tag}.{ext}'))