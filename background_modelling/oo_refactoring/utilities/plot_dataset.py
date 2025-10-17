import ROOT
import os
import argparse

f = ROOT.TFile.Open("/eos/home-n/npalmeri/www/DiElectron/PS_reweighting/fw_output_actualReweight/zsnap/era2023/base_8_TriggerPSReweight/InclusiveMinBias.root")

t = f.Get("Events")

# plot DiElectron_fitted_mass distribution in 0-11 GeV range weighted by weight branch
m = ROOT.RooRealVar("DiElectron_fitted_mass", "DiElectron_fitted_mass", 0, 11)
w = ROOT.RooRealVar("weight", "weight", 0, 1e6)
data = ROOT.RooDataSet("data", "data", ROOT.RooArgSet(m), ROOT.RooFit.WeightVar(w))
print(f"Filling dataset with {t.GetEntries()} entries from tree...")
for i in range(t.GetEntries()):
    t.GetEntry(i)

    for mass_val in t.DiElectron_fitted_mass:
        if mass_val < 0 or mass_val > 11:
            continue

        weight = t.weight
        m.setVal(mass_val)
        data.add(ROOT.RooArgSet(m), weight * 58.9/7.98)

outfolder = "/eos/home-n/npalmeri/www/DiElectron/background_model/fit"

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
# set minimum to 0.1

canvas.SetLogy()

frame.Draw()
frame.SetMinimum(1e3)
frame.SetMaximum(frame.GetMaximum() * 1.6)
# # draw vertical line at 1.2 GeV
# lines = []
# for val in [1.2, 2.6, 4.2, 8]:
#     line = ROOT.TLine(val, 0, val, frame.GetMaximum())
#     line.SetLineColor(ROOT.kRed)
#     line.SetLineStyle(2)
#     line.SetLineWidth(2)
#     line.Draw("SAME")
#     lines.append(line)  # Keep a reference to the line to prevent it from being garbage collected

# for val in [2.7, 3.3, 3.5, 3.8]:
#     # same, but light gray 
#     line = ROOT.TLine(val, 0, val, frame.GetMaximum())
#     line.SetLineColor(ROOT.kGray)
#     line.SetLineStyle(2)
#     line.SetLineWidth(1)
#     line.Draw("SAME")
#     lines.append(line)  # Keep a reference to the line to prevent it from being garbage collected

canvas.SaveAs(os.path.join(outfolder, f"data_fullRange.png"))
canvas.SaveAs(os.path.join(outfolder, f"data_fullRange.pdf"))