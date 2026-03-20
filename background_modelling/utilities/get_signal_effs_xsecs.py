import matplotlib.pyplot as plt
import mplhep as hep
import numpy as np
from scipy.optimize import curve_fit
from scipy.interpolate import interp1d, PchipInterpolator
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

def novosibirsk(x, peak, width, tail):
    """Novosibirsk function - asymmetric peak shape.
    peak: peak position
    width: width parameter
    tail: tail parameter (asymmetry)
    """
    # Avoid division by zero
    tail = np.where(np.abs(tail) < 1e-7, 1e-7, tail)
    
    arg = (x - peak) / width
    log_arg = 1 - arg * tail
    
    # Avoid log of negative numbers
    log_arg = np.where(log_arg > 0, log_arg, 1e-10)
    
    y = -0.5 * (np.log(log_arg) / tail) ** 2 - 0.5 * tail ** 2
    
    return np.exp(y)


# Helper function to construct input folders based on era and folder_tag
def get_input_folders(era="2023", folder_tag="260226"):
    """Construct input folder paths based on era and folder_tag.
    
    Args:
        era: Data-taking era (e.g., "2023", "2022", "2022EE", "2023BPix")
        folder_tag: Folder tag for organizing runs (default: "260226" for reference)
    
    Returns:
        Tuple of (input_folder, input_folder_snap) paths
    """
    # base_path = "/eos/home-n/npalmeri/www/DiElectron/PS_reweighting/nanov15/per_subera/signal_model_withScaleSyst_IDSF_triggerSF"
    # input_folder = f"{base_path}/ztables/era{era}/base_11_full/csv"
    # input_folder_snap = f"{base_path}/zsnap/era{era}/base_11_full"
    base_path = "/eos/home-n/npalmeri/www/DiElectron/PS_reweighting/nanov15/per_subera/260312/signal_model_withScaleSyst_IDSF_triggerSF_isoCut"
    input_folder = f"{base_path}/ztables/era{era}/base_12_full/csv"
    input_folder_snap = f"{base_path}/zsnap/era{era}/base_12_full"
    return input_folder, input_folder_snap

# Default folders (for backward compatibility and standalone usage)
input_folder, input_folder_snap = get_input_folders(era="2023", folder_tag="260226")

def clean_string(s):
    # Convert subscript/superscript characters to normal characters
    cleaned = unicodedata.normalize("NFKC", s.strip("%")).replace("−", "-").replace(" ̇", ".").strip() #that minus...
    # split central value, minus error and plus error
    central = float(cleaned.split("-")[0])
    lower_err = float(cleaned.split("-")[1].split("+")[0])
    upper_err = float(cleaned.split("-")[1].split("+")[1])

    return (central, lower_err, upper_err)

def clean_string_number(s):
    # split plus/minus and return nominal +- uncertainty
    cleaned = unicodedata.normalize("NFKC", s.replace("±", "+-")).replace("−", "-").replace(" ̇", ".").strip() #that minus...
    central = float(cleaned.split("+-")[0])
    uncertainty = float(cleaned.split("+-")[1])
    return (central, uncertainty)

