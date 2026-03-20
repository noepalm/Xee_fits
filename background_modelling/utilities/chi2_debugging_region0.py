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

# ALTERNATIVE: build RooRealSumPdf from all components; compare to RooAddPdf
bkg_components = ROOT.RooArgList([dy, phi, omega, eta])
ordered_list = ["ndy", "nphi", "nomega", "neta"]
neta = bkg_all.getParameters(m).find("neta")
nphi = bkg_all.getParameters(m).find("nphi")
nomega = bkg_all.getParameters(m).find("nomega")
ndy = bkg_all.getParameters(m).find("ndy")



bkg_coeffs = ROOT.RooArgList([ndy, nphi, nomega, neta])
bkg_sum = ROOT.RooRealSumPdf("bkg_sum", "Sum of bkg components", bkg_components, bkg_coeffs)

# plot data and bkg
canvas = ROOT.TCanvas("canvas", "canvas", 800, 600)
# use region0 range for frame
frame = m.frame(0.17, 2)

data.plotOn(frame, ROOT.RooFit.Name("data"))
# plot overall bkg

bkg_all.plotOn(frame, ROOT.RooFit.LineColor(ROOT.kBlue), ROOT.RooFit.Name("bkg_all"))
# bkg_sum.plotOn(frame, ROOT.RooFit.LineColor(ROOT.kGreen), ROOT.RooFit.Name("bkg_sum"))

# # COMPUTE AND PRINT CHI2 between data and full bkg model
# chi2 = frame.chiSquare("bkg_all", "data", 1)
ndf = data.numEntries() - bkg_all.getParameters(m).getSize()
# print(f"Chi2 / ndf = {chi2:.2f} / {ndf} = {chi2/ndf:.2f}")

print("ALTERNTAIVE: Chi2 between data and bkg_sum")
chi2_sum = frame.chiSquare("bkg_sum", "data", 1)
print(f"Chi2 / ndf = {chi2_sum:.2f} / {ndf} = {chi2_sum/ndf:.2f}")

# EVAL FUNCTION VALUES AT SPECIFIC POINTS
points_to_eval = [0.21, 0.22, 0.25475]
for point in points_to_eval:
    m.setVal(point)
    bkg_val = bkg_sum.getVal(ROOT.RooArgSet(m))
    print("###################")
    print(f"DEBUG: bkg_sum at m={point} GeV: {bkg_val}")

frame.Draw()
frame.SetMinimum(1)

# draw vertical line at 0.21
line = ROOT.TLine(0.22, frame.GetMinimum(), 0.22, frame.GetMaximum())
line.SetLineColor(ROOT.kBlue)
line.SetLineStyle(ROOT.kDashed)
line.SetLineWidth(2)
line.Draw()

line = ROOT.TLine(0.25475, frame.GetMinimum(), 0.25475, frame.GetMaximum())
line.SetLineColor(ROOT.kRed)
line.SetLineStyle(ROOT.kDashed)
line.SetLineWidth(2)
line.Draw()


# set log scale
canvas.SetLogy()
canvas.SaveAs("chi2_debugging.png")