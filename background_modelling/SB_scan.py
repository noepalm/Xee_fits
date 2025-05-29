import ROOT
import os
import argparse
import numpy as np
from scipy.optimize import curve_fit

# -------- UTILITIES -------- #
def logprint(msg, f):
    print(msg)
    f.write(msg + "\n")

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
parser.add_argument("--binned", action="store_true", help="Use binned dataset", default = False)

args = parser.parse_args()
use_jpsi = args.use_jpsi
use_reduced_mass = args.use_reduced_mass

tag = args.tag
if tag != "":
    tag = "_" + tag
    if use_reduced_mass:
        tag = tag + "_reducedMass"

binning_suffix = "_binned" if args.binned else ""

# -------- MISC SETTINGS -------- #

# turn on batch mode
ROOT.gROOT.SetBatch(True)

# -------- I/O FILES -------- #
use_jpsi = False
sample_suffix = "_jpsi" if use_jpsi else "_minbias"
suffix = "" if not use_reduced_mass else "_reducedMass"
f = ROOT.TFile.Open(f"datasets/dataset{sample_suffix}{suffix}{binning_suffix}_full.root")

w = f.Get("w")
data = w.obj("data")
m = w.obj("mass")

# set binning
m.setBins(300)

outfolder = "/eos/home-n/npalmeri/www/DiElectron/background_model/fit_tests/SB_fits_finer"

# open output log
if not os.path.exists(outfolder):
    os.makedirs(outfolder)
logfile = f"{outfolder}/fit{sample_suffix}{suffix}{tag}_log.txt"
f = open(logfile, "w")

# ---------- DATASET SETUP --------- #
# reweight dataset to normalization

n_bkg_exp = 7.98 * 1e3 # luminosity (in pb-1)
n_bkg_exp *= 545900000 # xsec (in pb)
n_bkg_exp *= 0.0008490073 # filter efficiency
n_bkg_exp *= 0.00052 # analyzer selection efficiency
n_bkg_exp *= 0.48138 # fw selection efficiency

logprint(f"Expected background events: {n_bkg_exp:.2f}", f)

# create weight variable with constant value
weight = ROOT.RooRealVar("weight", "weight", n_bkg_exp / data.sumEntries())
weight.setConstant(True)
logprint(f"Weight: {weight.getValV():.2f}", f)

# create weighted dataset
if args.binned:
    weighted_data = ROOT.RooDataHist("weighted_data", "weighted_data", ROOT.RooArgSet(m))
else:
    weighted_data = ROOT.RooDataSet("weighted_data", "weighted_data", ROOT.RooArgSet(m), ROOT.RooFit.WeightVar(weight))

# fill weighted dataset with original data
for i in range(data.numEntries()):
    m.setVal(data.get(i).getRealValue("mass"))
    weighted_data.add(m, n_bkg_exp / data.sumEntries())

# ----------- ACTUAL FITS ----------- #
xmin, xmax = m.getRange("unblinded")
# m.setMin(xmin)
# m.setMax(xmax)

# SIGNAL MODEL
# retrieve all signal models with mass between xmin and xmax
signal_models = {}
for pdf in w.allPdfs():
    if "Zd" in pdf.GetName():
        mass = pdf.GetName().split("_M")[-1]
        # mass = float(mass.replace("p", "."))
        mass = float(mass)
        if xmin < mass < xmax:
            signal_models[mass] = pdf

# # DEBUG: use only first signal model
# signal_models = {list(signal_models.keys())[0]: list(signal_models.values())[0]}

# -- Interpolate xsec, selection efficiency
masses = np.array([1, 3.1, 5, 5.5, 6, 6.5])
effs = np.array([1.562, 14.010, 19.821, 20.552, 18.541, 11.550]) # %
effs_err = np.array([0.055, 0.155, 0.179, 0.181, 0.2, 0.143])
xsecs = np.array([3.396, 2.679, 1.952, 1.910, 1.865, 1.834]) # pb
xsecs_err = np.array([0.01646, 0.0095, 0.003978, 0.003451, 0.001997, 0.001002])

# effs
popt_eff, _ = curve_fit(lambda x, a, b, c, d : np.polyval((a, b, c, d), x), masses, effs, sigma=effs_err, absolute_sigma=True)
# plot data and fit curve
x = np.linspace(np.min(masses), np.max(masses), 1000)
y = np.polyval(popt_eff, x)
# plot
import matplotlib.pyplot as plt
plt.errorbar(masses, effs, yerr=effs_err, fmt='o', markersize=3, label='data with error bars', capsize=3)
plt.plot(x, y, '-', label='fit')
plt.xlabel('mass [GeV]')
plt.ylabel('efficiency [%]')
plt.legend()
plt.title("Selection efficiency vs mass")
plt.savefig(os.path.join(outfolder, "signal_efficiency_fit.png"))
plt.close()

