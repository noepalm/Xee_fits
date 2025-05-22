import ROOT

f = ROOT.TFile.Open("../signal_model.root")
w = f.Get("w")

# turn on batch mode
ROOT.gROOT.SetBatch(True)

# retrieve 
data = w.obj("data_Zd_M6p5")#.binnedClone()
m = w.obj("mass_Zd_M6p5")

# create dCB with final parameters

cb = w.obj("response_function_Zd_M6p5")

# print parameters from workspace
print("PRE-FIT dCB parameters:")
for param in cb.getParameters(data):
    print(f"{param.GetName()}: {param.getValV():.3f} +/- {param.getError():.3f} (min = {param.getMin():.3f}, max = {param.getMax():.3f})")

w.obj("response_alphaL_Zd_M6p5").setVal(0.7)
w.obj("response_nL_Zd_M6p5").setVal(2)
w.obj("response_alphaR_Zd_M6p5").setVal(1.45)
w.obj("response_nR_Zd_M6p5").setVal(3)
# w.obj("response_mean_Zd_M6p5").setVal()
# w.obj("response_nsgn_Zd_M6p5").setVal()
# w.obj("response_sigma_Zd_M6p5").setVal()

# for param in cb.getParameters(data):
    # # set min, max to +- 10% of current value
    # min_val = param.getValV() * 0.9
    # max_val = param.getValV() * 1.1
    # param.setMin(min_val)
    # param.setMax(max_val)

# try to fit
cb.fitTo(data, ROOT.RooFit.Range(5.1, 7.4), ROOT.RooFit.Extended(False), ROOT.RooFit.Strategy(2), ROOT.RooFit.Minos(False))

print("POST-FIT:")
for param in cb.getParameters(data):
    print(f"{param.GetName()}: {param.getValV():.3f} +/- {param.getError():.3f} (min = {param.getMin():.3f}, max = {param.getMax():.3f})")

# response_alphaL_Zd_M6p5: 1.07009046967299 +/- 0.05639702407073055
# response_nL_Zd_M6p5: 0.6643371851414681 +/- 0.057643033401055366
# response_alphaR_Zd_M6p5: 2.210966079403988 +/- 0.07422448130123338
# response_nR_Zd_M6p5: 0.22924239476289887 +/- 0.07260443349714535
# response_mean_Zd_M6p5: 6.471090703624644 +/- 0.003976024389860111
# response_nsgn_Zd_M6p5: 999.9999999989972 +/- 0.07319393855306089
# response_sigma_Zd_M6p5: 0.13941258486350544 +/- 0.0038964462015961543

# draw them overlaid
canvas = ROOT.TCanvas("canvas", "canvas", 800, 600)
frame = m.frame(5.1, 7.4)
data.plotOn(frame, ROOT.RooFit.Name("data"))
cb.plotOn(frame, ROOT.RooFit.LineColor(ROOT.kRed), ROOT.RooFit.Name("dCB"))

print(f"dCB, chi2 = {frame.chiSquare('dCB', 'data'):.2f}")

frame.Draw()

canvas.SaveAs("dCB_fit.png")
