import ROOT
import os

use_jpsi = False
suffix = "_jpsi" if use_jpsi else "_minbias"
f = ROOT.TFile.Open(f"datasets/dataset{suffix}.root")
w = f.Get("w")
data = w.obj("data")
m = w.obj("mass_test")

outfolder = "/eos/home-n/npalmeri/www/DiElectron/background_model/fit_tests"

# ----- FIT SIDEBANDS with ENVELOPE ----- #
# 1) fit each background model separately

# 4-th degree Bernstein polynomial
# w.factory("mass_test[5, 0, 11]")
for i in range(5):
    w.factory(f"a{i}[0.5, -1, 1]")    # Bernstein coefficients
    w.factory(f"b{i}[0, 1]")    # Polynomial coefficients
    w.factory("bb0[-1, -10, 10]")      # Exponential coefficient
    w.factory(f"c{i}[-2, -10, 10]")    # Exponential coefficients
    w.factory(f"cc{i}[1, -10, 10]")   # Exponential coefficients

bernstein_degree = 3
bkg_f0 = ROOT.RooBernstein("bkg_f0", "bkg_f0", m, ROOT.RooArgList([w.obj(f"a{i}") for i in range(bernstein_degree)]))

# 4-th degree polynomial times exponential
bkg_f1_poly = ROOT.RooPolynomial("bkg_f1_poly", "bkg_f1_poly", m, ROOT.RooArgList([w.obj(f"b{i}") for i in range(4)]))
bkg_f1_exp = ROOT.RooExponential("bkg_f1_exp", "bkg_f1_exp", m, w.obj("bb0"))
bkg_f1 = ROOT.RooProdPdf("bkg_f1", "bkg_f1", bkg_f1_poly, bkg_f1_exp)

f2_exp_degree = 4
bkg_f2_exps = []
for i in range(f2_exp_degree):
    bkg_f2_exps.append(ROOT.RooExponential(f"bkg_f2_exp{i}", f"bkg_f2_exp{i}", m, w.obj(f"c{i}")))
bkg_f2 = ROOT.RooAddPdf("bkg_f2", "bkg_f2", ROOT.RooArgList(bkg_f2_exps), ROOT.RooArgList([w.obj(f"cc{i}") for i in range(f2_exp_degree)]))

alpha = ROOT.RooRealVar("alpha", "alpha", -1.5, -10, 10)
bkg_f3 = ROOT.RooExponential("bkg_f3", "bkg_f3", m, alpha)

# 2) fit each model to the sidebands
# MUMU UNBLINDED RANGE: 2.6, 4.2
m.setRange("unblinded", 2, 4)
m.setRange("sidebandL", 2, 2.5)
m.setRange("sidebandC", 3.25, 3.5)
m.setRange("sidebandR", 3.8, 4)
m.setRange("jpsi", 2.5, 3.25)
m.setRange("psi2s", 3.5, 3.8)
# fit backgrounds to both sidebands
fitres_0 = bkg_f0.fitTo(data, ROOT.RooFit.Range("sidebandL,sidebandC,sidebandR"), ROOT.RooFit.Save())
fitres_1 = bkg_f1.fitTo(data, ROOT.RooFit.Range("sidebandL,sidebandC,sidebandR"), ROOT.RooFit.Save())
fitres_2 = bkg_f2.fitTo(data, ROOT.RooFit.Range("sidebandL,sidebandC,sidebandR"), ROOT.RooFit.Save())
fitres_3 = bkg_f3.fitTo(data, ROOT.RooFit.Range("sidebandL,sidebandC,sidebandR"), ROOT.RooFit.Save())
    

# 3) test S+B fit with bkg f4
# retrieve jpsi model
jpsi_model = w.obj("model_test_M3p1")
psi2s_model = w.obj("model_test_M3p7")

print(jpsi_model)
print(psi2s_model)

# create S+B model summing both signals
# sb_model = ROOT.RooAddPdf("sb_model", "sb_model", ROOT.RooArgList(jpsi_model, psi2s_model, bkg_f0), ROOT.RooArgList(ROOT.RooRealVar("nsig1", "nsig1", 1, 0, 10000), ROOT.RooRealVar("nsig2", "nsig2", 1, 0, 10000), ROOT.RooRealVar("nbkg", "bkg", 1, 0, 10000)), False)
normalizations = ["nsig1", "nsig2", "nbkg"]
initializations = [2e2, 1e1, 7e2]
mins = [2e2, 1e1, 4e2]
maxes = [1e4, 1e3, 1e4]
for var, init, min_, max_ in zip(normalizations, initializations, mins, maxes):
    w.factory(f"{var}[{init}, {min_}, {max_}]")

w.factory(f"fs1[0.4, 0, 1]") # fraction of jpsi
w.factory(f"fs2[0.005, 0, 1]") # fraction of psi2s
w.factory(f"fbkg[0.595, 0, 1]") # fraction of psi2s

fracs = ["fs1", "fs2", "fbkg"]

jpsi_model_extended = ROOT.RooExtendPdf("jpsi_model_extended", "jpsi_model_extended", jpsi_model, w.obj("nsig1"))
psi2s_model_extended = ROOT.RooExtendPdf("psi2s_model_extended", "psi2s_model_extended", psi2s_model, w.obj("nsig2"))
bkg_f3_extended = ROOT.RooExtendPdf("bkg_f3_extended", "bkg_f3_extended", bkg_f3, w.obj("nbkg"))

