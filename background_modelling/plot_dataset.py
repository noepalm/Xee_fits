import ROOT
import os
import argparse

use_jpsi = False
suffix = "_jpsi" if use_jpsi else "_minbias"
f = ROOT.TFile.Open(f"dataset{suffix}.root")
w = f.Get("w")
data = w.obj("data")
m = w.obj("mass_test")

outfolder = "/eos/home-n/npalmeri/www/DiElectron/background_model/fit_tests"

# set batch mode
ROOT.gROOT.SetBatch(True)

canvas = ROOT.TCanvas("canvas", "canvas", 1000, 600)
canvas.SetGrid()

# plot dataset
frame = m.frame(
    ROOT.RooFit.Bins(300),
)
frame.SetTitle("")
frame.GetXaxis().SetTitle("m(ee) [GeV]")

data.plotOn(frame,
    ROOT.RooFit.Name("data"),
    ROOT.RooFit.MarkerColor(ROOT.kBlack),
    ROOT.RooFit.MarkerStyle(20),
    ROOT.RooFit.MarkerSize(0.6),
    # ROOT.RooFit.DataError(ROOT.RooAbsData.SumW2),
)

# set log scale y
canvas.SetLogy()

frame.Draw()
# draw vertical line at 1.2 GeV
lines = []
for val in [1.2, 2.6, 4.2, 8]:
    line = ROOT.TLine(val, 0, val, frame.GetMaximum())
    line.SetLineColor(ROOT.kRed)
    line.SetLineStyle(2)
    line.SetLineWidth(2)
    line.Draw("SAME")
    lines.append(line)  # Keep a reference to the line to prevent it from being garbage collected

for val in [2.7, 3.3, 3.5, 3.8]:
    # same, but light gray 
    line = ROOT.TLine(val, 0, val, frame.GetMaximum())
    line.SetLineColor(ROOT.kGray)
    line.SetLineStyle(2)
    line.SetLineWidth(1)
    line.Draw("SAME")
    lines.append(line)  # Keep a reference to the line to prevent it from being garbage collected

canvas.SaveAs(os.path.join(outfolder, f"data_fullRange{suffix}.png"))
canvas.SaveAs(os.path.join(outfolder, f"data_fullRange{suffix}.pdf"))
