import ROOT

f1 = ROOT.TFile.Open("higgsCombineinjectingSignal.FitDiagnostics.mH120.123456.root", "READ")
dataset = f1.Get("toys/toy_asimov")

# now retrieve RooRealVar to plot from other workspace
f2 = ROOT.TFile.Open("Xee_ee_0_2023.root", "READ")
m = f2.Get("w").var("mass")

# finally, retrieve total S+B fit distribution from last file
f3 = ROOT.TFile.Open("fitDiagnosticsinjectingSignal.root", "READ")
total_distro = f3.Get("shapes_fit_s/Xee_ee_0_2023/total")

# draw
ROOT.gROOT.SetBatch()

c = ROOT.TCanvas("c", "c", 800, 600)
frame = m.frame(2, 4.2)
dataset.plotOn(frame, ROOT.RooFit.DataError(ROOT.RooAbsData.SumW2), ROOT.RooFit.MarkerSize(0.5))

frame.Draw()
ROOT.gPad.SetLogy()

# # rescale histogram to same area as dataset
# total_bkg = f3.Get("shapes_fit_s/Xee_ee_0_2023/total_background")
# total_bkg.Scale(dataset.sumEntries() / total_distro.Integral() * total_bkg.Integral() / total_distro.Integral())
# total_bkg.Draw("same")

# rescale histogram to same area as dataset
total_distro.Scale(dataset.sumEntries() / total_distro.Integral())
total_distro.Draw("same")


c.SaveAs("toy_data_plot.png")