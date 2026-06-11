import ROOT
import numpy as np
import matplotlib.pyplot as plt
import os
import mplhep as hep
import argparse
from scipy.interpolate import PchipInterpolator

parser = argparse.ArgumentParser()
parser.add_argument('-o', '--output_folder', type=str, default='/eos/home-n/npalmeri/www/DiElectron/sensitivity/fitDiagnostics/mu0', help='Output folder for the plots')
parser.add_argument('-i', '--input_cards', type=str, nargs='+', default=['cards'], help='Input cards folder(s) - must match number of regions in order')
parser.add_argument('-c', '--category', type=str, default='etaHigh', help='Category to plot (default: etaHigh)')
parser.add_argument('-t', '--tag', type=str, default="", help='Optional additional tag for output files')
parser.add_argument('-r', '--region', type=str, nargs='+', default=['region1'], choices=["region0", "region1", "region2"], help='Region(s) to plot (can specify multiple)')
parser.add_argument('--rescale_full', action='store_true', help='Rescale all limits to full luminosity')
parser.add_argument('--era', type=str, default='2023', help='Era to use for file naming (e.g., 2023, allYears)')
args = parser.parse_args()

is_data = ["data" in folder for folder in args.input_cards]

# Validate that input_cards matches the number of regions
if len(args.input_cards) != len(args.region):
    raise ValueError(f"Number of input_cards ({len(args.input_cards)}) must match number of regions ({len(args.region)})")

# limit_bounds = {
#     "region0" : (0.4, 1.8),
#     "region1" : (2.2, 4.0),
#     "region2" : (4.4, 10.8),
# }

# # 0.4, 10.8
# # 0.9 ,10.7
# limit_bounds = {
#     "region0" : (0.4, 2.2),
#     "region1" : (1.8, 4.4),
#     "region2" : (4.0, 10.8),
# }

# 0.4, 10.8
# 0.9 ,10.7
# limit_bounds = {
#     "region0" : (0.5, 2.2),
#     "region1" : (1.8, 5.6),
#     "region2" : (5.4, 10.0),
# }

limit_bounds = {
    "region0": (0.5, 2.2),
    "region1": (1.8, 4.9),
    # "region2": (4.9, 10.5),
    "region2": (4.9, 9.7),
}

# # TEMPORARY: just for 18/12 plots
# limit_bounds = {
#     "region0" : (0.9, 2.2),
#     "region1" : (1.8, 4.4),
#     "region2" : (4.0, 10.4),
# }

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
    "etaCombination" : 4, # same expected number
    "dRCombination" : 4, # same expected number
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

        # Check if mass falls within any of the specified regions
        mass_value = float(folder)
        if not is_mass_in_regions(mass_value, [region]):
            continue
        print("    # processing mass value:", mass_value)

        folder_path = os.path.join(cards_folder, "ee", folder)

        # check if it's a directory
        if not os.path.isdir(folder_path):
            continue

        # iterate over files in the subfolder
        for file in os.listdir(folder_path):
            # find higgsCombine_inclusive.AsymptoticLimits.mH120.root
            if file == f"higgsCombine_{category_with_era}{tag}.AsymptoticLimits.mH120.root":
                # print("    Found limit output root file:", file)
                f = ROOT.TFile.Open(os.path.join(folder_path, file))
                t = f.Get("limit")
                quantiles = [-1, 0.025, 0.16, 0.5, 0.84, 0.975]
                limit = {}
                
                # apply cut on "quantileExpected" and find corresponding "limit"
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

                # throw warning if no expected limits saved
                if "expected_50" not in limit:
                    print("    WARNING: no expected limits produced for mass", folder, "; will use median and sigma.")
                    list_failed_mass_points.append(folder)
                    continue

                # retrieve mass value as float
                mass = folder

                # if mass point already saved: only update it if median limit is better
                if mass in r_values:
                    if r_values[mass]["expected_50"] < limit["expected_50"]:
                        continue
                    else:
                        print(f"    UPDATED limit for mass {mass} to region {cards_folder.split('region')[1][0]}: prev median limit = {r_values[mass]['expected_50']} => new = {limit['expected_50']}")

                r_values[mass] = limit