def retrieve_efficiencies_from_snap(input_folder, input_folder_snap, era="2023"):
    """Retrieve efficiencies from snap files.
    
    Args:
        input_folder: Path to CSV files
        input_folder_snap: Path to ROOT snap files
        era: Data-taking era (for file path construction)
    """
    ID_efficiencies = {}
    reweight_efficiencies = {}
    reweight_relative_efficiencies = {}

    # print("DEBUG: opening snap ", input_folder_snap, " running on era ", era)

    # First, detect if trigger variations are available by checking the first file
    has_trigger_variations = False
    first_file = next((f for f in os.listdir(input_folder_snap) if f.endswith(".root") and not f.startswith(".")), None)
    if first_file:
        with ROOT.TFile.Open(os.path.join(input_folder_snap, first_file)) as root_file:
            print("DEBUG: checking for trigger variations in file ", first_file)
            rdf = ROOT.RDataFrame(root_file.Get("Events"))
            columns = rdf.GetColumnNames()
            has_trigger_variations = "weight__triggerSF1DCorrection_up" in columns
    
    print(f"Detected trigger variations: {has_trigger_variations}")

    n_evts_final = {}
    for filename in os.listdir(input_folder_snap):
        if filename.endswith(".root") and not filename.startswith("."):
            with ROOT.TFile.Open(os.path.join(input_folder_snap, filename)) as root_file:
                rdf = ROOT.RDataFrame(root_file.Get("Events"))
                n_evts_nominal = rdf.Sum("weight").GetValue()
                n_evts_electronID_up = rdf.Sum("weight__electronID_up").GetValue()
                n_evts_electronID_down = rdf.Sum("weight__electronID_down").GetValue()
                
                outdict = {
                    "nominal" : n_evts_nominal,
                    "electronID_up" : n_evts_electronID_up,
                    "electronID_down" : n_evts_electronID_down,
                }
                
                if has_trigger_variations:
                    n_evts_trigger_up = rdf.Sum("weight__triggerSF1DCorrection_up").GetValue()
                    n_evts_trigger_down = rdf.Sum("weight__triggerSF1DCorrection_down").GetValue()
                    outdict["trigger_up"] = n_evts_trigger_up
                    outdict["trigger_down"] = n_evts_trigger_down
                    
                n_evts_final[filename.replace('.root', '')] = outdict
                print("DEBUG: era ", era, " file ", filename, " n_evts_nominal = ", n_evts_nominal)

    for filename in os.listdir(input_folder):
        if filename.endswith(".csv"):
            with open(os.path.join(input_folder, filename), 'r') as csvfile:
                reader = csv.reader(csvfile, delimiter=",")
                header = next(reader)

                # scan rows until we find the ID one (second entry)
                for row in reader:
                    # first, scan until you find the nEvents line (should be first)
                    if row[1] == "nEvents":
                        n_evts_initial = clean_string_number(row[3])[0]
                        print("DEBUG: era ", era, " file ", filename, " n_evts_initial = ", n_evts_initial)
                        sample_name = filename.replace('.csv', '')
                        nominal_eff = n_evts_final[sample_name]["nominal"] / n_evts_initial * 100
                        electronID_up_eff = n_evts_final[sample_name]["electronID_up"] / n_evts_initial * 100
                        electronID_down_eff = n_evts_final[sample_name]["electronID_down"] / n_evts_initial * 100

                        # print("DEBUG: initial events = ", n_evts_initial, " final nominal events = ", n_evts_final[sample_name]["nominal"], " nominal efficiency = ", nominal_eff)
                        # print("DEBUG: electronID up events = ", n_evts_final[sample_name]["electronID_up"], " electronID up efficiency = ", electronID_up_eff)
                        
                        # Use flat 1% relative uncertainty (temporary)
                        flat_unc = nominal_eff * 0.01
                        
                        if has_trigger_variations:
                            # New naming scheme with both ID and trigger
                            trigger_up_eff = n_evts_final[sample_name]["trigger_up"] / n_evts_initial * 100
                            trigger_down_eff = n_evts_final[sample_name]["trigger_down"] / n_evts_initial * 100
                            reweight_efficiencies[sample_name] = {
                                'nominal': nominal_eff,
                                'electronID_up': electronID_up_eff,
                                'electronID_down': electronID_down_eff,
                                'trigger_up': trigger_up_eff,
                                'trigger_down': trigger_down_eff,
                                'unc_down': flat_unc,
                                'unc_up': flat_unc
                            }
                            print("DEBUG: final nominal efficiency = ", nominal_eff, " electronID up efficiency = ", electronID_up_eff, " trigger up efficiency = ", trigger_up_eff)
                        else:
                            # Old naming scheme with just ID (backward compatibility)
                            reweight_efficiencies[sample_name] = {
                                'nominal': nominal_eff,
                                'up': electronID_up_eff,
                                'down': electronID_down_eff,
                                'unc_down': flat_unc,
                                'unc_up': flat_unc
                            }
                    elif row[1] == "ID":
                        # retrieve cumulative selection efficiency at that step
                        ID_efficiencies[filename.replace('.csv', '')] = clean_string(row[5])
    
    # print(f"DEBUG: reweight efficiencies = {reweight_efficiencies}")
    return {"ID_efficiencies": ID_efficiencies, "reweight_efficiencies": reweight_efficiencies, "has_trigger_variations": has_trigger_variations}


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
                    print("ROW: ", row)
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
# outfolder = "/eos/home-n/npalmeri/www/DiElectron/signal_model/fw_output/nanov15"
# outfolder = "/eos/home-n/npalmeri/www/DiElectron/signal_model/use_reco_mass_nanov15_withSyst"
# outfolder = "/eos/home-n/npalmeri/www/DiElectron/signal_model/use_reco_mass_nanov15_withScaleSyst_IDSF"
# outfolder = "/eos/home-n/npalmeri/www/DiElectron/signal_model/260226/use_reco_mass_nanov15_withScaleSyst_IDSF_triggerSF"
outfolder = "/eos/home-n/npalmeri/www/DiElectron/signal_model/260312/use_reco_mass_nanov15_withScaleSyst_IDSF_triggerSF_isoCut"

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

