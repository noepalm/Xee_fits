#!/usr/bin/env python

from __future__ import absolute_import
from __future__ import print_function
import CombineHarvester.CombineTools.ch as ch
import ROOT as R
import os
import numpy as np

cb = ch.CombineHarvester()
# increase verbosity for debugging
cb.SetVerbosity(5)

input_dir = '../background_modelling/datasets/'
# input_dir = '../background_modelling/datasets/forPresentation_11062025/'

# add workspace
f = R.TFile.Open(input_dir + "dataset_minbias_binned_full.root", "READ")
w = f.Get("w")

# NOTE: CURRENTLY DOESN'T WORK
# Need to generate initial workspace with the correct mass range
m = w.var("mass")
m.setMin(2.0)
m.setMax(4.2)
w.RecursiveRemove(w.var("mass"))
w.Import(m, R.RooFit.RenameVariable("mass", "mass"))

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

cats = {
  'ee_2023': [ (0, 'ee_cat0') ]
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
cb.cp().process(['dy', 'jpsi']).AddSyst(cb, 'scale_$PROCESS', 'rateParam', ch.SystMap()(1.0))
cb.cp().process(['psi2s']).AddSyst(cb, 'scale_psi2s', 'rateParam', ch.SystMap()(0.1))

print('>> Extracting shapes...')
# Update with actual root file and object naming convention
for era in eras:
    for chn in chns:
        cb.ExtractData("w", "$PROCESS")

        cb.ExtractPdfs(
            cb.cp().channel([chn]).era([era]).backgrounds(),
            "w", '$PROCESS', '$PROCESS_$SYSTEMATIC'
        )

        cb.ExtractPdfs(
            cb.cp().channel([chn]).era([era]).signals(),
            "w", '$PROCESS_M$MASS', '$PROCESS_M$MASS_$SYSTEMATIC'
        )

print('>> Setting rate values...')
cb.ForEachProc(lambda p: p.set_rate(-1))

# get signal process rates from the workspace (saved as Zd_MX_expected)
cb.cp().signals().ForEachProc(lambda p: p.set_rate(
    w.var(f'Zd_M{p.mass()}_expected').getValV() * 58.9/7.98
))

# get background process rates from the workspace (saved as jpsi_expected, psi2s_expected, etc.)
cb.cp().process(["jpsi"]).ForEachProc(lambda p: p.set_rate(
    w.var('jpsi_expected').getValV() * 2 * 58.9/7.98 #minbias norm offset * lumi rescale
))

# set psi2s to jpsi rate/10
cb.cp().process(["psi2s"]).ForEachProc(lambda p: p.set_rate(
    w.var('jpsi_expected').getValV() / 10 * 2 * 58.9/7.98 #minbias norm offset * lumi rescale
))

# set dy rate to 1/3 of jpsi rate
cb.cp().process(["dy"]).ForEachProc(lambda p: p.set_rate(
    w.var('jpsi_expected').getValV() / 3 * 2 * 58.9/7.98 #minbias norm offset * lumi rescale
))

print('>> Setting standardised bin names...')
ch.SetStandardBinNames(cb)

writer = ch.CardWriter('$TAG/$MASS/$ANALYSIS_$CHANNEL_$BINID_$ERA.txt',
                       '$TAG/common/$ANALYSIS_$CHANNEL.input.root')

# # write single datacard for all channels
# cb.mass(["*"]).WriteDatacard('cards/cmb.txt', 'cards/cmb.input.root')

writer.WriteCards('cards/cmb', cb)
for chn in cb.channel_set():
    writer.WriteCards(f'cards/{chn}', cb.cp().channel([chn]))

print('>> Done!')