# plot central expected limit with 1 sigma and 2 sigma bands IN BRAZILIAN STYLE PLOT
masses = [float(mass) for mass in sorted(r_values.keys(), key=float)]
observed = [float(r_values[mass]["observed"]) for mass in sorted(r_values.keys(), key=float)]
expected_50 = np.array([float(r_values[mass]["expected_50"]) for mass in sorted(r_values.keys(), key=float)])
expected_16 = np.array([float(r_values[mass]["expected_16"]) for mass in sorted(r_values.keys(), key=float)])
expected_84 = np.array([float(r_values[mass]["expected_84"]) for mass in sorted(r_values.keys(), key=float)])
expected_2p5 = np.array([float(r_values[mass]["expected_2p5"]) for mass in sorted(r_values.keys(), key=float)])
expected_97p5 = np.array([float(r_values[mass]["expected_97p5"]) for mass in sorted(r_values.keys(), key=float)])

# # TEMPORARY: remove mass points in gap regions
# masses_to_remove = [1.9, 2.0, 2.1, 4.1, 4.2, 4.3]
# for mass in masses_to_remove:
#     if mass in masses:
#         idx = masses.index(mass)
#         masses.pop(idx)
#         observed.pop(idx)
#         expected_50 = np.delete(expected_50, idx)
#         expected_16 = np.delete(expected_16, idx)
#         expected_84 = np.delete(expected_84, idx)
#         expected_2p5 = np.delete(expected_2p5, idx)
#         expected_97p5 = np.delete(expected_97p5, idx)

# Now convert these to model-independent limits

# 1) retrieve Nexpected, xsec, efficiency for each mass point from input workspace
# For each mass point, determine which region it belongs to and use the corresponding input file

# Get luminosity from the first region's input file
first_cards_folder = args.input_cards[0]
f_lumi = ROOT.TFile.Open(f"{first_cards_folder}/ee/common/Xee_ee_{args.era if args.era != 'allYears' else '2022'}.input.root")
w_lumi = f_lumi.Get("w")

# luminosity = 6.68
# # luminosity = 58.9
# if w_lumi.var(f"luminosity_{args.era}"):
#     luminosity = w_lumi.var((f"luminosity_{args.era}")).getValV()
# else:
#     print(f"WARNING: luminosity variable not found in workspace for era {args.era}, using default value of {luminosity} fb^-1")
# f_lumi.Close()
# print(f"Using luminosity = {luminosity} fb^-1")

total_luminosity = 58.6
luminosity = 6.68

lumi_computed = False

