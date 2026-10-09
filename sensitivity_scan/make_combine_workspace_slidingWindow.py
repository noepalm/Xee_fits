#!/usr/bin/env python

from __future__ import absolute_import
from __future__ import print_function
import CombineHarvester.CombineTools.ch as ch
import ROOT as R
import os
import numpy as np
import argparse
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

region_mass_ranges = {
    # "region0": {"min": 0.3, "max": 2.4},
    # "region1": {"min": 1.6, "max": 4.6},
    # "region2": {"min": 3.8, "max": 11.0},
    #
    # "region0": {"min": 0.3, "max": 2.4},
    # "region1": {"min": 1.6, "max": 6},
    # "region2": {"min": 4.9, "max": 10.5},
    #
    "region0": {"min": 0.3, "max": 2.4},
    "region1": {"min": 2.0, "max": 7.0}, #was [1.6, 7.0]
    "region2": {"min": 6.0, "max": 12.0},
}

CUSTOM_MASS_MIN = 1.3 #1.6
CUSTOM_MASS_MAX = 2.4 #2.2
# N_SIGMAS_WINDOW = 5.0

def is_mass_in_region(mass, region):
    mass = float(mass)
    if region in region_mass_ranges:
        return region_mass_ranges[region]["min"] <= mass < region_mass_ranges[region]["max"]
    else:
        print("Warning: Invalid region specified for mass range check. Returning False.")
        return False

def create_sliced_mass_workspace(base_ws, mass_str, era, chn):
    m_val = float(mass_str)

    # 1. Retrieve resolution
    sig_sigma_var = base_ws.obj(f"sigma_test_M{mass_str.replace('.', 'p')}_{era}")
    sigma = sig_sigma_var.evaluate() if sig_sigma_var else 0.02 * m_val

    # 2. Build local workspace
    ws_slice = R.RooWorkspace("w")
    orig_mass_var = base_ws.var("mass")
    orig_data = base_ws.data("data_obs")
    is_binned = isinstance(orig_data, R.RooDataHist)

    parent_min = orig_mass_var.getMin()
    parent_max = orig_mass_var.getMax()

    if is_binned:
        # Snap boundaries to the exact parent binning
        orig_binning = orig_mass_var.getBinning()
        # raw_min = max(parent_min, m_val - N_SIGMAS_WINDOW * sigma)
        # raw_max = min(parent_max, m_val + N_SIGMAS_WINDOW * sigma)
        raw_min = CUSTOM_MASS_MIN
        raw_max = CUSTOM_MASS_MAX

        # Clamp bin indices to valid parent range [0, n_bins - 1]
        max_bin_idx = orig_binning.numBins() - 1
        bin_low = max(0, min(orig_binning.binNumber(raw_min), max_bin_idx))
        bin_high = max(0, min(orig_binning.binNumber(raw_max), max_bin_idx))

        m_min = orig_binning.binLow(bin_low)
        m_max = orig_binning.binHigh(bin_high)
        n_bins_slice = bin_high - bin_low + 1

        # Single, correctly bounded mass variable
        new_mass = R.RooRealVar(
            "mass", "mass", m_val, m_min, m_max, orig_mass_var.getUnit()
        )
        new_mass.setBins(n_bins_slice)
        getattr(ws_slice, "import")(new_mass)

        # Populate RooDataHist directly on the snapped grid
        reduced_data = R.RooDataHist("data_obs", "data_obs", R.RooArgSet(new_mass))
        argset = R.RooArgSet(new_mass)

        for i in range(n_bins_slice):
            orig_idx = bin_low + i
            center = orig_binning.binCenter(orig_idx)

            orig_data.get(orig_idx)
            wgt = orig_data.weight()

            new_mass.setVal(center)
            reduced_data.add(argset, wgt)

        getattr(ws_slice, "import")(reduced_data)
    else:   
        # Unbinned dataset
        m_min = max(parent_min, m_val - N_SIGMAS_WINDOW * sigma)
        m_max = min(parent_max, m_val + N_SIGMAS_WINDOW * sigma)
        new_mass = R.RooRealVar(
            "mass", "mass", m_val, m_min, m_max, orig_mass_var.getUnit()
        )
        new_mass.setBins(orig_mass_var.getBins())
        getattr(ws_slice, "import")(new_mass)

        reduced_data = orig_data.reduce(
            R.RooFit.SelectVars(R.RooArgSet(new_mass)),
            R.RooFit.Cut(f"mass >= {m_min} && mass <= {m_max}"),
        )
        reduced_data.SetName("data_obs")
        getattr(ws_slice, "import")(reduced_data)

    # 3. Import remaining workspace elements
    for var in base_ws.allVars():
        if var.GetName() != "mass":
            getattr(ws_slice, "import")(var, R.RooFit.Silence())

    for cat in base_ws.allCats():
        getattr(ws_slice, "import")(cat, R.RooFit.Silence())

    for pdf in base_ws.allPdfs():
        getattr(ws_slice, "import")(pdf, R.RooFit.RecycleConflictNodes(), R.RooFit.Silence())

    return ws_slice

