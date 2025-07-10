import ROOT
import os
import argparse

# -------- INPUT PARAMETERS -------- #
parser = argparse.ArgumentParser()

parser.add_argument("--fit_region", help="Pick fit region among defined", default="unblinded")
parser.add_argument("--tag", help="Tag for output files", default="")
parser.add_argument("--use_reduced_mass", action="store_true", help="Use reduced mass instead of fitted mass", default = False)
parser.add_argument("--use_jpsi", action="store_true", help="Use Jpsi sample instead of MinBias sample", default = False)
parser.add_argument("--freeze_bkg_sidebands", action="store_true", help="Freeze background parameters on sidebands when fitting in unblinded region", default = False)
parser.add_argument("--floating_signal", action="store_true", help="Use floating signal model instead of fully parametric one", default = False)
parser.add_argument("--fit_jpsi_first", action="store_true", help="Fit J/psi only first and freeze before S+B fit", default = False)
parser.add_argument("--fit_jpsi_prompt", action="store_true", help="Fit Jpsi, Psi2S model from prompt Jpsi", default = False)
parser.add_argument("--bkg_function", default = 0, type=int, choices=[0, 1, 2, 3], help="Choose which background function to use in unblinded region (0: Bernstein, 1: Polynomial + Exponential, 2: Sum of exponentials, 3: Exponential)")
parser.add_argument("--binned", default = False, action="store_true", help="Use binned data instead of unbinned")

args = parser.parse_args()
use_jpsi = args.use_jpsi
use_reduced_mass = args.use_reduced_mass

tag = args.tag
if tag != "":
    tag = "_" + tag
    if use_reduced_mass:
        tag = tag + "_reducedMass"

# check if fit region from input is defined
fit_range = args.fit_region

if fit_range == "bkg_left":
    side_suffix = "_left"
elif fit_range == "bkg_right":
    side_suffix = "_right"
elif fit_range == "unblinded":
    side_suffix = "_unblinded"

binning_suffix = "_binned" if args.binned else ""

# print all arguments
print("Arguments:")
for arg in vars(args):
    print(f"\t{arg}: {getattr(args, arg)}")
print("")

# -------- MISC SETTINGS -------- #

# turn on batch mode
ROOT.gROOT.SetBatch(True)

# -------- UTILIES -------- #

def logprint(msg, f):
    print(msg)
    f.write(msg + "\n")

# -------- INPUT FILES -------- #

use_jpsi = False
sample_suffix = "_jpsi" if use_jpsi else "_minbias"
suffix = "" if not use_reduced_mass else "_reducedMass"
f = ROOT.TFile.Open(f"datasets/dataset{sample_suffix}{suffix}.root")
w = f.Get("w")
data = w.obj("data_obs")
m = w.obj("mass")

if args.binned:
    m.setBins(100)
    data_binned = ROOT.RooDataHist("data_obs", "data_obs", ROOT.RooArgSet(m))
    for i in range(data.numEntries()):
        m.setVal(data.get(i).getRealValue("mass"))
        weight = data.weight()
        data_binned.add(ROOT.RooArgSet(m))#, weight)
    data = data_binned
    w.Import(data, True)

outfolder = "/eos/home-n/npalmeri/www/DiElectron/background_model/fit_tests_reweight"

log_file = open(os.path.join(outfolder, f"post_fit_params{side_suffix}{tag}{binning_suffix}.log"), "w")

# ----- FIT SIDEBANDS with ENVELOPE ----- #
# 1) fit each background model separately

# 4-th degree Bernstein polynomial
bernstein_degree = 5 #4
# bernstein_inits = [0.5, 0.5, -0.5, 0.5, 0.5 ]
bernstein_inits = [0.36903, 0.11880, -0.46547, 0.56438, -0.58503]
for i in range(bernstein_degree):
    w.factory(f"a{i}[{bernstein_inits[i]}, -5, 5]")    # Bernstein coefficients # GOOD FOR DESCENDING
    # w.factory(f"a{i}[-0.5, -1, 1]")    # Bernstein coefficients # GOOD FOR DESCENDING
    # w.factory(f"a{i}[0.1, 0, 1]")    # Bernstein coefficients # GOOD FOR ASCENDING
bkg_f0 = ROOT.RooBernstein("bkg_f0", "bkg_f0", m, ROOT.RooArgList([w.obj(f"a{i}") for i in range(bernstein_degree)]))