for mass in masses:
    # Determine which region this mass belongs to
    mass_region = None
    for region in args.region:
        lower, upper = limit_bounds[region]
        if lower <= mass <= upper:
            mass_region = region
            break
    
    if mass_region is None:
        print(f"WARNING: mass {mass} does not fall in any specified region, skipping efficiency/xsec retrieval")
        continue
    
    # Use the region-specific input file from the mapping
    input_cards_folder = region_to_cards[mass_region]

    effs = []
    xsecs = []
    acceptances = []
    ns_expected = []
    ns_data = []
    lumis = []

    eras_to_check = [args.era] if args.era != "allYears" else ["2022", "2022EE", "2023", "2023BPix"]

    # ### FIXME TEMPORARY: interpolating acceptances here
    # madgraph_acceptances = [0.004685, 0.008324, 0.008045, 0.006681, 0.009087, 0.015415, 0.084712, 0.099632, 0.106361]
    # signal_masses = [0.5, 1.0, 2.0, 3.1, 4.0, 6.0, 8.0, 10.0, 12.0]
    # madgraph_acceptance_interp = PchipInterpolator(signal_masses, madgraph_acceptances, extrapolate=True)

    for era in eras_to_check:
        # year combination uses all workspaces; take the first one (they all contain efficiencies for all masses)
        input_file_path = f"{input_cards_folder}/ee/common/Xee_ee_{era}.input.root"
        f = ROOT.TFile.Open(input_file_path)
        w = f.Get("w")
        
        category_label = "" if (args.category == "inclusive" or "combination" in args.category.lower()) else f"_cat_{category_label_map[args.category]}"
        # print("DEBUG: opened file ", input_file_path, " for era ", era, " category label = ", category_label)
        # print("DEBUG: looking for efficiency variable with name ", f"Zd_M{mass:.1f}_efficiency_{era}", ": ", w.var(f"Zd_M{mass:.1f}_efficiency_{era}"))
        # print("DEBUG: looking for fraction variable with name ", f"Zd{category_label}_M{mass:.1f}_fraction_{era}", ": ", w.var(f"Zd{category_label}_M{mass:.1f}_fraction_{era}"))
        eff = w.var(f"Zd_M{mass:.1f}_efficiency_{era}").getValV() * w.var(f"Zd{category_label}_M{mass:.1f}_fraction_{era}").getValV() # efficiency should take into account category efficiency as well
        xsec = w.var(f"Zd_M{mass:.1f}_xsec_{era}").getValV()
        acceptance = w.var(f"Zd_M{mass:.1f}_acceptance_{era}").getValV()
        
        # print(f"DEBUG: Pythia acceptance for mass {mass} = {acceptance}")
        # madgraph_acceptance = float(madgraph_acceptance_interp(mass))
        # acceptance *= madgraph_acceptance
        # print(f"DEBUG: Interpolated MadGraph acceptance for mass {mass} = {madgraph_acceptance}, corrected acceptance = {acceptance}")

        # n_expected = w.var(f"Zd_M{mass:.1f}_expected").getValV()
        if not lumi_computed:
            lumi = w.var(f"luminosity_{era}").getValV()

        # get n_expected from datacard root file (might be manipulated during workspace creation by e.g. custom signal multiplier)
        datacard_file_path = f"{input_cards_folder}/ee/{mass:.1f}/Xee_ee_{category_map[args.category]}_{era}.root"
        f_datacard = ROOT.TFile.Open(datacard_file_path)
        w_datacard = f_datacard.Get("w")
        # NB: for category combination, given perfect orthogonality, the expected number is the same as inclusive
        n_expected = w_datacard.obj(f"n_exp_binXee_ee_{category_map[args.category]}_{era}_proc_Zd").getValV()
        # also retrieve #data (neeed to compute weighted signal efficiency when combining years)
        n_data = w_datacard.data("data_obs").sumEntries()

        effs.append(eff)
        xsecs.append(xsec)
        acceptances.append(acceptance)
        lumis.append(lumi)
        ns_expected.append(n_expected)
        ns_data.append(n_data)

    r_values[f"{mass:.1f}"]["efficiency"] = np.average(effs, weights=ns_data)
    r_values[f"{mass:.1f}"]["xsec"] = np.average(xsecs, weights=ns_data) #not era-dependent, but just for consistency
    r_values[f"{mass:.1f}"]["acceptance"] = np.average(acceptances, weights=ns_data) #not era-dependent, but just for consistency
    r_values[f"{mass:.1f}"]["Nexpected"] = np.sum(ns_expected)
    # print(f"DEBUG: efficiency for mass {mass:.1f} = {r_values[f'{mass:.1f}']['efficiency']}, xsec = {r_values[f'{mass:.1f}']['xsec']}, Nexpected = {r_values[f'{mass:.1f}']['Nexpected']}")
    # print(f"DEBUG: (per era: effs = {effs}, xsecs = {xsecs}, lumis = {lumis}, ns_expected = {ns_expected}, ns_data = {ns_data})")
    if not lumi_computed:
        luminosity = np.sum(lumis)
        lumi_computed = True #compute just once; luminosity is per sample (not per mass point)
    
    f.Close()
    f_datacard.Close()

luminosity = luminosity * 1e3 # convert to pb^-1
print("DEBUG: Using luminosity =", luminosity, "pb^-1 for era ", args.era)

