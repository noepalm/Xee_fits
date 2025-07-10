import numpy as np
import matplotlib.pyplot as plt
import mplhep as hep
import os
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('-m', '--mu', type=float, default=0, help='Value of mu to plot')
parser.add_argument('-o', '--output_folder', type=str, default='plots', help='Output folder for the plots')
args = parser.parse_args()
mu = args.mu
outfolder = args.output_folder

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
        if "fitDiagnostics" in file and "log" in file:
            with open(os.path.join(folder_path, file), 'r') as f:
                lines = f.readlines()
                # find the line starting with "Best fit r"
                for line in lines:
                    if "Best fit r" in line:
                        # format is: Best fit r: 0.00867265  -0.00176151/+0.00176533  (68% CL)
                        parts = line.split("Best fit r: ")[1].split()
                        r_value = float(parts[0].strip())
                        r_min = float(parts[1].split("/")[0].strip().strip("-"))
                        r_plus = float(parts[1].split("/")[1].split()[0].strip())

                        r = {
                            "r_value": r_value,
                            "r_min": r_min,
                            "r_plus": r_plus
                        }

                        # retrieve mass value as float
                        mass = folder[1:]
                        
                        r_values[mass] = r


# plot r +- r_min/r_plus for each mass value
r_central = [r_values[mass]["r_value"] for mass in sorted(r_values.keys(), key=float)]
r_min = [r_values[mass]["r_min"] for mass in sorted(r_values.keys(), key=float)]
r_plus = [r_values[mass]["r_plus"] for mass in sorted(r_values.keys(), key=float)]
masses = [float(mass) for mass in sorted(r_values.keys(), key=float)]

hep.style.use(hep.style.CMS)
palette = [
    "#3f90da",
    "#ffa90e",
    "#ff4c4c",
    "#00bfae",
    "#a8a8a8",
]
plt.rcParams['axes.prop_cycle'] = plt.cycler(color=palette)

fig, ax = plt.subplots(figsize=(12, 8))

ax.errorbar(masses, r_central, yerr=[r_min, r_plus], fmt='o', capsize=5)
ax.set_xlabel("Mass [GeV]", fontsize=20)
ax.set_ylabel(r"$\mu$", fontsize = 20)
ax.set_title("Best fit $\mu$ values with uncertainties (68% CL)")
ax.tick_params(axis='both', which='major', labelsize=20, length=8)
ax.grid()
# ax.set_yscale("log")
# ax.set_ylim(-0.1, 5)

suffix = "_injectedSignal" if mu > 0 else ""

plt.savefig(os.path.join(outfolder, f"mu_fit{suffix}_results.png"))
plt.savefig(os.path.join(outfolder, f"mu_fit{suffix}_results.pdf"))

