import matplotlib.pyplot as plt
import mplhep as hep
import numpy as np
from scipy.optimize import curve_fit
from scipy.interpolate import interp1d
import os
import csv
import unicodedata
from pathlib import Path
import ROOT

"""This script retrieves the signal model efficiencies and cross-sections from the specified input folder,
interpolates them, and plots the results.
It also compares the new reweighted values with the old ones.
It assumes the input folder contains CSV files with the required data.

NB: these efficiencies DO include reweighting.
"""

def crystal_ball(x, mean, sigma, alphaL, nL, alphaR, nR):
    """Crystal Ball function with two tails."""
    A = np.power(nL / abs(alphaL), nL) * np.exp(-0.5 * np.power(alphaL, 2))
    B = nL / abs(alphaL) - abs(alphaL)
    C = np.power(nR / abs(alphaR), nR) * np.exp(-0.5 * np.power(alphaR, 2))
    D = nR / abs(alphaR) - abs(alphaR)
    # Vectorized numpy implementation
    conditions = [
        x < mean - alphaL * sigma,
        x <= mean + alphaR * sigma
    ]
    choices = [
        A * np.power(B - (x - mean) / sigma, -nL),
        np.exp(-0.5 * np.power((x - mean) / sigma, 2)),
    ]
    default = C * np.power((D + (x - mean) / sigma), -nR)
    return np.select(conditions, choices, default=default)


# iterate over samples in the folder (one .csv file per sample)
# input_folder = "/eos/home-n/npalmeri/www/DiElectron/signal_model/fw_output/signal_model_reweighted/ztables/era2023/base_9_GenMatching/csv"
input_folder = "/eos/home-n/npalmeri/www/DiElectron/signal_model/fw_output/nanov15/signal_model_reweighted/ztables/era2023/base_9_GenMatching/csv"

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

def retrieve_producer_efficiencies(input_py):
    # Parse the Python file as text to extract MCDict structure
    import re
    
    with open(input_py, 'r') as f:
        content = f.read()
    
    # Extract the MCDict dictionary from the file content
    # Find the MCDict = { ... } block
    match = re.search(r'MCDict\s*=\s*\{', content)
    if not match:
        raise ValueError("Could not find MCDict in the file")
    
    # Find matching braces to extract the full dictionary
    start_idx = match.end() - 1
    brace_count = 0
    end_idx = start_idx
    for i, char in enumerate(content[start_idx:], start=start_idx):
        if char == '{':
            brace_count += 1
        elif char == '}':
            brace_count -= 1
            if brace_count == 0:
                end_idx = i + 1
                break
    
    dict_str = content[start_idx:end_idx]
    
    # Remove lines containing "color" to avoid importing undefined objects
    dict_lines = dict_str.split('\n')
    filtered_lines = [line for line in dict_lines if '"color"' not in line and "'color'" not in line]
    dict_str = '\n'.join(filtered_lines)
    
    # Safely evaluate the dictionary
    file_dict = eval(dict_str)
    
    base_path = Path("/eos/cms/store/cmst3/group/xee")

    efficiencies = {}
    for sample_name, sample_info in file_dict.items():
        path = sample_info["groups"][0]["samples"][sample_name]["path"]
        path = path.format(name=sample_name, era="2023")
        # retrieve efficiency value from path string
        full_path = base_path / Path(path)
        f = ROOT.TFile.Open(str(full_path))
        # see if it contains "Events" tree
        t = f.Get("Events")
        if not t:
            print(f"Warning: 'Events' tree not found in file {full_path}")
            continue
        nentries = t.GetEntries()
        total_evts = 38062 if sample_name == "HAHM_13p6TeV_M6" else 50000
        efficiencies[sample_name] = nentries / total_evts

    return efficiencies


# outfolder = "/eos/home-n/npalmeri/www/DiElectron/signal_model/fw_output"
# outfolder = "/eos/home-n/npalmeri/www/DiElectron/background_model/fit_tests_reweight_NEW"
# outfolder = "/eos/home-n/npalmeri/www/DiElectron/background_model/fit"
outfolder = "/eos/home-n/npalmeri/www/DiElectron/signal_model/fw_output/nanov15"

# -- Interpolate xsec, selection efficiency
samples = [
    "HAHM_13p6TeV_M1",
    "HAHM_13p6TeV_M3p1",
    "HAHM_13p6TeV_M5",
    "HAHM_13p6TeV_M5p5",
    "HAHM_13p6TeV_M6",
    "HAHM_13p6TeV_M6p5",
    "HAHM_13p6TeV_M8",
    "HAHM_13p6TeV_M10",
]