# 2) compute model-independent limits
expected_50_indep = np.array([float(r_values[mass]["expected_50"]) * r_values[mass]["Nexpected"] / (r_values[mass]["efficiency"] * luminosity) for mass in sorted(r_values.keys(), key=float)])
expected_16_indep = np.array([float(r_values[mass]["expected_16"]) * r_values[mass]["Nexpected"] / (r_values[mass]["efficiency"] * luminosity) for mass in sorted(r_values.keys(), key=float)])
expected_84_indep = np.array([float(r_values[mass]["expected_84"]) * r_values[mass]["Nexpected"] / (r_values[mass]["efficiency"] * luminosity) for mass in sorted(r_values.keys(), key=float)])
expected_2p5_indep = np.array([float(r_values[mass]["expected_2p5"]) * r_values[mass]["Nexpected"] / (r_values[mass]["efficiency"] * luminosity) for mass in sorted(r_values.keys(), key=float)])
expected_97p5_indep = np.array([float(r_values[mass]["expected_97p5"]) * r_values[mass]["Nexpected"] / (r_values[mass]["efficiency"] * luminosity) for mass in sorted(r_values.keys(), key=float)])
expected_50_indep_noaccept = np.array([float(r_values[mass]["expected_50"]) * r_values[mass]["Nexpected"] / (r_values[mass]["efficiency"] * r_values[mass]["acceptance"] * luminosity) for mass in sorted(r_values.keys(), key=float)])
expected_16_indep_noaccept = np.array([float(r_values[mass]["expected_16"]) * r_values[mass]["Nexpected"] / (r_values[mass]["efficiency"] * r_values[mass]["acceptance"] * luminosity) for mass in sorted(r_values.keys(), key=float)])
expected_84_indep_noaccept = np.array([float(r_values[mass]["expected_84"]) * r_values[mass]["Nexpected"] / (r_values[mass]["efficiency"] * r_values[mass]["acceptance"] * luminosity) for mass in sorted(r_values.keys(), key=float)])
expected_2p5_indep_noaccept = np.array([float(r_values[mass]["expected_2p5"]) * r_values[mass]["Nexpected"] / (r_values[mass]["efficiency"] * r_values[mass]["acceptance"] * luminosity) for mass in sorted(r_values.keys(), key=float)])
expected_97p5_indep_noaccept = np.array([float(r_values[mass]["expected_97p5"]) * r_values[mass]["Nexpected"] / (r_values[mass]["efficiency"] * r_values[mass]["acceptance"] * luminosity) for mass in sorted(r_values.keys(), key=float)])
# observed_indep = np.array([float(r_values[mass]["observed"]) * r_values[mass]["Nexpected"] / (r_values[mass]["efficiency"] * luminosity) for mass in sorted(r_values.keys(), key=float)])

# add arrays to r_values dictionary
for idx, mass in enumerate(sorted(r_values.keys(), key=float)):
    r_values[mass]["expected_50_indep"] = expected_50_indep[idx]
    r_values[mass]["expected_16_indep"] = expected_16_indep[idx]
    r_values[mass]["expected_84_indep"] = expected_84_indep[idx]
    r_values[mass]["expected_2p5_indep"] = expected_2p5_indep[idx]
    r_values[mass]["expected_97p5_indep"] = expected_97p5_indep[idx]
    r_values[mass]["expected_50_indep_noaccept"] = expected_50_indep_noaccept[idx]
    r_values[mass]["expected_16_indep_noaccept"] = expected_16_indep_noaccept[idx]
    r_values[mass]["expected_84_indep_noaccept"] = expected_84_indep_noaccept[idx]
    r_values[mass]["expected_2p5_indep_noaccept"] = expected_2p5_indep_noaccept[idx]
    r_values[mass]["expected_97p5_indep_noaccept"] = expected_97p5_indep_noaccept[idx]
    # r_values[mass]["observed_indep"] = observed_indep[idx]

### -------------------------------
### ---------- PLOTTING -----------
### -------------------------------

lumi_rescale_factor = np.sqrt(total_luminosity * 1e3 / luminosity)
print("DEBUG: Rescaling limits by factor", lumi_rescale_factor, "to account for luminosity difference between", luminosity * 1e-3, "fb^-1 and target full luminosity of", total_luminosity, "fb^-1")
print("DEBUG: before rescaling: expected_50 =", expected_50)
if args.rescale_full:
    expected_50 /= lumi_rescale_factor
    expected_16 /= lumi_rescale_factor
    expected_84 /= lumi_rescale_factor
    expected_2p5 /= lumi_rescale_factor
    expected_97p5 /= lumi_rescale_factor
print("DEBUG: after rescaling: expected_50 =", expected_50)

label_kwargs = {
    "loc" : 0,
    "com" : 13.6, 
    "data" : is_data,
    "year" : "2022+2023" if args.era == "allYears" else args.era,
    "lumi" : luminosity * 1e-3,
}

# if args.rescale_full:
#     label_kwargs["lumi"] = 58.9

### LIMITS ON MU 
fig_width = 15 if len(args.region) > 1 else 10
fig, ax = plt.subplots(figsize=(fig_width, 10))

# plt.plot(masses, observed, color="k", marker='o', label="Observed", zorder = 10)
plt.plot(masses, expected_50, color="k", label="Median expected", zorder = 5, linestyle='--', alpha = 0.3)
plt.fill_between(masses, expected_16, expected_84, color = '#FFDF7Fff', label="68% expected", zorder = 3)
plt.fill_between(masses, expected_2p5, expected_97p5, color = '#85D1FBff', label="95% expected", zorder = 2)