# def create_sliced_mass_workspace(base_ws, mass_str, era, chn, rebin_factor=2):
#     m_val = float(mass_str)

#     # 1. Retrieve resolution
#     sig_sigma_var = base_ws.obj(f"sigma_test_M{mass_str.replace('.', 'p')}_{era}")
#     sigma = sig_sigma_var.evaluate() if sig_sigma_var else 0.02 * m_val

#     # 2. Build local workspace
#     ws_slice = R.RooWorkspace("w")
#     orig_mass_var = base_ws.var("mass")
#     orig_data = base_ws.data("data_obs")
#     is_binned = isinstance(orig_data, R.RooDataHist)

#     if is_binned:
#         # Snap boundaries to the exact parent binning
#         orig_binning = orig_mass_var.getBinning()
#         # raw_min = m_val - N_SIGMAS_WINDOW * sigma
#         # raw_max = m_val + N_SIGMAS_WINDOW * sigma
#         raw_min = 1.3
#         raw_max = 2.4

#         bin_low = orig_binning.binNumber(raw_min)
#         bin_high = orig_binning.binNumber(raw_max)

#         if rebin_factor > 1:
#             raw_span = bin_high - bin_low + 1
#             if raw_span % rebin_factor != 0:
#                 bin_high += rebin_factor - (raw_span % rebin_factor)

#         m_min = orig_binning.binLow(bin_low)
#         m_max = orig_binning.binHigh(bin_high)
#         n_bins_slice = (bin_high - bin_low + 1) // rebin_factor

#         # Single, correctly bounded mass variable
#         new_mass = R.RooRealVar(
#             "mass", "mass", m_val, m_min, m_max, orig_mass_var.getUnit()
#         )
#         new_mass.setBins(n_bins_slice)
#         getattr(ws_slice, "import")(new_mass)

#         # Populate RooDataHist directly on the snapped grid
#         reduced_data = R.RooDataHist("data_obs", "data_obs", R.RooArgSet(new_mass))
#         argset = R.RooArgSet(new_mass)

#         new_binning = new_mass.getBinning()
#         for i in range(n_bins_slice):
#             center = new_binning.binCenter(i)

#             wgt = 0.0
#             for step in range(rebin_factor):
#                 orig_idx = bin_low + i * rebin_factor + step
#                 orig_data.get(orig_idx)
#                 wgt += orig_data.weight()

#             new_mass.setVal(center)
#             reduced_data.add(argset, wgt)

#         getattr(ws_slice, "import")(reduced_data)
#     else:   
#         # Unbinned dataset
#         m_min = m_val - 6.0 * sigma
#         m_max = m_val + 6.0 * sigma
#         new_mass = R.RooRealVar(
#             "mass", "mass", m_val, m_min, m_max, orig_mass_var.getUnit()
#         )
#         new_mass.setBins(orig_mass_var.getBins())
#         getattr(ws_slice, "import")(new_mass)

#         reduced_data = orig_data.reduce(
#             R.RooFit.SelectVars(R.RooArgSet(new_mass)),
#             R.RooFit.Cut(f"mass >= {m_min} && mass <= {m_max}"),
#         )
#         reduced_data.SetName("data_obs")
#         getattr(ws_slice, "import")(reduced_data)

#     # 3. Import remaining workspace elements
#     for var in base_ws.allVars():
#         if var.GetName() != "mass":
#             getattr(ws_slice, "import")(var, R.RooFit.Silence())

#     for cat in base_ws.allCats():
#         getattr(ws_slice, "import")(cat, R.RooFit.Silence())

#     for pdf in base_ws.allPdfs():
#         getattr(ws_slice, "import")(
#             pdf, R.RooFit.RecycleConflictNodes(), R.RooFit.Silence()
#         )

#     return ws_slice

parser = argparse.ArgumentParser()
parser.add_argument('--data', action='store_true',
                    help='Run on data instead of MinBias MC')
parser.add_argument('--cat', type=str, default='inclusive', choices=["inclusive", "eta", "dR"],
                    help='Which category to process')
parser.add_argument('--region', '-r', type=str, default='region1', choices=["region0", "region1", "region2"],
                    help='Which mass region to process (possibilities: region0: (0, 2), region1: (2, 4.6), region2: (4.6, 11))')
parser.add_argument('--era', type=str, default="2023", choices=["2022", "2022EE", "2023", "2023BPix"],
                    help='Which era to process (2022, 2022EE, 2023, 2023BPix)')
parser.add_argument('--withSyst', action='store_true', default=False,
                    help='Include systematics in the datacard')
parser.add_argument('--no_reweight', action='store_true',
                    help='Use non-reweighted datasets (refers to trigger reweighting only -- applies to both signal and background modelling)')                    
