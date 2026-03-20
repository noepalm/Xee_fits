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
    "region0": {"min": 0.3, "max": 2.4},
    "region1": {"min": 1.6, "max": 4.6},
    "region2": {"min": 3.8, "max": 11.0},
}

def is_mass_in_region(mass, region):
    mass = float(mass)
    if region in region_mass_ranges:
        return region_mass_ranges[region]["min"] <= mass < region_mass_ranges[region]["max"]
    else:
        print("Warning: Invalid region specified for mass range check. Returning False.")
        return False

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
print(">> Using dataset:", dataset_name, flush = True)

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
    "2022" : 0.83,
    "2022EE" : 1.93,
    "2023" : 2.65,
    "2023BPix" : 1.27,
}
luminosity = luminosities[args.era] if args.data else 58.9
# luminosity = 6.68 if args.data else 58.9
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
    bkg_procs = {
        'ee': ['dy', 'jpsi', 'psi2s']
    }
elif args.region == "region2":
    bkg_procs = {
        'ee': ['dy', 'upsilon1s']
    }
elif args.region == "region0":
    bkg_procs = {
        'ee': ['dy', 'phi', 'omega']# 'eta']
    }
else:
    bkg_procs = {
        'ee': ['dy']
    }

if args.no_res:
    bkg_procs = {"ee": ['dy']}

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

masses = [f"{v:.1f}" for v in np.arange(0.1, 11.1, 0.1)]
# select subrange belonging to processed region
masses = [mass for mass in masses if is_mass_in_region(mass, args.region)]

# masses = [f"{v:.1f}" for v in np.arange(0.5, 10.5, 0.1)]
# masses = ch.ValsFromRange('3.0:10.0|2.0') # can't specify number of digits after the point
# masses = [f"M{mass:.1f}".replace(".", "p") for mass in np.arange(0.5, 10.5, 0.2)] # for old model naming convention

print('>> Creating processes and observations...')

for era in eras:
    for chn in chns:
        cb.AddObservations( ['*'],  ['Xee'], [era], [chn],                  cats[chn+"_"+era]        )
        cb.AddProcesses(    ['*'],  ['Xee'], [era], [chn], bkg_procs[chn],  cats[chn+"_"+era], False )
        cb.AddProcesses(    masses, ['Xee'], [era], [chn], sig_procs,       cats[chn+"_"+era], True  )

print('>> Adding systematics...')

# ID SF 
### first, determine highest variation across mass values AND between up/down
### apply worst case scenario as lnN uncertainty on signal yield
id_variation_value = 1.0
for mass in masses:
    w_var_nominal = w.var(f"Zd_M{mass}_expected_{args.era}")
    w_var_up = w.var(f"Zd_M{mass}_expected_electronID_up_{args.era}")
    w_var_down = w.var(f"Zd_M{mass}_expected_electronID_down_{args.era}")
    if w_var_nominal and w_var_up and w_var_down:
        var_nominal, var_up, var_down = w_var_nominal.getVal(), w_var_up.getVal(), w_var_down.getVal()
        if var_nominal > 0:
            frac_up = 1 + abs(1 - var_up/var_nominal)
            frac_down = 1 + abs(1 - var_down/var_nominal)
            max_frac = max(frac_up, frac_down)
            if max_frac > id_variation_value:
                id_variation_value = max_frac
        else:
            print(f"Warning: Nominal signal yield for mass {mass} is non-positive ({var_nominal}), skipping electron ID systematic for this mass point.")
    else:
        print(f"Warning: Missing variables for mass {mass}: nominal={w_var_nominal}, up={w_var_up}, down={w_var_down}. Skipping electron ID systematic for this mass point.")

print(f"Determined electron ID systematic lnN value: {id_variation_value:.4f}")
cb.cp().signals().AddSyst(cb, 'electronID_syst', 'lnN', ch.SystMap()(id_variation_value))