# add a vertical red band for all mass points where the limit failed
for mass in list_failed_mass_points:
    plt.axvspan(float(mass)-0.05, float(mass)+0.05, color='red', alpha=0.8, zorder=999)

# plot gray band in-between missing regions when plotting multiple regions
if len(args.region) > 1:
    # determine missing regions
    all_bounds = [limit_bounds[region] for region in args.region]
    all_bounds.sort()
    missing_regions = []
    for i in range(len(all_bounds)-1):
        upper_current = all_bounds[i][1]
        lower_next = all_bounds[i+1][0]
        if lower_next > upper_current:
            missing_regions.append( (upper_current, lower_next) )
    
    # plot gray bands for missing regions
    for lower, upper in missing_regions:
        plt.axvspan(lower - 0.08, upper + 0.07, color='lightgray', alpha=1, zorder=5)

# Set axes zorder to bring them above the shaded regions
ax.set_axisbelow(False)
ax.spines['bottom'].set_zorder(999)
ax.spines['left'].set_zorder(999)
ax.spines['top'].set_zorder(999)
ax.spines['right'].set_zorder(999)

# ### TEMPORARY: fix mu range to 1e-2 - 5e-1
# ax.set_ylim(1e-2, 5e-1)

hep.cms.label("Preliminary", ax=ax, **label_kwargs)
plt.xlabel("M(X) [GeV]")
plt.ylabel(r"$\mu$")
plt.yscale("log")
plt.legend()
if args.rescale_full:
    plt.title(f"(rescaled from {luminosity/1e3:.2f} $fb^{{-1}}$)", fontsize=18, pad=40)

for ext in ['png', 'pdf']:
    plt.savefig(os.path.join(outfolder, f"mu_limit_results{tag}_{region_tag}.{ext}"))
    print(f"Saved plot: {os.path.join(outfolder, f'mu_limit_results{tag}_{region_tag}.{ext}')}")

### MODEL-INDEPENDENT
print("DEBUG: before rescaling model-independent limits: expected_50_indep =", expected_50_indep)
if args.rescale_full:
    expected_50_indep /= lumi_rescale_factor
    expected_16_indep /= lumi_rescale_factor
    expected_84_indep /= lumi_rescale_factor
    expected_2p5_indep /= lumi_rescale_factor
    expected_97p5_indep /= lumi_rescale_factor
    expected_50_indep_noaccept /= lumi_rescale_factor
    expected_16_indep_noaccept /= lumi_rescale_factor
    expected_84_indep_noaccept /= lumi_rescale_factor
    expected_2p5_indep_noaccept /= lumi_rescale_factor
    expected_97p5_indep_noaccept /= lumi_rescale_factor
print("DEBUG: after rescaling model-independent limits: expected_50_indep =", expected_50_indep)

# epsilon^2 limits: mu * Nexpected / (xsec * luminosity * efficiency)
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

for idx, mass in enumerate(sorted(r_values.keys(), key=float)):
    r_values[mass]["expected_50_eps2"] = expected_50_eps2[idx]
    r_values[mass]["expected_16_eps2"] = expected_16_eps2[idx]
    r_values[mass]["expected_84_eps2"] = expected_84_eps2[idx]
    r_values[mass]["expected_2p5_eps2"] = expected_2p5_eps2[idx]
    r_values[mass]["expected_97p5_eps2"] = expected_97p5_eps2[idx]

# plot model-independent expected limit with 1 sigma and 2 sigma bands IN BRAZILIAN STYLE PLOT
fig, ax = plt.subplots(figsize=(fig_width, 10))
plt.plot(masses, expected_50_indep, color="k", label="Median expected", zorder = 5, linestyle='--', alpha = 0.3)
plt.fill_between(masses, expected_16_indep, expected_84_indep, color = '#FFDF7Fff', label="68% expected", zorder = 3)
plt.fill_between(masses, expected_2p5_indep, expected_97p5_indep, color = '#85D1FBff', label="95% expected", zorder = 2)

# add a vertical red band for all mass points where the limit failed
for mass in list_failed_mass_points:
    plt.axvspan(float(mass)-0.05, float(mass)+0.05, color='red', alpha=0.8, zorder=999)