# fit xsecs vs masses with polynomial
popt_xsec, _ = curve_fit(lambda x, a, b, c, d, e : np.polyval((a, b, c, d, e), x), masses, xsecs, sigma=xsecs_err, absolute_sigma=True)

# plot data and fit curve
x2 = np.linspace(np.min(masses), np.max(masses), 1000)
y2 = np.polyval(popt_xsec, x2)
# plot
plt.plot(masses, xsecs, 'o', label='data')
plt.plot(x2, y2, '-', label='fit')
plt.xlabel('mass [GeV]')
plt.ylabel('xsec [pb]')
plt.legend()
plt.title("Cross section vs mass")
plt.savefig(os.path.join(outfolder, "signal_xsec_fit.png"))

# BACKGROUND MODEL
# retrieve full_bkg_model
full_bkg_model = w.pdf("full_bkg_model")
# also retrieve components
jpsi_model = w.pdf("jpsi_model")
psi2s_model = w.pdf("psi2s_model")
bkg_model = w.pdf("bkg_function")
bkg_components = [jpsi_model, psi2s_model, bkg_model]

# fit S+B for each mass hypothesis:
for mass_v, sgn_model in signal_models.items():
    logprint(f"Fitting mass hypothesis: {mass_v}", f)
    # create sum pdf
    # sgn_fraction = ROOT.RooRealVar(f"sgn_fraction_{mass_v:.1f}", "sgn_fraction", 0.2, 0, 1)
    # s_plus_b = ROOT.RooAddPdf("s_plus_b", "s_plus_b", ROOT.RooArgList(sgn_model, full_bkg_model), ROOT.RooArgList(sgn_fraction))
    n_sgn = ROOT.RooRealVar(f"n_sgn_{mass_v:.1f}", "n_sgn", 100, 0, 1e7)
    n_bkg = ROOT.RooRealVar(f"n_bkg_{mass_v:.1f}", "n_bkg", 1e4, 0, 1e7)
    s_plus_b = ROOT.RooAddPdf("s_plus_b", "s_plus_b", ROOT.RooArgList(sgn_model, full_bkg_model), ROOT.RooArgList(n_sgn, n_bkg))

    # # create s_plus_b model from renaming full_bkg_model
    # s_plus_b = full_bkg_model.Clone(f"s_plus_b")

    # for mu in [1]:
    for mu in [0, 1, 10]:
        logprint(f"\tTesting mu = {mu}", f)

        # INJECTING SIGNAL
        n_sgn_exp = 7.98 * 1e3 # luminosity (in pb-1)
        n_sgn_exp *= np.polyval(popt_eff, mass_v) # selection efficiency (in %)
        n_sgn_exp *= np.polyval(popt_xsec, mass_v) # xsec (in pb), interpolated
        logprint(f"\t\tExpected signal events: {n_sgn_exp:.0f} ; injecting {mu * n_sgn_exp:.0f} (mu = {mu})", f)
                    
        # add signal data to the original dataset
        pseudodata = weighted_data.Clone(f"pseudodata_{sgn_model.GetName()}")

        if mu * n_sgn_exp > 0:
            if args.binned:
                # generate mu * expected signal events with same binning
                signal_data = sgn_model.generateBinned(ROOT.RooArgSet(m), mu * n_sgn_exp)
                # add data to pseudodata dataset
                pseudodata.add(signal_data)

            else:
                # add mu * expected signal events to the dataset
                signal_data = sgn_model.generate(ROOT.RooArgSet(m), mu * n_sgn_exp)
                # add data to pseudodata dataset
                pseudodata.append(signal_data)

        # fit pseudodata in "unblinded" region with s+b model
        fit_result = s_plus_b.fitTo(pseudodata, ROOT.RooFit.Save(), ROOT.RooFit.Range("unblinded"), ROOT.RooFit.NumCPU(4), ROOT.RooFit.SumW2Error(ROOT.kTRUE))

        # print fitted mu value
        logprint(f"\t\tFITTED MU VALUE: {n_sgn.getValV() / n_sgn_exp:.3g} +- ? (vs. mu = {mu})", f)

        # PLOTTING
        c = ROOT.TCanvas(f"c_{sgn_model.GetName()}_mu{mu:.0f}", "c", 800, 600)
        c.SetGrid()

        frame = m.frame(xmin, xmax)
        frame.SetTitle(f"Fit result for {sgn_model.GetName()}")
        frame.GetXaxis().SetTitle("m(ee) [GeV]")
        
        # Plot pseudodata and fit
        pseudodata.plotOn(frame, ROOT.RooFit.Name("pseudodata"), 
                          ROOT.RooFit.MarkerColor(ROOT.kBlack), 
                          ROOT.RooFit.MarkerStyle(20), ROOT.RooFit.MarkerSize(0.8),
                          ROOT.RooFit.DataError(ROOT.RooAbsData.SumW2))
                        #   ROOT.RooFit.DataError(getattr(ROOT.RooAbsData, "None")))
                        #   ROOT.RooFit.DataError(ROOT.RooAbsData.SumW2))
        s_plus_b.plotOn(frame, ROOT.RooFit.Name("s+b"), ROOT.RooFit.LineColor(ROOT.kRed), ROOT.RooFit.LineWidth(2))
        # plot components
        colors = [ROOT.kBlue, ROOT.kViolet, ROOT.kOrange]
        for color, component in zip(colors, bkg_components):
            s_plus_b.plotOn(frame, ROOT.RooFit.Name(component.GetName()), ROOT.RooFit.Components(component.GetName()), ROOT.RooFit.LineColor(color), ROOT.RooFit.LineWidth(2), ROOT.RooFit.Range("unblinded"))

        s_plus_b.plotOn(frame, ROOT.RooFit.Name("sgn_model"), ROOT.RooFit.Components(sgn_model.GetName()), ROOT.RooFit.LineColor(ROOT.kGreen), ROOT.RooFit.LineWidth(2))
        # draw component
        s_plus_b.plotOn(frame, ROOT.RooFit.Name("full_bkg_model"), ROOT.RooFit.Components(full_bkg_model.GetName()), ROOT.RooFit.LineColor(ROOT.kBlack), ROOT.RooFit.LineWidth(2), ROOT.RooFit.Range("unblinded"))

        frame.Draw()

        # compute chi2
        npar = s_plus_b.getParameters(pseudodata).selectByAttrib("Constant", False).getSize()
        chi2 = frame.chiSquare("s+b", "pseudodata", npar)

        logprint(f"\t\tS+B chi2: {chi2:.2f}", f)

        # draw legend
        leg = ROOT.TLegend(0.6, 0.3, 0.9, 0.9)
        leg.SetBorderSize(0)
        leg.SetFillStyle(0)
        leg.SetTextSize(0.03)
        # change padding between legend entries
        leg.SetEntrySeparation(0.02)
        
        leg.AddEntry("pseudodata", "MinBias + injected signal", "p")
        leg.AddEntry("s+b", f"S+B fit (chi2 = {chi2:.2f})", "l")
        # leg.AddEntry("sgn_model", f"Signal (frac = {sgn_fraction.getValV():.2g})", "f")
        # leg.AddEntry("sgn_model", f"#splitline{{Signal}}{{n. evts = {n_sgn.getValV():.2g} +- {n_sgn.getError():.2g}}}{{mu = {n_sgn.getValV() / n_sgn_exp:.3g}}}", "f")
        leg.AddEntry("sgn_model", f"#splitline{{Signal}}{{#splitline{{n. evts = {n_sgn.getValV():.2g} +- {n_sgn.getError():.2g}}}{{mu = {n_sgn.getValV() / n_sgn_exp:.3g}}}}}", "l")
        leg.AddEntry("full_bkg_model", f"#splitline{{Background tot.}}{{#evts = {n_bkg.getValV():.2g} +- {n_bkg.getError():.2g}}}", "l")
        leg.AddEntry(frame.findObject("jpsi_model"), "J/#psi", "l")
        leg.AddEntry(frame.findObject("psi2s_model"), "#Psi(2S)", "l")
        leg.AddEntry(frame.findObject("bkg_function"), "Background", "l")
        
        leg.Draw("same")
        
        # save canvas
        c.SaveAs(f"{outfolder}/mu{mu:.0f}/fit_sb{tag}_M{str(mass_v).replace('.', 'p')}.png")
        c.SaveAs(f"{outfolder}/mu{mu:.0f}/fit_sb{tag}_M{str(mass_v).replace('.', 'p')}.pdf")

        # log scale
        c.SetLogy()    

        # NOTE: needed for log scale plot. 
        frame.SetMinimum(3e2)

        c.SaveAs(f"{outfolder}/mu{mu:.0f}/fit_sb{tag}_M{str(mass_v).replace('.', 'p')}_log.png")
        c.SaveAs(f"{outfolder}/mu{mu:.0f}/fit_sb{tag}_M{str(mass_v).replace('.', 'p')}_log.pdf")

        # close canvas
        c.Close()

# close log file
f.close()



