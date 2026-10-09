import ROOT
import numpy as np
import matplotlib.pyplot as plt
import os
import mplhep as hep
import argparse
from scipy.interpolate import PchipInterpolator
import pickle

parser = argparse.ArgumentParser()
parser.add_argument('-o', '--output_folder', type=str, default='/eos/home-n/npalmeri/www/DiElectron/sensitivity/fitDiagnostics/mu0', help='Output folder for the plots')
parser.add_argument('-i', '--input_cards', type=str, nargs='+', default=['cards'], help='Input cards folder(s) - must match number of regions in order')
parser.add_argument('-c', '--category', type=str, default='etaHigh', help='Category to plot (default: etaHigh)')
parser.add_argument('-t', '--tag', type=str, default="", help='Optional additional tag for output files')
parser.add_argument('-r', '--region', type=str, nargs='+', default=['region1'], choices=["region0", "region1", "region2"], help='Region(s) to plot (can specify multiple)')
parser.add_argument('--rescale_full', action='store_true', help='Rescale all limits to full luminosity')
parser.add_argument('--rescale_muon_lumi', action='store_true', help='Rescale all limits to muon luminosity')
parser.add_argument('--era', type=str, default='2023', help='Era to use for file naming (e.g., 2023, allYears)')
parser.add_argument('--unblind', action='store_true', help='Overlay observed limit curve (solid black line)')
args = parser.parse_args()

if args.rescale_muon_lumi and not args.rescale_full:
    raise ValueError("Cannot rescale to muon luminosity without also rescaling to full luminosity. Use --rescale_full with --rescale_muon_lumi.")

is_data = ["data" in folder for folder in args.input_cards]

# Validate that input_cards matches the number of regions
if len(args.input_cards) != len(args.region):
    raise ValueError(f"Number of input_cards ({len(args.input_cards)}) must match number of regions ({len(args.region)})")

limit_bounds = {
    "region0": (0.6, 2.2),
    # "region1": (1.8, 4.9),
    # "region2": (4.9, 9.7),
    "region1": (2.2, 6.5),
    "region2": (6.5, 10.1),
}

# Create mapping from region to input_cards folder
region_to_cards = {region: cards for region, cards in zip(args.region, args.input_cards)}

# Create region tag for output files
region_tag = "_".join(args.region)

# Helper function to check if mass is in any of the specified regions
def is_mass_in_regions(mass_value, regions):
    """Check if mass falls within any of the specified regions"""
    for region in regions:
        lower, upper = limit_bounds[region]
        if lower <= mass_value <= upper:
            return True
    return False

# print all arguments
print("Arguments:")
print(f"  Output folder: {args.output_folder}")
print(f"  Category: {args.category}")
print(f"  Era: {args.era}")
print(f"  Tag: {args.tag}")
print(f"  Unblind: {args.unblind}")
print(f"  Region(s) and input cards:")
for region, cards in region_to_cards.items():
    print(f"    {region}: {limit_bounds[region][0]} - {limit_bounds[region][1]} GeV → {cards}")

outfolder = args.output_folder
infolder = args.input_cards
tag = f"_{args.tag}" if args.tag != "" else args.tag

plt.style.use(hep.style.CMS)

r_values = {}

category_map = {
    "etaHigh" : 0,
    "etaLow" : 1,
    "dRHigh" : 2,
    "dRLow" : 3,
    "inclusive" : 4,
    "etaCombination" : 4,
    "dRCombination" : 4,
}

category_label_map = {
    "etaHigh" : "etap0p6",
    "etaLow" : "etam0p6",
    "dRHigh" : "dRp0p3",
    "dRLow" : "dRm0p3",
}

list_failed_mass_points = []

# Construct full category name with era for file matching
category_with_era = f"{args.category}_{args.era}"