# plot gray band in-between missing regions when plotting multiple regions
if len(args.region) > 1:
    # determine missing regions
    all_bounds = [limit_bounds[region] for region in args.region]
    all_bounds.sort()
    missing_regions = []
    for i in range(len(all_bounds)-1):
        upper_current = all_bounds[i][1]
        lower_next = all_bounds[i+1][0]
        if lower_next > upper_current:
            missing_regions.append( (upper_current, lower_next) )
    
    # plot gray bands for missing regions
    for lower, upper in missing_regions:
        plt.axvspan(lower - 0.08, upper + 0.07, color='lightgray', alpha=1, zorder=5)

# Set axes zorder to bring them above the shaded regions
ax.set_axisbelow(False)
ax.spines['bottom'].set_zorder(999)
ax.spines['left'].set_zorder(999)
ax.spines['top'].set_zorder(999)
ax.spines['right'].set_zorder(999)

hep.cms.label("Preliminary", ax=ax, **label_kwargs)
plt.xlabel("M(X) [GeV]")
plt.ylabel(r"$\sigma(pp \to X) \cdot \text{BR}(X \to ee) \cdot A$ [pb]")
plt.yscale("log")
plt.legend()
if args.rescale_full:
    plt.title(f"(rescaled from {luminosity/1e3:.2f} $fb^{{-1}}$)", fontsize=18, pad=40)


for ext in ['png', 'pdf']:
    plt.savefig(os.path.join(outfolder, f"mu_limit_results_indep_xsecBR{tag}_{region_tag}.{ext}"))
    print(f"Saved plot: {os.path.join(outfolder, f'mu_limit_results_indep_xsecBR{tag}_{region_tag}.{ext}')}")

# plot epsilon^2 limits
fig, ax = plt.subplots(figsize=(fig_width, 10))
plt.plot(masses, expected_50_eps2, color="k", label="Median expected", zorder=5, linestyle='--', alpha=0.3)
plt.fill_between(masses, expected_16_eps2, expected_84_eps2, color='#FFDF7Fff', label="68% expected", zorder=3)
plt.fill_between(masses, expected_2p5_eps2, expected_97p5_eps2, color='#85D1FBff', label="95% expected", zorder=2)

for mass in list_failed_mass_points:
    plt.axvspan(float(mass)-0.05, float(mass)+0.05, color='red', alpha=0.8, zorder=999)

if len(args.region) > 1:
    all_bounds = [limit_bounds[region] for region in args.region]
    all_bounds.sort()
    missing_regions = []
    for i in range(len(all_bounds)-1):
        upper_current = all_bounds[i][1]
        lower_next = all_bounds[i+1][0]
        if lower_next > upper_current:
            missing_regions.append((upper_current, lower_next))

    for lower, upper in missing_regions:
        plt.axvspan(lower - 0.08, upper + 0.07, color='lightgray', alpha=1, zorder=5)

ax.set_axisbelow(False)
ax.spines['bottom'].set_zorder(999)
ax.spines['left'].set_zorder(999)
ax.spines['top'].set_zorder(999)
ax.spines['right'].set_zorder(999)

hep.cms.label("Preliminary", ax=ax, **label_kwargs)
plt.xlabel("M(X) [GeV]")
plt.ylabel(r"$\epsilon^2$")
plt.yscale("log")
plt.legend()
if args.rescale_full:
    plt.title(f"(rescaled from {luminosity/1e3:.2f} $fb^{{-1}}$)", fontsize=18, pad=40)

for ext in ['png', 'pdf']:
    plt.savefig(os.path.join(outfolder, f"mu_limit_results_eps2{tag}_{region_tag}.{ext}"))
    print(f"Saved plot: {os.path.join(outfolder, f'mu_limit_results_eps2{tag}_{region_tag}.{ext}')}" )

# plot model-independent expected limit with 1 sigma and 2 sigma bands divided by acceptance
fig, ax = plt.subplots(figsize=(fig_width, 10))
plt.plot(masses, expected_50_indep_noaccept, color="k", label="Median expected", zorder = 5, linestyle='--', alpha = 0.3)
plt.fill_between(masses, expected_16_indep_noaccept, expected_84_indep_noaccept, color = '#FFDF7Fff', label="68% expected", zorder = 3)
plt.fill_between(masses, expected_2p5_indep_noaccept, expected_97p5_indep_noaccept, color = '#85D1FBff', label="95% expected", zorder = 2)

for mass in list_failed_mass_points:
    plt.axvspan(float(mass)-0.05, float(mass)+0.05, color='red', alpha=0.8, zorder=999)