parser.add_argument('--input_tag', type=str, default="",
                    help='Tag used for dataset creation')
parser.add_argument('--envelope', action='store_true',
                    help='Use dataset with envelope of background functions.')
parser.add_argument('--tag', type=str, default="",
                    help='Tag to append to output folder name')
parser.add_argument('--folder_tag', type=str, default="",
                    help='Base folder output name; card folder is created inside.')
parser.add_argument('--signal_multiplier', '-s', type=float, default=1.0,
                    help='Multiplier to apply to signal rates (for testing purposes)')
parser.add_argument('--bkg_x2', action='store_true',
                    help='Multiply background rates by 2 (for testing purposes)')
parser.add_argument('--bkg_div100', action='store_true',
                    help='Divide background rates by 100 (for testing purposes)')
parser.add_argument('--binned', action='store_true',
                    help='Use binned data')
parser.add_argument('--no_res', action='store_true',
                    help='Exclude resonant backgrounds from the fit')
args = parser.parse_args()

cb = ch.CombineHarvester()
# increase verbosity for debugging
cb.SetVerbosity(5)

if args.data:
    if args.withSyst:
        input_dir = f'/eos/home-n/npalmeri/DiEleAnalyzer/Xee_fits/background_modelling/datasets/{args.folder_tag}/{args.era}/'
    else:
        input_dir = '/eos/home-n/npalmeri/DiEleAnalyzer/Xee_fits/background_modelling/datasets/' # datasets/without_region_overlap for old files
else:
    input_dir = '/eos/home-n/npalmeri/DiEleAnalyzer/Xee_fits/background_modelling/datasets/nanov15_overlap/' # datasets/without_region_overlap for old files
    # input_dir = '/eos/home-n/npalmeri/DiEleAnalyzer/Xee_fits/background_modelling/datasets/forPresentation_11062025/'

if (args.bkg_x2 and not args.no_reweight):
    raise RuntimeError("Error: --bkg_x2 can currently only be used with --no_reweight")

# add workspace
sample_suffix = "_data" if args.data else "_minbias"
binned_suffix = "_binned" if args.binned else ""
reweight_suffix = "_noReweight" if args.no_reweight else ""
bkg_scale_suffix = "_x2wgt" if args.bkg_x2 else ("_div100wgt" if args.bkg_div100 else "")
input_tag_suffix = f"_{args.input_tag}" if args.input_tag != "" else ""
data_suffix = "_data" if args.data else ""
envelope_suffix = "_envelope" if args.envelope else ""

dataset_name = f"dataset{sample_suffix}_{args.region}{binned_suffix}{bkg_scale_suffix}{reweight_suffix}{data_suffix}{input_tag_suffix}_{args.era}{envelope_suffix}_full.root"
print(">> Using dataset:", input_dir + dataset_name, flush = True)

# dataset_name = "dataset_minbias_reweight_full.root" if not args.no_reweight else "dataset_minbias_noReweight_full.root"
# if args.no_reweight and args.bkg_x2:
#     dataset_name = "dataset_minbias_noReweight_x2wgt_full.root"
# if args.no_reweight and args.bkg_div100:
#     dataset_name = "dataset_minbias_noReweight_div100wgt_full.root"

f = R.TFile.Open(input_dir + dataset_name, "READ")
w = f.Get("w")

# Need to generate initial workspace with the correct mass range
m = w.var("mass")
# m.setMin(2.0)
# m.setMax(4.2)
# m.setBins(100)
# w.RecursiveRemove(w.var("mass"))
# w.Import(m, R.RooFit.RenameVariable("mass", "mass"))

# # also remove all references to mass_test (possibly disruptive, just to be safe)
# w.RecursiveRemove(w.var("mass_test"))

# CHANGE DATASET RANGE: ONLY KEEP BINS BETWEEN 2 AND 4.2
data = w.data("data_obs")
# data = data.reduce(R.RooFit.Cut(f"mass > 2 && mass < 4.2"))
# data.Print()
# w.RecursiveRemove(w.data("data_obs"))
# w.Import(data)

# save luminosity of projection for later use
# luminosity = 8.1842 if args.data else 58.9
luminosities = {
    # "2022" : 0.83,
    # "2022EE" : 1.93,
    # "2023" : 2.65,
    # "2023BPix" : 1.27,
    "2022" : 7.73,
    "2022EE" : 26.62,
    "2023" : 14.54,
    "2023BPix" : 9.68,
}
luminosity = luminosities[args.era] if args.data else 58.6
# luminosity = 6.68 if args.data else 58.6
lumi = R.RooRealVar(f"luminosity_{args.era}", f"luminosity_{args.era}", luminosity)
lumi.setConstant(True)
w.Import(lumi)

# w.Import(data, R.RooCmdArg())

cb.AddWorkspace(w)

# Basic configuration
chns = ['ee']
# eras = ['2023']
eras = [args.era]
era = args.era
era_energy = '13p6TeV'