# iterate over subfolders -- only consider the ones of the type M{X}.{Y}
for region, cards_folder in zip(args.region, infolder):
    print(f"### PROCESSING {region.upper()}")
    for folder in os.listdir(f"{cards_folder}/ee"):
        if not folder.replace(".", "").isdigit():
            print(f"  Skipping {folder}, not a mass folder")
            continue

        mass_value = float(folder)
        if not is_mass_in_regions(mass_value, [region]):
            continue
        print("    # processing mass value:", mass_value)

        folder_path = os.path.join(cards_folder, "ee", folder)
        if not os.path.isdir(folder_path):
            continue

        for file in os.listdir(folder_path):
            if file == f"higgsCombine_{category_with_era}{tag}.AsymptoticLimits.mH120.root":
                f = ROOT.TFile.Open(os.path.join(folder_path, file))
                t = f.Get("limit")
                limit = {}
                
                for entry in t:
                    quantile = entry.quantileExpected
                    limit_value = entry.limit

                    if quantile == -1:
                        limit["observed"] = str(limit_value)
                    elif abs(quantile - 0.025) < 1e-3:
                        limit["expected_2p5"] = str(limit_value)
                    elif abs(quantile - 0.16) < 1e-3:
                        limit["expected_16"] = str(limit_value)
                    elif abs(quantile - 0.5) < 1e-3:
                        limit["expected_50"] = str(limit_value)
                    elif abs(quantile - 0.84) < 1e-3:
                        limit["expected_84"] = str(limit_value)
                    elif abs(quantile - 0.975) < 1e-3:
                        limit["expected_97p5"] = str(limit_value)
                
                f.Close()

                if "expected_50" not in limit:
                    print("    WARNING: no expected limits produced for mass", folder, "; will use median and sigma.")
                    list_failed_mass_points.append(folder)
                    continue

                if args.unblind and "observed" not in limit:
                    print(f"    WARNING: unblind requested but no observed limit found in file for mass {folder}")

                mass = folder

                if mass in r_values:
                    if r_values[mass]["expected_50"] < limit["expected_50"]:
                        continue
                    else:
                        print(f"    UPDATED limit for mass {mass} to region {cards_folder.split('region')[1][0]}: prev median limit = {r_values[mass]['expected_50']} => new = {limit['expected_50']}")

                r_values[mass] = limit


# Extract base arrays
masses = [float(mass) for mass in sorted(r_values.keys(), key=float)]
observed = np.array([float(r_values[mass].get("observed", 0.0)) for mass in sorted(r_values.keys(), key=float)])
expected_50 = np.array([float(r_values[mass]["expected_50"]) for mass in sorted(r_values.keys(), key=float)])
expected_16 = np.array([float(r_values[mass]["expected_16"]) for mass in sorted(r_values.keys(), key=float)])
expected_84 = np.array([float(r_values[mass]["expected_84"]) for mass in sorted(r_values.keys(), key=float)])
expected_2p5 = np.array([float(r_values[mass]["expected_2p5"]) for mass in sorted(r_values.keys(), key=float)])
expected_97p5 = np.array([float(r_values[mass]["expected_97p5"]) for mass in sorted(r_values.keys(), key=float)])

total_luminosity = 58.6
luminosity = 6.68
lumi_computed = False

for mass in masses:
    mass_region = None
    for region in args.region:
        lower, upper = limit_bounds[region]
        if lower <= mass <= upper:
            mass_region = region
            break
    
    if mass_region is None:
        print(f"WARNING: mass {mass} does not fall in any specified region, skipping efficiency/xsec retrieval")
        continue
    
    input_cards_folder = region_to_cards[mass_region]

    effs = []
    xsecs = []
    acceptances = []
    ns_expected = []
    ns_data = []
    lumis = []

    eras_to_check = [args.era] if args.era != "allYears" else ["2022", "2022EE", "2023", "2023BPix"]

    for era in eras_to_check:
        input_file_path = f"{input_cards_folder}/ee/common/Xee_ee_{era}.input.root"
        f = ROOT.TFile.Open(input_file_path)
        w = f.Get("w")
        
        category_label = "" if (args.category == "inclusive" or "combination" in args.category.lower()) else f"_cat_{category_label_map[args.category]}"
        eff = w.var(f"Zd_M{mass:.1f}_efficiency_{era}").getValV() * w.var(f"Zd{category_label}_M{mass:.1f}_fraction_{era}").getValV()
        xsec = w.var(f"Zd_M{mass:.1f}_xsec_{era}").getValV()
        acceptance = w.var(f"Zd_M{mass:.1f}_acceptance_{era}").getValV()
        
        if not lumi_computed:
            lumi = w.var(f"luminosity_{era}").getValV()

        datacard_file_path = f"{input_cards_folder}/ee/{mass:.1f}/Xee_ee_{category_map[args.category]}_{era}.root"
        f_datacard = ROOT.TFile.Open(datacard_file_path)
        w_datacard = f_datacard.Get("w")
        n_expected = w_datacard.obj(f"n_exp_binXee_ee_{category_map[args.category]}_{era}_proc_Zd").getValV()
        n_data = w_datacard.data("data_obs").sumEntries()

        effs.append(eff)
        xsecs.append(xsec)
        acceptances.append(acceptance)
        lumis.append(lumi)
        ns_expected.append(n_expected)
        ns_data.append(n_data)

    r_values[f"{mass:.1f}"]["efficiency"] = np.average(effs, weights=ns_data)
    r_values[f"{mass:.1f}"]["xsec"] = np.average(xsecs, weights=ns_data)
    r_values[f"{mass:.1f}"]["acceptance"] = np.average(acceptances, weights=ns_data)
    r_values[f"{mass:.1f}"]["Nexpected"] = np.sum(ns_expected)

    if not lumi_computed:
        luminosity = np.sum(lumis)
        lumi_computed = True
    
    f.Close()
    f_datacard.Close()

