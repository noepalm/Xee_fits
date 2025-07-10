import matplotlib.pyplot as plt
import mplhep as hep
import numpy as np
from scipy.optimize import curve_fit
import os
import csv
import unicodedata

# iterate over samples in the folder (one .csv file per sample)
input_folder = "/eos/home-n/npalmeri/www/DiElectron/signal_model/fw_output/signal_model_reweighted/ztables/era2023/base_9_GenMatching/csv"

def clean_string(s):
    # Convert subscript/superscript characters to normal characters
    cleaned = unicodedata.normalize("NFKC", s.strip("%")).replace("−", "-").replace(" ̇", ".").strip() #that minus...
    # split central value, minus error and plus error
    central = float(cleaned.split("-")[0])
    lower_err = float(cleaned.split("-")[1].split("+")[0])
    upper_err = float(cleaned.split("-")[1].split("+")[1])

    return (central, lower_err, upper_err)

def retrieve_efficiencies(input_folder):
    ID_efficiencies = {}
    reweight_efficiencies = {}
    for filename in os.listdir(input_folder):
        if filename.endswith(".csv"):
            with open(os.path.join(input_folder, filename), 'r') as csvfile:
                reader = csv.reader(csvfile, delimiter=",")
                header = next(reader)

                # scan rows until we find the ID one (second entry)
                for row in reader:
                    if row[1] == "ID":
                        # retrieve cumulative selection efficiency at that step
                        ID_efficiencies[filename.replace('.csv', '')] = clean_string(row[5])
                    elif row[1] == "TriggerPSReweight":
                        # retrieve cumulative selection efficiency at that step
                        reweight_efficiencies[filename.replace('.csv', '')] = clean_string(row[5])
    
    return {"ID_efficiencies": ID_efficiencies, "reweight_efficiencies": reweight_efficiencies}

outfolder = "/eos/home-n/npalmeri/www/DiElectron/signal_model/fw_output"

# -- Interpolate xsec, selection efficiency
samples = [
    "HAHM_13p6TeV_M1",
    "HAHM_13p6TeV_M3p1",
    "HAHM_13p6TeV_M5",
    "HAHM_13p6TeV_M5p5",
    "HAHM_13p6TeV_M6",
    "HAHM_13p6TeV_M6p5"
]

both_efficiencies = retrieve_efficiencies("/eos/home-n/npalmeri/www/DiElectron/signal_model/fw_output/signal_model_reweighted/ztables/era2023/base_9_GenMatching/csv")
efficiencies = both_efficiencies["reweight_efficiencies"]
old_efficiencies = both_efficiencies["ID_efficiencies"]

masses = np.array([1, 3.1, 5, 5.5, 6, 6.5])

effs = np.array([efficiencies[sample][0] for sample in samples]) / 100
effs_err = np.array([(efficiencies[sample][1]+efficiencies[sample][2])/2 / 100 for sample in samples]) #take average of lower and upper error for simplicity

effs_old = np.array([old_efficiencies[sample][0] for sample in samples]) / 100
effs_err_old = np.array([(old_efficiencies[sample][1]+old_efficiencies[sample][2])/2 / 100 for sample in samples]) #take average of lower and upper error for simplicity

# effs = np.array([1.562, 14.010, 19.821, 20.552, 18.541, 11.550]) # %
# effs_err = np.array([0.055, 0.155, 0.179, 0.181, 0.2, 0.143])
xsecs = np.array([39.62, 16.00, 11.31, 11.06, 10.81, 10.07]) # pb
xsecs_err = xsecs * 0.0015 # oom for available points
xsecs_old = np.array([3.396, 2.679, 1.952, 1.910, 1.865, 1.834]) # pb
xsecs_err_old = np.array([0.01646, 0.0095, 0.003978, 0.003451, 0.001997, 0.001002])

