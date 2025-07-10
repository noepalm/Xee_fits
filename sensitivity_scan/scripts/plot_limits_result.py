import ROOT
import numpy as np
import matplotlib.pyplot as plt
import os
import mplhep as hep
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('-o', '--output_folder', type=str, default='/eos/home-n/npalmeri/www/DiElectron/sensitivity/fitDiagnostics/mu0', help='Output folder for the plots')
args = parser.parse_args()
outfolder = args.output_folder

plt.style.use(hep.style.CMS)

r_values = {}

# iterate over subfolders -- only consider the ones of the type M{X}.{Y}
for folder in os.listdir(outfolder):
    if not folder.startswith("M") or not folder[1:].replace(".", "").isdigit():
        continue
    
    folder_path = os.path.join(outfolder, folder)
    
    # check if it's a directory
    if not os.path.isdir(folder_path):
        continue

    # iterate over files in the subfolder
    for file in os.listdir(folder_path):
        # find fitDiagnostics.log
        if file == "fitAsymptotic.log":
            with open(os.path.join(folder_path, file), 'r') as f:
                lines = f.readlines()
                # find the line starting with "Best fit r"
                for idx, line in enumerate(lines):
                    if " -- AsymptoticLimits ( CLs ) --" in line:
                        break
                limit = {}
                limit["observed"] = lines[idx+1].split("r < ")[1].strip()

                # check if "Expected" lines are found at all (may not be computed)
                if "Expected" not in lines[idx+2]:
                    print("WARNING: no expected limits produced for mass", folder[1:])
                    continue
                limit["expected_2p5"] = lines[idx+2].split("r < ")[1].strip()
                limit["expected_16"] = lines[idx+3].split("r < ")[1].strip()
                limit["expected_50"] = lines[idx+4].split("r < ")[1].strip()
                limit["expected_84"] = lines[idx+5].split("r < ")[1].strip()
                limit["expected_97p5"] = lines[idx+6].split("r < ")[1].strip()

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

hep.cms.label("Preliminary", loc=0, ax=ax, com = 13.6)
plt.xlabel("M(Zd) [GeV]")
plt.ylabel(r"$\mu$")
plt.yscale("log")
plt.legend()

plt.savefig(os.path.join(outfolder, "mu_limit_results.png"))
plt.savefig(os.path.join(outfolder, "mu_limit_results.pdf"))
print("Saved mu_limit_results.png to:", outfolder)


# Now convert these to model-independent limits

# 1) retrieve Nexpected, xsec, efficiency for each mass point from input workspace
f = ROOT.TFile.Open("cards/ee/common/Xee_ee.input.root")
w = f.Get("w")

for mass in masses:
    eff = w.var(f"Zd_M{mass:.1f}_efficiency").getValV()
    xsec = w.var(f"Zd_M{mass:.1f}_xsec").getValV()
    n_expected = w.var(f"Zd_M{mass:.1f}_expected").getValV()

    r_values[f"{mass:.1f}"]["efficiency"] = eff/100
    r_values[f"{mass:.1f}"]["xsec"] = xsec
    r_values[f"{mass:.1f}"]["Nexpected"] = n_expected

luminosity = 7.98e3  # in pb-1, as used in the text2workspace step

# 2) compute model-independent limits
expected_50_indep = np.array([float(r_values[mass]["expected_50"]) * r_values[mass]["Nexpected"] / (r_values[mass]["efficiency"] * luminosity) for mass in sorted(r_values.keys(), key=float)])
expected_16_indep = np.array([float(r_values[mass]["expected_16"]) * r_values[mass]["Nexpected"] / (r_values[mass]["efficiency"] * luminosity) for mass in sorted(r_values.keys(), key=float)])
expected_84_indep = np.array([float(r_values[mass]["expected_84"]) * r_values[mass]["Nexpected"] / (r_values[mass]["efficiency"] * luminosity) for mass in sorted(r_values.keys(), key=float)])
expected_2p5_indep = np.array([float(r_values[mass]["expected_2p5"]) * r_values[mass]["Nexpected"] / (r_values[mass]["efficiency"] * luminosity) for mass in sorted(r_values.keys(), key=float)])
expected_97p5_indep = np.array([float(r_values[mass]["expected_97p5"]) * r_values[mass]["Nexpected"] / (r_values[mass]["efficiency"] * luminosity) for mass in sorted(r_values.keys(), key=float)])
# observed_indep = np.array([float(r_values[mass]["observed"]) * r_values[mass]["Nexpected"] / (r_values[mass]["efficiency"] * luminosity) for mass in sorted(r_values.keys(), key=float)])