# # manually create polynomial coefficients
# w.factory("b0[0.01, -1, 1]")
# w.factory("b1[0.5, 0, 1]")
# w.factory("b2[0.01, -1, 1]")
# w.factory("b3[0.001, -1, 1]")
# w.factory("b4[0.0001, -1, 1]")
# w.factory("b5[0.00001, 0, 1]")
# w.factory("b6[0.000001, 0, 1]")

# w.factory("b0[0.01, -3, 1]")
# w.factory("b1[0.5, 0, 1]")
# w.factory("b2[0.01, -1, 2]")
# w.factory("b3[0.001, -1, 1]")
# w.factory("b4[0.0001, -1, 1]")
# w.factory("b5[0.00001, 0, 1]")
# w.factory("b6[0.000001, 0, 1]")

# # # 4-th degree polynomial times exponential
# polynomial_degree = 4
# bkg_f1_poly = ROOT.RooPolynomial("bkg_f1_poly", "bkg_f1_poly", m, ROOT.RooArgList([w.obj(f"b{i}") for i in range(polynomial_degree)]))
# w.factory("bb0[-1, -10, 10]")      # Exponential coefficient
# bkg_f1_exp = ROOT.RooExponential("bkg_f1_exp", "bkg_f1_exp", m, w.obj("bb0"))
# bkg_f1 = ROOT.RooProdPdf("bkg_f1", "bkg_f1", bkg_f1_poly, bkg_f1_exp)

# manually create polynomial coefficients
polynomial_degree = 4
mins = [-1 if i == 1 or i == 3 else 0 for i in range(polynomial_degree)]
inits = [-0.9, 3.2, -1.4, 0.16, 0.00001, 0.000001]
for i in range(polynomial_degree):
    w.factory(f"b{i}[{inits[i]}, -5, 5]")    # Polynomial coefficients

# 4-th degree polynomial times exponential
polynomial_degree = 4
bkg_f1_poly = ROOT.RooGenericPdf("bkg_f1_poly", "(1 + @0*@1 + @0**2 * @2 + @0**3 * @3 + @0**4 * @4 ) > 0 ? (1 + @0*@1 + @0**2 * @2 + @0**3 * @3 + @0**4 * @4 ) : 1e-6", ROOT.RooArgList([m] + [w.obj(f"b{i}") for i in range(polynomial_degree)]))
# bkg_f1_poly = ROOT.RooGenericPdf("bkg_f1_poly", "(1 + @0*@1 + @0**2 * @2 + @0**3 * @3 + @0**4 * @4 )", ROOT.RooArgList([m] + [w.obj(f"b{i}") for i in range(polynomial_degree)]))
w.factory("bb0[0, -10, 10]")      # Exponential coefficient
bkg_f1_exp = ROOT.RooExponential("bkg_f1_exp", "bkg_f1_exp", m, w.obj("bb0"))
bkg_f1 = ROOT.RooProdPdf("bkg_f1", "bkg_f1", bkg_f1_poly, bkg_f1_exp)

# bkg_f1 = ROOT.RooGenericPdf("bkg_f1", "(1 + @0*@1 + @0**2 * @2 + @0**3 * @3 + @0**4 * @4 ) > 0 ? (1 + @0*@1 + @0**2 * @2 + @0**3 * @3 + @0**4 * @4 ) : 1e-6", ROOT.RooArgList([m] + [w.obj(f"b{i}") for i in range(polynomial_degree)]))
# bkg_f1 = ROOT.RooGenericPdf("bkg_f1", "(1 + @0*@1 + @0**2 * @2 + @0**3 * @3 + @0**4 * @4 )", ROOT.RooArgList([m] + [w.obj(f"b{i}") for i in range(polynomial_degree)]))

# Sum of exponentials
f2_exp_degree = 4

for i in range(f2_exp_degree):
    w.factory(f"cc{i}[{1./f2_exp_degree * (-1 * (i % 2))}, -1, 1]")   # Exponential coefficients
