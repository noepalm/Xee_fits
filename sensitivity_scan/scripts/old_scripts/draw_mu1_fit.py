import ROOT
import argparse
import os

# argparse
parser = argparse.ArgumentParser()
parser.add_argument('-i', '--input', type=str, default='higgsCombine.injectedSignal.FitDiagnostics.mH120.123456.root', help='File output from combine -M FitDiagnostics containing toys')
parser.add_argument('-d', '--datacard', type=str, default='Xee_ee_0_2023.root', help='Name of the combine workspace; output of text2workspace')
parser.add_argument('-f', '--fit_file', type=str, default='fitDiagnostics.injectedSignal.root', help='File containing fit results')
parser.add_argument('-o', '--output_folder', type=str, default='plots', help='Output folder')
parser.add_argument('-m', '--mass', type=float, default=3.0, help='Mass value to plot')

args = parser.parse_args()

# print all arguments
print("Arguments:")
for arg in vars(args):
    print(f"{arg}: {getattr(args, arg)}")

# retrieve datacard workspace for later use
f_datacard = ROOT.TFile.Open(args.datacard, "READ")

# # now retrieve RooRealVar to plot from other workspace
# f1 = ROOT.TFile.Open(args.input, "READ")
# dataset = f1.Get("toys/toy_1")

# now retrieve RooRealVar to plot from other workspace
f1 = ROOT.TFile.Open(args.input, "READ")
dataset = f1.Get("w").data("data_obs")
m = dataset.get().find("mass")

# finally, retrieve total S+B fit distribution from last file
f2 = ROOT.TFile.Open(args.fit_file, "READ")
print(args.fit_file)
# total_distro = f2.Get("shapes_fit_b/Xee_ee_0_2023/total")
# dy_bkg = f2.Get("shapes_fit_b/Xee_ee_0_2023/dy")
# psi2s_bkg = f2.Get("shapes_fit_b/Xee_ee_0_2023/psi2s")
# jpsi_bkg = f2.Get("shapes_fit_b/Xee_ee_0_2023/jpsi")

# dy_n = f2.Get("norm_fit_b").selectByName("Xee_ee_0_2023/dy").first().getValV()
# psi2s_n = f2.Get("norm_fit_b").selectByName("Xee_ee_0_2023/psi2s").first().getValV()
# jpsi_n = f2.Get("norm_fit_b").selectByName("Xee_ee_0_2023/jpsi").first().getValV()
# total_n = f2.Get("norm_fit_b").selectByName("Xee_ee_0_2023/total_background").first().getValV()

# draw
ROOT.gROOT.SetBatch()

# c = ROOT.TCanvas("c", "c", 800, 600)
# ROOT.gPad.SetGrid()
# frame = m.frame(2, 4.2)
# frame.SetTitle("")
# frame.GetXaxis().SetTitle("m(ee) [GeV]")

# dataset.plotOn(frame, ROOT.RooFit.DataError(ROOT.RooAbsData.SumW2), ROOT.RooFit.MarkerSize(0.5))

# frame.Draw()
# ROOT.gPad.SetLogy()

# # rescale histogram to same area as dataset
# dy_frac = dy_n / total_n
# dy_bkg.Scale(dataset.sumEntries() / total_distro.Integral() * dy_frac)
# dy_bkg.SetLineColor(ROOT.kRed)
# dy_bkg.Draw("same")

# jpsi_frac = jpsi_n / total_n
# jpsi_bkg.Scale(dataset.sumEntries() / total_distro.Integral() * jpsi_frac)
# jpsi_bkg.SetLineColor(ROOT.kBlue)
# jpsi_bkg.Draw("same")

# psi2s_frac = psi2s_n / total_n
# psi2s_bkg.Scale(dataset.sumEntries() / total_distro.Integral() * psi2s_frac)
# psi2s_bkg.SetLineColor(ROOT.kGreen)
# psi2s_bkg.Draw("same")

