import ROOT
import numpy as np

f = ROOT.TFile.Open("../datasets/dataset_data_region2_binned_data_altbkg_poly_full.root")
w = f.Get("w")

# turn on batch mode
ROOT.gROOT.SetBatch(True)

# retrieve 
data = w.obj("data_obs")
m = w.obj("mass")

# non-resonant background
dy = w.obj("dy")
upsilon = w.obj("upsilon1s_resonant_bkg")

bkg_all = w.obj("full_bkg_model")

# retrieve all parameters of dy function
params = dy.getParameters(m)
print("Fitted parameters:")
for par in params:
    print(f" - {par.GetName()} = {par.getVal():.4f} +/- {par.getError():.4f}")

    # if par.GetName() == "b0":
    #     par.setVal(2) #0
    # if par.GetName() == "b1":
    #     par.setVal(-0.3) #0.06
    # if par.GetName() == "b2":
    #     par.setVal(0.012) #-0.3
    # if par.GetName() == "b3":
    #     par.setVal(-0.00035) #1.497
    # if par.GetName() == "b4":
    #     par.setVal(0.0002) #1.497

    if par.GetName() == "b0":
        par.setVal(-0.1) #0
    if par.GetName() == "b1":
        par.setVal(-0.0023) #0.06
    if par.GetName() == "b2":
        par.setVal(1e-4) #-0.3
    if par.GetName() == "b3":
        par.setVal(6e-6) #1.497
    if par.GetName() == "b4":
        par.setVal(2e-6) #1.497


params = bkg_all.getParameters(m)
# for par in params:
#     if par.GetName() == "neta":
#         par.setVal(par.getValV() * 20)

# plot data and bkg
canvas = ROOT.TCanvas("canvas", "canvas", 800, 600)
# use region0 range for frame
frame = m.frame(ROOT.RooFit.Range("region0"))

data.plotOn(frame, ROOT.RooFit.Name("data"))
# plot overall bkg

# try fitting bkg_all to data
fit_result = bkg_all.fitTo(data, ROOT.RooFit.Range("region2"), ROOT.RooFit.Save(True))

# ######### CMS SHAPE TEST ###########

# # try building and fitting a RooCMSShape
# alpha = ROOT.RooRealVar("alpha", "alpha", 1.5, -5, 5)
# beta = ROOT.RooRealVar("beta", "beta", -0.3, -5, 5)
# gamma = ROOT.RooRealVar("gamma", "gamma", -0.3, -5, 5)
# peak = ROOT.RooRealVar("peak", "peak", 5, 2, 20)

# # define RooCMSShape pdf with the following formula:
# # Double_t RooCMSShape::evaluate() const {
# #   Double_t erf = RooMath::erfc((alpha - x) * beta);
# #   Double_t u = (x - peak) * gamma;

# #   if (u < -70)
# #     u = 1e20;
# #   else if (u > 70)
# #     u = 0;
# #   else
# #     u = exp(-u);  //exponential decay
# #   return erf * u;
# # }

# cmsshape_formula = "TMath::Erfc((@1 - @0) * @2) * TMath::Exp(-(@0 - @3) * @4)"
# # var order: m = @0, alpha = @1, beta = @2, peak = @3, gamma = @4
# cmsshape = ROOT.RooGenericPdf("cmsshape", "cmsshape", cmsshape_formula, ROOT.RooArgList(m, alpha, beta, peak, gamma))

# f_upsilon = ROOT.RooRealVar("frac_upsilon", "frac_upsilon", 0.1, 0, 1)
# bkg_all_new = ROOT.RooAddPdf("bkg_all_new", "bkg_all_new", ROOT.RooArgList(upsilon, cmsshape), ROOT.RooArgList(f_upsilon))

# bkg_all_new.fitTo(data, ROOT.RooFit.Range("region2"), ROOT.RooFit.Save(True))

# # plot total and components
# bkg_all_new.plotOn(frame, ROOT.RooFit.LineColor(ROOT.kBlue), ROOT.RooFit.Name("bkg_all_new"))
# # plot components from function names
# for component in ["upsilon1s_resonant_bkg", "cmsshape"]:
#     bkg_all_new.plotOn(frame, ROOT.RooFit.Components(component), ROOT.RooFit.LineStyle(ROOT.kDashed), ROOT.RooFit.LineColor(ROOT.kRed), ROOT.RooFit.Name(component))

# for param in bkg_all_new.getParameters(m):
#     print(f" - {param.GetName()} = {param.getVal():.4f} +/- {param.getError():.4f}")

# ######### END CMS SHAPE TEST ###########

bkg_all.plotOn(frame, ROOT.RooFit.LineColor(ROOT.kBlue), ROOT.RooFit.Name("bkg_all"))
# plot components from function names
for component in ["upsilon1s_resonant_bkg", "bkg_f1"]:
    bkg_all.plotOn(frame, ROOT.RooFit.Components(component), ROOT.RooFit.LineStyle(ROOT.kDashed), ROOT.RooFit.LineColor(ROOT.kRed), ROOT.RooFit.Name(component))

for param in bkg_all.getParameters(m):
    print(f" - {param.GetName()} = {param.getVal():.4g} +/- {param.getError():.4g}")

frame.Draw()
# set log scale
canvas.SetLogy()
canvas.SaveAs("bkg_tuning.png")