luminosity = luminosity * 1e3  # convert to pb^-1
print("DEBUG: Using luminosity =", luminosity, "pb^-1 for era ", args.era)

# Model-independent limits computation
expected_50_indep = np.array([float(r_values[mass]["expected_50"]) * r_values[mass]["Nexpected"] / (r_values[mass]["efficiency"] * luminosity) for mass in sorted(r_values.keys(), key=float)])
expected_16_indep = np.array([float(r_values[mass]["expected_16"]) * r_values[mass]["Nexpected"] / (r_values[mass]["efficiency"] * luminosity) for mass in sorted(r_values.keys(), key=float)])
expected_84_indep = np.array([float(r_values[mass]["expected_84"]) * r_values[mass]["Nexpected"] / (r_values[mass]["efficiency"] * luminosity) for mass in sorted(r_values.keys(), key=float)])
expected_2p5_indep = np.array([float(r_values[mass]["expected_2p5"]) * r_values[mass]["Nexpected"] / (r_values[mass]["efficiency"] * luminosity) for mass in sorted(r_values.keys(), key=float)])
expected_97p5_indep = np.array([float(r_values[mass]["expected_97p5"]) * r_values[mass]["Nexpected"] / (r_values[mass]["efficiency"] * luminosity) for mass in sorted(r_values.keys(), key=float)])
observed_indep = np.array([float(r_values[mass].get("observed", 0.0)) * r_values[mass]["Nexpected"] / (r_values[mass]["efficiency"] * luminosity) for mass in sorted(r_values.keys(), key=float)])

expected_50_indep_noaccept = np.array([float(r_values[mass]["expected_50"]) * r_values[mass]["Nexpected"] / (r_values[mass]["efficiency"] * r_values[mass]["acceptance"] * luminosity) for mass in sorted(r_values.keys(), key=float)])
expected_16_indep_noaccept = np.array([float(r_values[mass]["expected_16"]) * r_values[mass]["Nexpected"] / (r_values[mass]["efficiency"] * r_values[mass]["acceptance"] * luminosity) for mass in sorted(r_values.keys(), key=float)])
expected_84_indep_noaccept = np.array([float(r_values[mass]["expected_84"]) * r_values[mass]["Nexpected"] / (r_values[mass]["efficiency"] * r_values[mass]["acceptance"] * luminosity) for mass in sorted(r_values.keys(), key=float)])
expected_2p5_indep_noaccept = np.array([float(r_values[mass]["expected_2p5"]) * r_values[mass]["Nexpected"] / (r_values[mass]["efficiency"] * r_values[mass]["acceptance"] * luminosity) for mass in sorted(r_values.keys(), key=float)])
expected_97p5_indep_noaccept = np.array([float(r_values[mass]["expected_97p5"]) * r_values[mass]["Nexpected"] / (r_values[mass]["efficiency"] * r_values[mass]["acceptance"] * luminosity) for mass in sorted(r_values.keys(), key=float)])
observed_indep_noaccept = np.array([float(r_values[mass].get("observed", 0.0)) * r_values[mass]["Nexpected"] / (r_values[mass]["efficiency"] * r_values[mass]["acceptance"] * luminosity) for mass in sorted(r_values.keys(), key=float)])