if __name__ == "__main__":
    print(effs)
    print(effs_old)
    print(effs/effs_old)

    # also plot
    fig, ax = plt.subplots(figsize=(9, 8))
    hep.style.use(hep.style.CMS)

    palette = [
        "#3f90da",
        "#ffa90e",
        "#ff4c4c",
        "#00bfae",
        "#a8a8a8",
    ]
    ax.set_prop_cycle(color=palette)

    ax.errorbar(
        masses, effs_old * 100, yerr=effs_err_old * 100, fmt='o', label='No reweight',
        markersize=8, capsize=7, elinewidth=2
    )
    ax.errorbar(
        masses, effs * 100, yerr=effs_err * 100, fmt='o', label='After trigger reweight',
        markersize=8, capsize=7, elinewidth=2
    )

    ax.set_xlabel("M($Z_D$) [GeV]", fontsize=24)
    ax.set_ylabel("Efficiency [%]", fontsize=24)
    ax.tick_params(axis='both', which='major', labelsize=20, length=10)
    ax.grid()
    ax.legend()
    
    plt.savefig(os.path.join(outfolder,"efficiency_vs_mass.png"))
    plt.savefig(os.path.join(outfolder,"efficiency_vs_mass.pdf"))

    # Xsec values
    fig, ax = plt.subplots(figsize=(9, 8))

    ax.errorbar(
        masses, xsecs, yerr=xsecs_err, fmt='o',
        markersize=8, capsize=7, elinewidth=2
    )

    ax.set_xlabel("M($Z_D$) [GeV]")
    ax.set_ylabel("$\sigma$ [pb]")
    ax.grid()

    plt.savefig(os.path.join(outfolder, "xsec_vs_mass.png"))
    plt.savefig(os.path.join(outfolder, "xsec_vs_mass.pdf"))

    # do the same for old xsec values
    fig, ax = plt.subplots(figsize=(9, 8))
    
    ax.errorbar(
        masses, xsecs_old, yerr=xsecs_err_old, fmt='o', label="Cross-sections",
        markersize=8, capsize=7, elinewidth=2
    )

    # fit xsecs vs masses with polynomial
    popt_xsec, _ = curve_fit(lambda x, a, b, c, d, e : np.polyval((a, b, c, d, e), x), masses, xsecs_old, sigma=xsecs_err_old, absolute_sigma=True)

    # plot data and fit curve
    x2 = np.linspace(np.min(masses), np.max(masses), 1000)
    y2 = np.polyval(popt_xsec, x2)

    ax.plot(x2, y2, label='4th-deg. polynomial fit', linewidth=3)

    ax.set_xlabel("M($Z_D$) [GeV]")
    ax.set_ylabel("$\sigma$ [pb]")
    ax.grid()
    ax.legend()

    plt.savefig(os.path.join(outfolder, "xsec_vs_mass_old.png"))
    plt.savefig(os.path.join(outfolder, "xsec_vs_mass_old.pdf"))


    # do the same for old xsec values
    fig, ax = plt.subplots(figsize=(9, 8))
    
    ax.errorbar(
        masses, effs_old * 100, yerr=effs_err_old * 100, fmt='o', label="Efficiencies",
        markersize=8, capsize=7, elinewidth=2
    )
    
    # fit efficiency
    popt_eff, _ = curve_fit(lambda x, a, b, c, d : np.polyval((a, b, c, d), x), masses, effs_old, sigma=effs_err_old, absolute_sigma=True)
    # plot data and fit curve
    x = np.linspace(np.min(masses), np.max(masses), 1000)
    y = np.polyval(popt_eff, x)

    ax.plot(x, y*100, label='3rd-deg. polynomial fit', linewidth=3)

    ax.set_xlabel("M($Z_D$) [GeV]")
    ax.set_ylabel("Efficiency [%]")
    ax.grid()
    ax.legend()

    plt.savefig(os.path.join(outfolder, "efficiency_vs_mass_old.png"))
    plt.savefig(os.path.join(outfolder, "efficiency_vs_mass_old.pdf"))
    