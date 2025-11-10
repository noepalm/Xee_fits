import matplotlib.pyplot as plt
import mplhep as hep
import numpy as np
from scipy.optimize import curve_fit
import os
import csv
import unicodedata

"""This script retrieves the signal model efficiencies and cross-sections from the specified input folder,
interpolates them, and plots the results.
It also compares the new reweighted values with the old ones.
It assumes the input folder contains CSV files with the required data.

NB: these efficiencies DO include reweighting.
"""

def crystal_ball(x, mean, sigma, alphaL, nL, alphaR, nR):
    """Crystal Ball function with two tails."""
    A = (nL / abs(alphaL))**nL * np.exp(-0.5 * alphaL**2)
    B = nL / abs(alphaL) - abs(alphaL)
    C = (nR / abs(alphaR))**nR * np.exp(-0.5 * alphaR**2)
    D = nR / abs(alphaR) - abs(alphaR)
    # Vectorized numpy implementation
    conditions = [
        x < mean - alphaL * sigma,
        x <= mean + alphaR * sigma
    ]
    choices = [
        A * (B - (x - mean) / sigma)**(-nL),
        np.exp(-0.5 * ((x - mean) / sigma)**2)
    ]
    default = C * (D + (x - mean) / sigma)**(-nR)
    return np.select(conditions, choices, default=default)


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
    reweight_relative_efficiencies = {}
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
                        reweight_relative_efficiencies[filename.replace('.csv', '')] = clean_string(row[4])
    
    return {"ID_efficiencies": ID_efficiencies, "reweight_efficiencies": reweight_efficiencies, "reweight_relative_efficiencies": reweight_relative_efficiencies}

# outfolder = "/eos/home-n/npalmeri/www/DiElectron/signal_model/fw_output"
# outfolder = "/eos/home-n/npalmeri/www/DiElectron/background_model/fit_tests_reweight_NEW"
outfolder = "/eos/home-n/npalmeri/www/DiElectron/background_model/fit"

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
x = np.linspace(0, 11, 1000) # for plotting; was 1, 7

effs = np.array([efficiencies[sample][0] for sample in samples]) / 100
effs_err = np.array([(efficiencies[sample][1]+efficiencies[sample][2])/2 / 100 for sample in samples]) #take average of lower and upper error for simplicity

effs_old = np.array([old_efficiencies[sample][0] for sample in samples]) / 100
effs_err_old = np.array([(old_efficiencies[sample][1]+old_efficiencies[sample][2])/2 / 100 for sample in samples]) #take average of lower and upper error for simplicity

# FIXME!!! manually adding upsilon efficiency until new signal samples are processed
masses_ext = np.append(masses, 9.46)
effs_ext = np.append(effs, 0.043/100) # from old samples
effs_err_ext = np.append(effs_err, 0.002 / 100)
effs_old_ext = np.append(effs_old, 0.088/100)
effs_err_old_ext = np.append(effs_err_old, 0.002/100)

masses_dict = {
    "ext" : masses_ext,
    "base" : masses
}
effs_dict = {
    "ext" : {
        "new" : (effs_ext, effs_err_ext),
        "old" : (effs_old_ext, effs_err_old_ext)
    },
    "base" : {
        "new" : (effs, effs_err),
        "old" : (effs_old, effs_err_old)
    }
}

# effs = np.array([1.562, 14.010, 19.821, 20.552, 18.541, 11.550]) # %
# effs_err = np.array([0.055, 0.155, 0.179, 0.181, 0.2, 0.143])
xsecs = np.array([39.62, 16.00, 11.31, 11.06, 10.81, 10.07]) # pb
xsecs_err = xsecs * 0.0015 # oom for available points

# TODO: update with new mass points
# xsecs = np.array([39.62, 16.00, 11.31, 11.06, 10.81, 10.07]) # pb
# xsecs_err = xsecs * 0.0015 # oom for available points

xsecs_old = np.array([3.396, 2.679, 1.952, 1.910, 1.865, 1.834]) # pb
xsecs_err_old = np.array([0.01646, 0.0095, 0.003978, 0.003451, 0.001997, 0.001002])

def fit_effs(use_old = False, use_crystalball=False):
    args = {}

    if use_crystalball:
        fit_func = lambda x, mean, sigma, alphaL, nL, alphaR, nR : 0.16 * crystal_ball(x, mean, sigma, alphaL, nL, alphaR, nR)
        args["p0"] = [5.5, 1, 0.3, 1, 1.5, 3]
        args["bounds"] = ([5.5, 0, 0, -10, 0, -10], [8, 5, 10, 10, 10, 10])
    else:
        fit_func = lambda x, a, b, c, d : np.polyval((a, b, c, d), x)

    mass = masses_dict["ext"] if use_crystalball else masses_dict["base"]
    extension_flag = "ext" if use_crystalball else "base"
    old_flag = "old" if use_old else "new"
    y, y_err = effs_dict[extension_flag][old_flag]

    popt_eff, _ = curve_fit(fit_func, mass, y, sigma=y_err, absolute_sigma=True, **args)
    return {"fit_function" : fit_func, "fit_parameters" : popt_eff}