if len(args.region) > 1:
    all_bounds = [limit_bounds[region] for region in args.region]
    all_bounds.sort()
    missing_regions = []
    for i in range(len(all_bounds)-1):
        upper_current = all_bounds[i][1]
        lower_next = all_bounds[i+1][0]
        if lower_next > upper_current:
            missing_regions.append( (upper_current, lower_next) )

    for lower, upper in missing_regions:
        plt.axvspan(lower - 0.08, upper + 0.07, color='lightgray', alpha=1, zorder=5)

ax.set_axisbelow(False)
ax.spines['bottom'].set_zorder(999)
ax.spines['left'].set_zorder(999)
ax.spines['top'].set_zorder(999)
ax.spines['right'].set_zorder(999)

hep.cms.label("Preliminary", ax=ax, **label_kwargs)
plt.xlabel("M(X) [GeV]")
plt.ylabel(r"$\sigma(pp \to X) \cdot \text{BR}(X \to ee)$ [pb]")
plt.yscale("log")
plt.legend()
if args.rescale_full:
    plt.title(f"(rescaled from {luminosity/1e3:.2f} $fb^{{-1}}$)", fontsize=18, pad=40)

for ext in ['png', 'pdf']:
    plt.savefig(os.path.join(outfolder, f"mu_limit_results_indep_xsecBR_noaccept{tag}_{region_tag}.{ext}"))
    print(f"Saved plot: {os.path.join(outfolder, f'mu_limit_results_indep_xsecBR_noaccept{tag}_{region_tag}.{ext}')}")

expected_50_indep_accept = np.array([float(r_values[mass]["expected_50"]) * r_values[mass]["Nexpected"] / (luminosity) for mass in sorted(r_values.keys(), key=float)])
expected_16_indep_accept = np.array([float(r_values[mass]["expected_16"]) * r_values[mass]["Nexpected"] / (luminosity) for mass in sorted(r_values.keys(), key=float)])
expected_84_indep_accept = np.array([float(r_values[mass]["expected_84"]) * r_values[mass]["Nexpected"] / (luminosity) for mass in sorted(r_values.keys(), key=float)])
expected_2p5_indep_accept = np.array([float(r_values[mass]["expected_2p5"]) * r_values[mass]["Nexpected"] / (luminosity) for mass in sorted(r_values.keys(), key=float)])
expected_97p5_indep_accept = np.array([float(r_values[mass]["expected_97p5"]) * r_values[mass]["Nexpected"] / (luminosity) for mass in sorted(r_values.keys(), key=float)])
# observed_indep = np.array([float(r_values[mass]["observed"]) * r_values[mass]["Nexpected"] / (r_values[mass]["efficiency"] * luminosity) for mass in sorted(r_values.keys(), key=float)])

for idx, mass in enumerate(sorted(r_values.keys(), key=float)):
    r_values[mass]["expected_50_indep_accept"] = expected_50_indep_accept[idx]
    r_values[mass]["expected_16_indep_accept"] = expected_16_indep_accept[idx]
    r_values[mass]["expected_84_indep_accept"] = expected_84_indep_accept[idx]
    r_values[mass]["expected_2p5_indep_accept"] = expected_2p5_indep_accept[idx]
    r_values[mass]["expected_97p5_indep_accept"] = expected_97p5_indep_accept[idx]
    # r_values[mass]["observed_indep"] = observed_indep[idx]

# plot model-independent expected limit with 1 sigma and 2 sigma bands IN BRAZILIAN STYLE PLOT
if args.rescale_full:
    expected_50_indep_accept /= lumi_rescale_factor
    expected_16_indep_accept /= lumi_rescale_factor
    expected_84_indep_accept /= lumi_rescale_factor
    expected_2p5_indep_accept /= lumi_rescale_factor
    expected_97p5_indep_accept /= lumi_rescale_factor

fig, ax = plt.subplots(figsize=(fig_width, 10))
plt.plot(masses, expected_50_indep_accept, color="k", label="Median expected", zorder = 5, linestyle='--', alpha = 0.3)
plt.fill_between(masses, expected_16_indep_accept, expected_84_indep_accept, color = '#FFDF7Fff', label="68% expected", zorder = 3)
plt.fill_between(masses, expected_2p5_indep_accept, expected_97p5_indep_accept, color = '#85D1FBff', label="95% expected", zorder = 2)

# add a vertical red band for all mass points where the limit failed
for mass in list_failed_mass_points:
    plt.axvspan(float(mass)-0.05, float(mass)+0.05, color='red', alpha=0.8, zorder=999)

