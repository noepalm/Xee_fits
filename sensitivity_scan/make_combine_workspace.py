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
args = parser.parse_args()


cb = ch.CombineHarvester()
# increase verbosity for debugging
cb.SetVerbosity(5)

input_dir = '/eos/home-n/npalmeri/DiEleAnalyzer/Xee_fits/background_modelling/oo_refactoring/datasets/'
# input_dir = '/eos/home-n/npalmeri/DiEleAnalyzer/Xee_fits/background_modelling/datasets/forPresentation_11062025/'

# add workspace
f = R.TFile.Open(input_dir + "dataset_minbias_full.root", "READ")
w = f.Get("w")

# Need to generate initial workspace with the correct mass range
m = w.var("mass")
m.setMin(2.0)
m.setMax(4.2)
w.RecursiveRemove(w.var("mass"))
w.Import(m, R.RooFit.RenameVariable("mass", "mass"))

# # also remove all references to mass_test (possibly disruptive, just to be safe)
# w.RecursiveRemove(w.var("mass_test"))

# CHANGE DATASET RANGE: ONLY KEEP BINS BETWEEN 2 AND 4.2
data = w.data("data_obs")
data = data.reduce(R.RooFit.Cut(f"mass > 2 && mass < 4.2"))
data.Print()
w.RecursiveRemove(w.data("data_obs"))
w.Import(data)

# w.Import(data, R.RooCmdArg())

cb.AddWorkspace(w)

# Basic configuration
chns = ['ee']
eras = ['2023']
era_energy = '13p6TeV'

bkg_procs = {
  'ee': ['dy', 'jpsi', 'psi2s']
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
cb.cp().process(['dy', 'jpsi']).AddSyst(cb, 'scale_$PROCESS_$BIN', 'rateParam', ch.SystMap()(1.0))
cb.cp().process(['psi2s']).AddSyst(cb, 'scale_psi2s_$BIN', 'rateParam', ch.SystMap()(0.2))

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
#     w.var(f'Zd_M{p.mass()}_cat_{p.bin()}_expected').getValV() * 58.9/7.98
# ))


cb.cp().signals().ForEachProc(lambda p: p.set_rate(
    w.var(f'Zd_cat_{p.bin()}_M{p.mass()}_expected').getValV() * 58.9/7.98 if args.cat != "inclusive" else
    w.var(f'Zd_M{p.mass()}_expected').getValV() * 58.9/7.98
))

# get background process rates from the workspace (saved as jpsi_expected, psi2s_expected, etc.)
for era in eras:
    for chn in chns:
        for cat in [cat[1] for cat in cats[chn+"_"+era]]:
            if args.cat == "inclusive":
                suffix = ""
            else:
                suffix = f"_cat_{cat}"
            n_jpsi = w.var(f'jpsi{suffix}_expected').getValV() * 58.9/7.98  # lumi rescale
            
            cb.cp().channel([chn]).era([era]).bin([cat]).process(['jpsi']).ForEachProc(lambda p: p.set_rate(n_jpsi))

            # set psi2s to jpsi rate/10
            cb.cp().channel([chn]).era([era]).bin([cat]).process(['psi2s']).ForEachProc(lambda p: p.set_rate(n_jpsi / 10))

            # set dy rate to 1/3 of jpsi rate
            cb.cp().channel([chn]).era([era]).bin([cat]).process(['dy']).ForEachProc(lambda p: p.set_rate(n_jpsi / 3))

print('>> Setting standardised bin names...')
ch.SetStandardBinNames(cb)

# writer = ch.CardWriter('$TAG/$MASS/$ANALYSIS_$BIN.txt',
#                        '$TAG/common/$ANALYSIS_$BIN.input.root')

writer = ch.CardWriter('$TAG/$MASS/$ANALYSIS_$CHANNEL_$BINID_$ERA.txt',
                       '$TAG/common/$ANALYSIS_$CHANNEL.input.root')


# # write single datacard for all channels
# cb.mass(["*"]).WriteDatacard('cards/cmb.txt', 'cards/cmb.input.root')

writer.WriteCards('cards/cmb', cb)
for chn in cb.channel_set():
    for bin in cb.cp().channel([chn]).bin_set():
        # Write cards for each channel and bin
        writer.WriteCards(f'cards/{chn}', cb.cp().channel([chn]).bin([bin]))

print('>> Done!')