# exp_inits = [0, -1, 2, 1.3, 1.4, -1, -1, 1]
# exp_inits = [-0.1, +1, -3, +4]
exp_inits = [1, 4, 0.1, -1, 5]
bkg_f2_exps = []
for i in range(f2_exp_degree):
    # w.factory(f"c{i}[{exp_inits[i]}, {-10 + 20./f2_exp_degree * i}, {-10 + 20./f2_exp_degree * (i+1)}]")   # Exponential coefficients
    # w.factory(f"c{i}[{exp_inits[i]}, -20, 20]")   # Exponential coefficients
    w.factory(f"c{i}[{exp_inits[i]}, -10, 10]")   # Exponential coefficients
    bkg_f2_exps.append(ROOT.RooExponential(f"bkg_f2_exp{i}", f"bkg_f2_exp{i}", m, w.obj(f"c{i}")))

# w.obj("c0").setConstant(True)
# w.obj("c1").setConstant(True)

bkg_f2 = ROOT.RooAddPdf("bkg_f2", "bkg_f2", ROOT.RooArgList(bkg_f2_exps), ROOT.RooArgList([w.obj(f"cc{i}") for i in range(f2_exp_degree - 1)]))

# Simple exponential (for reference)
alpha = ROOT.RooRealVar("alpha", "alpha", -1.5, -10, 10)
bkg_f3 = ROOT.RooExponential("bkg_f3", "bkg_f3", m, alpha)

# SAVE #FREE PARAMETRES (before subsequent freezes)
n_free_params = {}
for pdf in [bkg_f0, bkg_f1, bkg_f2, bkg_f3]:
    npar = pdf.getParameters(data).selectByAttrib("Constant", False).getSize()
    n_free_params[pdf.GetName()] = npar

# 2) fit each model to the sidebands
# MUMU UNBLINDED RANGE: 2.6, 4.2
# xmin = 2.6
# xmax = 4.2
xmin = 2 #2
xmax = 4.2 #4.2

m.setRange("unblinded", xmin, xmax)
m.setRange("sidebandL", xmin, 2.6) #2.7, 2.8 before
m.setRange("sidebandC", 3.3, 3.5)
m.setRange("sidebandR", 3.8, xmax)
m.setRange("jpsi", 3.05, 3.12)
m.setRange("psi2s", 3.6, 3.8)

m.setRange("bkg_left", 1.2, 2.6)
m.setRange("bkg_right", 4.2, 8)
m.setRange("full", 1.2, 8)

# fit backgrounds to both sidebands
if fit_range != "unblinded":
    fitres_0 = bkg_f0.fitTo(data, ROOT.RooFit.NumCPU(8), ROOT.RooFit.Range(fit_range), ROOT.RooFit.Save())
    fitres_1 = bkg_f1.fitTo(data, ROOT.RooFit.NumCPU(8), ROOT.RooFit.Range(fit_range), ROOT.RooFit.Save())
    fitres_2 = bkg_f2.fitTo(data, ROOT.RooFit.NumCPU(8), ROOT.RooFit.Range(fit_range), ROOT.RooFit.Save())
    fitres_3 = bkg_f3.fitTo(data, ROOT.RooFit.NumCPU(8), ROOT.RooFit.Range(fit_range), ROOT.RooFit.Save())
    
# 3) test S+B fit with bkg f0

# retrieve jpsi model
jpsi_model = w.obj("Zd_M3.1")
psi2s_model = w.obj("Zd_M3.7")

if not args.floating_signal:
    # retrieve pre-fit parameter values
    prefit_param_values = {}
    for pdf in [jpsi_model, psi2s_model]:
        for param in pdf.getParameters(data):
            prefit_param_values[param.GetName()] = param.getValV()