def plot_effs(funcs_to_draw, outname, use_old = False, use_crystalball=False, plot_both = False):
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

    mass = masses_dict["ext"] if use_crystalball else masses_dict["base"]
    extension_flag = "ext" if use_crystalball else "base"
    old_flag = "old" if use_old else "new"
    y, y_err = effs_dict[extension_flag][old_flag]

    if plot_both:
        y_old, y_err_old = effs_dict[extension_flag]["old"]
        ax.errorbar(
            mass, y_old * 100, yerr=y_err_old * 100, fmt='o', label='No reweight',
            markersize=8, capsize=7, elinewidth=2
        )

    ax.errorbar(
        mass, y * 100, yerr=y_err * 100, fmt='o', label='After trigger reweight',
        markersize=8, capsize=7, elinewidth=2
    )

    for label, fit_info in funcs_to_draw.items():
        fit_func = fit_info["fit_function"]
        fit_params = fit_info["fit_parameters"]

        y_fit = fit_func(x, *fit_params)
        ax.plot(x, y_fit * 100, label=f'{label} fit', linewidth=2, linestyle="--") 

    ax.set_xlabel("M($Z_D$) [GeV]", fontsize=24)
    ax.set_ylabel("Efficiency [%]", fontsize=24)
    ax.set_ylim(0, 25)
    ax.tick_params(axis='both', which='major', labelsize=20, length=10)
    ax.grid()
    ax.legend(fontsize=15)
    # add cms label
    hep.cms.label(ax=ax, data=False, year=2023, com=13.6)
    
    for ext in [".png", ".pdf"]:
        plt.savefig(os.path.join(outfolder,outname + ext))    

def fit_xsecs(use_old = False):
    if use_old:
        xsecs_to_use = xsecs_old
        xsecs_err_to_use = xsecs_err_old
    else:
        xsecs_to_use = xsecs
        xsecs_err_to_use = xsecs_err

    if use_old:
        fit_func = lambda x, a, b, c, d, e : np.polyval((a, b, c, d, e), x)
        p0 = None
    else:
        # fit_func = lambda x, a, b : a * x + b * x**2
        # p0 = None
        # fit_func = lambda x, a, b, c, d, e : np.polyval((a, b, c, d, e), x)
        # p0 = None
        fit_func = lambda x, a, b : b * np.exp(-x / a)
        p0 = [3, 60]

    popt_xsec, _ = curve_fit(fit_func, masses, xsecs_to_use, p0=p0, sigma=xsecs_err_to_use, absolute_sigma=True)
    return {"fit_function" : fit_func, "fit_parameters" : popt_xsec}

def plot_xsecs(fit_func, fit_params, outname = "xsec_vs_mass", use_old = False):
    # Xsec values
    fig, ax = plt.subplots(figsize=(9, 8))

    if use_old:
        xsecs_to_use = xsecs_old
        xsecs_err_to_use = xsecs_err_old
    else:
        xsecs_to_use = xsecs
        xsecs_err_to_use = xsecs_err

    ax.errorbar(
        masses, xsecs_to_use, yerr=xsecs_err_to_use, fmt='o',
        markersize=8, capsize=7, elinewidth=2, label=r"$\sigma$(pp → $Z_D$) · BR($Z_D$ → ee)"
    )

    y = fit_func(x, *fit_params)
    ax.plot(x, y, label='Exponential fit', linewidth=2, linestyle="--")

    ax.set_xlabel("M($Z_D$) [GeV]")
    ax.set_ylabel("$\sigma$ [pb]")
    ax.set_ylim(0, 5 if use_old else 45)
    ax.grid()

    ax.legend()

    for ext in [".png", ".pdf"]:
        plt.savefig(os.path.join(outfolder, outname + ext))

if __name__ == "__main__":
    print(effs)
    print(effs_old)
    print(effs/effs_old)

    # post-reweight efficiencies, plot and fit (also plotting old for comparison)
    fit_result = fit_effs(use_crystalball=True)
    fit_result_poly = fit_effs(use_crystalball=False)
    print("FIT RESULTS: ", fit_result["fit_parameters"])
    plot_effs(use_old=False, use_crystalball=True,
              funcs_to_draw = {"dCB" : fit_result,
                              "Polynomial" : fit_result_poly},
              outname="efficiency_vs_mass", plot_both = True)

    # updated xsec values, plot and fit
    fit_result_xsec = fit_xsecs()
    print("XSEC FIT RESULTS: ", fit_result_xsec["fit_parameters"])
    plot_xsecs(fit_func=fit_result_xsec["fit_function"], fit_params=fit_result_xsec["fit_parameters"], outname="xsec_vs_mass")

    # same for old xsec values
    fit_result_eff_old = fit_effs(use_old = True, use_crystalball=False)
    print("EFF OLD FIT RESULTS: ", fit_result_eff_old["fit_parameters"])
    plot_effs(use_old=True, use_crystalball=False,
              funcs_to_draw = {"dCB" : fit_result_eff_old}, outname="efficiency_vs_mass_old")

    # same for old xsec values
    fit_result_xsec_old = fit_xsecs(use_old=True)
    print("XSEC OLD FIT RESULTS: ", fit_result_xsec_old["fit_parameters"])
    plot_xsecs(fit_func=fit_result_xsec_old["fit_function"], fit_params=fit_result_xsec_old["fit_parameters"], outname="xsec_vs_mass_old", use_old=True)