expected_50_indep_accept = np.array([float(r_values[mass]["expected_50"]) * r_values[mass]["Nexpected"] / (luminosity) for mass in sorted(r_values.keys(), key=float)])
expected_16_indep_accept = np.array([float(r_values[mass]["expected_16"]) * r_values[mass]["Nexpected"] / (luminosity) for mass in sorted(r_values.keys(), key=float)])
expected_84_indep_accept = np.array([float(r_values[mass]["expected_84"]) * r_values[mass]["Nexpected"] / (luminosity) for mass in sorted(r_values.keys(), key=float)])
expected_2p5_indep_accept = np.array([float(r_values[mass]["expected_2p5"]) * r_values[mass]["Nexpected"] / (luminosity) for mass in sorted(r_values.keys(), key=float)])
expected_97p5_indep_accept = np.array([float(r_values[mass]["expected_97p5"]) * r_values[mass]["Nexpected"] / (luminosity) for mass in sorted(r_values.keys(), key=float)])
observed_indep_accept = np.array([float(r_values[mass].get("observed", 0.0)) * r_values[mass]["Nexpected"] / (luminosity) for mass in sorted(r_values.keys(), key=float)])

expected_50_eps2 = np.array([
    float(r_values[mass]["expected_50"]) * r_values[mass]["Nexpected"] * (2e-2)**2 /
    (r_values[mass]["xsec"] * r_values[mass]["efficiency"] * luminosity)
    for mass in sorted(r_values.keys(), key=float)
])
expected_16_eps2 = np.array([
    float(r_values[mass]["expected_16"]) * r_values[mass]["Nexpected"] * (2e-2)**2 /
    (r_values[mass]["xsec"] * r_values[mass]["efficiency"] * luminosity)
    for mass in sorted(r_values.keys(), key=float)
])
expected_84_eps2 = np.array([
    float(r_values[mass]["expected_84"]) * r_values[mass]["Nexpected"] * (2e-2)**2 /
    (r_values[mass]["xsec"] * r_values[mass]["efficiency"] * luminosity)
    for mass in sorted(r_values.keys(), key=float)
])
expected_2p5_eps2 = np.array([
    float(r_values[mass]["expected_2p5"]) * r_values[mass]["Nexpected"] * (2e-2)**2 /
    (r_values[mass]["xsec"] * r_values[mass]["efficiency"] * luminosity)
    for mass in sorted(r_values.keys(), key=float)
])
expected_97p5_eps2 = np.array([
    float(r_values[mass]["expected_97p5"]) * r_values[mass]["Nexpected"] * (2e-2)**2 /
    (r_values[mass]["xsec"] * r_values[mass]["efficiency"] * luminosity)
    for mass in sorted(r_values.keys(), key=float)
])
observed_eps2 = np.array([
    float(r_values[mass].get("observed", 0.0)) * r_values[mass]["Nexpected"] * (2e-2)**2 /
    (r_values[mass]["xsec"] * r_values[mass]["efficiency"] * luminosity)
    for mass in sorted(r_values.keys(), key=float)
])

# Add dictionary entries
for idx, mass in enumerate(sorted(r_values.keys(), key=float)):
    r_values[mass]["expected_50_indep"] = expected_50_indep[idx]
    r_values[mass]["expected_16_indep"] = expected_16_indep[idx]
    r_values[mass]["expected_84_indep"] = expected_84_indep[idx]
    r_values[mass]["expected_2p5_indep"] = expected_2p5_indep[idx]
    r_values[mass]["expected_97p5_indep"] = expected_97p5_indep[idx]
    r_values[mass]["observed_indep"] = observed_indep[idx]

    r_values[mass]["expected_50_indep_noaccept"] = expected_50_indep_noaccept[idx]
    r_values[mass]["expected_16_indep_noaccept"] = expected_16_indep_noaccept[idx]
    r_values[mass]["expected_84_indep_noaccept"] = expected_84_indep_noaccept[idx]
    r_values[mass]["expected_2p5_indep_noaccept"] = expected_2p5_indep_noaccept[idx]
    r_values[mass]["expected_97p5_indep_noaccept"] = expected_97p5_indep_noaccept[idx]
    r_values[mass]["observed_indep_noaccept"] = observed_indep_noaccept[idx]

    r_values[mass]["expected_50_indep_accept"] = expected_50_indep_accept[idx]
    r_values[mass]["expected_16_indep_accept"] = expected_16_indep_accept[idx]
    r_values[mass]["expected_84_indep_accept"] = expected_84_indep_accept[idx]
    r_values[mass]["expected_2p5_indep_accept"] = expected_2p5_indep_accept[idx]
    r_values[mass]["expected_97p5_indep_accept"] = expected_97p5_indep_accept[idx]
    r_values[mass]["observed_indep_accept"] = observed_indep_accept[idx]

    r_values[mass]["expected_50_eps2"] = expected_50_eps2[idx]
    r_values[mass]["expected_16_eps2"] = expected_16_eps2[idx]
    r_values[mass]["expected_84_eps2"] = expected_84_eps2[idx]
    r_values[mass]["expected_2p5_eps2"] = expected_2p5_eps2[idx]
    r_values[mass]["expected_97p5_eps2"] = expected_97p5_eps2[idx]
    r_values[mass]["observed_eps2"] = observed_eps2[idx]


