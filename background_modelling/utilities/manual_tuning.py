import ROOT
import numpy as np

f = ROOT.TFile.Open("../dataset_minbias_full.root")
w = f.Get("w")

# turn on batch mode
ROOT.gROOT.SetBatch(True)

# retrieve 
data = w.obj("data")
m = w.obj("mass_test")

m.setRange("unblinded", 1.8, 4.2)
m.setRange("unblinded", 0, 2)

# make fourht degree polynomial
polynomial_degree = 4
mins = [-1 if i == 1 or i == 3 else 0 for i in range(polynomial_degree)]
inits = [-0.9, 3.2, -1.4, 0.16, 0.00001, 0.000001]
for i in range(polynomial_degree):
    w.factory(f"bnew{i}[{inits[i]}, -5, 5]")    # Polynomial coefficients

bkg = ROOT.RooPolynomial("bkg", "bkg", m, ROOT.RooArgList([w.obj(f"bnew{i}") for i in range(polynomial_degree)]), lowestOrder=1)
# bkg = ROOT.RooGenericPdf("bkg", "(1 + @0*@1 + @0**2 * @2 + @0**3 * @3 + @0**4 * @4 ) > 0 ? (1 + @0*@1 + @0**2 * @2 + @0**3 * @3 + @0**4 * @4 ) : 1e-6", ROOT.RooArgList([m] + [w.obj(f"bnew{i}") for i in range(polynomial_degree)]))

bkg.fitTo(data, ROOT.RooFit.Range("sidebandL,sidebandC,sidebandR"))

# plot data and bkg
canvas = ROOT.TCanvas("canvas", "canvas", 800, 600)
xmin, xmax = m.getRange("unblinded")
frame = m.frame(xmin, xmax)
data.plotOn(frame, ROOT.RooFit.Name("data"))
bkg.plotOn(frame, ROOT.RooFit.LineColor(ROOT.kRed), ROOT.RooFit.Name("bkg"), ROOT.RooFit.Range("unblinded"), ROOT.RooFit.NormRange("sidebandL,sidebandC,sidebandR"))
bkg.paramOn(frame)


frame.Draw()
# set log scale
canvas.SetLogy()
canvas.SaveAs("bkg_tuning.png")