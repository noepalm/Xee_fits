import ROOT
import os
import argparse

is_data = False

# f = ROOT.TFile.Open("/eos/home-n/npalmeri/www/DiElectron/PS_reweighting/nanov15/fw_output_actualReweight/zsnap/era2023/base_8_TriggerPSReweight/InclusiveMinBias.root")
# f = ROOT.TFile.Open("/eos/home-n/npalmeri/www/DiElectron/PS_reweighting/fw_output_actualReweight/zsnap/era2023/base_8_TriggerPSReweight/InclusiveMinBias.root")

if is_data:
    f = ROOT.TFile.Open("/eos/home-n/npalmeri/www/DiElectron/PS_reweighting/nanov15/fw_output_corrected/zsnap/era2023/base_2_Final/DoubleElectronNANO_Run3_2023_data_allNano_2025Oct07_*.root_Run2023Dv1.root")
else:
    f = ROOT.TFile.Open("/eos/home-n/npalmeri/www/DiElectron/PS_reweighting/nanov15/fw_output_corrected/zsnap/era2023/base_2_Final/InclusiveMinBias.root")

t = f.Get("Events")

# plot DiElectron_fitted_mass distribution in 0-11 GeV range weighted by weight branch
m = ROOT.RooRealVar("DiElectron_fitted_mass_corrected", "DiElectron_fitted_mass_corrected", 0, 11)
w = ROOT.RooRealVar("weight", "weight", 0, 1e6)
data = ROOT.RooDataSet("data", "data", ROOT.RooArgSet(m), ROOT.RooFit.WeightVar(w))
print(f"Filling dataset with {t.GetEntries()} entries from tree...")
for i in range(t.GetEntries()):
    t.GetEntry(i)

    for mass_val in t.DiElectron_fitted_mass_corrected:
        if mass_val < 0 or mass_val > 11:
            continue

        weight = t.weight
        m.setVal(mass_val)
        data.add(ROOT.RooArgSet(m), weight * 58.9/7.98)

outfolder = "/eos/home-n/npalmeri/www/DiElectron/background_model/260122/fit_binned_data_altbkg_chebyshev_withSyst"

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

prefix = "data" if is_data else "minbias"
canvas.SaveAs(os.path.join(outfolder, f"{prefix}_fullRange.png"))
canvas.SaveAs(os.path.join(outfolder, f"{prefix}_fullRange.pdf"))

# make zoom in region 0-2 GeV (i.e. region 0)
canvas_zoom = ROOT.TCanvas("canvas_zoom", "canvas_zoom", 1000, 600)
canvas_zoom.SetGrid()

xmin = 0
xmax = 2

frame_zoom = m.frame(
    ROOT.RooFit.Bins(100),
    ROOT.RooFit.Range(xmin, xmax),
)
frame_zoom.SetTitle("")
frame_zoom.GetXaxis().SetTitle("m(ee) [GeV]")

data.plotOn(frame_zoom,
    ROOT.RooFit.Name("data"),
    ROOT.RooFit.MarkerColor(ROOT.kBlack),
    ROOT.RooFit.MarkerStyle(20),
    ROOT.RooFit.MarkerSize(0.6),
    # ROOT.RooFit.DataError(ROOT.RooAbsData.SumW2),
)

# set log scale y
canvas_zoom.SetLogy()

frame_zoom.Draw()
frame_zoom.SetMinimum(1e1)
frame_zoom.SetMaximum(frame_zoom.GetMaximum() * 1.6)

canvas_zoom.SaveAs(os.path.join(outfolder, f"{prefix}_region0.png"))
canvas_zoom.SaveAs(os.path.join(outfolder, f"{prefix}_region0.pdf"))