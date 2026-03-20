import ROOT
import numpy as np

f = ROOT.TFile.Open("../datasets/dataset_minbias_region0_debug_test_full.root")
w = f.Get("w")

# turn on batch mode
ROOT.gROOT.SetBatch(True)

# retrieve 
data = w.obj("data_obs")
m = w.obj("mass")

# non-resonant background
dy = w.obj("dy")
phi = w.obj("phi_resonant_bkg")
omega = w.obj("omega_resonant_bkg")
eta = w.obj("eta_resonant_bkg")

bkg_all = w.obj("full_bkg_model")

# retrieve all parameters of dy function
params = dy.getParameters(m)
print("Fitted parameters:")
for par in params:
    print(f" - {par.GetName()} = {par.getVal():.4f} +/- {par.getError():.4f}")

    # # FIRST SET
    # if par.GetName() == "a0":
    #     par.setVal(0.0) #0
    # if par.GetName() == "a1":
    #     par.setVal(0.055) #0.06
    # if par.GetName() == "a2":
    #     par.setVal(-0.25) #-0.3
    # if par.GetName() == "a3":
    #     par.setVal(1.497) #1.497

    if par.GetName() == "a0":
        par.setVal(0.0) #0
    if par.GetName() == "a1":
        par.setVal(0.01) #0.06
    if par.GetName() == "a2":
        par.setVal(-0.07) #-0.3
    if par.GetName() == "a3":
        par.setVal(1.1) #1.497


params = bkg_all.getParameters(m)
for par in params:
    if par.GetName() == "neta":
        par.setVal(par.getValV() * 20)

# plot data and bkg
canvas = ROOT.TCanvas("canvas", "canvas", 800, 600)
# use region0 range for frame
frame = m.frame(ROOT.RooFit.Range("region0"))

data.plotOn(frame, ROOT.RooFit.Name("data"))
# plot overall bkg

bkg_all.plotOn(frame, ROOT.RooFit.LineColor(ROOT.kBlue), ROOT.RooFit.Name("bkg_all"))
# plot components from function names
for component in ["phi_resonant_bkg", "omega_resonant_bkg", "eta_resonant_bkg", "bkg_f0"]:
    bkg_all.plotOn(frame, ROOT.RooFit.Components(component), ROOT.RooFit.LineStyle(ROOT.kDashed), ROOT.RooFit.LineColor(ROOT.kRed), ROOT.RooFit.Name(component))

for param in bkg_all.getParameters(m):
    print(f" - {param.GetName()} = {param.getVal():.4f} +/- {param.getError():.4f}")

frame.Draw()
# set log scale
canvas.SetLogy()
canvas.SaveAs("bkg_tuning.png")