producer_efficiencies = retrieve_producer_efficiencies("/eos/home-n/npalmeri/www/DiElectron/signal_model/fw_output/nanov15/signal_model_reweighted/zlog/data/MC/Zd_nJet012_pTe5_eta1p2_nanov15.py")
both_efficiencies = retrieve_efficiencies("/eos/home-n/npalmeri/www/DiElectron/signal_model/fw_output/nanov15/signal_model_reweighted/ztables/era2023/base_9_GenMatching/csv")
efficiencies = both_efficiencies["reweight_efficiencies"]
old_efficiencies = both_efficiencies["ID_efficiencies"]
for sample in samples:
    efficiencies[sample] = [eff * producer_efficiencies[sample] for eff in efficiencies[sample]]
    old_efficiencies[sample] = [eff * producer_efficiencies[sample] for eff in old_efficiencies[sample]]

masses = np.array([1, 3.1, 5, 5.5, 6, 6.5, 8, 10])
x = np.linspace(0, 11, 1000) # for plotting; was 1, 7

effs = np.array([efficiencies[sample][0] for sample in samples]) / 100
effs_err = np.array([(efficiencies[sample][1]+efficiencies[sample][2])/2 / 100 for sample in samples]) #take average of lower and upper error for simplicity

effs_old = np.array([old_efficiencies[sample][0] for sample in samples]) / 100
effs_err_old = np.array([(old_efficiencies[sample][1]+old_efficiencies[sample][2])/2 / 100 for sample in samples]) #take average of lower and upper error for simplicity

# # FIXME!!! manually adding upsilon efficiency until new signal samples are processed
# masses_ext = np.append(masses, 9.46)
# effs_ext = np.append(effs, 0.043/100) # from old samples
# effs_err_ext = np.append(effs_err, 0.002 / 100)
# effs_old_ext = np.append(effs_old, 0.088/100)
# effs_err_old_ext = np.append(effs_err_old, 0.002/100)

masses_ext = masses
effs_ext = effs
effs_err_ext = effs_err
effs_old_ext = effs_old
effs_err_old_ext = effs_err_old

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
xsecs = np.array([39.62, 16.00, 11.31, 11.06, 10.81, 10.07, 8.273, 6.458]) # pb
xsecs_err = xsecs * 0.0015 # oom for available points

# TODO: update with new mass points
# xsecs = np.array([39.62, 16.00, 11.31, 11.06, 10.81, 10.07]) # pb
# xsecs_err = xsecs * 0.0015 # oom for available points

xsecs_old = np.array([3.396, 2.679, 1.952, 1.910, 1.865, 1.834]) # pb
xsecs_err_old = np.array([0.01646, 0.0095, 0.003978, 0.003451, 0.001997, 0.001002])

def fit_effs(use_old = False, use_crystalball=False):
    args = {}

    if use_crystalball:
        fit_func = lambda x, mean, sigma, alphaL, nL, alphaR, nR: 0.16 * crystal_ball(x, mean, sigma, alphaL, nL, alphaR, nR)
        args["p0"] = [5.5, 1, 0.3, 1, 1.5, 3]
        args["bounds"] = ([5.5, 0, 0, -10, 0, -10], [8, 5, 10, 10, 10, 10])
    else:
        args["bounds"] = [[0, -1, -1, -1, -1], [10, 20, 10, 10, 10]]
        args["p0"] = [0.1, 10, 0.1, 0.1, 0.5]
        fit_func = lambda x, a, b, c, d, e: np.polyval((b, c, d, e), x) * np.exp( - a * x)

    mass = masses_dict["ext"] if use_crystalball else masses_dict["base"]
    extension_flag = "ext" if use_crystalball else "base"
    old_flag = "old" if use_old else "new"
    y, y_err = effs_dict[extension_flag][old_flag]

    popt_eff, _ = curve_fit(fit_func, mass, y, sigma=y_err, absolute_sigma=True, **args)
    return {"fit_function" : fit_func, "fit_parameters" : popt_eff}

def interp_effs(use_old = False, use_crystalball=False):
    """Linear interpolation for efficiencies."""
    mass = masses_dict["ext"] if use_crystalball else masses_dict["base"]
    extension_flag = "ext" if use_crystalball else "base"
    old_flag = "old" if use_old else "new"
    y, y_err = effs_dict[extension_flag][old_flag]
    
    interp_func = interp1d(mass, y, kind='linear', bounds_error=False, fill_value='extrapolate')
    # Wrap in lambda to match the interface expected by plotting
    fit_func = lambda x: interp_func(x)
    
    return {"fit_function" : fit_func, "fit_parameters" : []}

# Default efficiency function for module usage
def get_efficiency_function(use_old=False):
    """Returns the default (linear interpolation) efficiency function."""
    return interp_effs(use_old=use_old, use_crystalball=False)

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

        if len(fit_params) > 0:  # parametric fit with parameters
            y_fit = fit_func(x, *fit_params)
        else:  # interpolation function with no parameters
            y_fit = fit_func(x)
        ax.plot(x, y_fit * 100, label=f'{label}', linewidth=2, linestyle="--") 

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
        masses_to_use = masses[:6]  # old xsecs only up to 6.5 GeV
        xsecs_to_use = xsecs_old
        xsecs_err_to_use = xsecs_err_old
    else:
        masses_to_use = masses
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

    popt_xsec, _ = curve_fit(fit_func, masses_to_use, xsecs_to_use, p0=p0, sigma=xsecs_err_to_use, absolute_sigma=True)
    return {"fit_function" : fit_func, "fit_parameters" : popt_xsec}

