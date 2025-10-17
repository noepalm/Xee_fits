import ROOT
import argparse
import os

# argparse
parser = argparse.ArgumentParser()
parser.add_argument('-i', '--input', type=str, default='Xee_ee_0_2023.root', help='File containing input dataset and models; output of text2workspace')
parser.add_argument('-f', '--fit_file', type=str, default='fitDiagnosticsTest.root', help='File containing fit results')
parser.add_argument('-o', '--output_folder', type=str, default='plots', help='Output folder')
parser.add_argument('-m', '--mass', type=float, default=3.0, help='Mass value to plot')
parser.add_argument('-c', '--cat_id', type=int, default=0, help='Category ID to plot')
parser.add_argument('-r', '--region', type=str, default='region1', choices=["region0", "region1", "region2"],)
parser.add_argument('--tag', type=str, default='', help='Tag to append to output folder name')

args = parser.parse_args()
cat_id = args.cat_id
tag_label = f"_{args.tag}" if args.tag else ""

# print all arguments
print("Arguments:")
for arg in vars(args):
    print(f"{arg}: {getattr(args, arg)}")

# now retrieve RooRealVar to plot from other workspace
f1 = ROOT.TFile.Open(args.input, "READ")
m = f1.Get("w").var("mass")
m_min = m.getMin()
m_max = m.getMax()
dataset = f1.Get("w").data("data_obs")

# finally, retrieve total S+B fit distribution from last file
f2 = ROOT.TFile.Open(args.fit_file, "READ")
# total_distro = f2.Get(f"shapes_fit_b/Xee_ee_{cat_id}_2023/total_background")
# dy_bkg = f2.Get(f"shapes_fit_b/Xee_ee_{cat_id}_2023/dy")
# psi2s_bkg = f2.Get(f"shapes_fit_b/Xee_ee_{cat_id}_2023/psi2s")
# jpsi_bkg = f2.Get(f"shapes_fit_b/Xee_ee_{cat_id}_2023/jpsi")
# dy_n = f2.Get("norm_fit_b").selectByName(f"Xee_ee_{cat_id}_2023/dy").first().getValV()
# psi2s_n = f2.Get("norm_fit_b").selectByName(f"Xee_ee_{cat_id}_2023/psi2s").first().getValV()
# jpsi_n = f2.Get("norm_fit_b").selectByName(f"Xee_ee_{cat_id}_2023/jpsi").first().getValV()
# total_n = f2.Get("norm_fit_b").selectByName(f"Xee_ee_{cat_id}_2023/total_background").first().getValV()

if args.region == "region1":
    resonant_bkgs = ["jpsi", "psi2s"]
elif args.region == "region2":
    resonant_bkgs = ["upsilon1s"]
else:
    resonant_bkgs = []

all_bkgs = ["dy"] + resonant_bkgs + ["total_background"]
bkg_components = ["dy"] + resonant_bkgs
bkg_component_labels = ["DY", "J/psi", "psi(2S)"] if args.region == "region1" else ["DY", "Upsilon(1S)"]

bkgs = {bkg_name : f2.Get(f"shapes_fit_b/Xee_ee_{cat_id}_2023/{bkg_name}") for bkg_name in all_bkgs}
bkg_norms = {bkg_name : f2.Get("norm_fit_b").selectByName(f"Xee_ee_{cat_id}_2023/{bkg_name}").first().getValV() for bkg_name in all_bkgs}


# draw
ROOT.gROOT.SetBatch()

c = ROOT.TCanvas("c", "c", 800, 800)

# split canvas between 70% for plot and 30% for pulls
c.Divide(1, 2)
c.cd(1)
ROOT.gPad.SetPad(0, 0.3, 1, 1)
ROOT.gPad.SetBottomMargin(0.001)
ROOT.gPad.SetGrid()
c.cd(2)
# ROOT.gPad.SetTopMargin(0)
ROOT.gPad.SetPad(0, 0, 1, 0.3)
ROOT.gPad.SetGrid()

c.cd(1)
frame = m.frame(m_min, m_max)
frame.SetTitle("")
frame.GetXaxis().SetTitle("m(ee) [GeV]")

dataset.plotOn(frame, ROOT.RooFit.DataError(ROOT.RooAbsData.SumW2), ROOT.RooFit.MarkerSize(0.5))

frame.Draw()
ROOT.gPad.SetLogy()

# colors = ["#5790fc", "#f89c20", "#e42536"]

colors = [
    "#3f90da",
    "#ffa90e",
    "#bd1f01",
    "#94a4a2",
    "#832db6",
    "#a96b59",
    "#e76300",
]

# rescale histogram to same area as dataset
for idx, bkg_name in enumerate(all_bkgs):
    bkgs[bkg_name].Scale(bkgs[bkg_name].GetBinWidth(1))
    if bkg_name != "total_background":
        bkgs[bkg_name].SetLineColor(ROOT.TColor.GetColor(colors[idx]))
    bkgs[bkg_name].Draw("same")

