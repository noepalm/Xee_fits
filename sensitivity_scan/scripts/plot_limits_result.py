import ROOT
import numpy as np
import matplotlib.pyplot as plt
import os
import mplhep as hep
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('-o', '--output_folder', type=str, default='/eos/home-n/npalmeri/www/DiElectron/sensitivity/fitDiagnostics/mu0', help='Output folder for the plots')
parser.add_argument('-i', '--input_cards', type=str, nargs='+', default=['cards'], help='Input cards folder(s) - must match number of regions in order')
parser.add_argument('-c', '--category', type=str, default='etaHigh', help='Category to plot (default: etaHigh)')
parser.add_argument('-t', '--tag', type=str, default="", help='Optional additional tag for output files')
parser.add_argument('-r', '--region', type=str, nargs='+', default=['region1'], choices=["region0", "region1", "region2"], help='Region(s) to plot (can specify multiple)')
args = parser.parse_args()

# Validate that input_cards matches the number of regions
if len(args.input_cards) != len(args.region):
    raise ValueError(f"Number of input_cards ({len(args.input_cards)}) must match number of regions ({len(args.region)})")

limit_bounds = {
    "region0" : (0, 2.2),
    "region1" : (2.2, 4.0),
    "region2" : (4.0, 10.8),
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
print(f"  Tag: {args.tag}")
print(f"  Region(s) and input cards:")
for region, cards in region_to_cards.items():
    print(f"    {region}: {limit_bounds[region][0]} - {limit_bounds[region][1]} GeV → {cards}")


outfolder = args.output_folder
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

# iterate over subfolders -- only consider the ones of the type M{X}.{Y}
for folder in os.listdir(outfolder):
    if not folder.startswith("M") or not folder[1:].replace(".", "").isdigit():
        continue
    
    # Check if mass falls within any of the specified regions
    mass_value = float(folder[1:])
    if not is_mass_in_regions(mass_value, args.region):
        continue
    print("  Processing mass value:", mass_value)

    folder_path = os.path.join(outfolder, folder)
    
    # check if it's a directory
    if not os.path.isdir(folder_path):
        continue

    # iterate over files in the subfolder
    for file in os.listdir(folder_path):
        # find fitDiagnostics.log
        if file == f"fitAsymptotic_{args.category}{tag}.log":
            print("    Found log file:", file)
            with open(os.path.join(folder_path, file), 'r') as f:
                lines = f.readlines()
                # find the line starting with "Best fit r"
                for idx, line in enumerate(lines):
                    if " -- AsymptoticLimits ( CLs ) --" in line:
                        break
                limit = {}
                limit["observed"] = lines[idx+1].split("r < ")[1].strip()

                # check if "Expected" lines are found at all (may not be computed)
                if "Expected" in lines[idx+2]:
                    limit["expected_2p5"] = lines[idx+2].split("r < ")[1].strip()
                    limit["expected_16"] = lines[idx+3].split("r < ")[1].strip()
                    limit["expected_50"] = lines[idx+4].split("r < ")[1].strip()
                    limit["expected_84"] = lines[idx+5].split("r < ")[1].strip()
                    limit["expected_97p5"] = lines[idx+6].split("r < ")[1].strip()
                else:
                    print("WARNING: no expected limits produced for mass", folder[1:], "; will use median and sigma.")
                    list_failed_mass_points.append(folder[1:])
                    continue
                    # # find line "Median for expected limits = "
                    # for line in lines:
                    #     if "Median for expected limits = " in line:
                    #         median = float(line.split("Median for expected limits = ")[1].split(",")[0])
                    #         sigma = float(line.split("Sigma for expected limits = ")[1].strip())
                    #         limit["expected_2p5"] = median - 2 * sigma
                    #         limit["expected_16"] = median - sigma
                    #         limit["expected_50"] = median
                    #         limit["expected_84"] = median + sigma
                    #         limit["expected_97p5"] = median + 2 * sigma
                    #         break

                # retrieve mass value as float
                mass = folder[1:]
                
                r_values[mass] = limit

# plot central expected limit with 1 sigma and 2 sigma bands IN BRAZILIAN STYLE PLOT
fig, ax = plt.subplots(figsize=(10, 10))
masses = [float(mass) for mass in sorted(r_values.keys(), key=float)]
observed = [float(r_values[mass]["observed"]) for mass in sorted(r_values.keys(), key=float)]
expected_50 = np.array([float(r_values[mass]["expected_50"]) for mass in sorted(r_values.keys(), key=float)])
expected_16 = np.array([float(r_values[mass]["expected_16"]) for mass in sorted(r_values.keys(), key=float)])
expected_84 = np.array([float(r_values[mass]["expected_84"]) for mass in sorted(r_values.keys(), key=float)])
expected_2p5 = np.array([float(r_values[mass]["expected_2p5"]) for mass in sorted(r_values.keys(), key=float)])
expected_97p5 = np.array([float(r_values[mass]["expected_97p5"]) for mass in sorted(r_values.keys(), key=float)])

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
        plt.axvspan(lower, upper, color='gray', alpha=0.8, zorder=999)

hep.cms.label("Preliminary", loc=0, ax=ax, com = 13.6)
plt.xlabel("M(Zd) [GeV]")
plt.ylabel(r"$\mu$")
plt.yscale("log")
plt.legend()

print("DEBUG: limits for category", args.category)
print("Masses:", masses)
print("Observed:", observed)
print("Expected 50%:", expected_50)
print("Expected 16%:", expected_16)
print("Expected 84%:", expected_84)
print("Expected 2.5%:", expected_2p5)
print("Expected 97.5%:", expected_97p5)

for ext in ['png', 'pdf']:
    plt.savefig(os.path.join(outfolder, f"mu_limit_results{tag}_{region_tag}.{ext}"))
    print(f"Saved plot: {os.path.join(outfolder, f'mu_limit_results{tag}_{region_tag}.{ext}')}")

# Now convert these to model-independent limits

# 1) retrieve Nexpected, xsec, efficiency for each mass point from input workspace
# For each mass point, determine which region it belongs to and use the corresponding input file

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
    input_file_path = f"{input_cards_folder}/ee/common/Xee_ee.input.root"
    f = ROOT.TFile.Open(input_file_path)
    w = f.Get("w")
    
    category_label = "" if (args.category == "inclusive" or "combination" in args.category.lower()) else f"_cat_{category_label_map[args.category]}"
    eff = w.var(f"Zd_M{mass:.1f}_efficiency").getValV() * w.var(f"Zd{category_label}_M{mass:.1f}_fraction").getValV() # efficiency should take into account category efficiency as well
    xsec = w.var(f"Zd_M{mass:.1f}_xsec").getValV()
    # n_expected = w.var(f"Zd_M{mass:.1f}_expected").getValV()

    # get n_expected from datacard root file (might be manipulated during workspace creation)
    datacard_file_path = f"{input_cards_folder}/ee/{mass:.1f}/Xee_ee_{category_map[args.category]}_2023.root"
    f_datacard = ROOT.TFile.Open(datacard_file_path)
    w_datacard = f_datacard.Get("w")
    # NB: for category combination, given perfect orthogonality, the expected number is the same as inclusive
    n_expected = w_datacard.obj(f"n_exp_binXee_ee_{category_map[args.category]}_2023_proc_Zd").getValV()

    r_values[f"{mass:.1f}"]["efficiency"] = eff
    r_values[f"{mass:.1f}"]["xsec"] = xsec
    r_values[f"{mass:.1f}"]["Nexpected"] = n_expected
    
    f.Close()
    f_datacard.Close()

# Get luminosity from the first region's input file
first_cards_folder = args.input_cards[0]
f_lumi = ROOT.TFile.Open(f"{first_cards_folder}/ee/common/Xee_ee.input.root")
w_lumi = f_lumi.Get("w")

luminosity = 58.9
if w_lumi.var("luminosity"):
    luminosity = w_lumi.var("luminosity").getValV()
f_lumi.Close()

# 2) compute model-independent limits
expected_50_indep = np.array([float(r_values[mass]["expected_50"]) * r_values[mass]["Nexpected"] / (r_values[mass]["efficiency"] * luminosity) for mass in sorted(r_values.keys(), key=float)])
expected_16_indep = np.array([float(r_values[mass]["expected_16"]) * r_values[mass]["Nexpected"] / (r_values[mass]["efficiency"] * luminosity) for mass in sorted(r_values.keys(), key=float)])
expected_84_indep = np.array([float(r_values[mass]["expected_84"]) * r_values[mass]["Nexpected"] / (r_values[mass]["efficiency"] * luminosity) for mass in sorted(r_values.keys(), key=float)])
expected_2p5_indep = np.array([float(r_values[mass]["expected_2p5"]) * r_values[mass]["Nexpected"] / (r_values[mass]["efficiency"] * luminosity) for mass in sorted(r_values.keys(), key=float)])
expected_97p5_indep = np.array([float(r_values[mass]["expected_97p5"]) * r_values[mass]["Nexpected"] / (r_values[mass]["efficiency"] * luminosity) for mass in sorted(r_values.keys(), key=float)])
# observed_indep = np.array([float(r_values[mass]["observed"]) * r_values[mass]["Nexpected"] / (r_values[mass]["efficiency"] * luminosity) for mass in sorted(r_values.keys(), key=float)])

# add arrays to r_values dictionary
for idx, mass in enumerate(sorted(r_values.keys(), key=float)):
    r_values[mass]["expected_50_indep"] = expected_50_indep[idx]
    r_values[mass]["expected_16_indep"] = expected_16_indep[idx]
    r_values[mass]["expected_84_indep"] = expected_84_indep[idx]
    r_values[mass]["expected_2p5_indep"] = expected_2p5_indep[idx]
    r_values[mass]["expected_97p5_indep"] = expected_97p5_indep[idx]
    # r_values[mass]["observed_indep"] = observed_indep[idx]

# plot model-independent expected limit with 1 sigma and 2 sigma bands IN BRAZILIAN STYLE PLOT
fig, ax = plt.subplots(figsize=(10, 10))
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
        plt.axvspan(lower, upper, color='gray', alpha=0.8, zorder=999)

hep.cms.label("Preliminary", loc=0, ax=ax, com = 13.6)
plt.xlabel("M(X) [GeV]")
plt.ylabel(r"$\sigma(pp \to X) \cdot \text{BR}(X \to ee)$ [pb]")
plt.yscale("log")
plt.legend()


for ext in ['png', 'pdf']:
    plt.savefig(os.path.join(outfolder, f"mu_limit_results_indep_xsecBR{tag}_{region_tag}.{ext}"))
    print(f"Saved plot: {os.path.join(outfolder, f'mu_limit_results_indep_xsecBR{tag}_{region_tag}.{ext}')}")

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
fig, ax = plt.subplots(figsize=(10, 10))
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
        plt.axvspan(lower, upper, color='gray', alpha=0.8, zorder=999)

hep.cms.label("Preliminary", loc=0, ax=ax, com = 13.6)
plt.xlabel("M(X) [GeV]")
plt.ylabel(r"$\sigma(pp \to X) \cdot \text{BR}(X \to ee) \cdot A $ [pb]")
plt.yscale("log")
plt.legend()

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
    print(f"  efficiency: {limit['efficiency'] * 100:.2f} %")
    print(f"  mu_50: {limit['expected_50']}")
    print(f"  mu_16: {limit['expected_16']}")
    print(f"  mu_84: {limit['expected_84']}")
    print(f"  mu_2p5: {limit['expected_2p5']}")
    print(f"  mu_97p5: {limit['expected_97p5']}\n")
    # print model-independent limits too
    print(f"  Model-independent mu_50: {expected_50_indep[idx]:.4f}")
    print(f"  Model-independent mu_16: {expected_16_indep[idx]:.4f}")
    print(f"  Model-independent mu_84: {expected_84_indep[idx]:.4f}")
    print(f"  Model-independent mu_2p5: {expected_2p5_indep[idx]:.4f}")
    print(f"  Model-independent mu_97p5: {expected_97p5_indep[idx]:.4f}")
    # print observed limit
    print(f"  Observed limit: {float(limit['observed']) * limit['Nexpected'] / (limit['efficiency'] * luminosity):.4f}\n")

# Dump results to pickle
import pickle
with open(os.path.join(outfolder, f"limits_results{tag}_{region_tag}.pkl"), 'wb') as f:
    print(f"Dumping results to {os.path.join(outfolder, f'limits_results{tag}_{region_tag}.pkl')}")
    pickle.dump(r_values, f, protocol=pickle.HIGHEST_PROTOCOL)