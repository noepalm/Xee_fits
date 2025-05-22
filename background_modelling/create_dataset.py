import ROOT
import os
import numpy as np
import argparse

# argparse
parser = argparse.ArgumentParser(description='Create a dataset from the input files.')
parser.add_argument('--use_jpsi', action='store_true', default = False, help='Use Jpsi sample instead of MinBias sample')
parser.add_argument('--use_reduced_mass', action='store_true', default = False, help='Use reduced mass instead of fitted mass')

args = parser.parse_args()

use_jpsi = args.use_jpsi
use_reduced_mass = args.use_reduced_mass

if use_jpsi:
    filepath = '/eos/home-n/npalmeri/www/DiElectron/background_model/PromptJpsi_tests/zsnap/era2022/base_7_ID'
else:
    filepath = '/eos/home-n/npalmeri/www/DiElectron/background_model/MinBias_tests/MinBias_skimmed/zsnap/era2022/base_7_ID/'

w = ROOT.RooWorkspace('w')

suffix = "" if not use_reduced_mass else "_reducedMass"
signal_ws_file = f'../signal_modelling/signal_model{suffix}.root'
signal_ws = ROOT.TFile.Open(signal_ws_file).Get('w')

m = signal_ws.var('mass_test')
w.Import(m, ROOT.RooCmdArg())

data = ROOT.RooDataSet('data', 'data', ROOT.RooArgSet(m))

# 1) create dataset out files there
for file in os.listdir(filepath):
    if file.endswith('.root'):
        print(file)
        f = ROOT.TFile.Open(os.path.join(filepath, file))
        tree = f.Get('Events')

        for i in range(tree.GetEntries()):  
            tree.GetEntry(i)
            # print(tree.SelectedDiEle_fitted_mass)
            # print(tree.GenZd_invMass)
            for val in tree.DiElectron_fitted_mass:
                m.setVal(val)
                data.add(ROOT.RooArgSet(m))

print(data)
w.Import(data, ROOT.RooCmdArg())

# 2) import signal models
models = {mass : signal_ws.obj(f"model_test_M{f'{mass:.1f}'.replace('.', 'p')}") for mass in np.concatenate([np.arange(0.5, 10.5, 0.5), [3.1, 3.7]])}
for mass, model in models.items():
    w.Import(model, ROOT.RooCmdArg())

# save workspace to file
sample_suffix = "_jpsi" if use_jpsi else "_minbias"
w.writeToFile(f'dataset{sample_suffix}{suffix}.root')