### -------------------------------
### ---------- RESCALING ----------
### -------------------------------

lumi_rescale_factor = np.sqrt(total_luminosity * 1e3 / luminosity)
print("DEBUG: Rescaling limits by factor", lumi_rescale_factor, "to account for luminosity difference between", luminosity * 1e-3, "fb^-1 and target full luminosity of", total_luminosity, "fb^-1")

if args.rescale_full:
    expected_50 /= lumi_rescale_factor
    expected_16 /= lumi_rescale_factor
    expected_84 /= lumi_rescale_factor
    expected_2p5 /= lumi_rescale_factor
    expected_97p5 /= lumi_rescale_factor
    observed /= lumi_rescale_factor

    expected_50_indep /= lumi_rescale_factor
    expected_16_indep /= lumi_rescale_factor
    expected_84_indep /= lumi_rescale_factor
    expected_2p5_indep /= lumi_rescale_factor
    expected_97p5_indep /= lumi_rescale_factor
    observed_indep /= lumi_rescale_factor

    expected_50_indep_noaccept /= lumi_rescale_factor
    expected_16_indep_noaccept /= lumi_rescale_factor
    expected_84_indep_noaccept /= lumi_rescale_factor
    expected_2p5_indep_noaccept /= lumi_rescale_factor
    expected_97p5_indep_noaccept /= lumi_rescale_factor
    observed_indep_noaccept /= lumi_rescale_factor

    expected_50_indep_accept /= lumi_rescale_factor
    expected_16_indep_accept /= lumi_rescale_factor
    expected_84_indep_accept /= lumi_rescale_factor
    expected_2p5_indep_accept /= lumi_rescale_factor
    expected_97p5_indep_accept /= lumi_rescale_factor
    observed_indep_accept /= lumi_rescale_factor

    expected_50_eps2 /= lumi_rescale_factor
    expected_16_eps2 /= lumi_rescale_factor
    expected_84_eps2 /= lumi_rescale_factor
    expected_2p5_eps2 /= lumi_rescale_factor
    expected_97p5_eps2 /= lumi_rescale_factor
    observed_eps2 /= lumi_rescale_factor

if args.rescale_muon_lumi:
    muon_scale = np.sqrt(175 / 58.6)
    expected_50 /= muon_scale
    expected_16 /= muon_scale
    expected_84 /= muon_scale
    expected_2p5 /= muon_scale
    expected_97p5 /= muon_scale
    observed /= muon_scale

    expected_50_indep /= muon_scale
    expected_16_indep /= muon_scale
    expected_84_indep /= muon_scale
    expected_2p5_indep /= muon_scale
    expected_97p5_indep /= muon_scale
    observed_indep /= muon_scale

    expected_50_indep_noaccept /= muon_scale
    expected_16_indep_noaccept /= muon_scale
    expected_84_indep_noaccept /= muon_scale
    expected_2p5_indep_noaccept /= muon_scale
    expected_97p5_indep_noaccept /= muon_scale
    observed_indep_noaccept /= muon_scale

    expected_50_indep_accept /= muon_scale
    expected_16_indep_accept /= muon_scale
    expected_84_indep_accept /= muon_scale
    expected_2p5_indep_accept /= muon_scale
    expected_97p5_indep_accept /= muon_scale
    observed_indep_accept /= muon_scale

    expected_50_eps2 /= muon_scale
    expected_16_eps2 /= muon_scale
    expected_84_eps2 /= muon_scale
    expected_2p5_eps2 /= muon_scale
    expected_97p5_eps2 /= muon_scale
    observed_eps2 /= muon_scale

label_kwargs = {
    "loc" : 0,
    "com" : 13.6, 
    "data" : True if args.unblind else is_data,
    "year" : "2022+2023" if args.era == "allYears" else args.era,
    "lumi" : luminosity * 1e-3,
}

