import ROOT

# create RooFitworkspace
w = ROOT.RooWorkspace("w")

x = ROOT.RooRealVar("x","x", -10, 10)

# create breit-wigner
meanBW = ROOT.RooRealVar("meanBW","meanBW", 5, 4, 6)
sigmaBW = ROOT.RooRealVar("widthBW","widthBW", 0.0001, 0, 10)

BW = ROOT.RooBreitWigner("BW","BW", x, meanBW, sigmaBW)


# create double crystal ball function

meanCB = ROOT.RooRealVar("meanCB","meanCB", 0, -0.6, 0.6)
sigmaCB = ROOT.RooRealVar("sigmaCB","sigmaCB", 0.2, 0, 1)
alphaLCB = ROOT.RooRealVar("alphaLCB","alphaLCB", 2, 0, 10)
nLCB = ROOT.RooRealVar("nLCB","nLCB", 3, 0, 10)
alphaRCB = ROOT.RooRealVar("alphaRCB","alphaRCB", 2, 0, 10)
nRCB = ROOT.RooRealVar("nRCB","nRCB", 3, 0, 10)

# CB = ROOT.RooCrystalBall("CB","CB", x, shiftedMean, sigmaCB, alphaLCB, nLCB, alphaRCB, nRCB)

CB = ROOT.RooGaussian("CB","CB", x, meanCB, sigmaCB)

# create convolution
x.setBins(10000, "cache")
conv = ROOT.RooFFTConvPdf("conv","conv",x,CB,BW)

meanCB.Print()
sigmaCB.Print()
meanBW.Print()
sigmaBW.Print()

# plot convolution function
# enable batch mode
ROOT.gROOT.SetBatch(True)
c = ROOT.TCanvas()
frame = x.frame()
conv.plotOn(frame)
# BW.plotOn(frame, ROOT.RooFit.LineColor(ROOT.kRed))
# CB.plotOn(frame, ROOT.RooFit.LineColor(ROOT.kBlue))
frame.Draw()
c.Draw()
c.SaveAs("convolution.png")