# Helper function to load efficiency data for a specific era and folder_tag
def _load_efficiency_data(era="2023", folder_tag="260226"):
    """Load efficiency data for the specified era and folder_tag.
    
    This updates the global variables used by the interpolation functions.
    """
    global efficiencies, old_efficiencies, has_trigger_variations, producer_efficiencies
    global input_folder, input_folder_snap
    global effs_dict, masses_dict, effs_nominal, effs_err, effs_old, effs_err_old
    global effs_electronID_up, effs_electronID_down, effs_trigger_up, effs_trigger_down
    global masses_ext, effs_ext, effs_err_ext, effs_old_ext, effs_err_old_ext
    
    # Get folder paths for this era
    input_folder, input_folder_snap = get_input_folders(era=era, folder_tag=folder_tag)
    
    # Load producer efficiencies (currently era-independent, using default path)
    # TODO: Update this if producer efficiencies become era-dependent
    producer_eff_path = f"/eos/home-n/npalmeri/www/DiElectron/PS_reweighting/nanov15/per_subera/signal_model_withScaleSyst_IDSF_triggerSF/zlog/data/MC/Zd_nJet012_pTe5_eta1p2_nanov15.py"
    producer_efficiencies = retrieve_producer_efficiencies(producer_eff_path)
    
    # Load efficiencies from snap r
    both_efficiencies = retrieve_efficiencies_from_snap(input_folder, input_folder_snap, era=era)
    efficiencies = both_efficiencies["reweight_efficiencies"]
    old_efficiencies = both_efficiencies["ID_efficiencies"]
    has_trigger_variations = both_efficiencies.get("has_trigger_variations", False)
    
    # Apply producer efficiencies
    print("DEBUG: applying producer efficiencies")
    for sample in samples:
        prod_eff = producer_efficiencies[sample]
        print("DEBUG:   era ", era, " sample ", sample, " producer efficiency = ", prod_eff)
        if isinstance(efficiencies[sample], dict):
            # Apply to all keys in dict
            for key in efficiencies[sample].keys():
                if key not in ['unc_down', 'unc_up']:
                    efficiencies[sample][key] *= prod_eff
            efficiencies[sample]['unc_down'] *= prod_eff
            efficiencies[sample]['unc_up'] *= prod_eff
        else:
            # Old tuple format (central, err_down, err_up)
            efficiencies[sample] = [eff * prod_eff for eff in efficiencies[sample]]
        
        # Old efficiencies are still in tuple format
        old_efficiencies[sample] = [eff * prod_eff for eff in old_efficiencies[sample]]
    
    # Rebuild efficiency arrays and dictionaries with the new data
    effs_old = np.array([old_efficiencies[sample][0] for sample in samples]) / 100
    effs_err_old = np.array([(old_efficiencies[sample][1]+old_efficiencies[sample][2])/2 / 100 for sample in samples])
    
    effs_nominal = np.array([efficiencies[sample]['nominal'] if isinstance(efficiencies[sample], dict) else efficiencies[sample][0] for sample in samples]) / 100
    effs_err = np.array([(efficiencies[sample]['unc_down']+efficiencies[sample]['unc_up'])/2 if isinstance(efficiencies[sample], dict) else (efficiencies[sample][1]+efficiencies[sample][2])/2 for sample in samples]) / 100
    
    if has_trigger_variations:
        effs_electronID_up = np.array([efficiencies[sample]['electronID_up'] for sample in samples]) / 100
        effs_electronID_down = np.array([efficiencies[sample]['electronID_down'] for sample in samples]) / 100
        effs_trigger_up = np.array([efficiencies[sample]['trigger_up'] for sample in samples]) / 100
        effs_trigger_down = np.array([efficiencies[sample]['trigger_down'] for sample in samples]) / 100
    else:
        effs_electronID_up = np.array([efficiencies[sample]['up'] for sample in samples]) / 100
        effs_electronID_down = np.array([efficiencies[sample]['down'] for sample in samples]) / 100
        effs_trigger_up = None
        effs_trigger_down = None
    
    effs_old_ext = effs_old
    effs_err_old_ext = effs_err_old
    masses_ext = masses
    effs_ext = effs_nominal
    effs_err_ext = effs_err
    
    masses_dict = {
        "ext": masses_ext,
        "base": masses
    }
    
    effs_dict = {
        "ext": {
            "new": (effs_nominal, effs_err),
            "old": (effs_old_ext, effs_err_old_ext)
        },
        "base": {
            "new": (effs_nominal, effs_err),
            "old": (effs_old, effs_err_old)
        }
    }
    
    if has_trigger_variations:
        effs_dict["ext"].update({
            "new_electronID_up": (effs_electronID_up, effs_err),
            "new_electronID_down": (effs_electronID_down, effs_err),
            "new_trigger_up": (effs_trigger_up, effs_err),
            "new_trigger_down": (effs_trigger_down, effs_err),
        })
        effs_dict["base"].update({
            "new_electronID_up": (effs_electronID_up, effs_err),
            "new_electronID_down": (effs_electronID_down, effs_err),
            "new_trigger_up": (effs_trigger_up, effs_err),
            "new_trigger_down": (effs_trigger_down, effs_err),
        })
    else:
        effs_dict["ext"].update({
            "new_up": (effs_electronID_up, effs_err),
            "new_down": (effs_electronID_down, effs_err),
        })
        effs_dict["base"].update({
            "new_up": (effs_electronID_up, effs_err),
            "new_down": (effs_electronID_down, effs_err),
        })