# plot model-independent expected limit with 1 sigma and 2 sigma bands IN BRAZILIAN STYLE PLOT
fig, ax = plt.subplots(figsize=(10, 10))
plt.plot(masses, expected_50_indep, color="k", label="Median expected", zorder = 5, linestyle='--', alpha = 0.3)
plt.fill_between(masses, expected_16_indep, expected_84_indep, color = '#FFDF7Fff', label="68% expected", zorder = 3)
plt.fill_between(masses, expected_2p5_indep, expected_97p5_indep, color = '#85D1FBff', label="95% expected", zorder = 2)
hep.cms.label("Preliminary", loc=0, ax=ax, com = 13.6)
plt.xlabel("M(X) [GeV]")
plt.ylabel(r"$\sigma(pp \to X) \cdot \text{BR}(X \to ee)$ [pb]")
plt.yscale("log")
plt.legend()

plt.savefig(os.path.join(outfolder, "mu_limit_results_indep_xsecBR.png"))
plt.savefig(os.path.join(outfolder, "mu_limit_results_indep_xsecBR.pdf"))

expected_50_indep_accept = np.array([float(r_values[mass]["expected_50"]) * r_values[mass]["Nexpected"] / (luminosity) for mass in sorted(r_values.keys(), key=float)])
expected_16_indep_accept = np.array([float(r_values[mass]["expected_16"]) * r_values[mass]["Nexpected"] / (luminosity) for mass in sorted(r_values.keys(), key=float)])
expected_84_indep_accept = np.array([float(r_values[mass]["expected_84"]) * r_values[mass]["Nexpected"] / (luminosity) for mass in sorted(r_values.keys(), key=float)])
expected_2p5_indep_accept = np.array([float(r_values[mass]["expected_2p5"]) * r_values[mass]["Nexpected"] / (luminosity) for mass in sorted(r_values.keys(), key=float)])
expected_97p5_indep_accept = np.array([float(r_values[mass]["expected_97p5"]) * r_values[mass]["Nexpected"] / (luminosity) for mass in sorted(r_values.keys(), key=float)])
# observed_indep = np.array([float(r_values[mass]["observed"]) * r_values[mass]["Nexpected"] / (r_values[mass]["efficiency"] * luminosity) for mass in sorted(r_values.keys(), key=float)])

# plot model-independent expected limit with 1 sigma and 2 sigma bands IN BRAZILIAN STYLE PLOT
fig, ax = plt.subplots(figsize=(10, 10))
plt.plot(masses, expected_50_indep_accept, color="k", label="Median expected", zorder = 5, linestyle='--', alpha = 0.3)
plt.fill_between(masses, expected_16_indep_accept, expected_84_indep_accept, color = '#FFDF7Fff', label="68% expected", zorder = 3)
plt.fill_between(masses, expected_2p5_indep_accept, expected_97p5_indep_accept, color = '#85D1FBff', label="95% expected", zorder = 2)
hep.cms.label("Preliminary", loc=0, ax=ax, com = 13.6)
plt.xlabel("M(X) [GeV]")
plt.ylabel(r"$\sigma(pp \to X) \cdot \text{BR}(X \to ee) \cdot A $ [pb]")
plt.yscale("log")
plt.legend()

plt.savefig(os.path.join(outfolder, "mu_limit_results_indep_xsecBRAcceptance.png"))
plt.savefig(os.path.join(outfolder, "mu_limit_results_indep_xsecBRAcceptance.pdf"))


# Finally, for each mass point, print the number of expected events, xsec, efficiency and mu upper limit
print("\nModel-independent limits:")
for idx, mass in enumerate(sorted(r_values.keys(), key=float)):
    limit = r_values[mass]
    print(f"Mass: {mass} GeV")
    print(f"  N_expected: {limit['Nexpected']:.2f}")
    print(f"  xsec: {limit['xsec']:.2f} pb")
    print(f"  efficiency: {limit['efficiency']:.2f} %")
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