# Trigger SF 
### first, determine highest variation across mass values AND between up/down
### apply worst case scenario as lnN uncertainty on signal yield
id_variation_value = 1.0
for mass in masses:
    w_var_nominal = w.var(f"Zd_M{mass}_expected_{args.era}")
    w_var_up = w.var(f"Zd_M{mass}_expected_trigger_up_{args.era}")
    w_var_down = w.var(f"Zd_M{mass}_expected_trigger_down_{args.era}")
    if w_var_nominal and w_var_up and w_var_down:
        var_nominal, var_up, var_down = w_var_nominal.getVal(), w_var_up.getVal(), w_var_down.getVal()
        if var_nominal > 0:
            frac_up = 1 + abs(1 - var_up/var_nominal)
            frac_down = 1 + abs(1 - var_down/var_nominal)
            max_frac = max(frac_up, frac_down)
            if max_frac > id_variation_value:
                id_variation_value = max_frac
        else:
            print(f"Warning: Nominal signal yield for mass {mass} is non-positive ({var_nominal}), skipping trigger SF systematic for this mass point.")
    else:
        print(f"Warning: Missing variables for mass {mass}: nominal={w_var_nominal}, up={w_var_up}, down={w_var_down}. Skipping trigger SF systematic for this mass point.")

print(f"Determined trigger SF systematic lnN value: {id_variation_value:.4f}")
cb.cp().signals().AddSyst(cb, 'triggerSF_syst', 'lnN', ch.SystMap()(id_variation_value))

# Scale and smearing
if args.withSyst:
    print(f"DEBUG: adding systematic on signal scale for signal processes: {sig_procs}")    
    # add a "param" systematic (gaussian distributed with mean = 0 and sigma = 1)
    # cb.cp().process(sig_procs).AddSyst(cb, 'sigma_nuisance', 'shape', ch.SystMap()(1.0))
    # NOTE: can't get param only to get added, so doing that manually using AddDatacardLineAtEnd
    cb.AddDatacardLineAtEnd("mean_nuisance_electronScaleVariation      param 0 1")

# # Discrete nuisance parameter for discrete profiling ("pdf_index")
# cb.cp().backgrounds().AddSyst(cb, 'bkg_func_choice', 'discrete', ch.SystMap()(1))

# # Luminosity uncertainty (flat 1%)
# cb.cp().AddSyst(cb, 'lumi_2023', 'lnN', ch.SystMap()(1.01))

# Add a rateParam for each background process (let the yield freely float)
# FOR OLD RATE APPROACH: use these inits
# cb.cp().process(['dy', 'jpsi']).AddSyst(cb, 'scale_$PROCESS_$BIN', 'rateParam', ch.SystMap()(1.0))
# cb.cp().process(['psi2s']).AddSyst(cb, 'scale_psi2s_$BIN', 'rateParam', ch.SystMap()(0.2))

# # NEW APPROACH
# cb.cp().process(bkg_procs['ee']).AddSyst(cb, 'scale_$PROCESS_$BIN', 'rateParam', ch.SystMap()(1.0))

# NEW APPROACH + different min/max values
#FIXME: make min/max work with cb command (see attempts above)
for bkg in bkg_procs['ee']:
    for bins_tuple in cats[f'ee_{era}']:
        cb.AddDatacardLineAtEnd(f"scale_{bkg}_{bins_tuple[1]}_{era} rateParam *       {bkg}       1 [0,10]")

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

signal_yield_scaling = 1 if args.data else lumi.getValV()/7.98 * args.signal_multiplier 
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
            
            for bkg_proc in bkg_procs["ee"]:
                n_proc = w.var(f"n{bkg_proc}{suffix}").getValV()
                cb.cp().channel([chn]).era([era]).bin([cat]).process([bkg_proc]).ForEachProc(lambda p: p.set_rate(n_proc))

            

print('>> Setting standardised bin names...')
ch.SetStandardBinNames(cb)

# writer = ch.CardWriter('$TAG/$MASS/$ANALYSIS_$BIN.txt',
#                        '$TAG/common/$ANALYSIS_$BIN.input.root')

writer = ch.CardWriter('$TAG/$MASS/$ANALYSIS_$CHANNEL_$BINID_$ERA.txt',
                       '$TAG/common/$ANALYSIS_$CHANNEL_$ERA.input.root')

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

print(f'>> Writing datacards to folder: {outfolder}', flush = True)

writer.WriteCards(f'{outfolder}/cmb', cb)
for chn in cb.channel_set():
    for bin in cb.cp().channel([chn]).bin_set():
        # Write cards for each channel and bin
        writer.WriteCards(f'{outfolder}/{chn}', cb.cp().channel([chn]).bin([bin]))

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