fig_width = 15 if len(args.region) > 1 else 10

def draw_decorations(ax):
    for mass_failed in list_failed_mass_points:
        ax.axvspan(float(mass_failed)-0.05, float(mass_failed)+0.05, color='red', alpha=0.8, zorder=999)

    if len(args.region) > 1:
        all_bounds = [limit_bounds[reg] for reg in args.region]
        all_bounds.sort()
        missing_regions = []
        for i in range(len(all_bounds)-1):
            upper_current = all_bounds[i][1]
            lower_next = all_bounds[i+1][0]
            if lower_next > upper_current:
                missing_regions.append((upper_current, lower_next))
        
        for lower, upper in missing_regions:
            ax.axvspan(lower - 0.08, upper + 0.07, color='lightgray', alpha=1, zorder=5)

    ax.set_axisbelow(False)
    ax.spines['bottom'].set_zorder(999)
    ax.spines['left'].set_zorder(999)
    ax.spines['top'].set_zorder(999)
    ax.spines['right'].set_zorder(999)


### 1. LIMITS ON MU
fig, ax = plt.subplots(figsize=(fig_width, 10))

if args.unblind:
    plt.plot(masses, observed, color="k", marker='o', label="Observed", zorder=10, linestyle='-')
plt.plot(masses, expected_50, color="k", label="Median expected", zorder=5, linestyle='--', alpha=0.3)
plt.fill_between(masses, expected_16, expected_84, color='#FFDF7Fff', label=r"68% expected", zorder=3)
plt.fill_between(masses, expected_2p5, expected_97p5, color='#85D1FBff', label=r"95% expected", zorder=2)

draw_decorations(ax)
hep.cms.label("Preliminary", ax=ax, **label_kwargs)
plt.xlabel("M(X) [GeV]")
plt.ylabel(r"$\mu$")
plt.yscale("log")
plt.legend()
if args.rescale_full:
    plt.title(f"(rescaled from {luminosity/1e3:.2f} $fb^{{-1}}$)", fontsize=18, pad=40)
if args.rescale_muon_lumi:
    plt.title(f"(rescaled from {luminosity/1e3:.2f} $fb^{{-1}}$ to 175/fb muon luminosity)", fontsize=18, pad=40)

for ext in ['png', 'pdf']:
    plt.savefig(os.path.join(outfolder, f"mu_limit_results{tag}_{region_tag}.{ext}"))
    print(f"Saved plot: {os.path.join(outfolder, f'mu_limit_results{tag}_{region_tag}.{ext}')}")


### 2. MODEL-INDEPENDENT (sigma * BR * A)
fig, ax = plt.subplots(figsize=(fig_width, 10))

if args.unblind:
    plt.plot(masses, observed_indep, color="k", marker='o', label="Observed", zorder=10, linestyle='-')
plt.plot(masses, expected_50_indep, color="k", label="Median expected", zorder=5, linestyle='--', alpha=0.3)
plt.fill_between(masses, expected_16_indep, expected_84_indep, color='#FFDF7Fff', label=r"68% expected", zorder=3)
plt.fill_between(masses, expected_2p5_indep, expected_97p5_indep, color='#85D1FBff', label=r"95% expected", zorder=2)

draw_decorations(ax)
hep.cms.label("Preliminary", ax=ax, **label_kwargs)
plt.xlabel("M(X) [GeV]")
plt.ylabel(r"$\sigma(pp \to X)\ \mathcal{B}(X \to ee)\ \mathcal{A}$ [pb]")
plt.yscale("log")
plt.legend()
if args.rescale_full:
    plt.title(f"(rescaled from {luminosity/1e3:.2f} $fb^{{-1}}$)", fontsize=18, pad=40)
if args.rescale_muon_lumi:
    plt.title(f"(rescaled from {luminosity/1e3:.2f} $fb^{{-1}}$ to 175/fb muon luminosity)", fontsize=18, pad=40)

for ext in ['png', 'pdf']:
    plt.savefig(os.path.join(outfolder, f"mu_limit_results_indep_xsecBR{tag}_{region_tag}.{ext}"))
    print(f"Saved plot: {os.path.join(outfolder, f'mu_limit_results_indep_xsecBR{tag}_{region_tag}.{ext}')}")


### 3. EPSILON^2 LIMITS
fig, ax = plt.subplots(figsize=(fig_width, 10))