# Initialize with default era and folder_tag (for backward compatibility and standalone usage)
# This will populate all the global variables (efficiencies, effs_dict, etc.)
masses = np.array([1, 3.1, 5, 5.5, 6, 6.5, 8, 10])
x = np.linspace(0, 11, 1000)  # for plotting; was 1, 7

_load_efficiency_data(era="2023", folder_tag="260226")

print(f"\nUsing naming scheme: {'new (electronID/trigger)' if has_trigger_variations else 'old (up/down for ID only)'}")

# effs = np.array([1.562, 14.010, 19.821, 20.552, 18.541, 11.550]) # %
# effs_err = np.array([0.055, 0.155, 0.179, 0.181, 0.2, 0.143])
xsecs = np.array([39.62, 16.00, 11.31, 11.06, 10.81, 10.07, 8.273, 6.458]) # pb
xsecs_err = xsecs * 0.0015 # oom for available points

# TODO: update with new mass points
# xsecs = np.array([39.62, 16.00, 11.31, 11.06, 10.81, 10.07]) # pb
# xsecs_err = xsecs * 0.0015 # oom for available points

xsecs_old = np.array([3.396, 2.679, 1.952, 1.910, 1.865, 1.834]) # pb
xsecs_err_old = np.array([0.01646, 0.0095, 0.003978, 0.003451, 0.001997, 0.001002])

def fit_effs(use_old = False, use_crystalball=False, use_lognormal=False, use_novosibirsk=False, use_poly_exp=False):
    args = {}

    if use_poly_exp:
        # # Polynomial * exponential fit (like the old default)
        # args["bounds"] = [[0, -1, -1, -1, -1], [10, 20, 10, 10, 10]]
        # args["p0"] = [0.1, 10, 0.1, 0.1, 0.5]
        fit_func = lambda x, a, b, c, d: np.polyval((a, b, c, d), x)
    elif use_novosibirsk:
        # Novosibirsk function: asymmetric peak shape
        def novosibirsk_scaled(x, peak, width, tail, amplitude):
            return amplitude * novosibirsk(x, peak, width, tail)
        
        fit_func = novosibirsk_scaled
        args["p0"] = [5.5, 2.0, -0.3, 0.15]  # peak, width, tail, amplitude
        args["bounds"] = ([3, 0.5, -2, 0], [8, 5, 2, 0.3])
    elif use_lognormal:
        # Log-normal distribution: f(x) = (1/(x*sigma*sqrt(2*pi))) * exp(-(ln(x)-mu)^2 / (2*sigma^2))
        # Parameterized as: amplitude * lognormal(x, mu, sigma)
        def lognormal(x, mu, sigma, amplitude):
            return amplitude / (x * sigma * np.sqrt(2 * np.pi)) * np.exp(-0.5 * ((np.log(x) - mu) / sigma) ** 2)
        
        fit_func = lognormal
        args["p0"] = [1.5, 0.5, 0.15]  # mu, sigma, amplitude
        args["bounds"] = ([0, 0.1, 0], [3, 2, 1])
    elif use_crystalball:
        fit_func = lambda x, mean, sigma, alphaL, nL, alphaR, nR: 0.16 * crystal_ball(x, mean, sigma, alphaL, nL, alphaR, nR)
        args["p0"] = [5.5, 1, 0.3, 1, 1.5, 3]
        args["bounds"] = ([5.5, 0, 0, -10, 0, -10], [8, 5, 10, 10, 10, 10])
    else:
        # args["bounds"] = [[0, -1, -1, -1, -1], [10, 20, 10, 10, 10]]
        # args["p0"] = [0.1, 10, 0.1, 0.1, 0.5]
        fit_func = lambda x, a, b, c, d: np.polyval((a, b, c, d), x)

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

