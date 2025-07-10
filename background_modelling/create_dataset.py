import ROOT
import os
import numpy as np
from scipy.optimize import curve_fit
import argparse

# argparse
parser = argparse.ArgumentParser(description='Create a dataset from the input files.')
parser.add_argument('--use_jpsi', action='store_true', default = False, help='Use Jpsi sample instead of MinBias sample')
parser.add_argument('--use_reduced_mass', action='store_true', default = False, help='Use reduced mass instead of fitted mass')

args = parser.parse_args()

use_jpsi = args.use_jpsi
use_reduced_mass = args.use_reduced_mass

if use_jpsi:
    # filepath = '/eos/home-n/npalmeri/www/DiElectron/background_model/fw_output/PromptJpsi_tests/zsnap/era2022/base_7_ID'
    filepath = '/eos/home-n/npalmeri/www/DiElectron/PS_reweighting/fw_output_Jpsi_reweight/zsnap/era2023/base_8_TriggerPSReweight/'
else:
    # filepath = '/eos/home-n/npalmeri/www/DiElectron/background_model/fw_output/MinBias_tests/MinBias_skimmed/zsnap/era2022/base_7_ID/'
    filepath = '/eos/home-n/npalmeri/www/DiElectron/PS_reweighting/fw_output_actualReweight/zsnap/era2023/base_8_TriggerPSReweight/'

w = ROOT.RooWorkspace('w')

suffix = "" if not use_reduced_mass else "_reducedMass"
# signal_ws_file = f'../signal_modelling/workspaces/signal_model{suffix}.root'
signal_ws_file = f'../signal_modelling/workspaces/signal_model_UpdatedSelection_withTriggerReweight{suffix}.root'
signal_ws = ROOT.TFile.Open(signal_ws_file).Get('w')

m = signal_ws.var('mass_test')
m.SetName("mass")
m.setMin(2.0)
m.setMax(4.2)
w.Import(m, ROOT.RooCmdArg())

dataset_args = [
    ROOT.RooArgSet(m),
]

# weight = 1 # for prompt jpsi dataset, do not reweight

# if not use_jpsi:
weightVar = ROOT.RooRealVar("weight", "weight", 1)
dataset_args.append(ROOT.RooFit.WeightVar(weightVar))    

data = ROOT.RooDataSet('data', 'data', *dataset_args)

# 1) create dataset out files there
for file in os.listdir(filepath):
    if file.endswith('.root') and "DoubleElectronNANO" not in file:
        print(file)
        f = ROOT.TFile.Open(os.path.join(filepath, file))
        tree = f.Get('Events')
        wgt = 1

        for i in range(tree.GetEntries()):  
            tree.GetEntry(i)
            wgt = tree.weight # weight includes expected events + trigger PS reweighting
            wgt *= 58.9/7.98 # 22+23 lumi rescale wrt processed
            # print(tree.SelectedDiEle_fitted_mass)
            # print(tree.GenZd_invMass)
            for val in tree.DiElectron_fitted_mass:
                m.setVal(val)
                data.add(ROOT.RooArgSet(m), wgt)

print(data)
# rename data variable to 'data_obs'
data.SetName("data_obs")
data = data.reduce(ROOT.RooFit.Cut(f"mass > 2 && mass < 4.2"))
w.Import(data, ROOT.RooCmdArg())

# 2) import signal models
masses_models = []
for model in signal_ws.allGenericObjects():
    if model.GetName().startswith('model_test_M'):
        w.Import(model, ROOT.RooFit.RenameVariable(model.GetName(), f'Zd_{model.GetName().split("_")[2].replace("p", ".")}'))
        masses_models.append(model.GetName().split("_")[2].replace("p", ".").replace("M", ""))

# 3) compute rate for each model and save normalization to workspace
## a) signal model