else:
    # create jpsi and psi2s parameters
    signal_models = {}
    prefit_param_values = {}

    # [TO EVENTUALLY CHANGE] this are good init values; makes fit robust wrt signal model 
    # (tails get easily messed up for some reason)
    inits = {
        "jpsi" : {
            "mean" : 3.1,
            "sigma" : 0.045,
            "alphaL" : 0.60,
            "nL" : 3.1,
            "alphaR" : 1.5,
            "nR" : 2.9,
        },
        "psi2s" : {
            "mean" : 3.7,
            "sigma" : 0.05,
            "alphaL" : 0.5,
            "nL" : 5,
            "alphaR" : 1,
            "nR" : 6,
        }
    }
    for name, model in {"jpsi" : jpsi_model, "psi2s" : psi2s_model}.items():
        logprint(f"Creating {name} model", log_file)
        mparams = model.getParameters(data)
        mparams = {p.GetName(): p for p in mparams}
        nominal_mass = 3.1 if name == "jpsi" else 3.7
        params = ["mean", "sigma", "alphaL", "nL", "alphaR", "nR"]
        for param in params:
            v = mparams[f"{param}_fit_par1"].getValV() * nominal_mass + mparams[f"{param}_fit_par0"].getValV()
            if use_reduced_mass:
                if param == "mean":
                    v = v + nominal_mass
                if param == "sigma":
                    v = v * nominal_mass
            v = inits[name][param]
            # w.factory(f"{param}_{name}[{v}, {v*0.5}, {v*1.5}]")
            # w.factory(f"{param}_{name}[{v}, {v*0.99}, {v*1.1}]")
            logprint(f"param: {param}_{name} = {v}", log_file)
            w.factory(f"{param}_{name}[{v}, {v*0.1}, {v*10}]")
            prefit_param_values[f"{param}_{name}"] = v

            # w.obj(f"{param}_{name}").setConstant(True)
        # create signal model
        signal_models[name] = ROOT.RooCrystalBall(f"{name}_model", f"{name}_model", m, *[w.obj(f"{param}_{name}") for param in params])

    jpsi_model = signal_models["jpsi"]
    psi2s_model = signal_models["psi2s"]

if args.fit_jpsi_prompt:
    # retrieve prompt jpsi, psi2s dataset from other file
    prompt_file = ROOT.TFile.Open(f"datasets/dataset_jpsi.root")
    prompt_w = prompt_file.Get("w")
    prompt_data = prompt_w.obj("data_obs")

    # fit jpsi and psi2s model to prompt data
    fraction_psi2s = ROOT.RooRealVar("fraction_psi2s", "fraction_psi2s", 0.3, 0, 1)
    jpsi_plus_psi2s = ROOT.RooAddPdf("jpsi_plus_psi2s", "jpsi_plus_psi2s", ROOT.RooArgList(jpsi_model, psi2s_model), ROOT.RooArgList(fraction_psi2s))
    jpsi_plus_psi2s.fitTo(prompt_data, ROOT.RooFit.NumCPU(8), ROOT.RooFit.Range("unblinded"), ROOT.RooFit.Save(), ROOT.RooFit.SumW2Error(True))

    logprint("Fitted jpsi and psi2s models to prompt data", log_file)
    # print fitted parameters
    for param in jpsi_plus_psi2s.getParameters(prompt_data):
        logprint(f"param: {param.GetName()}, value: {param.getValV():.5f}, error: {param.getError():.5f} (limits: [{param.getMin():.5g}, {param.getMax():.5g}])", log_file)

    # PLOTTING
    canvas_prompt = ROOT.TCanvas("canvas_prompt", "canvas_prompt", 800, 600)
    canvas_prompt.SetGrid()
    # plot dataset
    xmin, xmax = m.getRange("unblinded")
    frame_prompt = m.frame(xmin, xmax)
    frame_prompt.SetTitle("")

    # draw data
    prompt_data.plotOn(frame_prompt,
                ROOT.RooFit.Name("prompt_data"),
                ROOT.RooFit.Binning(100),
                # ROOT.RooFit.NormRange("unblinded"),
    )

    # plot models
    jpsi_plus_psi2s.plotOn(frame_prompt, ROOT.RooFit.LineColor(ROOT.kBlack), ROOT.RooFit.Name("jpsi_plus_psi2s"), ROOT.RooFit.NormRange("unblinded"))
    # plot components
    jpsi_plus_psi2s.plotOn(frame_prompt, ROOT.RooFit.Components("jpsi_model"), ROOT.RooFit.LineColor(ROOT.kRed), ROOT.RooFit.Name("jpsi_model"), ROOT.RooFit.NormRange("unblinded"))
    jpsi_plus_psi2s.plotOn(frame_prompt, ROOT.RooFit.Components("psi2s_model"), ROOT.RooFit.LineColor(ROOT.kBlue), ROOT.RooFit.Name("psi2s_model"), ROOT.RooFit.NormRange("unblinded"))

    # draw frame
    frame_prompt.Draw()
    frame_prompt.GetXaxis().SetTitle("m(ee) [GeV]")

    # compute chi2
    # print all objects in frame
    frame_prompt.Print()
    npar = jpsi_plus_psi2s.getParameters(prompt_data).selectByAttrib("Constant", False).getSize()
    chi2_val = frame_prompt.chiSquare("jpsi_plus_psi2s", "prompt_data", int(npar))
    logprint(f"chi2 = {chi2_val} (n. free params = {npar})", log_file)

    # freeze jpsi and psi2s model parameters (HERE for correct counting of parameters)
    for param in jpsi_model.getParameters(prompt_data):
        param.setConstant(True)
    for param in psi2s_model.getParameters(prompt_data):
        param.setConstant(True)

    # plot legend
    legend_prompt = ROOT.TLegend(0.2, 0.15, 0.9, 0.45)
    legend_prompt.SetBorderSize(0)
    legend_prompt.SetFillColor(0)
    legend_prompt.SetFillStyle(0)
    legend_prompt.SetTextSize(0.04)
    legend_prompt.AddEntry(frame_prompt.findObject("data_obs"), "data_obs", "p")
    legend_prompt.AddEntry(frame_prompt.findObject("jpsi_plus_psi2s"), f"#splitline{{J/psi + psi(2S) model}}{{chi2 = {chi2_val:.2f}}}", "l")
    legend_prompt.AddEntry(frame_prompt.findObject("jpsi_model"), "J/psi model", "l")
    legend_prompt.AddEntry(frame_prompt.findObject("psi2s_model"), "psi(2S) model", "l")
    legend_prompt.Draw()

    canvas_prompt.SaveAs(os.path.join(outfolder, f"dataset_prompt{tag}.png"))
    canvas_prompt.SaveAs(os.path.join(outfolder, f"dataset_prompt{tag}.pdf"))

    # set log scale
    frame_prompt.SetMinimum(1)
    canvas_prompt.SetLogy()
    canvas_prompt.SaveAs(os.path.join(outfolder, f"dataset_prompt{tag}_log.png"))
    canvas_prompt.SaveAs(os.path.join(outfolder, f"dataset_prompt{tag}_log.pdf"))