if args.region == "region1":
    candidate_resonances = ['jpsi', 'psi2s']
elif args.region == "region2":
    candidate_resonances = ['upsilon1s', 'upsilon2s']
elif args.region == "region0":
    candidate_resonances = ['phi', 'omega']
else:
    candidate_resonances = []

if args.no_res:
    candidate_resonances = []

def get_resonance_sigma(res, era_str):
    if res == "jpsi":
        s_var = w.var(f"jpsi_sigma_{era_str}")
        score_var = w.var(f"jpsi_sigma_core_{era_str}")
        s_val = s_var.getVal() if s_var else None
        score_val = score_var.getVal() if score_var else None
        if s_val is not None and score_val is not None:
            return np.sqrt(s_val**2 + score_val**2)
        elif s_val is not None:
            return s_val
        elif score_val is not None:
            return score_val
    else:
        s_var = w.var(f"{res}_sigma_{era_str}")
        if s_var:
            return s_var.getVal()
    return None

def get_resonance_mass(res, era_str):
    m_var = w.var(f"{res}_mean_{era_str}") or w.var(f"{res}_mass_{era_str}") or w.var(f"m_{res}_{era_str}") or w.var(f"{res}_mean") or w.var(f"{res}_mass")
    if m_var:
        return m_var.getVal()
    # Nominal fallback PDG masses in GeV
    pdg_masses = {
        "phi": 1.0195,
        "omega": 0.7827,
        "eta": 0.5479,
        "jpsi": 3.0969,
        "psi2s": 3.6861,
        "upsilon1s": 9.4603,
        "upsilon2s": 10.0233,
    }
    return pdg_masses.get(res, None)

# masses = [f"{v:.1f}" for v in np.arange(0.1, 11.1, 0.1)]
masses = [f"{v:.1f}" for v in np.arange(0.1, 12.9, 0.1)]
# select subrange belonging to processed region
masses = [mass for mass in masses if is_mass_in_region(mass, args.region)]

# # TEMPORARY: only process 1.7, 5.0, 7.1 for debugging
masses = [mass for mass in masses if mass in ["1.8", "1.9", "2.0", "2.1"]]

# Per-mass background processes
# Only add a resonance if |mass - res_mass| <= 5 * res_sigma
bkg_procs_per_mass = {}
for m_str in masses:
    m_val = float(m_str)
    procs = ['dy']
    for res in candidate_resonances:
        res_sigma = get_resonance_sigma(res, args.era)
        res_mean = get_resonance_mass(res, args.era)
        if res_sigma is not None and res_mean is not None:
            if abs(m_val - res_mean) <= 5.0 * res_sigma:
                procs.append(res)
                print(f">> Mass {m_str}: adding resonance '{res}' (|{m_val} - {res_mean:.4f}| = {abs(m_val - res_mean):.4f} <= 5 * {res_sigma:.4f} = {5.0 * res_sigma:.4f})")
            else:
                print(f">> Mass {m_str}: excluding resonance '{res}' (|{m_val} - {res_mean:.4f}| = {abs(m_val - res_mean):.4f} > 5 * {res_sigma:.4f} = {5.0 * res_sigma:.4f})")
        else:
            # Fallback if sigma/mean not found: include resonance to be safe
            print(f"Warning: Could not retrieve sigma or mass for resonance '{res}' in era {args.era} (sigma={res_sigma}, mean={res_mean}), adding by default.")
            procs.append(res)
    bkg_procs_per_mass[m_str] = {'ee': procs}

# Combined set of all background processes present in at least one mass point
all_bkg_procs = sorted(list({p for mp in bkg_procs_per_mass.values() for p in mp['ee']}))
bkg_procs = {'ee': all_bkg_procs}

sig_procs = ['Zd']

if args.cat == "eta":
    cats = {
        f'ee_{era}': [
            (0, 'etap0p6'),
            (1, 'etam0p6'),
        ] for era in eras
    }
elif args.cat == "dR":
    cats = {
        f'ee_{era}': [
            (2, 'dRp0p3'),
            (3, 'dRm0p3'),
        ] for era in eras
    }
elif args.cat == "inclusive":
    cats = {
        f'ee_{era}' : [
            (4, 'inclusive'),
        ] for era in eras
    }

print('>> Creating processes and observations...')

for era in eras:
    for chn in chns:
        cb.AddObservations( masses, ['Xee'], [era], [chn], cats[chn+"_"+era] )
        for mass in masses:
            cb.AddProcesses( [mass], ['Xee'], [era], [chn], bkg_procs_per_mass[mass][chn], cats[chn+"_"+era], False )
        cb.AddProcesses( masses, ['Xee'], [era], [chn], sig_procs, cats[chn+"_"+era], True )

print('>> Adding systematics...')