# sb_model = ROOT.RooAddPdf("sb_model", "sb_model", ROOT.RooArgList(jpsi_model, psi2s_model, bkg_f3), ROOT.RooArgList([w.obj(var) for var in normalizations]))
sb_model = ROOT.RooAddPdf("sb_model", "sb_model", ROOT.RooArgList(jpsi_model, psi2s_model, bkg_f0), ROOT.RooArgList([w.obj(var) for var in fracs]))
# sb_model = ROOT.RooAddPdf("sb_model", "sb_model", ROOT.RooArgList(jpsi_model_extended, psi2s_model_extended, bkg_f3_extended))
# sb_model = ROOT.RooAddPdf("sb_model", "sb_model", ROOT.RooArgList(bkg_f3), ROOT.RooArgList([w.obj(var) for var in normalizations[2:]]))

# sb_fitres = sb_model.fitTo(data, ROOT.RooFit.Range("unblinded"), ROOT.RooFit.Save(), ROOT.RooFit.Extended(True))

# 1) draw dataset around jpsi (2.5, 4.1 range)
# set batch mode
ROOT.gROOT.SetBatch(True)
# create canvas
canvas = ROOT.TCanvas("canvas", "canvas", 800, 600)

# plot dataset
xmin = 2 #2.5, 0
xmax = 4 #4.1, 11
frame = m.frame(xmin, xmax)
draw_args = [
    ROOT.RooFit.Name("data"),
    ROOT.RooFit.Binning(300),
    ROOT.RooFit.MarkerSize(0.5),
    # draw option as histogram
    ROOT.RooFit.DrawOption("HIST PLC"),
]
data.plotOn(frame, *draw_args, 
            ROOT.RooFit.Name("data"), 
            ROOT.RooFit.NormRange("unblinded"),
            # ROOT.RooFit.Rescale(1./(data.sumEntries() * frame.getFitRangeBinW()))
)

# plot background models
bkg_f0.plotOn(frame, ROOT.RooFit.LineColor(ROOT.kRed), ROOT.RooFit.Name("bkg_f0"), ROOT.RooFit.NormRange("sidebandL,sidebandC,sidebandR"))
bkg_f1.plotOn(frame, ROOT.RooFit.LineColor(ROOT.kBlue), ROOT.RooFit.Name("bkg_f1"), ROOT.RooFit.NormRange("sidebandL,sidebandC,sidebandR"))
bkg_f2.plotOn(frame, ROOT.RooFit.LineColor(ROOT.kGreen), ROOT.RooFit.Name("bkg_f2"), ROOT.RooFit.NormRange("sidebandL,sidebandC,sidebandR"))
bkg_f3.plotOn(frame, ROOT.RooFit.LineColor(ROOT.kOrange), ROOT.RooFit.Name("bkg_f3"), ROOT.RooFit.NormRange("sidebandL,sidebandC,sidebandR"))

# bkg_f0.paramOn(frame)
# bkg_f1.paramOn(frame)
# bkg_f2.paramOn(frame)
# bkg_f3.paramOn(frame)

# # plot S+B models
# sb_model.plotOn(frame, ROOT.RooFit.LineColor(ROOT.kBlack), ROOT.RooFit.Name("sb_model"), 
#                 ROOT.RooFit.NormRange("unblinded"))
#                 # ROOT.RooFit.Normalization(data.sumEntries(), ROOT.RooAbsReal.NumEvent))
# # plot components
# sb_model.plotOn(frame, ROOT.RooFit.Components("model_test_M3p1"), ROOT.RooFit.LineColor(ROOT.kRed), ROOT.RooFit.Name("jpsi_model"), ROOT.RooFit.NormRange("unblinded"))
# sb_model.plotOn(frame, ROOT.RooFit.Components("model_test_M3p7"), ROOT.RooFit.LineColor(ROOT.kBlue), ROOT.RooFit.Name("psi2s_model"), ROOT.RooFit.NormRange("unblinded"))
# sb_model.plotOn(frame, ROOT.RooFit.Components("bkg_f3"), ROOT.RooFit.LineColor(ROOT.kGreen), ROOT.RooFit.Name("bkg_f3"), ROOT.RooFit.NormRange("unblinded"))

# sb_model.paramOn(frame)

# draw frame
frame.Draw()
frame.GetXaxis().SetTitle("DiElectron mass [GeV]")
frame.GetYaxis().SetTitle("Events")

# plot legend
legend = ROOT.TLegend(0.6, 0.7, 0.9, 0.9)
legend.SetBorderSize(0)
legend.SetFillColor(0)
legend.SetTextSize(0.04)

legend.AddEntry(frame.findObject("data"), "Data", "p")
legend.AddEntry(frame.findObject("bkg_f0"), "Background model 0", "l")
legend.AddEntry(frame.findObject("bkg_f1"), "Background model 1", "l")
legend.AddEntry(frame.findObject("bkg_f2"), "Background model 2", "l")
legend.AddEntry(frame.findObject("bkg_f3"), "Background model 3", "l")
legend.Draw()

canvas.SaveAs(os.path.join(outfolder, f"dataset{suffix}.png"))
canvas.SaveAs(os.path.join(outfolder, f"dataset{suffix}.pdf"))

# set log scale 
canvas.SetLogy()

canvas.SaveAs(os.path.join(outfolder, f"dataset{suffix}_log.png"))
canvas.SaveAs(os.path.join(outfolder, f"dataset{suffix}_log.pdf"))