def interp_xsecs(use_old=False):
    """Linear interpolation for cross-sections."""
    if use_old:
        masses_to_use = masses[:6]  # old xsecs only up to 6.5 GeV
        xsecs_to_use = xsecs_old
    else:
        masses_to_use = masses
        xsecs_to_use = xsecs
    
    interp_func = interp1d(masses_to_use, xsecs_to_use, kind='linear', bounds_error=False, fill_value='extrapolate')
    # Wrap in lambda to match the interface
    fit_func = lambda x: interp_func(x)
    
    return {"fit_function" : fit_func, "fit_parameters" : []}

# Default xsec function for module usage
def get_xsec_function(use_old=False):
    """Returns the default (linear interpolation) cross-section function."""
    return interp_xsecs(use_old=use_old)

def plot_xsecs(funcs_to_draw, outname = "xsec_vs_mass", use_old = False):
    # Xsec values
    fig, ax = plt.subplots(figsize=(9, 8))

    if use_old:
        masses_to_use = masses[:6]  # old xsecs only up to 6.5 GeV
        xsecs_to_use = xsecs_old
        xsecs_err_to_use = xsecs_err_old
    else:
        masses_to_use = masses
        xsecs_to_use = xsecs
        xsecs_err_to_use = xsecs_err

    ax.errorbar(
        masses_to_use, xsecs_to_use, yerr=xsecs_err_to_use, fmt='o',
        markersize=8, capsize=7, elinewidth=2, label=r"$\sigma$(pp → $Z_D$) · BR($Z_D$ → ee)"
    )

    for label, fit_info in funcs_to_draw.items():
        fit_func = fit_info["fit_function"]
        fit_params = fit_info["fit_parameters"]
        
        if len(fit_params) > 0:  # parametric fit with parameters
            y = fit_func(x, *fit_params)
        else:  # interpolation function with no parameters
            y = fit_func(x)
        ax.plot(x, y, label=label, linewidth=2, linestyle="--")

    ax.set_xlabel("M($Z_D$) [GeV]")
    ax.set_ylabel("$\sigma$ [pb]")
    ax.set_ylim(0, 5 if use_old else 45)
    ax.grid()

    ax.legend()

    for ext in [".png", ".pdf"]:
        plt.savefig(os.path.join(outfolder, outname + ext))

if __name__ == "__main__":
    print("effs (NEW) = ", effs)
    print("effs (OLD) = ", effs_old)
    print("effs (NEW / OLD) = ", effs/effs_old)

    # post-reweight efficiencies, plot and fit (also plotting old for comparison)
    fit_result = fit_effs(use_crystalball=True)
    fit_result_poly = fit_effs(use_crystalball=False)
    interp_result = interp_effs(use_old=False, use_crystalball=False)
    print("FIT RESULTS dCB: ", fit_result["fit_parameters"])
    print("FIT RESULTS poly: ", fit_result_poly["fit_parameters"])
    plot_effs(use_old=False, use_crystalball=True,
              funcs_to_draw = {"dCB fit" : fit_result,
                              "Polynomial fit" : fit_result_poly,
                              "Linear interpolation" : interp_result},
              outname="efficiency_vs_mass", plot_both = True)

    # updated xsec values, plot and fit
    fit_result_xsec = fit_xsecs()
    interp_result_xsec = interp_xsecs()
    print("XSEC FIT RESULTS: ", fit_result_xsec["fit_parameters"])
    plot_xsecs(funcs_to_draw={"Exponential fit" : fit_result_xsec,
                              "Linear interpolation" : interp_result_xsec},
               outname="xsec_vs_mass")

    # # same for old xsec values
    # fit_result_eff_old = fit_effs(use_old = True, use_crystalball=False)
    # print("EFF OLD FIT RESULTS: ", fit_result_eff_old["fit_parameters"])
    # plot_effs(use_old=True, use_crystalball=False,
    #           funcs_to_draw = {"dCB" : fit_result_eff_old}, outname="efficiency_vs_mass_old")

    # # same for old xsec values
    # fit_result_xsec_old = fit_xsecs(use_old=True)
    # print("XSEC OLD FIT RESULTS: ", fit_result_xsec_old["fit_parameters"])
    # plot_xsecs(fit_func=fit_result_xsec_old["fit_function"], fit_params=fit_result_xsec_old["fit_parameters"], outname="xsec_vs_mass_old", use_old=True)