# create S+B model summing both signals
# sb_model = ROOT.RooAddPdf("sb_model", "sb_model", ROOT.RooArgList(jpsi_model, psi2s_model, bkg_f0), ROOT.RooArgList(ROOT.RooRealVar("nsig1", "nsig1", 1, 0, 10000), ROOT.RooRealVar("nsig2", "nsig2", 1, 0, 10000), ROOT.RooRealVar("nbkg", "bkg", 1, 0, 10000)), False)
normalizations = ["nsig1", "nsig2", "nbkg"]
initializations = [2e2, 2e2, 1e4]
mins = [2e2, 1e1, 3e2]
maxes = [1e6, 1e5, 1e6]
for var, init, min_, max_ in zip(normalizations, initializations, mins, maxes):
    w.factory(f"{var}[{init}, {min_}, {max_}]")

w.factory(f"fs1[0.4, 0, 1]") # fraction of jpsi
w.factory(f"fs2[0.01, 0, 1]") # fraction of psi2s #0.005, 0, 1 before
w.factory(f"fbkg[0.595, 0, 1]") # fraction of psi2s

fracs = ["fs1", "fs2", "fbkg"]

bkg_fs = {0 : bkg_f0, 1 : bkg_f1, 2 : bkg_f2, 3 : bkg_f3}
chosen_bkg = bkg_fs[args.bkg_function].Clone("bkg_function")

# sb_model = ROOT.RooAddPdf("sb_model", "sb_model", 
#                         ROOT.RooArgList(jpsi_model, psi2s_model, chosen_bkg),
#                         ROOT.RooArgList([w.obj(var) for var in fracs[:2]]))

sb_model = ROOT.RooAddPdf("sb_model", "sb_model", 
                        ROOT.RooArgList(jpsi_model, psi2s_model, chosen_bkg),
                        ROOT.RooArgList([w.obj(var) for var in normalizations]))

n_free_params[sb_model.GetName()] = sb_model.getParameters(data).selectByAttrib("Constant", False).getSize()
    
