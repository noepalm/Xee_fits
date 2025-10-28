#!/usr/bin/env python

from __future__ import absolute_import
from __future__ import print_function
import CombineHarvester.CombineTools.ch as ch
import ROOT as R
import os
import numpy as np
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--cat', type=str, default='inclusive', choices=["inclusive", "eta", "dR"],
                    help='Which category to process')
parser.add_argument('--region', '-r', type=str, default='region1', choices=["region0", "region1", "region2"],
                    help='Which mass region to process (possibilities: region0: (0, 2), region1: (2, 4.6), region2: (4.6, 11))')
parser.add_argument('--no_reweight', action='store_true',
                    help='Use non-reweighted datasets (refers to trigger reweighting only -- applies to both signal and background modelling)')
parser.add_argument('--tag', type=str, default="",
                    help='Tag to append to output folder name')
parser.add_argument('--signal_multiplier', '-s', type=float, default=1.0,
                    help='Multiplier to apply to signal rates (for testing purposes)')
parser.add_argument('--bkg_x2', action='store_true',
                    help='Multiply background rates by 2 (for testing purposes)')
parser.add_argument('--bkg_div100', action='store_true',
                    help='Divide background rates by 100 (for testing purposes)')
parser.add_argument('--binned', action='store_true',
                    help='Use binned data')
args = parser.parse_args()

cb = ch.CombineHarvester()
# increase verbosity for debugging
cb.SetVerbosity(5)

input_dir = '/eos/home-n/npalmeri/DiEleAnalyzer/Xee_fits/background_modelling/oo_refactoring/datasets/without_region_overlap/' # datasets/without_region_overlap for old files
# input_dir = '/eos/home-n/npalmeri/DiEleAnalyzer/Xee_fits/background_modelling/datasets/forPresentation_11062025/'

if (args.bkg_x2 and not args.no_reweight):
    raise RuntimeError("Error: --bkg_x2 can currently only be used with --no_reweight")

# add workspace
binned_suffix = "_binned" if args.binned else ""
reweight_suffix = "_noReweight" if args.no_reweight else ""
bkg_scale_suffix = "_x2wgt" if args.bkg_x2 else ("_div100wgt" if args.bkg_div100 else "")

dataset_name = f"dataset_minbias_{args.region}{binned_suffix}{bkg_scale_suffix}{reweight_suffix}_full.root"
print(">> Using dataset:", dataset_name)

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
lumi = R.RooRealVar("luminosity", "luminosity", 58.9)
lumi.setConstant(True)
w.Import(lumi)

# w.Import(data, R.RooCmdArg())

cb.AddWorkspace(w)

# Basic configuration
chns = ['ee']
eras = ['2023']
era_energy = '13p6TeV'

if args.region == "region1":
    bkg_procs = {
        'ee': ['dy', 'jpsi', 'psi2s']
    }
elif args.region == "region2":
    bkg_procs = {
        'ee': ['dy', 'upsilon1s']
    }

sig_procs = ['Zd']

if args.cat == "eta":
    cats = {
        'ee_2023': [
            (0, 'etap0p6'),
            (1, 'etam0p6'),
        ]
    }
elif args.cat == "dR":
    cats = {
        'ee_2023': [
            (2, 'dRp0p3'),
            (3, 'dRm0p3'),
        ]
    }
elif args.cat == "inclusive":
    cats = {
        'ee_2023' : [
            (4, 'inclusive'),
        ]
    }

# masses = [f"{v:.1f}" for v in np.arange(0.1, 11.1, 0.1)]
masses = [f"{v:.1f}" for v in np.arange(0.5, 10.5, 0.1)]
# masses = ch.ValsFromRange('3.0:10.0|2.0') # can't specify number of digits after the point
# masses = [f"M{mass:.1f}".replace(".", "p") for mass in np.arange(0.5, 10.5, 0.2)] # for old model naming convention

print('>> Creating processes and observations...')

for era in eras:
    for chn in chns:
        cb.AddObservations( ['*'],  ['Xee'], [era], [chn],                  cats[chn+"_"+era]        )
        cb.AddProcesses(    ['*'],  ['Xee'], [era], [chn], bkg_procs[chn],  cats[chn+"_"+era], False )
        cb.AddProcesses(    masses, ['Xee'], [era], [chn], sig_procs,       cats[chn+"_"+era], True  )

print('>> Adding systematics...')

# # Luminosity uncertainty (flat 1%)
# cb.cp().AddSyst(cb, 'lumi_2023', 'lnN', ch.SystMap()(1.01))

# Add a rateParam for each background process (let the yield freely float)
# FOR OLD RATE APPROACH: use these inits
# cb.cp().process(['dy', 'jpsi']).AddSyst(cb, 'scale_$PROCESS_$BIN', 'rateParam', ch.SystMap()(1.0))
# cb.cp().process(['psi2s']).AddSyst(cb, 'scale_psi2s_$BIN', 'rateParam', ch.SystMap()(0.2))
cb.cp().process(bkg_procs['ee']).AddSyst(cb, 'scale_$PROCESS_$BIN', 'rateParam', ch.SystMap()(1.0))

print('>> Extracting shapes...')
# Update with actual root file and object naming convention
for era in eras:
    for chn in chns:
        if args.cat == "inclusive":
            suffix = ""
        else:
            suffix = "_cat_$BIN"

        cb.ExtractData("w", f"$PROCESS{suffix}")

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


cb.cp().signals().ForEachProc(lambda p: p.set_rate(
    w.var(f'Zd_cat_{p.bin()}_M{p.mass()}_expected').getValV() * lumi.getValV()/7.98 * args.signal_multiplier if args.cat != "inclusive" else
    w.var(f'Zd_M{p.mass()}_expected').getValV() * lumi.getValV()/7.98 * args.signal_multiplier
))

# get background process rates from the workspace (saved as jpsi_expected, psi2s_expected, etc.)
for era in eras:
    for chn in chns:
        for cat in [cat[1] for cat in cats[chn+"_"+era]]:
            if args.cat == "inclusive":
                suffix = ""
            else:
                suffix = f"_cat_{cat}"
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
                       '$TAG/common/$ANALYSIS_$CHANNEL.input.root')


# # write single datacard for all channels
# cb.mass(["*"]).WriteDatacard('cards/cmb.txt', 'cards/cmb.input.root')

outfolder = f"cards_{args.region}"

if args.no_reweight:
    outfolder += "_noReweight"
    
if args.tag != "":
    outfolder += f"_{args.tag}"

outfolder += binned_suffix

writer.WriteCards(f'{outfolder}/cmb', cb)
for chn in cb.channel_set():
    for bin in cb.cp().channel([chn]).bin_set():
        # Write cards for each channel and bin
        writer.WriteCards(f'{outfolder}/{chn}', cb.cp().channel([chn]).bin([bin]))

print('>> Done!')