if args.unblind:
    plt.plot(masses, observed_eps2, color="k", marker='o', label="Observed", zorder=10, linestyle='-')
plt.plot(masses, expected_50_eps2, color="k", label="Median expected", zorder=5, linestyle='--', alpha=0.3)
plt.fill_between(masses, expected_16_eps2, expected_84_eps2, color='#FFDF7Fff', label=r"68% expected", zorder=3)
plt.fill_between(masses, expected_2p5_eps2, expected_97p5_eps2, color='#85D1FBff', label=r"95% expected", zorder=2)

draw_decorations(ax)
hep.cms.label("Preliminary", ax=ax, **label_kwargs)
plt.xlabel("M(X) [GeV]")
plt.ylabel(r"$\epsilon^2$")
plt.yscale("log")
plt.legend()
if args.rescale_full:
    plt.title(f"(rescaled from {luminosity/1e3:.2f} $fb^{{-1}}$)", fontsize=18, pad=40)
if args.rescale_muon_lumi:
    plt.title(f"(rescaled from {luminosity/1e3:.2f} $fb^{{-1}}$ to 175/fb muon luminosity)", fontsize=18, pad=40)

for ext in ['png', 'pdf']:
    plt.savefig(os.path.join(outfolder, f"mu_limit_results_eps2{tag}_{region_tag}.{ext}"))
    print(f"Saved plot: {os.path.join(outfolder, f'mu_limit_results_eps2{tag}_{region_tag}.{ext}')}")


### 4. MODEL-INDEPENDENT DIVIDED BY ACCEPTANCE (sigma * BR)
fig, ax = plt.subplots(figsize=(fig_width, 10))

if args.unblind:
    plt.plot(masses, observed_indep_noaccept, color="k", marker='o', label="Observed", zorder=10, linestyle='-')
plt.plot(masses, expected_50_indep_noaccept, color="k", label="Median expected", zorder=5, linestyle='--', alpha=0.3)
plt.fill_between(masses, expected_16_indep_noaccept, expected_84_indep_noaccept, color='#FFDF7Fff', label=r"68% expected", zorder=3)
plt.fill_between(masses, expected_2p5_indep_noaccept, expected_97p5_indep_noaccept, color='#85D1FBff', label=r"95% expected", zorder=2)

draw_decorations(ax)
hep.cms.label("Preliminary", ax=ax, **label_kwargs)
plt.xlabel("M(X) [GeV]")
plt.ylabel(r"$\sigma(pp \to X)\ \mathcal{B}(X \to ee)$ [pb]")
plt.yscale("log")
plt.legend()
if args.rescale_full:
    plt.title(f"(rescaled from {luminosity/1e3:.2f} $fb^{{-1}}$)", fontsize=18, pad=40)
if args.rescale_muon_lumi:
    plt.title(f"(rescaled from {luminosity/1e3:.2f} $fb^{{-1}}$ to 175/fb muon luminosity)", fontsize=18, pad=40)

for ext in ['png', 'pdf']:
    plt.savefig(os.path.join(outfolder, f"mu_limit_results_indep_xsecBR_noaccept{tag}_{region_tag}.{ext}"))
    print(f"Saved plot: {os.path.join(outfolder, f'mu_limit_results_indep_xsecBR_noaccept{tag}_{region_tag}.{ext}')}")


### 5. MODEL-INDEPENDENT WITH ACCEPTANCE & EFFICIENCY (sigma * BR * A * eps)
fig, ax = plt.subplots(figsize=(fig_width, 10))

if args.unblind:
    plt.plot(masses, observed_indep_accept, color="k", marker='o', label="Observed", zorder=10, linestyle='-')
plt.plot(masses, expected_50_indep_accept, color="k", label="Median expected", zorder=5, linestyle='--', alpha=0.3)
plt.fill_between(masses, expected_16_indep_accept, expected_84_indep_accept, color='#FFDF7Fff', label=r"68% expected", zorder=3)
plt.fill_between(masses, expected_2p5_indep_accept, expected_97p5_indep_accept, color='#85D1FBff', label=r"95% expected", zorder=2)

draw_decorations(ax)
hep.cms.label("Preliminary", ax=ax, **label_kwargs)
plt.xlabel("M(X) [GeV]")
plt.ylabel(r"$\sigma(pp \to X)\ \mathcal{B}(X \to ee)\ \mathcal{A}\ \epsilon$ [pb]")
plt.yscale("log")
plt.legend()
if args.rescale_full:
    plt.title(f"(rescaled from {luminosity/1e3:.2f} $fb^{{-1}}$)", fontsize=18, pad=40)