if fit_range == "unblinded" and args.fit_jpsi_first:
    logprint("Fitting jpsi model first", log_file)
    # create auxiliary extended pdf
    jpsi_bkg_model = ROOT.RooExtendPdf("jpsi_bkg_model", "jpsi_bkg_model", jpsi_model, w.obj("nsig1"))
    # fit jpsi model first
    jpsi_bkg_model.fitTo(data, ROOT.RooFit.Range("jpsi"), ROOT.RooFit.Save())
    # estimate number of events in full range
    sig_frac = jpsi_bkg_model.createIntegral(ROOT.RooArgSet(m), ROOT.RooFit.Range("jpsi")).getVal()
    sig_frac_unblinded = jpsi_bkg_model.createIntegral(ROOT.RooArgSet(m), ROOT.RooFit.Range("unblinded")).getVal()
    # set nsig1 to the expected number of events
    logprint("nsig1 fitted = ", w.var("nsig1").getValV(), "with fraction = ", sig_frac, " in jpsi region, ", sig_frac_unblinded, " in unblinded region", log_file)
    w.var("nsig1").setVal(w.var("nsig1").getValV() / sig_frac * sig_frac_unblinded)
    w.var("nsig1").setConstant(True)
    logprint(f"nsig1 = ", w.var("nsig1").getValV(), log_file)

if fit_range == "unblinded":
    # refit bkg to sidebands
    fitres_0_sb = chosen_bkg.fitTo(data, ROOT.RooFit.Range("sidebandL,sidebandC,sidebandR"), ROOT.RooFit.Save())
    # # create extended pdf
    # chosen_bkg_ext = ROOT.RooExtendPdf("chosen_bkg_ext", "chosen_bkg_ext", chosen_bkg, w.obj("nbkg"))
    # # fit bkg to sidebands
    # fitres_0_sb = chosen_bkg_ext.fitTo(data, ROOT.RooFit.Range("sidebandL,sidebandC,sidebandR"), ROOT.RooFit.Save(), ROOT.RooFit.Extended(True))
    # print("Fitted background; nbkg = ", w.obj("nbkg").getValV())

# # restrict range of bkg parameters to +-10% of sidebands fit
# for param in bkg_f0.getParameters(data):
#     param.setMin(param.getValV() * 0.9)
#     param.setMax(param.getValV() * 1.1)

if args.freeze_bkg_sidebands:
    # freeze background parameters
    for param in chosen_bkg.getParameters(data):
        print("Freezing parameter:", param.GetName())
        param.setConstant(True)
    # # compute normalization 
    # chosen_bkg_norm = chosen_bkg.createIntegral(ROOT.RooArgSet(m), ROOT.RooFit.Range("sidebandL,sidebandC,sidebandR")).getVal()
    # nbkg_projected = w.obj("nbkg").getValV() / chosen_bkg_norm
    # print("nbkg projected:", nbkg_projected, "from nbkg = ", w.obj("nbkg").getValV(), "and chosen_bkg_norm = ", chosen_bkg_norm)
    # w.obj("nbkg").setVal(nbkg_projected)
    # w.obj("nbkg").setConstant(True)

if fit_range == "unblinded":
    sb_fitres = sb_model.fitTo(data, ROOT.RooFit.Range("unblinded"), ROOT.RooFit.Save(), ROOT.RooFit.NumCPU(8), ROOT.RooFit.SumW2Error(True))

# Import SB model to workspace as full_bkg_model
w.Import(jpsi_model, ROOT.RooFit.RenameVariable("jpsi_model", "jpsi"))
w.Import(psi2s_model, ROOT.RooFit.RenameVariable("psi2s_model", "psi2s"))
w.Import(chosen_bkg, ROOT.RooFit.RenameVariable("bkg_function", "dy"))
w.Import(sb_model, ROOT.RooFit.RenameVariable("sb_model", "full_bkg_model"))

w.writeToFile(f"datasets/dataset{sample_suffix}{suffix}{binning_suffix}_full.root")

# 1) draw dataset around jpsi (2.5, 4.1 range)
# set batch mode
ROOT.gROOT.SetBatch(True)
# create canvas
canvas = ROOT.TCanvas("canvas", "canvas", 800, 600)
canvas.SetGrid()

# plot dataset
xmin, xmax = m.getRange(fit_range)
frame = m.frame(xmin, xmax)
frame.SetTitle("")
draw_args = [
    ROOT.RooFit.Name("data_obs"),
    ROOT.RooFit.MarkerSize(1),
    ROOT.RooFit.MarkerColor(ROOT.kBlack),
    ROOT.RooFit.LineColor(ROOT.kBlack),
    ROOT.RooFit.DrawOption("HIST"),
]