# ID SF 
# ### first, determine highest variation across mass values AND between up/down
# ### apply worst case scenario as lnN uncertainty on signal yield
# id_variation_value = 1.0
# for mass in masses:
#     w_var_nominal = w.var(f"Zd_M{mass}_expected_{args.era}")
#     w_var_up = w.var(f"Zd_M{mass}_expected_electronID_up_{args.era}")
#     w_var_down = w.var(f"Zd_M{mass}_expected_electronID_down_{args.era}")
#     if w_var_nominal and w_var_up and w_var_down:
#         var_nominal, var_up, var_down = w_var_nominal.getVal(), w_var_up.getVal(), w_var_down.getVal()
#         if var_nominal > 0:
#             frac_up = 1 + abs(1 - var_up/var_nominal)
#             frac_down = 1 + abs(1 - var_down/var_nominal)
#             max_frac = max(frac_up, frac_down)
#             if max_frac > id_variation_value:
#                 id_variation_value = max_frac
#         else:
#             print(f"Warning: Nominal signal yield for mass {mass} is non-positive ({var_nominal}), skipping electron ID systematic for this mass point.")
#     else:
#         print(f"Warning: Missing variables for mass {mass}: nominal={w_var_nominal}, up={w_var_up}, down={w_var_down}. Skipping electron ID systematic for this mass point.")
# print(f"Determined electron ID systematic lnN value: {id_variation_value:.4f}")
# cb.cp().signals().AddSyst(cb, 'electronID_syst', 'lnN', ch.SystMap()(id_variation_value))

def id_syst_for_mass(mass, era, variation="electronID"):
    nominal = w.var(f"Zd_M{mass:.1f}_expected_{era}").getVal()
    down = w.var(f"Zd_M{mass:.1f}_expected_{variation}_down_{era}").getVal()
    up = w.var(f"Zd_M{mass:.1f}_expected_{variation}_up_{era}").getVal()
    if nominal <= 0:
        raise RuntimeError(f"Non-positive nominal for M={mass:.1f}, era={era}")
    return (down / nominal, up / nominal)

syst_map = ch.SystMap("era", "mass")
for mass in masses:
    down, up = id_syst_for_mass(float(mass), args.era, variation="electronID")
    syst_map = syst_map([args.era], [mass], (down, up))

cb.cp().signals().AddSyst(cb, "CMS_eff_e_id", "lnN", syst_map)
# cb.cp().signals().AddSyst(cb, "electronID_syst", "lnN", syst_map)

# Trigger SF 
# ### first, determine highest variation across mass values AND between up/down
# ### apply worst case scenario as lnN uncertainty on signal yield
# id_variation_value = 1.0
# for mass in masses:
#     w_var_nominal = w.var(f"Zd_M{mass}_expected_{args.era}")
#     w_var_up = w.var(f"Zd_M{mass}_expected_trigger_up_{args.era}")
#     w_var_down = w.var(f"Zd_M{mass}_expected_trigger_down_{args.era}")
#     if w_var_nominal and w_var_up and w_var_down:
#         var_nominal, var_up, var_down = w_var_nominal.getVal(), w_var_up.getVal(), w_var_down.getVal()
#         if var_nominal > 0:
#             frac_up = 1 + abs(1 - var_up/var_nominal)
#             frac_down = 1 + abs(1 - var_down/var_nominal)
#             max_frac = max(frac_up, frac_down)
#             if max_frac > id_variation_value:
#                 id_variation_value = max_frac
#         else:
#             print(f"Warning: Nominal signal yield for mass {mass} is non-positive ({var_nominal}), skipping trigger SF systematic for this mass point.")
#     else:
#         print(f"Warning: Missing variables for mass {mass}: nominal={w_var_nominal}, up={w_var_up}, down={w_var_down}. Skipping trigger SF systematic for this mass point.")

# print(f"Determined trigger SF systematic lnN value: {id_variation_value:.4f}")
# cb.cp().signals().AddSyst(cb, 'triggerSF_syst', 'lnN', ch.SystMap()(id_variation_value))

syst_map = ch.SystMap("era", "mass")
for mass in masses:
    down, up = id_syst_for_mass(float(mass), args.era, variation="trigger")
    syst_map = syst_map([args.era], [mass], (down, up))

# cb.cp().signals().AddSyst(cb, "triggerSF_syst", "lnN", syst_map)
cb.cp().signals().AddSyst(cb, "CMS_eff_trigger_e", "lnN", syst_map)

# Reco SF
syst_map = ch.SystMap("era", "mass")
for mass in masses:
    down, up = id_syst_for_mass(float(mass), args.era, variation="reco")
    syst_map = syst_map([args.era], [mass], (down, up))

# cb.cp().signals().AddSyst(cb, "recoSF_syst", "lnN", syst_map)
cb.cp().signals().AddSyst(cb, "CMS_eff_e_reco", "lnN", syst_map)