if args.rescale_muon_lumi:
    plt.title(f"(rescaled from {luminosity/1e3:.2f} $fb^{{-1}}$ to 175/fb muon luminosity)", fontsize=18, pad=40)

for ext in ['png', 'pdf']:
    plt.savefig(os.path.join(outfolder, f"mu_limit_results_indep_xsecBRAcceptance{tag}_{region_tag}.{ext}"))
    print(f"Saved plot: {os.path.join(outfolder, f'mu_limit_results_indep_xsecBRAcceptance{tag}_{region_tag}.{ext}')}")


### SUMMARY PRINT
print("\nModel-independent limits:")
for idx, mass in enumerate(sorted(r_values.keys(), key=float)):
    limit = r_values[mass]
    print(f"Mass: {mass} GeV")
    print(f"  N_expected: {limit['Nexpected']:.2f}")
    print(f"  xsec: {limit['xsec']:.2f} pb")
    print(f"  efficiency: {limit['efficiency'] * 100:.3g} %")
    print(f"  acceptance: {limit['acceptance'] * 100:.3g} %")
    print(f"  mu_50: {limit['expected_50']}")
    print(f"  mu_16: {limit['expected_16']}")
    print(f"  mu_84: {limit['expected_84']}")
    print(f"  mu_2p5: {limit['expected_2p5']}")
    print(f"  mu_97p5: {limit['expected_97p5']}")
    if args.unblind:
        print(f"  mu_obs: {limit.get('observed', 'N/A')}")
    print()

    if args.rescale_full:
        print(f"FOLLOWING RESCALED TO FULL LUMI: {total_luminosity} fb^-1 (rescale factor = {lumi_rescale_factor:.2f})")
    if args.rescale_muon_lumi:
        print(f"FOLLOWING FURTHER RESCALED TO MUON LUMI: 175 fb^-1 (rescale factor = {np.sqrt(175 / 58.6):.2f})")
    print(f"  Model-independent mu_50: {expected_50_indep[idx]:.4f}")
    print(f"  Model-independent mu_16: {expected_16_indep[idx]:.4f}")
    print(f"  Model-independent mu_84: {expected_84_indep[idx]:.4f}")
    print(f"  Model-independent mu_2p5: {expected_2p5_indep[idx]:.4f}")
    print(f"  Model-independent mu_97p5: {expected_97p5_indep[idx]:.4f}")
    if args.unblind:
        print(f"  Model-independent mu_obs: {observed_indep[idx]:.4f}")

    print(f"  Model-independent mu_50 no acceptance: {expected_50_indep_noaccept[idx]:.4f}")
    print(f"  Model-independent mu_16 no acceptance: {expected_16_indep_noaccept[idx]:.4f}")
    print(f"  Model-independent mu_84 no acceptance: {expected_84_indep_noaccept[idx]:.4f}")
    print(f"  Model-independent mu_2p5 no acceptance: {expected_2p5_indep_noaccept[idx]:.4f}")
    print(f"  Model-independent mu_97p5 no acceptance: {expected_97p5_indep_noaccept[idx]:.4f}")
    if args.unblind:
        print(f"  Model-independent mu_obs no acceptance: {observed_indep_noaccept[idx]:.4f}")

    print(f"  Model-independent mu_50 with acceptance: {expected_50_indep_accept[idx]:.4f}")
    print(f"  Model-independent mu_16 with acceptance: {expected_16_indep_accept[idx]:.4f}")
    print(f"  Model-independent mu_84 with acceptance: {expected_84_indep_accept[idx]:.4f}")
    print(f"  Model-independent mu_2p5 with acceptance: {expected_2p5_indep_accept[idx]:.4f}")
    print(f"  Model-independent mu_97p5 with acceptance: {expected_97p5_indep_accept[idx]:.4f}")
    if args.unblind:
        print(f"  Model-independent mu_obs with acceptance: {observed_indep_accept[idx]:.4f}")

# Dump results to pickle
with open(os.path.join(outfolder, f"limits_results{tag}_{region_tag}.pkl"), 'wb') as f:
    print(f"\nDumping results to {os.path.join(outfolder, f'limits_results{tag}_{region_tag}.pkl')}")
    pickle.dump(r_values, f, protocol=pickle.HIGHEST_PROTOCOL)