# plot gray band in-between missing regions when plotting multiple regions
if len(args.region) > 1:
    # determine missing regions
    all_bounds = [limit_bounds[region] for region in args.region]
    all_bounds.sort()
    missing_regions = []
    for i in range(len(all_bounds)-1):
        upper_current = all_bounds[i][1]
        lower_next = all_bounds[i+1][0]
        if lower_next > upper_current:
            missing_regions.append( (upper_current, lower_next) )
    
    # plot gray bands for missing regions
    for lower, upper in missing_regions:
        plt.axvspan(lower - 0.08, upper + 0.07, color='lightgray', alpha=1, zorder=5)

# Set axes zorder to bring them above the shaded regions
ax.set_axisbelow(False)
ax.spines['bottom'].set_zorder(999)
ax.spines['left'].set_zorder(999)
ax.spines['top'].set_zorder(999)
ax.spines['right'].set_zorder(999)

hep.cms.label("Preliminary", ax=ax, **label_kwargs)
plt.xlabel("M(X) [GeV]")
plt.ylabel(r"$\sigma(pp \to X) \cdot \text{BR}(X \to ee) \cdot A \cdot \epsilon$ [pb]")
plt.yscale("log")
plt.legend()
if args.rescale_full:
    plt.title(f"(rescaled from {luminosity/1e3:.2f} $fb^{{-1}}$)", fontsize=18, pad=40)


# plt.ylim(10, 7e2)

for ext in ['png', 'pdf']:
    plt.savefig(os.path.join(outfolder, f"mu_limit_results_indep_xsecBRAcceptance{tag}_{region_tag}.{ext}"))
    print(f"Saved plot: {os.path.join(outfolder, f'mu_limit_results_indep_xsecBRAcceptance{tag}_{region_tag}.{ext}')}")

# Finally, for each mass point, print the number of expected events, xsec, efficiency and mu upper limit
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
    print(f"  mu_97p5: {limit['expected_97p5']}\n")
    # print model-independent limits too
    if args.rescale_full:
        print(f"FOLLOWING RESCALED TO FULL LUMI: {total_luminosity} fb^-1 (rescale factor = {lumi_rescale_factor:.2f})")
    print(f"  Model-independent mu_50: {expected_50_indep[idx]:.4f}")
    print(f"  Model-independent mu_16: {expected_16_indep[idx]:.4f}")
    print(f"  Model-independent mu_84: {expected_84_indep[idx]:.4f}")
    print(f"  Model-independent mu_2p5: {expected_2p5_indep[idx]:.4f}")
    print(f"  Model-independent mu_97p5: {expected_97p5_indep[idx]:.4f}")
    print(f"  Model-independent mu_50 no acceptance: {expected_50_indep_noaccept[idx]:.4f}")
    print(f"  Model-independent mu_16 no acceptance: {expected_16_indep_noaccept[idx]:.4f}")
    print(f"  Model-independent mu_84 no acceptance: {expected_84_indep_noaccept[idx]:.4f}")
    print(f"  Model-independent mu_2p5 no acceptance: {expected_2p5_indep_noaccept[idx]:.4f}")
    print(f"  Model-independent mu_97p5 no acceptance: {expected_97p5_indep_noaccept[idx]:.4f}")
    # and, finally, model-independent w/ acceptance
    print(f"  Model-independent mu_50 with acceptance: {expected_50_indep_accept[idx]:.4f}")
    print(f"  Model-independent mu_16 with acceptance: {expected_16_indep_accept[idx]:.4f}")
    print(f"  Model-independent mu_84 with acceptance: {expected_84_indep_accept[idx]:.4f}")
    print(f"  Model-independent mu_2p5 with acceptance: {expected_2p5_indep_accept[idx]:.4f}")
    print(f"  Model-independent mu_97p5 with acceptance: {expected_97p5_indep_accept[idx]:.4f}")

    # # print observed limit
    # print(f"  Observed limit: {float(limit['observed']) * limit['Nexpected'] / (limit['efficiency'] * luminosity):.4f}\n")

# Dump results to pickle
import pickle
with open(os.path.join(outfolder, f"limits_results{tag}_{region_tag}.pkl"), 'wb') as f:
    print(f"Dumping results to {os.path.join(outfolder, f'limits_results{tag}_{region_tag}.pkl')}")
    pickle.dump(r_values, f, protocol=pickle.HIGHEST_PROTOCOL)