def pchip_effs(use_old = False, use_crystalball=False, variation=None):
    """PCHIP (Piecewise Cubic Hermite Interpolating Polynomial) interpolation for efficiencies.
    
    Args:
        use_old: Use old efficiencies without reweighting
        use_crystalball: Use extended mass range
        variation: None for nominal, 'up'/'down' for ID-only (backward compat),
                  'electronID_up'/'electronID_down' for electron ID variations,
                  'trigger_up'/'trigger_down' for trigger SF variations
    """
    mass = masses_dict["ext"] if use_crystalball else masses_dict["base"]
    extension_flag = "ext" if use_crystalball else "base"
    
    # Select appropriate efficiency values based on variation
    if use_old:
        old_flag = "old"
    elif variation in ["up", "down"]:
        # Backward compatibility naming
        old_flag = f"new_{variation}"
    elif variation in ["electronID_up", "electronID_down", "trigger_up", "trigger_down"]:
        # New naming scheme
        old_flag = f"new_{variation}"
    else:
        old_flag = "new"
    
    y, y_err = effs_dict[extension_flag][old_flag]
    
    # Add anchor points at low and high mass to control extrapolation
    mass_extended = np.concatenate([[0.0], mass, [13.0]])
    y_extended = np.concatenate([[0.0], y, [0.0]])
    
    pchip_func = PchipInterpolator(mass_extended, y_extended, extrapolate=True)
    # Wrap in lambda to match the interface expected by plotting
    fit_func = lambda x: pchip_func(x)
    
    return {"fit_function" : fit_func, "fit_parameters" : []}

# Default efficiency function for module usage
def get_efficiency_function(use_old=False, variation=None, era="2023", folder_tag="260226"):
    """Returns the default (PCHIP interpolation) efficiency function.
    
    Args:
        use_old: Use old efficiencies without reweighting
        variation: None for nominal, 'electronID_up'/'electronID_down' for electron ID variations,
                  'trigger_up'/'trigger_down' for trigger SF variations
        era: Data-taking era (default: "2023")
        folder_tag: Folder tag for organizing runs (default: "260226")
    
    Returns:
        Dictionary with 'fit_function' and 'fit_parameters' keys
    """
    # Load data for the specified era if not using old efficiencies
    if not use_old:
        _load_efficiency_data(era=era, folder_tag=folder_tag)
    return pchip_effs(use_old=use_old, use_crystalball=False, variation=variation)

def get_all_efficiency_functions(use_old=False, era="2023", folder_tag="260226"):
    """Returns all efficiency functions (nominal and variations) as a dictionary.
    
    Args:
        use_old: Use old efficiencies without reweighting
        era: Data-taking era (default: "2023")
        folder_tag: Folder tag for organizing runs (default: "260226")
    
    Returns:
        Dictionary with keys 'nominal' and available variations ('up'/'down' for ID-only,
        or 'electronID_up'/'electronID_down'/'trigger_up'/'trigger_down' for both)
    """
    # Load data for the specified era if not using old efficiencies
    if not use_old:
        _load_efficiency_data(era=era, folder_tag=folder_tag)
    
    result = {
        'nominal': pchip_effs(use_old=use_old, use_crystalball=False, variation=None),
    }
    
    if has_trigger_variations:
        result.update({
            'electronID_up': pchip_effs(use_old=use_old, use_crystalball=False, variation='electronID_up'),
            'electronID_down': pchip_effs(use_old=use_old, use_crystalball=False, variation='electronID_down'),
            'trigger_up': pchip_effs(use_old=use_old, use_crystalball=False, variation='trigger_up'),
            'trigger_down': pchip_effs(use_old=use_old, use_crystalball=False, variation='trigger_down')
        })
    else:
        # Backward compatibility: just 'up'/'down' for ID
        result.update({
            'up': pchip_effs(use_old=use_old, use_crystalball=False, variation='up'),
            'down': pchip_effs(use_old=use_old, use_crystalball=False, variation='down')
        })
    
    return result

