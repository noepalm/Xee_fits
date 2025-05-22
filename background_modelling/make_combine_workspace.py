import ROOT
import os

use_jpsi = False
suffix = "_jpsi" if use_jpsi else "_minbias"
f = ROOT.TFile.Open(f"datasets/dataset{suffix}.root")
w = f.Get("w")
data = w.obj("data")
m = w.obj("mass_test")

w_bkg = ROOT.RooWorkspace("w_bkg")

w_bkg.Import(data)
w_bkg.Import(m)

m.setRange("Region2", 1.2, 2.6)
m.setRange("Region3", 4.2, 8)

# 4-th degree Bernstein polynomial
bernstein_degree = 4
for i in range(bernstein_degree):
    w.factory(f"a{i}_Region2[0.1, 0, 1]")
    w.factory(f"a{i}_Region3[-0.5, -1, 1]")

bernsteins = []
for region in ["Region2", "Region3"]:
    bkg_f0 = ROOT.RooBernstein(f"bkg_f0_{region}", f"bkg_f0_{region}", m, ROOT.RooArgList([w.obj(f"a{i}_{region}") for i in range(bernstein_degree)]))
    bkg_f0.fitTo(data, ROOT.RooFit.Range(region))
    # print post-fit parameters
    for i in range(bernstein_degree):
        print(f"a{i}_{region}: {w.obj(f'a{i}_{region}').getValV()} +/- {w.obj(f'a{i}_{region}').getError()}")
    w_bkg.Import(bkg_f0)

# manually create polynomial coefficients
polynomial_degree = 4
mins = [-1 if i < 4 and i != 1 else 0 for i in range(polynomial_degree)]
inits = [0.01, 0.5, 0.01, 0.001, 0.0001, 0.00001, 0.000001]
for region in ["Region2", "Region3"]:
    for i in range(polynomial_degree):
        w.factory(f"b{i}_{region}[{inits[i]}, {mins[i]}, 1]")    # Polynomial coefficients

    # 4-th degree polynomial times exponential
    bkg_f1_poly = ROOT.RooPolynomial(f"bkg_f1_poly_{region}", f"bkg_f1_poly_{region}", m, ROOT.RooArgList([w.obj(f"b{i}_{region}") for i in range(polynomial_degree)]))
    w.factory(f"bb0_{region}[-1, -10, 10]")      # Exponential coefficient
    bkg_f1_exp = ROOT.RooExponential(f"bkg_f1_exp_{region}", f"bkg_f1_exp_{region}", m, w.obj(f"bb0_{region}"))

    bkg_f1 = ROOT.RooProdPdf(f"bkg_f1_{region}", f"bkg_f1_{region}", bkg_f1_poly, bkg_f1_exp)
    bkg_f1.fitTo(data, ROOT.RooFit.Range(region))
    # print post-fit parameters
    for i in range(polynomial_degree):
        print(f"b{i}_{region}: {w.obj(f'b{i}_{region}').getValV()} +/- {w.obj(f'b{i}_{region}').getError()}")
    print(f"bb0_{region}: {w.obj(f'bb0_{region}').getValV()} +/- {w.obj(f'bb0_{region}').getError()}")
    w_bkg.Import(bkg_f1)

# Sum of exponentials
f2_exp_degree = 4

for region in ["Region2", "Region3"]:
    for i in range(f2_exp_degree):
        w.factory(f"cc{i}_{region}[{1./f2_exp_degree * (-1 * (i % 2))}, -1, 1]")   # Exponential coefficients

    exp_inits = [1, 4, 0.1, -1, 5]
    bkg_f2_exps = []
    for i in range(f2_exp_degree):
        w.factory(f"c{i}_{region}[{exp_inits[i]}, -10, 10]")   # Exponential coefficients
        bkg_f2_exps.append(ROOT.RooExponential(f"bkg_f2_exp{i}_{region}", f"bkg_f2_exp{i}_{region}", m, w.obj(f"c{i}_{region}")))

    # w.obj("c0").setConstant(True)
    # w.obj("c1").setConstant(True)

    bkg_f2 = ROOT.RooAddPdf(f"bkg_f2_{region}", f"bkg_f2_{region}", ROOT.RooArgList(bkg_f2_exps), ROOT.RooArgList([w.obj(f"cc{i}_{region}") for i in range(f2_exp_degree - 1)]))
    bkg_f2.fitTo(data, ROOT.RooFit.Range(region))
    # print post-fit parameters
    for i in range(f2_exp_degree):
        print(f"c{i}_{region}: {w.obj(f'c{i}_{region}').getValV()} +/- {w.obj(f'c{i}_{region}').getError()}")
    for i in range(f2_exp_degree - 1):
        print(f"cc{i}_{region}: {w.obj(f'cc{i}_{region}').getValV()} +/- {w.obj(f'cc{i}_{region}').getError()}")
    w_bkg.Import(bkg_f2)

# Simple exponential (for reference)

for region in ["Region2", "Region3"]:
    alpha = ROOT.RooRealVar(f"alpha_{region}", f"alpha_{region}", -1.5, -10, 10)
    bkg_f3 = ROOT.RooExponential(f"bkg_f3_{region}", f"bkg_f3_{region}", m, alpha)
    bkg_f3.fitTo(data, ROOT.RooFit.Range(region))
    w_bkg.Import(bkg_f3)

### SAVE WORKSPACE
w_bkg.writeToFile("workspaces/workspace_background.root")