# Scale and smearing
if args.withSyst:
    print(f"DEBUG: adding systematic on signal scale for signal processes: {sig_procs}")    
    # add a "param" systematic (gaussian distributed with mean = 0 and sigma = 1)
    # cb.cp().process(sig_procs).AddSyst(cb, 'sigma_nuisance', 'shape', ch.SystMap()(1.0))
    # NOTE: can't get param only to get added, so doing that manually using AddDatacardLineAtEnd
    # cb.AddDatacardLineAtEnd("mean_nuisance_electronScaleVariation      param 0 1")
    cb.AddDatacardLineAtEnd("CMS_scale_e      param 0 1")   

# Signal modelling shape uncertainty
if args.withSyst:
    # for par in ["sigma", "alphaL", "alphaR", "nL", "nR"]:
    for par in ["sigma"]:
        # cb.AddDatacardLineAtEnd(f"{par}_nuisance_stat_{args.era}      param 0 1")
        cb.AddDatacardLineAtEnd(f"CMS_EXO25020_signalModel{par.capitalize()}Nuisance_{args.era}      param 0 1")

# # Discrete nuisance parameter for discrete profiling ("pdf_index")
# cb.cp().backgrounds().AddSyst(cb, 'bkg_func_choice', 'discrete', ch.SystMap()(1))

# Luminosity uncertainty
lumi1_uncertainties_by_era = {
    "2022" : 1.0138,
    "2022EE" : 1.0138,
    "2023" : 1.0117,
    "2023BPix" : 1.0117,
}
lumi2_uncertainties_by_era = {
    "2023" : 1.0127,
    "2023BPix" : 1.0127,
}

cb.cp().signals().AddSyst(cb, 'lumi_1', 'lnN', ch.SystMap()(lumi1_uncertainties_by_era[args.era]))
if args.era in lumi2_uncertainties_by_era:
    cb.cp().signals().AddSyst(cb, 'lumi_2', 'lnN', ch.SystMap()(lumi2_uncertainties_by_era[args.era]))

for bkg in all_bkg_procs:
    param_name = f"CMS_EXO25020_bkgScale_{bkg}_{era}"

    # 1. Add rateParam with initial value 1.0 (float)
    cb.cp().process([bkg]).era([era]).AddSyst(
        cb, param_name, "rateParam", ch.SystMap("era", "process")([era], [bkg], 1.0)
    )

    # 2. Set the parameter range in CombineHarvester's parameter container
    cb.GetParameter(param_name).set_range(0.0, 10.0)
  
print('>> Extracting shapes...')
# Update with actual root file and object naming convention
for era in eras:
    for chn in chns:
        if args.cat == "inclusive":
            suffix = f"_{era}"
        else:
            suffix = f"_cat_$BIN_{era}"

        # cb.ExtractData("w", f"$PROCESS{suffix}")
        cb.ExtractData("w", f"$PROCESS")

        cb.ExtractPdfs(
            cb.cp().channel([chn]).era([era]).backgrounds(),
            "w", f'$PROCESS{suffix}', f'$PROCESS{suffix}_$SYSTEMATIC'
        )

        cb.ExtractPdfs(
            cb.cp().channel([chn]).era([era]).signals(),
            "w", f'$PROCESS_M$MASS{suffix}', f'$PROCESS_M$MASS{suffix}_$SYSTEMATIC'
        )

print('>> Setting rate values...')
cb.ForEachProc(lambda p: p.set_rate(-1))

# get signal process rates from the workspace (saved as Zd_MX_expected)
# cb.cp().signals().ForEachProc(lambda p: p.set_rate(
#     w.var(f'Zd_M{p.mass()}_cat_{p.bin()}_expected').getValV() * lumi.getValV()/7.98
# ))

signal_yield_scaling = 1 * args.signal_multiplier if args.data else lumi.getValV()/7.98 * args.signal_multiplier 
cb.cp().signals().ForEachProc(lambda p: p.set_rate(
    w.var(f'Zd_cat_{p.bin()}_M{p.mass()}_expected_{p.era()}').getValV() * signal_yield_scaling if args.cat != "inclusive" else
    w.var(f'Zd_M{p.mass()}_expected_{p.era()}').getValV() * signal_yield_scaling 
))

# check that #expected signal is positive in every bin; throw error otherwise
cb.cp().signals().ForEachProc(lambda p:
    (p.rate() > 0) or
    (_ := (_ for _ in ()).throw(RuntimeError(f"Error: Expected signal yield for process {p.process()} in bin {p.bin()} is non-positive: {p.rate()}")))
)

