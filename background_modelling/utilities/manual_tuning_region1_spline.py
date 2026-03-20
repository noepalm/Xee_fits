import ROOT
import numpy as np

f = ROOT.TFile.Open("../datasets/withSyst_scaleOnly/dataset_data_region1_binned_data_altbkg_chebyshev_withSyst_scaleOnly_full.root")
w = f.Get("w")

# turn on batch mode
ROOT.gROOT.SetBatch(True)

# retrieve 
data = w.obj("data_obs")
m = w.obj("mass")

# non-resonant background
dy = w.obj("dy")
jpsi = w.obj("jpsi_resonant_bkg")
psi2s = w.obj("psi2s_resonant_bkg")

bkg_all = w.obj("full_bkg_model")

# # make all dy parameters positive
# params = dy.getParameters(m)
# print("Fitted parameters:")
# for par in params:
#     par.setRange(0, 20)

# # multiply dy by exponential
# exp_coeff = ROOT.RooRealVar("exp_coeff", "Exponential Coefficient", -1, -10, 0)
# exp_func = ROOT.RooExponential("exp_func", "Exponential Function", m, exp_coeff)
# dy_exp = ROOT.RooProdPdf("bkg_f1", "DY multiplied by Exponential", ROOT.RooArgSet(dy, exp_func))

# bkg_all = ROOT.RooAddPdf("full_bkg_model_exp", "Full Background Model with Exponential DY", ROOT.RooArgList(jpsi, psi2s, dy_exp), 
#                         ROOT.RooArgList(w.obj("njpsi"), w.obj("npsi2s"), w.obj("ndy")))

# square dy function
dy_squared = ROOT.RooProdPdf("dy_squared", "DY Squared Function", ROOT.RooArgSet(dy, dy))

bkg_all = ROOT.RooAddPdf("full_bkg_model_exp", "Full Background Model with DY**2", ROOT.RooArgList(jpsi, psi2s, dy_squared), 
                        ROOT.RooArgList(w.obj("njpsi"), w.obj("npsi2s"), w.obj("ndy")))

# # create a RooNKeysPdf to replace dy
# print(f"DEBUG: data type = {type(data)}")
# # make histogram from data
# xmin, xmax = m.getMin(), m.getMax()
# h = data.createHistogram("mass", ROOT.RooFit.Binning(100, xmin, xmax))
# dy = ROOT.RooNDKeysPdf("dy_nkeys", "Drell-Yan NKeys PDF", ROOT.RooArgList([m]), h)

# # create new full bkg model with new dy
# bkg_all = ROOT.RooAddPdf("full_bkg_model_nkeys", "Full Background Model with NKeys DY", ROOT.RooArgList(jpsi, psi2s, dy), ROOT.RooArgList(
#     w.obj("njpsi"),
#     w.obj("npsi2s"),
#     w.obj("ndy"),
# ))

# fit bkg_all to data in region1
fit_result = bkg_all.fitTo(data, ROOT.RooFit.Range("region1"), ROOT.RooFit.Save(True), ROOT.RooFit.PrintLevel(-1))

# retrieve all parameters of dy function
params = dy.getParameters(m)
print("Fitted parameters:")
for par in params:
    print(f" - {par.GetName()} = {par.getVal():.4f} +/- {par.getError():.4f}")

    # if par.GetName() == "a0":
    #     par.setVal(0.0) #0
    # if par.GetName() == "a1":
    #     par.setVal(0.01) #0.06
    # if par.GetName() == "a2":
    #     par.setVal(-0.07) #-0.3
    # if par.GetName() == "a3":
    #     par.setVal(1.1) #1.497

params = bkg_all.getParameters(m)
for par in params:
    if par.GetName() == "neta":
        par.setVal(par.getValV() * 20)

# plot data and bkg
canvas = ROOT.TCanvas("canvas", "canvas", 800, 800)

# Create two pads for plot and residuals
pad1 = ROOT.TPad("pad1", "pad1", 0, 0.3, 1, 1.0)
pad1.SetBottomMargin(0.02)
pad1.Draw()

pad2 = ROOT.TPad("pad2", "pad2", 0, 0.0, 1, 0.3)
pad2.SetTopMargin(0.02)
pad2.SetBottomMargin(0.3)
pad2.Draw()

pad1.cd()

# use region0 range for frame
frame = m.frame(ROOT.RooFit.Range("region1"))

data.plotOn(frame, ROOT.RooFit.Name("data"))
# plot overall bkg

bkg_all.plotOn(frame, ROOT.RooFit.LineColor(ROOT.kBlue), ROOT.RooFit.Name("bkg_all"))
# plot components from function names
for component in ["jpsi_resonant_bkg", "psi2s_resonant_bkg", "dy_squared"]:
    bkg_all.plotOn(frame, ROOT.RooFit.Components(component), ROOT.RooFit.LineStyle(ROOT.kDashed), ROOT.RooFit.LineColor(ROOT.kRed), ROOT.RooFit.Name(component))

for param in bkg_all.getParameters(m):
    print(f" - {param.GetName()} = {param.getVal():.4f} +/- {param.getError():.4f}")

# Calculate chi2
chi2 = frame.chiSquare("bkg_all", "data")
print(f"Chi2/ndf: {chi2:.3f}")

frame.Draw()
# set log scale
pad1.SetLogy()

# Add chi2 text to frame
text = ROOT.TLatex()
text.SetNDC()
text.SetTextSize(0.04)
text.DrawLatex(0.15, 0.85, f"#chi^{{2}}/ndf = {chi2:.3f}")

pad1.Update()

# Draw residuals/pulls
pad2.cd()
pad2.SetGrid()

residuals = frame.pullHist("data", "bkg_all")
residuals.SetMarkerStyle(20)
residuals.SetMarkerSize(0.8)

frame_residuals = m.frame(ROOT.RooFit.Range("region1"))
frame_residuals.addPlotable(residuals, "P")
frame_residuals.SetTitle("")
frame_residuals.GetYaxis().SetTitle("Pulls")
frame_residuals.GetYaxis().SetTitleSize(0.1)
frame_residuals.GetYaxis().SetTitleOffset(0.4)
frame_residuals.GetYaxis().SetLabelSize(0.1)
frame_residuals.GetYaxis().SetNdivisions(505)
frame_residuals.GetXaxis().SetTitleSize(0.12)
frame_residuals.GetXaxis().SetLabelSize(0.1)
frame_residuals.GetXaxis().SetTitle("Mass [GeV]")
frame_residuals.SetMinimum(-5)
frame_residuals.SetMaximum(5)
frame_residuals.Draw()

# Add zero line
line = ROOT.TLine(frame_residuals.GetXaxis().GetXmin(), 0, frame_residuals.GetXaxis().GetXmax(), 0)
line.SetLineStyle(2)
line.SetLineColor(ROOT.kBlack)
line.Draw()

canvas.cd()
canvas.SaveAs("bkg_tuning.png")
canvas.SaveAs("bkg_tuning.pdf")