# -- Interpolate xsec, selection efficiency
masses = np.array([1, 3.1, 5, 5.5, 6, 6.5])
from utilities.get_signal_effs_xsecs import effs, effs_err, xsecs, xsecs_err
# effs = np.array([1.562, 14.010, 19.821, 20.552, 18.541, 11.550])/100 # %
# effs_err = np.array([0.055, 0.155, 0.179, 0.181, 0.2, 0.143])/100
# xsecs = np.array([3.396, 2.679, 1.952, 1.910, 1.865, 1.834]) # pb
# xsecs_err = np.array([0.01646, 0.0095, 0.003978, 0.003451, 0.001997, 0.001002])

# effs
popt_eff, _ = curve_fit(lambda x, a, b, c, d : np.polyval((a, b, c, d), x), masses, effs, sigma=effs_err, absolute_sigma=True)
# plot data and fit curve
x = np.linspace(np.min(masses), np.max(masses), 1000)
y = np.polyval(popt_eff, x)

# fit xsecs vs masses with polynomial
popt_xsec, _ = curve_fit(lambda x, a, b, c, d, e : np.polyval((a, b, c, d, e), x), masses, xsecs, sigma=xsecs_err, absolute_sigma=True)

# plot data and fit curve
x2 = np.linspace(np.min(masses), np.max(masses), 1000)
y2 = np.polyval(popt_xsec, x2)

for mass in masses_models:
    n_sgn_exp = 7.98 * 1e3 # luminosity (in pb-1)
    n_sgn_exp *= np.polyval(popt_eff, float(mass)) # selection efficiency (in %)
    n_sgn_exp *= np.polyval(popt_xsec, float(mass)) # xsec (in pb), interpolated

    # create RooRealVar for the expected number of signal events
    norm = ROOT.RooRealVar(f'Zd_M{mass}_expected', f'Zd_{mass}_expected', n_sgn_exp)
    # norm.setConstant(True)
    w.Import(norm, ROOT.RooCmdArg())

    # also save efficiency and xsec separately 
    eff_var = ROOT.RooRealVar(f'Zd_M{mass}_efficiency', f'Zd_{mass}_efficiency', np.polyval(popt_eff, float(mass)))
    eff_var.setConstant(True)
    w.Import(eff_var, ROOT.RooCmdArg())
    xsec_var = ROOT.RooRealVar(f'Zd_M{mass}_xsec', f'Zd_{mass}_xsec', np.polyval(popt_xsec, float(mass)))
    xsec_var.setConstant(True)
    w.Import(xsec_var, ROOT.RooCmdArg())

## b) jpsi, psi2s, background model
n_jpsi_exp = 7.98 * 1e3 # luminosity (in pb-1)
n_jpsi_exp *= 5.352e5 # xsec * filter eff (/pb)
n_jpsi_exp *= 5.971/100 # branching ratio Jpsi -> ee
n_jpsi_exp *= 0.677/100 # analyzer selection efficiency (no nano prod. skimming on this sample)
# n_jpsi_exp *= 7.94e-3 # branching ratio psi(2s) -> ee

norm_jpsi = ROOT.RooRealVar("jpsi_expected", "jpsi_expected", n_jpsi_exp)
w.Import(norm_jpsi, ROOT.RooCmdArg())

norm_psi2s = ROOT.RooRealVar("psi2s_expected", "psi2s_expected", n_jpsi_exp) # meh can just rescale later
w.Import(norm_psi2s, ROOT.RooCmdArg())

## c) minbias 
# retrieve sum of all dataset entries
n_minbias_exp = data.sumEntries()
data_obs_expected = ROOT.RooRealVar('data_obs_expected', 'data_obs_expected', n_minbias_exp)
# data_obs_expected.setConstant(True)
w.Import(data_obs_expected, ROOT.RooCmdArg())

# save workspace to file
sample_suffix = "_jpsi" if use_jpsi else "_minbias"
w.writeToFile(f'datasets/dataset{sample_suffix}{suffix}.root')