# get background process rates from the workspace (saved as jpsi_expected, psi2s_expected, etc.)
for era in eras:
    for chn in chns:
        for cat in [cat[1] for cat in cats[chn+"_"+era]]:
            if args.cat == "inclusive":
                suffix = f"_{era}"
            else:
                suffix = f"_cat_{cat}_{era}"

            # # FIRST APPROACH: Use expected jpsi value (NO CATEG. FRACTION) and rescale empirically
            # n_jpsi = w.var(f'jpsi{suffix}_expected').getValV() * lumi.getValV()/7.98  # lumi rescale
            # cb.cp().channel([chn]).era([era]).bin([cat]).process(['jpsi']).ForEachProc(lambda p: p.set_rate(n_jpsi))
            # cb.cp().channel([chn]).era([era]).bin([cat]).process(['psi2s']).ForEachProc(lambda p: p.set_rate(n_jpsi / 10))
            # cb.cp().channel([chn]).era([era]).bin([cat]).process(['dy']).ForEachProc(lambda p: p.set_rate(n_jpsi / 3))

            # SECOND APPROACH: numbers are empirical and estimated from data maximum
            # n_jpsi = w.var(f"njpsi{suffix}").getValV()
            # n_psi2s = w.var(f"npsi2s{suffix}").getValV()
            # n_dy = w.var(f"nbkg{suffix}").getValV()

            # cb.cp().channel([chn]).era([era]).bin([cat]).process(['jpsi']).ForEachProc(lambda p: p.set_rate(n_jpsi))
            # cb.cp().channel([chn]).era([era]).bin([cat]).process(['psi2s']).ForEachProc(lambda p: p.set_rate(n_psi2s))
            # cb.cp().channel([chn]).era([era]).bin([cat]).process(['dy']).ForEachProc(lambda p: p.set_rate(n_dy))
            
            # for bkg_proc in bkg_procs["ee"]:
            #     n_proc = w.var(f"n{bkg_proc}{suffix}").getValV()
            #     cb.cp().channel([chn]).era([era]).bin([cat]).process([bkg_proc]).ForEachProc(lambda p: p.set_rate(n_proc))

            
            m_var = w.var("mass")
            mass_set = R.RooArgSet(m_var)

            parent_min = m_var.getMin()
            parent_max = m_var.getMax()

            for mass in masses:
                for bkg_proc in bkg_procs_per_mass[mass]['ee']:
                    n_proc_full = w.var(f"n{bkg_proc}{suffix}").getValV()

                    # Retrieve the process PDF (e.g. dy_2022, jpsi_cat_0_2022, etc.)
                    pdf_name = f"{bkg_proc}{suffix}"
                    pdf = w.pdf(pdf_name)
                    if not pdf:
                        # Fallback to process name without suffix if not found
                        pdf = w.pdf(bkg_proc)

                    sig_sigma_var = w.obj(f"sigma_test_M{mass.replace('.', 'p')}_{era}")
                    sigma = sig_sigma_var.evaluate() if sig_sigma_var else 0.02 * float(mass)

                    m_val = float(mass)
                    # raw_min = m_val - 5.0 * sigma
                    # raw_max = m_val + 5.0 * sigma
                    raw_min = CUSTOM_MASS_MIN
                    raw_max = CUSTOM_MASS_MAX

                    # Clamp boundaries strictly within the original observable range
                    window_min = max(parent_min, raw_min)
                    window_max = min(parent_max, raw_max)

                    # 1. Define temporary named range on the mass observable
                    range_name = f"range_{bkg_proc}_M{mass.replace('.', 'p')}"
                    m_var.setRange(range_name, window_min, window_max)

                    # 2. Compute the exact fraction of the PDF contained in [window_min, window_max]
                    if pdf:
                        int_obj = pdf.createIntegral(
                            mass_set,
                            R.RooFit.NormSet(mass_set),
                            R.RooFit.Range(range_name),
                        )
                        scale_fraction = int_obj.getVal()
                    else:
                        raise RuntimeError(f"Error: PDF for process {bkg_proc} not found in workspace for era {era} and suffix {suffix}. Cannot compute integral fraction.")
                        # # Fallback if PDF lookup fails
                        # full_width = float(region_mass_ranges[args.region]["max"]) - float(
                        #     region_mass_ranges[args.region]["min"]
                        # )
                        # scale_fraction = (6.0 * sigma) / full_width

                    # Guard against zero or floating-point precision artifacts
                    scale_fraction = max(1e-6, min(1.0, scale_fraction))
                    local_rate = n_proc_full * scale_fraction

                    print(
                        f"DEBUG: rescaled {bkg_proc} (M{mass}, {era}, {cat}): "
                        f"full={n_proc_full:.1f} -> local={local_rate:.1f} "
                        f"(integral fraction: {scale_fraction:.4e})"
                    )

                    # 3. Apply to this specific mass point
                    cb.cp().channel([chn]).era([era]).bin([cat]).mass([mass]).process(
                        [bkg_proc]
                    ).ForEachProc(lambda p, r=local_rate: p.set_rate(r))

print('>> Setting standardised bin names...')
ch.SetStandardBinNames(cb)

# writer = ch.CardWriter('$TAG/$MASS/$ANALYSIS_$BIN.txt',
#                        '$TAG/common/$ANALYSIS_$BIN.input.root')

writer = ch.CardWriter('$TAG/$MASS/$ANALYSIS_$CHANNEL_$BINID_$ERA.txt',
                       '$TAG/$MASS/$ANALYSIS_$CHANNEL_$ERA.input.root')