# dy_bkg.Scale(dy_bkg.GetBinWidth(1))
# dy_bkg.SetLineColor(ROOT.TColor.GetColor(colors[0]))
# dy_bkg.Draw("same")

# jpsi_bkg.Scale(jpsi_bkg.GetBinWidth(1))
# jpsi_bkg.SetLineColor(ROOT.TColor.GetColor(colors[1]))
# jpsi_bkg.Draw("same")

# psi2s_bkg.Scale(jpsi_bkg.GetBinWidth(1))
# psi2s_bkg.SetLineColor(ROOT.TColor.GetColor(colors[2]))
# psi2s_bkg.Draw("same")

# # rescale histogram to same area as dataset
# total_distro.Scale(total_distro.GetBinWidth(1))
# total_distro.Draw("same")

# compute chi2 of data wrt total model
data_h = dataset.createHistogram("data_hist", m, ROOT.RooFit.Binning(bkgs["total_background"].GetNbinsX()))
data_h.Sumw2()
chi2 = bkgs["total_background"].Chi2Test(data_h, "UU CHI2")
n_free_params = f1.Get("w").pdf("model_b").getParameters(f1.Get("w").data("data_obs")).selectByAttrib("Constant", False).getSize()
reduced_chi2 = chi2 / (bkgs["total_background"].GetNbinsX() - 1 - n_free_params)

# Make legend
legend = ROOT.TLegend(0.2, 0.15, 0.5, 0.5)
legend.SetFillStyle(0)
legend.SetBorderSize(0)
legend.SetTextSize(0.03)
legend.AddEntry(dataset, "Data", "p")
legend.AddEntry(bkgs["total_background"], f"#splitline{{Total B Fit = {bkg_norms['total_background']:.0f}}}{{chi2/ndof = {reduced_chi2:.2f}}}", "l")
for bkg_label, (bkg_name, bkg_norm) in zip(bkg_component_labels, bkg_norms.items()):
    legend.AddEntry(bkgs[bkg_name], f"{bkg_label} bkg = {bkg_norm:.0f}", "l")
# legend.AddEntry(dy_bkg, f"DY bkg = {dy_n:.0f}", "l")
# legend.AddEntry(jpsi_bkg, f"J/psi bkg = {jpsi_n:.0f}", "l")
# legend.AddEntry(psi2s_bkg, f"psi(2S) bkg = {psi2s_n:.0f}", "l")
legend.Draw()

if args.region == "region1":
    frame.SetMinimum(0.1)
elif args.region == "region2":
    frame.SetMinimum(10)

frame.SetMaximum(data_h.GetMaximum() * 5)

c.cd(2)
# compute pulls
pulls = ROOT.TGraphAsymmErrors()

for i in range(bkgs["total_background"].GetNbinsX()):
    x = bkgs["total_background"].GetBinCenter(i + 1)
    y = bkgs["total_background"].GetBinContent(i + 1)
    data_y = data_h.GetBinContent(i + 1)
    data_y_err = data_h.GetBinError(i + 1)

    # print(f"DEBUG: Bin {i+1}: x = {x}, y = {y}, data_y = {data_y}, data_y_err = {data_y_err}", flush = True)

    # print(f"DEBUG: x = {x}, y = {y}, data_y = {data_y}, data_y_err = {data_y_err}", flush = True)
    # print(f"       total bkg = {bkg_norms['total_background']}, dy = {bkg_norms['dy']}, jpsi = {bkg_norms.get('jpsi', 'N/A')}, psi2s = {bkg_norms.get('psi2s', 'N/A')}", flush = True)

    pull_value = 0
    if data_y_err > 0:
        pull_value = (data_y - y) / data_y_err
    else:
        print(f"WARNING: data_y_err is zero at bin {i+1}, setting pull to 0", flush = True)
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
    c.SaveAs(os.path.join(args.output_folder, "b", f"mu0_fit_b_M{args.mass:.1f}{tag_label}.{ext}"))

all_funcs = resonant_bkgs + ["dy", "Zd", "total"]
all_distros = {name: f2.Get(f"shapes_fit_s/Xee_ee_{cat_id}_2023/{name}") for name in all_funcs}
all_norms = {name: f2.Get("norm_fit_s").selectByName(f"Xee_ee_{cat_id}_2023/{name}").first().getValV() for name in all_funcs}
all_distro_labels = ["J/psi", "psi(2S)", "DY", "Signal", "Total S+B"] if args.region == "region1" else ["Upsilon(1S)", "DY","Signal", "Total S+B"]

# total_distro = f2.Get(f"shapes_fit_s/Xee_ee_{cat_id}_2023/total")
# dy_bkg = f2.Get(f"shapes_fit_s/Xee_ee_{cat_id}_2023/dy")
# psi2s_bkg = f2.Get(f"shapes_fit_s/Xee_ee_{cat_id}_2023/psi2s")
# jpsi_bkg = f2.Get(f"shapes_fit_s/Xee_ee_{cat_id}_2023/jpsi")
# signal = f2.Get(f"shapes_fit_s/Xee_ee_{cat_id}_2023/Zd")