if not args.binned:
    draw_args.append(ROOT.RooFit.Binning(100))

# Plot data
data.plotOn(frame, *draw_args, 
            # ROOT.RooFit.NormRange(fit_range),
)

# plot background models
if fit_range != "unblinded":
    bkg_f0.plotOn(frame, ROOT.RooFit.LineColor(ROOT.kRed), ROOT.RooFit.Name("bkg_f0"), ROOT.RooFit.NormRange(fit_range))
    bkg_f1.plotOn(frame, ROOT.RooFit.LineColor(ROOT.kBlue), ROOT.RooFit.Name("bkg_f1"), ROOT.RooFit.NormRange(fit_range))
    bkg_f2.plotOn(frame, ROOT.RooFit.LineColor(ROOT.kGreen), ROOT.RooFit.Name("bkg_f2"), ROOT.RooFit.NormRange(fit_range))
    bkg_f3.plotOn(frame, ROOT.RooFit.LineColor(ROOT.kOrange), ROOT.RooFit.Name("bkg_f3"), ROOT.RooFit.NormRange(fit_range))

# bkg_f0.paramOn(frame)
# bkg_f1.paramOn(frame)
# bkg_f2.paramOn(frame)
# bkg_f3.paramOn(frame)

# plot S+B models
if fit_range == "unblinded":
    sb_model.plotOn(frame, ROOT.RooFit.LineColor(ROOT.kBlack), ROOT.RooFit.Name("sb_model"), ROOT.RooFit.NormRange(fit_range))
                    # ROOT.RooFit.Normalization(data.sumEntries(), ROOT.RooAbsReal.NumEvent))
    # plot components
    sb_model.plotOn(frame, ROOT.RooFit.Components("Zd_M3.1"), ROOT.RooFit.LineColor(ROOT.kRed), ROOT.RooFit.Name("jpsi_model"), ROOT.RooFit.NormRange(fit_range))
    sb_model.plotOn(frame, ROOT.RooFit.Components("Zd_M3.7"), ROOT.RooFit.LineColor(ROOT.kBlue), ROOT.RooFit.Name("psi2s_model"), ROOT.RooFit.NormRange(fit_range))
    sb_model.plotOn(frame, ROOT.RooFit.Components("jpsi_model"), ROOT.RooFit.LineColor(ROOT.kRed), ROOT.RooFit.Name("jpsi_model"), ROOT.RooFit.NormRange(fit_range))
    sb_model.plotOn(frame, ROOT.RooFit.Components("psi2s_model"), ROOT.RooFit.LineColor(ROOT.kBlue), ROOT.RooFit.Name("psi2s_model"), ROOT.RooFit.NormRange(fit_range))
    sb_model.plotOn(frame, ROOT.RooFit.Components("bkg_function"), ROOT.RooFit.LineColor(ROOT.kGreen), ROOT.RooFit.Name("bkg_f3"), ROOT.RooFit.NormRange(fit_range))

# sb_model.paramOn(frame)

# Replot data on top
frame.drawAfter("bkg_f3", "data_obs")
# data.plotOn(frame, *draw_args, 
#             ROOT.RooFit.NormRange(fit_range),
# )

# # SAVE ALL PLOTTED STUFF TO WORKSPACE
# w_plot = ROOT.RooWorkspace("w_plot")
# w_plot.Import(data)
# w_plot.Import(m)
# w_plot.Import(bkg_f0)
# w_plot.Import(bkg_f1)
# w_plot.Import(bkg_f2)
# w_plot.Import(bkg_f3)
# w_plot.Import(sb_model)

# w_plot.writeToFile(os.path.join(outfolder, f"workspace_plot{suffix}{side_suffix}{tag}.root"))

# draw frame
frame.Draw()
frame.GetXaxis().SetTitle("m(ee) [GeV]")
# frame.GetYaxis().SetTitle("Events")

# compute chi2s
chi2s = {}
for pdf in [bkg_f0, bkg_f1, bkg_f2, bkg_f3, sb_model]:
    npar = pdf.getParameters(data).selectByAttrib("Constant", False).getSize()
    # compute chi2 from frame
    chi2_val = frame.chiSquare(pdf.GetName(), data.GetName(), int(npar))
    # save
    chi2s[pdf.GetName()] = chi2_val