# # write single datacard for all channels
# cb.mass(["*"]).WriteDatacard('cards/cmb.txt', 'cards/cmb.input.root')

sample_cards_suffix = "_data" if args.data else ""

subfolder = "" if args.folder_tag == "" else f"{args.folder_tag}/"
outfolder = f"cards/{subfolder}cards_{args.region}{sample_cards_suffix}"

if args.no_reweight:
    outfolder += "_noReweight"
    
if args.tag != "":
    outfolder += f"_{args.tag}"

outfolder += binned_suffix

# create subfolder if it doesn't exist
if not os.path.exists(outfolder):
    os.makedirs(outfolder, exist_ok=True)

print('>> Creating per-mass sliced input workspaces and updating card observations...', flush=True)
# 1. Update observations per mass point
for mass in masses:
    for era in eras:
        for chn in chns:
            # Create the sliced workspace in memory
            sliced_ws = create_sliced_mass_workspace(w, mass, era, chn)
            
            # Update CombineHarvester observation rate for this mass
            sliced_data = sliced_ws.data("data_obs")
            sliced_obs_yield = sliced_data.sumEntries()
            print(f"DEBUG: trying to change observed yield for mass {mass} to {sliced_obs_yield}")
            cb.cp().channel([chn]).era([era]).mass([mass]).ForEachObs(
                lambda obs, y=sliced_obs_yield: obs.set_rate(y)
            )

# 2. Write the text datacards (will NOT touch any .root files)
print(f'>> Writing datacards to folder: {outfolder}', flush=True)
writer.WriteCards(f'{outfolder}/cmb', cb)
for chn in cb.channel_set():
    for bin in cb.cp().channel([chn]).bin_set():
        writer.WriteCards(f'{outfolder}/{chn}', cb.cp().channel([chn]).bin([bin]))

# 3. Write the sliced workspaces to the respective mass folders
print('>> Writing sliced .input.root files...', flush=True)
for mass in masses:
    for era in eras:
        for chn in chns:
            mass_dir = os.path.join(outfolder, chn, mass)
            os.makedirs(mass_dir, exist_ok=True)
            target_path = os.path.join(mass_dir, f"Xee_{chn}_{era}.input.root")
            
            # Recreate or save the sliced workspace
            sliced_ws = create_sliced_mass_workspace(w, mass, era, chn)
            sliced_ws.writeToFile(target_path, True)

#######################################
######## CONVERT TO WORKSPACES ########
#######################################

# Also run text2workspace on the written datacards
print('>> Converting datacards to workspaces...')

def convert_datacard_to_workspace(job):
    """Helper function to convert a single datacard to workspace."""
    datacard_path = job["datacard_path"]
    workspace_path = datacard_path.replace(".txt", ".root")
    
    try:
        cmd = ["text2workspace.py", datacard_path, "-o", workspace_path]
        proc = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        return (True, f"OK: {datacard_path}")
    except subprocess.CalledProcessError as e:
        return (False, f"FAILED: {datacard_path} - {str(e)}")

# Collect all datacard paths
all_datacard_jobs = []
for mass in masses:
    # only process relevant mass points for region
    if not is_mass_in_region(mass, args.region):
        continue
    for era in eras:
        for chn in chns:
            cat_ids = [cat[0] for cat in cats[chn+"_"+era]]
            for cat_id in cat_ids:
                datacard_path = f'{outfolder}/{chn}/{mass}/Xee_{chn}_{cat_id}_{era}.txt'
                all_datacard_jobs.append({
                    "datacard_path": datacard_path,
                    "mass": mass,
                    "era": era,
                    "channel": chn,
                    "cat_id": cat_id,
                })

if all_datacard_jobs:
    # retrieve nproc
    n_proc = os.cpu_count() or 1
    n_workers = min(n_proc, len(all_datacard_jobs))  # default to 8 workers
    print(f'>> Using {n_workers} parallel workers for {len(all_datacard_jobs)} datacards')
    
    completed = 0
    failed = 0
    start_time = time.perf_counter()
    
    with ThreadPoolExecutor(max_workers=n_workers) as executor:
        futures = {executor.submit(convert_datacard_to_workspace, job): job for job in all_datacard_jobs}
        for future in as_completed(futures):
            try:
                success, msg = future.result()
                if success:
                    completed += 1
                    if completed % 50 == 0:
                        print(f'  >> Progress: {completed}/{len(all_datacard_jobs)} completed, {failed} failed', flush=True)
                else:
                    failed += 1
                    print(f'  >> {msg}', flush=True)
            except Exception as e:
                failed += 1
                print(f'  >> EXCEPTION: {str(e)}', flush=True)
    
    elapsed = time.perf_counter() - start_time
    print(f'>> Datacard conversion complete: {completed} succeeded, {failed} failed in {elapsed:.1f}s', flush=True)

print('>> Done!')