# # rescale histogram to same area as dataset
# total_distro.Scale(dataset.sumEntries() / total_distro.Integral())
# total_distro.Draw("same")

# # compute chi2 of data wrt total model
# chi2 = total_distro.Chi2Test(data_h, "WW CHI2")
# n_free_params = f_datacard.Get("w").pdf("model_b").getParameters(f_datacard.Get("w").data("data_obs")).selectByAttrib("Constant", False).getSize()
# reduced_chi2 = chi2 / (total_distro.GetNbinsX() - 1 - n_free_params)

# # Make legend
# legend = ROOT.TLegend(0.2, 0.15, 0.5, 0.5)
# legend.SetFillStyle(0)
# legend.SetBorderSize(0)
# legend.SetTextSize(0.03)
# legend.AddEntry(dataset, "Data", "p")
# legend.AddEntry(total_distro, f"#splitline{{Total B Fit = {total_n:.0f}}}{{chi2/ndof = {reduced_chi2:.2f}}}", "l")
# legend.AddEntry(dy_bkg, f"DY bkg = {dy_n:.0f}", "l")
# legend.AddEntry(jpsi_bkg, f"J/psi bkg = {jpsi_n:.0f}", "l")
# legend.AddEntry(psi2s_bkg, f"psi(2S) bkg = {psi2s_n:.0f}", "l")
# legend.Draw()

# frame.SetMinimum(1)

# for ext in ['png', 'pdf']:
#     c.SaveAs(os.path.join(args.output_folder, "b", f"mu1_fit_b_M{args.mass:.1f}.{ext}"))

total_distro = f2.Get("shapes_fit_s/Xee_ee_0_2023/total")
dy_bkg = f2.Get("shapes_fit_s/Xee_ee_0_2023/dy")
psi2s_bkg = f2.Get("shapes_fit_s/Xee_ee_0_2023/psi2s")
jpsi_bkg = f2.Get("shapes_fit_s/Xee_ee_0_2023/jpsi")
signal = f2.Get("shapes_fit_s/Xee_ee_0_2023/Zd")

total_n = f2.Get("norm_fit_s").selectByName("Xee_ee_0_2023/total").first().getValV()
dy_n = f2.Get("norm_fit_s").selectByName("Xee_ee_0_2023/dy").first().getValV()
psi2s_n = f2.Get("norm_fit_s").selectByName("Xee_ee_0_2023/psi2s").first().getValV()
jpsi_n = f2.Get("norm_fit_s").selectByName("Xee_ee_0_2023/jpsi").first().getValV()
signal_n = f2.Get("norm_fit_s").selectByName("Xee_ee_0_2023/Zd").first().getValV()

c2 = ROOT.TCanvas("c2", "c2", 800, 800)

# split canvas between 70% for plot and 30% for pulls
c2.Divide(1, 2)
c2.cd(1)
ROOT.gPad.SetPad(0, 0.3, 1, 1)
ROOT.gPad.SetBottomMargin(0.001)
ROOT.gPad.SetGrid()
c2.cd(2)
# ROOT.gPad.SetTopMargin(0)
ROOT.gPad.SetPad(0, 0, 1, 0.3)
ROOT.gPad.SetGrid()

c2.cd(1)

frame = m.frame(2, 4.2)
frame.SetTitle("")
frame.GetXaxis().SetTitle("m(ee) [GeV]")

dataset.plotOn(frame, ROOT.RooFit.DataError(ROOT.RooAbsData.SumW2), ROOT.RooFit.MarkerSize(0.5))

frame.Draw()
ROOT.gPad.SetLogy()

# rescale histogram to same area as dataset
colors = ["#5790fc", "#f89c20", "#e42536"]

dy_bkg.Scale(total_distro.GetBinWidth(1))
dy_bkg.SetLineColor(ROOT.TColor.GetColor(colors[0]))
dy_bkg.Draw("same")

jpsi_bkg.Scale(total_distro.GetBinWidth(1))
jpsi_bkg.SetLineColor(ROOT.TColor.GetColor(colors[1]))
jpsi_bkg.Draw("same")