# plot legend
if fit_range == "bkg_left":
    legend = ROOT.TLegend(0.2, 0.15, 0.9, 0.45)
elif fit_range == "bkg_right":
    legend = ROOT.TLegend(0.2, 0.6, 0.9, 0.9)
else:
    legend = ROOT.TLegend(0.15, 0.2, 0.3, 0.4)
legend.SetBorderSize(0)
legend.SetFillColor(0)
legend.SetFillStyle(0)
legend.SetTextSize(0.04)

legend.AddEntry(frame.findObject("data_obs"), "data_obs", "p")
fs_to_plot = {
    "bkg_f0" : {
        "label" : "Bernstein, {}th deg.",
        "degree" : bernstein_degree,
    },
    "bkg_f1" : {
        "label" : "Polynomial, {}th deg.",
        "degree" : polynomial_degree,
    },
    "bkg_f2" : {
        "label" : "Sum of {} exponentials",
        "degree" : f2_exp_degree,
    },
    "bkg_f3" : {
        "label" : "1 exponential",
        "degree" : 1,
    },
    "sb_model" : {
        "label" : "S+B, Bernstein + dCB",
        "degree" : 0,
    },
}

if fit_range == "unblinded":
    keys_to_plot = ["sb_model"]
else:
    keys_to_plot = list(fs_to_plot.keys())[:-1]

for pdf, info in {key : fs_to_plot[key] for key in keys_to_plot}.items():
    legend.AddEntry(frame.findObject(pdf), info["label"].format(info["degree"]) + f" (chi2 = {chi2s[pdf]:.2f}, npar = {n_free_params[pdf]})", "l")

legend.Draw()

if args.fit_jpsi_first:
    # draw vertical lines at edges of "jpsi" range
    xmin, xmax = m.getRange("jpsi")
    line0 = ROOT.TLine(xmin, 0, xmin, frame.GetMaximum())
    line0.SetLineColor(ROOT.kRed)
    line0.SetLineStyle(2)
    line0.Draw("same")
    line1 = ROOT.TLine(xmax, 0, xmax, frame.GetMaximum())
    line1.SetLineColor(ROOT.kRed)
    line1.SetLineStyle(2)
    line1.Draw("same")


canvas.SaveAs(os.path.join(outfolder, f"dataset{sample_suffix}{side_suffix}{tag}{binning_suffix}.png"))
canvas.SaveAs(os.path.join(outfolder, f"dataset{sample_suffix}{side_suffix}{tag}{binning_suffix}.pdf"))

# set log scale 
canvas.SetLogy()
canvas.SaveAs(os.path.join(outfolder, f"dataset{sample_suffix}{side_suffix}{tag}{binning_suffix}_log.png"))
canvas.SaveAs(os.path.join(outfolder, f"dataset{sample_suffix}{side_suffix}{tag}{binning_suffix}_log.pdf"))


# Save post-fit parameters for all fitted functions
if fit_range == "unblinded":
    pdfs = [sb_model]
else:
    pdfs = [bkg_f0, bkg_f1, bkg_f2, bkg_f3]

for pdf in pdfs:
    logprint(f"Post-fit parameters for {pdf.GetName()}:", log_file)
    for param in pdf.getParameters(data):
        logprint(f"\t{param.GetName()}: {param.getValV():.5f} +- {param.getError():.5f} (limits: {param.getMin():.3f}, {param.getMax():.3f})", log_file)
        if pdf.GetName() == "sb_model":
            # if parameter is not constant:
            if param.GetName().split("_")[0] in ["mean", "sigma", "alphaL", "nL", "alphaR", "nR"]:
                logprint(f"\t\tPrefit = {prefit_param_values[param.GetName()]:.5f} (rel. variation = {(param.getValV() - prefit_param_values[param.GetName()]) / param.getValV() * 100:.2f}%)", log_file)

    logprint(f"\n\tchi2 = {chi2s[pdf.GetName()]:.2f} (n. free params = {n_free_params[pdf.GetName()]})\n", log_file)

# print integral of all sb components
if fit_range == "unblinded":
    for pdf in [jpsi_model, psi2s_model, chosen_bkg]:
        integral = pdf.createIntegral(ROOT.RooArgSet(m), ROOT.RooFit.Range("unblinded"))
        logprint(f"Integral of {pdf.GetName()} in unblinded range: {integral.getVal():.5f}", log_file)

log_file.close()