def plot_effs(funcs_to_draw, outname, use_old = False, use_crystalball=False, plot_both = False, outfolder_arg=None):
    fig, ax = plt.subplots(figsize=(9, 8))
    hep.style.use(hep.style.CMS)
    palette = [
        "#3f90da",
        "#ffa90e",
        "#bd1f01",
        "#94a4a2",
        "#832db6",
        "#a96b59",
        "#e76300",
        "#b9ac70",
        "#717581",
        "#92dadd"
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

    # Plot nominal efficiency points
    ax.errorbar(
        mass, y * 100, yerr=y_err * 100, fmt='o', label='Nominal',
        markersize=8, capsize=7, elinewidth=2
    )
    
    # Plot up/down variation points if available (not for old efficiencies)
    if not use_old:
        # Check which variations are available
        if "new_electronID_up" in effs_dict[extension_flag]:
            # New naming scheme with separate ID and trigger variations
            color_electronID_up = '#4292c6'  # Light blue for electronID up
            color_electronID_down = '#08519c'  # Dark blue for electronID down
            color_trigger_up = '#fd8d3c'  # Light orange for trigger up
            color_trigger_down = '#d94801'  # Dark orange for trigger down
            
            y_electronID_up, y_err_electronID_up = effs_dict[extension_flag]["new_electronID_up"]
            y_electronID_down, y_err_electronID_down = effs_dict[extension_flag]["new_electronID_down"]
            
            ax.errorbar(
                mass, y_electronID_up * 100, yerr=y_err_electronID_up * 100, fmt='^', label='Electron ID SF up',
                markersize=7, capsize=5, elinewidth=1.5, color=color_electronID_up
            )
            ax.errorbar(
                mass, y_electronID_down * 100, yerr=y_err_electronID_down * 100, fmt='v', label='Electron ID SF down',
                markersize=7, capsize=5, elinewidth=1.5, color=color_electronID_down
            )
            
            if "new_trigger_up" in effs_dict[extension_flag]:
                y_trigger_up, y_err_trigger_up = effs_dict[extension_flag]["new_trigger_up"]
                y_trigger_down, y_err_trigger_down = effs_dict[extension_flag]["new_trigger_down"]
                
                ax.errorbar(
                    mass, y_trigger_up * 100, yerr=y_err_trigger_up * 100, fmt='>', label='Trigger SF up',
                    markersize=7, capsize=5, elinewidth=1.5, color=color_trigger_up
                )
                ax.errorbar(
                    mass, y_trigger_down * 100, yerr=y_err_trigger_down * 100, fmt='<', label='Trigger SF down',
                    markersize=7, capsize=5, elinewidth=1.5, color=color_trigger_down
                )
        elif "new_up" in effs_dict[extension_flag]:
            # Old naming scheme (backward compatibility) - just ID variations as up/down
            color_up = '#4292c6'  # Light blue for up
            color_down = '#08519c'  # Dark blue for down
            
            y_up, y_err_up = effs_dict[extension_flag]["new_up"]
            y_down, y_err_down = effs_dict[extension_flag]["new_down"]
            
            ax.errorbar(
                mass, y_up * 100, yerr=y_err_up * 100, fmt='^', label='Up variation',
                markersize=7, capsize=5, elinewidth=1.5, color=color_up
            )
            ax.errorbar(
                mass, y_down * 100, yerr=y_err_down * 100, fmt='v', label='Down variation',
                markersize=7, capsize=5, elinewidth=1.5, color=color_down
            )

    for label, fit_info in funcs_to_draw.items():
        fit_func = fit_info["fit_function"]
        fit_params = fit_info["fit_parameters"]

        if len(fit_params) > 0:  # parametric fit with parameters
            y_fit = fit_func(x, *fit_params)
        else:  # interpolation function with no parameters
            y_fit = fit_func(x)
        
        # Assign matching colors for up/down variations
        plot_kwargs = {'linewidth': 2, 'linestyle': '--'}
        
        # Handle both old and new naming schemes
        label_lower = label.lower()
        if "new_electronID_up" in effs_dict[extension_flag]:
            # New naming scheme
            if 'electronid' in label_lower and 'up' in label_lower:
                plot_kwargs['color'] = '#4292c6'
                plot_kwargs['alpha'] = 0.7
            elif 'electronid' in label_lower and 'down' in label_lower:
                plot_kwargs['color'] = '#08519c'
                plot_kwargs['alpha'] = 0.7
            elif 'trigger' in label_lower and 'up' in label_lower:
                plot_kwargs['color'] = '#fd8d3c'
                plot_kwargs['alpha'] = 0.7
            elif 'trigger' in label_lower and 'down' in label_lower:
                plot_kwargs['color'] = '#d94801'
                plot_kwargs['alpha'] = 0.7
        elif "new_up" in effs_dict[extension_flag]:
            # Old naming scheme (backward compatibility)
            if 'up' in label_lower and 'down' not in label_lower:
                plot_kwargs['color'] = '#4292c6'
                plot_kwargs['alpha'] = 0.7
            elif 'down' in label_lower:
                plot_kwargs['color'] = '#08519c'
                plot_kwargs['alpha'] = 0.7
        
        ax.plot(x, y_fit * 100, label=f'{label}', **plot_kwargs) 

    ax.set_xlabel("M($Z_D$) [GeV]", fontsize=24)
    ax.set_ylabel("Efficiency [%]", fontsize=24)
    # Use smaller ymax for final plot, larger for comparison plots
    ymax = 17 if not plot_both and len(funcs_to_draw) < 5 else 20
    # if maximum is larger than ymax, take max * 1.1
    max_y = max([max(effs_dict[extension_flag][key][0]) for key in effs_dict[extension_flag].keys()]) * 1.1 * 100
    ymin = -0.1 if not plot_both and len(funcs_to_draw) < 5 else 0
    ax.set_ylim(ymin, max_y)
    ax.tick_params(axis='both', which='major', labelsize=20, length=10)
    ax.grid()
    ax.legend(fontsize=15)
    # add cms label with reduced font size
    hep.cms.label(label="Preliminary", ax=ax, data=False, year=2023, com=13.6, fontsize=18)
    
    folder_to_use = outfolder_arg if outfolder_arg is not None else outfolder
    os.makedirs(folder_to_use, exist_ok=True)
    for ext in [".png", ".pdf"]:
        plt.savefig(os.path.join(folder_to_use, outname + ext))

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

def pchip_xsecs(use_old=False):
    """PCHIP (Piecewise Cubic Hermite Interpolating Polynomial) interpolation for cross-sections."""
    if use_old:
        masses_to_use = masses[:6]  # old xsecs only up to 6.5 GeV
        xsecs_to_use = xsecs_old
    else:
        masses_to_use = masses
        xsecs_to_use = xsecs
    
    pchip_func = PchipInterpolator(masses_to_use, xsecs_to_use, extrapolate=True)
    # Wrap in lambda to match the interface
    fit_func = lambda x: pchip_func(x)
    
    return {"fit_function" : fit_func, "fit_parameters" : []}

# Default xsec function for module usage
def get_xsec_function(use_old=False, era="2023", folder_tag="260226"):
    """Returns the default (PCHIP interpolation) cross-section function.
    
    Args:
        use_old: Use old cross-sections
        era: Data-taking era (default: "2023") - currently unused but kept for API consistency
        folder_tag: Folder tag (default: "260226") - currently unused but kept for API consistency
    """
    # Note: Cross-sections are currently era-independent, but we keep the parameters
    # for API consistency and potential future use
    return pchip_xsecs(use_old=use_old)

def plot_xsecs(funcs_to_draw, outname = "xsec_vs_mass", use_old = False, outfolder_arg=None):
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

    # add cms label with reduced font size
    hep.cms.label(label="Preliminary", ax=ax, data=False, year=2023, com=13.6, fontsize=18)

    folder_to_use = outfolder_arg if outfolder_arg is not None else outfolder
    os.makedirs(folder_to_use, exist_ok=True)
    for ext in [".png", ".pdf"]:
        plt.savefig(os.path.join(folder_to_use, outname + ext))

if __name__ == "__main__":
    # Process all eras
    all_eras = ["2022", "2022EE", "2023", "2023BPix"]
    # all_eras = ["2022"]
    
    for era in all_eras:
        print(f"\n{'='*80}")
        print(f"Processing era: {era}")
        print(f"{'='*80}\n")
        
        # Set era-specific output folder
        era_outfolder = os.path.join(outfolder, f"era{era}")
        os.makedirs(era_outfolder, exist_ok=True)  # Create if doesn't exist, no error if exists
        
        # Load efficiency data for this era
        _load_efficiency_data(era=era, folder_tag="260226")
        
        print("effs (NEW) = ", effs_nominal)
        print("effs (OLD) = ", effs_old)
        print("effs (NEW / OLD) = ", effs_nominal/effs_old)
        # pretty print eff +- error for new result:
        for i, sample in enumerate(samples):
            print(f"{sample}: {effs_nominal[i]*100:.3f} +- {effs_err[i]*100:.3f} % (new) [relative error = {effs_err[i]/effs_nominal[i]*100:.2f} %]")

        # post-reweight efficiencies, plot and fit (also plotting old for comparison)
        fit_result = fit_effs(use_crystalball=True)
        fit_result_poly = fit_effs(use_crystalball=False)
        fit_result_poly_exp = fit_effs(use_poly_exp=True)
        fit_result_lognormal = fit_effs(use_lognormal=True)
        fit_result_novosibirsk = fit_effs(use_novosibirsk=True)
        interp_result = interp_effs(use_old=False, use_crystalball=False)
        pchip_result = pchip_effs(use_old=False, use_crystalball=False, variation=None)
        
        if has_trigger_variations:
            pchip_result_electronID_up = pchip_effs(use_old=False, use_crystalball=False, variation='electronID_up')
            pchip_result_electronID_down = pchip_effs(use_old=False, use_crystalball=False, variation='electronID_down')
            pchip_result_trigger_up = pchip_effs(use_old=False, use_crystalball=False, variation='trigger_up')
            pchip_result_trigger_down = pchip_effs(use_old=False, use_crystalball=False, variation='trigger_down')
        else:
            # Backward compatibility
            pchip_result_electronID_up = pchip_effs(use_old=False, use_crystalball=False, variation='up')
            pchip_result_electronID_down = pchip_effs(use_old=False, use_crystalball=False, variation='down')
            pchip_result_trigger_up = None
            pchip_result_trigger_down = None
        
        print("FIT RESULTS dCB: ", fit_result["fit_parameters"])
        print("FIT RESULTS poly: ", fit_result_poly["fit_parameters"])
        print("FIT RESULTS poly*exp: ", fit_result_poly_exp["fit_parameters"])
        print("FIT RESULTS Novosibirsk: ", fit_result_novosibirsk["fit_parameters"])
        
        plot_effs(use_old=False, use_crystalball=True,
                  funcs_to_draw = {"dCB fit" : fit_result,
                                  "Polynomial (4th deg.) fit" : fit_result_poly_exp,
                                  "Novosibirsk fit" : fit_result_novosibirsk,
                                  "Log-normal fit" : fit_result_lognormal,
                                  "Linear interpolation" : interp_result,
                                  "PCHIP interpolation" : pchip_result,
                                  },
                  outname="efficiency_vs_mass", plot_both=True, outfolder_arg=era_outfolder)

        # updated xsec values, plot and fit
        fit_result_xsec = fit_xsecs()
        interp_result_xsec = interp_xsecs()
        pchip_result_xsec = pchip_xsecs()
        print("XSEC FIT RESULTS: ", fit_result_xsec["fit_parameters"])
        plot_xsecs(funcs_to_draw={"Exponential fit" : fit_result_xsec,
                                  "Linear interpolation" : interp_result_xsec,
                                  "PCHIP interpolation" : pchip_result_xsec},
                   outname="xsec_vs_mass", outfolder_arg=era_outfolder)
        
        # Clean plots with just final PCHIP interpolation and variations
        if has_trigger_variations:
            plot_effs(use_old=False, use_crystalball=False,
                      funcs_to_draw = {"PCHIP nominal" : pchip_result,
                                      "PCHIP electronID up" : pchip_result_electronID_up,
                                      "PCHIP electronID down" : pchip_result_electronID_down,
                                      "PCHIP trigger up" : pchip_result_trigger_up,
                                      "PCHIP trigger down" : pchip_result_trigger_down},
                      outname="efficiency_vs_mass_final", plot_both=False, outfolder_arg=era_outfolder)
        else:
            plot_effs(use_old=False, use_crystalball=False,
                      funcs_to_draw = {"PCHIP nominal" : pchip_result,
                                      "PCHIP up" : pchip_result_electronID_up,
                                      "PCHIP down" : pchip_result_electronID_down},
                      outname="efficiency_vs_mass_final", plot_both=False, outfolder_arg=era_outfolder)
        
        plot_xsecs(funcs_to_draw={"PCHIP interpolation" : pchip_result_xsec},
                   outname="xsec_vs_mass_final", outfolder_arg=era_outfolder)
        
        print(f"\nCompleted processing for era {era}. Plots saved to: {era_outfolder}\n")

    # # same for old xsec values
    # fit_result_eff_old = fit_effs(use_old = True, use_crystalball=False)
    # print("EFF OLD FIT RESULTS: ", fit_result_eff_old["fit_parameters"])
    # plot_effs(use_old=True, use_crystalball=False,
    #           funcs_to_draw = {"dCB" : fit_result_eff_old}, outname="efficiency_vs_mass_old")

    # # same for old xsec values
    # fit_result_xsec_old = fit_xsecs(use_old=True)
    # print("XSEC OLD FIT RESULTS: ", fit_result_xsec_old["fit_parameters"])
    # plot_xsecs(fit_func=fit_result_xsec_old["fit_function"], fit_params=fit_result_xsec_old["fit_parameters"], outname="xsec_vs_mass_old", use_old=True)