# total_n = f2.Get("norm_fit_s").selectByName(f"Xee_ee_{cat_id}_2023/total").first().getValV()
# dy_n = f2.Get("norm_fit_s").selectByName(f"Xee_ee_{cat_id}_2023/dy").first().getValV()
# psi2s_n = f2.Get("norm_fit_s").selectByName(f"Xee_ee_{cat_id}_2023/psi2s").first().getValV()
# jpsi_n = f2.Get("norm_fit_s").selectByName(f"Xee_ee_{cat_id}_2023/jpsi").first().getValV()
# signal_n = f2.Get("norm_fit_s").selectByName(f"Xee_ee_{cat_id}_2023/Zd").first().getValV()

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

frame = m.frame(m_min, m_max)
frame.SetTitle("")
frame.GetXaxis().SetTitle("m(ee) [GeV]")

dataset.plotOn(frame, ROOT.RooFit.DataError(ROOT.RooAbsData.SumW2), ROOT.RooFit.MarkerSize(0.5))

frame.Draw()
ROOT.gPad.SetLogy()

# rescale histogram to same area as dataset
for idx, (distro_name, distro) in enumerate(all_distros.items()):
    distro.Scale(distro.GetBinWidth(1))
    if list(all_distros.keys())[idx] != "":
        distro.SetLineColor(ROOT.TColor.GetColor(colors[idx]))
    if distro_name == "Zd":
        distro.SetLineColor(ROOT.kBlack)
        distro.SetLineWidth(2)
    distro.Draw("same")

# dy_bkg.Scale(dy_bkg.GetBinWidth(1))
# dy_bkg.SetLineColor(ROOT.TColor.GetColor(colors[0]))
# dy_bkg.Draw("same")

# jpsi_bkg.Scale(jpsi_bkg.GetBinWidth(1))
# jpsi_bkg.SetLineColor(ROOT.TColor.GetColor(colors[1]))
# jpsi_bkg.Draw("same")

# psi2s_bkg.Scale(jpsi_bkg.GetBinWidth(1))
# psi2s_bkg.SetLineColor(ROOT.TColor.GetColor(colors[2]))
# psi2s_bkg.Draw("same")

# signal.Scale(signal.GetBinWidth(1))
# signal.SetLineColor(ROOT.kBlack)
# signal.SetLineWidth(2)
# signal.Draw("same")

# # rescale histogram to same area as dataset
# total_distro.Scale(total_distro.GetBinWidth(1))
# total_distro.Draw("same")

# compute chi2 of data wrt total model
chi2 = all_distros["total"].Chi2Test(data_h, "UU CHI2")
n_free_params = f1.Get("w").pdf("model_s").getParameters(f1.Get("w").data("data_obs")).selectByAttrib("Constant", False).getSize()
reduced_chi2 = chi2 / (all_distros["total"].GetNbinsX() - 1 - n_free_params)

# change minimum to 0.1
if args.region == "region1":
    frame.SetMinimum(0.1)
elif args.region == "region2":
    frame.SetMinimum(10)

frame.SetMaximum(data_h.GetMaximum() * 5)

# Make legend
legend = ROOT.TLegend(0.2, 0.15, 0.5, 0.5)
legend.SetFillStyle(0)
legend.SetBorderSize(0)
legend.SetTextSize(0.03)
legend.AddEntry(dataset, "Data", "p")
legend.AddEntry(all_distros["total"], f"#splitline{{Total S+B Fit = {all_norms['total']:.0f}}}{{chi2/ndof = {reduced_chi2:.2f}}}", "l")
for distro_label, (distro_name, norm) in zip(all_distro_labels, all_norms.items()):
    if distro_name != "total":
        legend.AddEntry(all_distros[distro_name], f"{distro_label} = {norm:.0f}", "l")
# legend.AddEntry(dy_bkg, f"DY bkg = {dy_n:.0f}", "l")
# legend.AddEntry(jpsi_bkg, f"J/psi bkg = {jpsi_n:.0f}", "l")
# legend.AddEntry(psi2s_bkg, f"psi(2S) bkg = {psi2s_n:.0f}", "l")
# legend.AddEntry(signal, f"Signal = {signal_n:.0f}", "l")
legend.Draw()

c2.cd(2)
# compute pulls
pulls = ROOT.TGraphAsymmErrors()

for i in range(all_distros["total"].GetNbinsX()):
    x = all_distros["total"].GetBinCenter(i + 1)
    y = all_distros["total"].GetBinContent(i + 1)
    data_y = data_h.GetBinContent(i + 1)
    data_y_err = data_h.GetBinError(i + 1)

    print(f"DEBUG: Bin {i+1}: x = {x}, y = {y}, data_y = {data_y}, data_y_err = {data_y_err}", flush = True)

    pull_value = 0
    if data_y_err > 0:
        pull_value = (data_y - y) / data_y_err
    else:
        print(f"WARNING: data_y_err is zero at bin {i+1}, setting pull to 0", flush = True)
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
    c2.SaveAs(os.path.join(args.output_folder, "s", f"mu0_fit_s_M{args.mass:.1f}{tag_label}.{ext}"))