psi2s_bkg.Scale(total_distro.GetBinWidth(1))
psi2s_bkg.SetLineColor(ROOT.TColor.GetColor(colors[2]))
psi2s_bkg.Draw("same")

signal.Scale(total_distro.GetBinWidth(1))
signal.SetLineColor(ROOT.kBlack)
signal.SetLineWidth(2)
signal.Draw("same")

# rescale histogram to same area as dataset
total_distro.Scale(total_distro.GetBinWidth(1))
total_distro.Draw("same")

# compute chi2 of data wrt total model
# make histogram for later chi2 computation
data_h = dataset.createHistogram("data_hist", m, ROOT.RooFit.Binning(total_distro.GetNbinsX()))
data_h.Sumw2()

chi2 = total_distro.Chi2Test(data_h, "WW CHI2")
n_free_params = f_datacard.Get("w").pdf("model_s").getParameters(f_datacard.Get("w").data("data_obs")).selectByAttrib("Constant", False).getSize()
reduced_chi2 = chi2 / (total_distro.GetNbinsX() - 1 - n_free_params)

# Make legend
legend = ROOT.TLegend(0.2, 0.15, 0.5, 0.5)
legend.SetFillStyle(0)
legend.SetBorderSize(0)
legend.SetTextSize(0.03)
legend.AddEntry(dataset, "Data", "p")
legend.AddEntry(total_distro, f"#splitline{{Total S+B Fit = {total_n:.0f}}}{{chi2/ndof = {reduced_chi2:.2f}}}", "l")
legend.AddEntry(dy_bkg, f"DY bkg = {dy_n:.0f}", "l")
legend.AddEntry(jpsi_bkg, f"J/psi bkg = {jpsi_n:.0f}", "l")
legend.AddEntry(psi2s_bkg, f"psi(2S) bkg = {psi2s_n:.0f}", "l")
legend.AddEntry(signal, f"Signal = {signal_n:.0f}", "l")
legend.Draw()

frame.SetMinimum(4e1)
frame.SetMaximum(3e6)
# frame.SetMaximum(8e4)

c2.cd(2)
# compute pulls
pulls = ROOT.TGraphAsymmErrors()

for i in range(total_distro.GetNbinsX()):
    x = total_distro.GetBinCenter(i + 1)
    y = total_distro.GetBinContent(i + 1)
    data_y = data_h.GetBinContent(i + 1)
    data_y_err = data_h.GetBinError(i + 1)

    pull_value = (data_y - y) / data_y_err
    pulls.SetPoint(i, x, pull_value)
    pulls.SetPointError(i, 0, 0, 1, 1)

pulls.SetMarkerStyle(20)
pulls.SetMarkerSize(0.5)

# change x-axis range to match the frame
pulls.GetXaxis().SetLimits(frame.GetXaxis().GetXmin(), frame.GetXaxis().GetXmax())
pulls.GetXaxis().SetTitle("m(ee) [GeV]")
pulls.GetXaxis().SetLabelSize(0.07)
pulls.GetXaxis().SetTitleSize(0.1)
pulls.GetYaxis().SetTitle("Pulls")
pulls.GetYaxis().SetLabelSize(0.07)
pulls.GetYaxis().SetTitleSize(0.1)
pulls.GetYaxis().SetTitleOffset(0.3)

# change bottom padding
ROOT.gPad.SetBottomMargin(0.25)
pulls.Draw("AP E1")

# draw horizontal line at 0
line = ROOT.TLine(frame.GetXaxis().GetXmin(), 0, frame.GetXaxis().GetXmax(), 0)
line.SetLineColor(ROOT.kGray)
line.SetLineStyle(2)
line.Draw("same")

for ext in ['png', 'pdf']:
    c2.SaveAs(os.path.join(args.output_folder, "s", f"mu1_fit_s_M{args.mass:.1f}.{ext}"))


# close all files
f1.Close()
f2.Close()
f_datacard.Close()