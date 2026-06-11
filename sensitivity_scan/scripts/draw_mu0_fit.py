import ROOT
import argparse
import os
from math import sqrt

# argparse
parser = argparse.ArgumentParser()
parser.add_argument('-i', '--input', type=str, default='Xee_ee_4_2023.root', help='File containing input dataset and models; output of text2workspace')
parser.add_argument('-f', '--fit_file', type=str, default='fitDiagnosticsTest.root', help='File containing fit results')
parser.add_argument('-o', '--output_folder', type=str, default='plots', help='Output folder')
parser.add_argument('-m', '--mass', type=float, default=3.0, help='Mass value to plot')
parser.add_argument('-c', '--cat_id', type=int, default=4, help='Category ID to plot')
parser.add_argument('-r', '--region', type=str, default='region1', choices=["region0", "region1", "region2"],)
parser.add_argument('--era', type=str, default='2023', choices=["2022", "2022EE", "2023", "2023BPix", "allYears"], help='Data-taking era')
# parser.add_argument("--no_res", type=bool, default=False, help='Exclude resonant backgrounds from the plot')
parser.add_argument('--binned', type=bool, default=False, help='Use binned dataset for plotting')
parser.add_argument('--tag', type=str, default='', help='Tag to append to output folder name')

args = parser.parse_args()
cat_id = args.cat_id
tag_label = f"_{args.tag}" if args.tag else ""
era = args.era

# print all arguments
print("Arguments:")
for arg in vars(args):
    print(f"{arg}: {getattr(args, arg)}")

# now retrieve RooRealVar to plot from other workspace
f1 = ROOT.TFile.Open(args.input, "READ")
m = f1.Get("w").var("mass")
m_min = m.getMin()
m_max = m.getMax()
print(f"Mass range: {m_min} - {m_max}")

lumi = 6.68

# if running binned, need to retrieve INPUT dataset to get correct uncertainties
if args.binned:
    f2 = ROOT.TFile.Open(f"../common/Xee_ee_{era}.input.root", "READ")
    dataset = f2.Get("w").data("data_obs")
    # also retrieve luminosity
    lumi = f2.Get("w").var(f"luminosity_{era}").getVal()
else:
    dataset = f1.Get("w").data("data_obs")

print(f"Running on luminosity: {lumi} fb^-1")

# # DEBUG: iterate over dataset entries and print weight + weightError
# for i in range(dataset.numEntries()):
#     entry = dataset.get(i)
#     weight = dataset.weight()
#     weight_error = dataset.weightError(ROOT.RooAbsData.SumW2)
#     print(f"DEBUG: Entry {i}: weight = {weight}, weight_error = {weight_error}")

error_type = ROOT.RooAbsData.Poisson if args.binned and "data" not in args.tag else ROOT.RooAbsData.SumW2

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

# Define region-specific configurations
region_config = {
    "region0": {
        # "resonant_bkgs": ["phi", "omega", "eta"],
        # "bkg_labels": ["Non-resonant", "#phi", "#omega", "#eta"],
        # "all_labels": ["#phi", "#omega", "#eta", "Non-resonant", "Signal", "Total S+B"]
        "resonant_bkgs": ["phi", "omega"],
        "bkg_labels": ["Non-resonant", "#phi", "#omega"],
        "all_labels": ["#phi", "#omega", "Non-resonant", "Signal", "Total S+B"]
    },
    "region1": {
        "resonant_bkgs": ["jpsi", "psi2s"],
        "bkg_labels": ["Non-resonant", "J/#psi", "#psi(2S)"],
        "all_labels": ["J/#psi", "#psi(2S)", "Non-resonant", "Signal", "Total S+B"]
    },
    "region2": {
        "resonant_bkgs": ["upsilon1s"],
        "bkg_labels": ["Non-resonant", "#Upsilon(1S)"],
        "all_labels": ["#Upsilon(1S)", "Non-resonant", "Signal", "Total S+B"]
    }
}

# if args.no_res:
#     print(f"DEBUG: No resonant backgrounds will be included in the plot", flush=True)
#     for region in ["region0", "region1", "region2"]:
#         region_config[region]["resonant_bkgs"] = []
#         region_config[region]["bkg_labels"] = ["Non-resonant"]
#         region_config[region]["all_labels"] = ["Non-resonant", "Signal", "Total S+B"]

resonant_bkgs = region_config[args.region]["resonant_bkgs"]
all_bkgs = ["dy"] + resonant_bkgs + ["total_background"]
bkg_components = ["dy"] + resonant_bkgs
bkg_component_labels = region_config[args.region]["bkg_labels"]

# Build channel name based on era
channel_name = f"Xee_ee_{cat_id}_{era}"

for bkg_name in all_bkgs:
    print(f'DEBUG: {f2.Get("norm_fit_b").selectByName(f"{channel_name}/{bkg_name}").first()}')

bkgs = {bkg_name : f2.Get(f"shapes_fit_b/{channel_name}/{bkg_name}") for bkg_name in all_bkgs}
bkg_norms = {bkg_name : f2.Get("norm_fit_b").selectByName(f"{channel_name}/{bkg_name}").first().getValV() for bkg_name in all_bkgs}


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

dataset.plotOn(frame, ROOT.RooFit.DataError(error_type), ROOT.RooFit.MarkerSize(0.5))

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

# # compute chi2 of data wrt total model
# data_h = dataset.createHistogram("data_hist", m, ROOT.RooFit.Binning(bkgs["total_background"].GetNbinsX()))
# chi2 = bkgs["total_background"].Chi2Test(data_h, "UU CHI2")
# n_free_params = f1.Get("w").pdf("model_b").getParameters(f1.Get("w").data("data_obs")).selectByAttrib("Constant", False).getSize()
# reduced_chi2 = chi2 / (bkgs["total_background"].GetNbinsX() - 1 - n_free_params)
# print("DEBUG: chi2 =", chi2, "nbins =", bkgs ["total_background"].GetNbinsX(), "n_free_params =", n_free_params, "reduced_chi2 =", reduced_chi2)

# compute chi2 manually from bins
data_h = dataset.createHistogram("data_hist", m, ROOT.RooFit.Binning(bkgs["total_background"].GetNbinsX()))

chi2 = 0.0
for i in range(1, data_h.GetNbinsX() + 1):
    obs = data_h.GetBinContent(i)
    exp = bkgs["total_background"].GetBinContent(i)
    err = data_h.GetBinError(i)
    if err > 0:
        chi2 += ((obs - exp) / err)**2

n_free_params = f1.Get("w").pdf("model_b").getParameters(f1.Get("w").data("data_obs")).selectByAttrib("Constant", False).getSize()
ndof = bkgs["total_background"].GetNbinsX() - 1 - n_free_params
reduced_chi2 = chi2 / ndof if ndof > 0 else 0
print(f"DEBUG: chi2 = {chi2:.2f}, nbins = {bkgs['total_background'].GetNbinsX()}, n_free_params = {n_free_params}, reduced_chi2 = {reduced_chi2:.2f}")

# Make legend
xmin = 0.5 if args.region == "region0" else 0.535 #if args.region == "region1" else 0.2
ymin = 0.15 if args.region == "region0" else 0.6 #if args.region == "region1" else 0.2
# yheight = 0.25 if args.region == "region1" else 0.35
yheight = 0.35 if args.region == "region0" else 0.25
legend = ROOT.TLegend(xmin, ymin, xmin + 0.3, ymin + yheight)
legend.SetFillStyle(0)
legend.SetBorderSize(0)
legend.SetTextSize(0.03)
legend.AddEntry(dataset, "Data", "p")
legend.AddEntry(bkgs["total_background"], f"#splitline{{Total B Fit = {bkg_norms['total_background']:.0f}}}{{chi2/ndof = {chi2:.2f} / {(bkgs['total_background'].GetNbinsX() - 1 - n_free_params):.0f} = {reduced_chi2:.2f}}}", "l")
for bkg_label, (bkg_name, bkg_norm) in zip(bkg_component_labels, bkg_norms.items()):
    legend.AddEntry(bkgs[bkg_name], f"{bkg_label} bkg = {bkg_norm:.0f}", "l")
# legend.AddEntry(dy_bkg, f"DY bkg = {dy_n:.0f}", "l")
# legend.AddEntry(jpsi_bkg, f"J/psi bkg = {jpsi_n:.0f}", "l")
# legend.AddEntry(psi2s_bkg, f"psi(2S) bkg = {psi2s_n:.0f}", "l")
legend.Draw()

# Add CMS labels
latex = ROOT.TLatex()
latex.SetNDC()
latex.SetTextFont(42)
latex.SetTextSize(0.045)

# CMS Preliminary label (top left)
latex_cms = ROOT.TLatex()
latex_cms.SetNDC()
latex_cms.SetTextFont(61)  # Bold font for "CMS"
latex_cms.SetTextSize(0.05)
latex_cms.DrawLatex(0.1, 0.92, "CMS")

latex_prelim = ROOT.TLatex()
latex_prelim.SetNDC()
latex_prelim.SetTextFont(52)  # Italic font for "Preliminary"
latex_prelim.SetTextSize(0.04)
latex_prelim.DrawLatex(0.18, 0.92, "Preliminary")

# Luminosity and energy label (top right)
latex.SetTextAlign(31)  # Right align
latex.DrawLatex(0.91, 0.92, f"{lumi:.2f}" + " fb^{-1} (13.6 TeV)")

# if args.region == "region1":
#     frame.SetMinimum(8e2)
# elif args.region == "region2":
#     frame.SetMinimum(10)
# elif args.region == "region0":
#     frame.SetMinimum(1)

if args.region == "region1":
    frame.SetMinimum(10)
elif args.region == "region2":
    frame.SetMinimum(1)
elif args.region == "region0":
    frame.SetMinimum(1)

max_factor = 2 if args.region == "region1" else 5

frame.SetMaximum(data_h.GetMaximum() * max_factor)

c.cd(2)
# compute pulls
pulls = ROOT.TGraphAsymmErrors()

for i in range(bkgs["total_background"].GetNbinsX()):
    x = bkgs["total_background"].GetBinCenter(i + 1)
    y = bkgs["total_background"].GetBinContent(i + 1)
    data_y = data_h.GetBinContent(i + 1)
    data_y_err = data_h.GetBinError(i + 1)

    # print(f"DEBUG: Bin {i+1}: x = {x}, y = {y}, data_y = {data_y}, data_y_err = {data_y_err} => pull = {(data_y - y)/data_y_err}", flush = True)

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

# # change y-axis limits to +/- 5
# pulls.GetYaxis().SetRangeUser(-5, 5)

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
all_distros = {name: f2.Get(f"shapes_fit_s/{channel_name}/{name}") for name in all_funcs}
all_norms = {name: f2.Get("norm_fit_s").selectByName(f"{channel_name}/{name}").first().getValV() for name in all_funcs}
all_distro_labels = region_config[args.region]["all_labels"]

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

dataset.plotOn(frame, ROOT.RooFit.DataError(error_type), ROOT.RooFit.MarkerSize(0.5))

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

# # compute chi2 of data wrt total model
# chi2 = all_distros["total"].Chi2Test(data_h, "UU CHI2")
# n_free_params = f1.Get("w").pdf("model_s").getParameters(f1.Get("w").data("data_obs")).selectByAttrib("Constant", False).getSize()
# reduced_chi2 = chi2 / (all_distros["total"].GetNbinsX() - 1 - n_free_params)

# compute chi2 manually from bins
chi2 = 0.0
for i in range(1, data_h.GetNbinsX() + 1):
    obs = data_h.GetBinContent(i)
    exp = all_distros["total"].GetBinContent(i)
    err = data_h.GetBinError(i)
    if err > 0:
        chi2 += ((obs - exp) / err)**2

n_free_params = f1.Get("w").pdf("model_s").getParameters(f1.Get("w").data("data_obs")).selectByAttrib("Constant", False).getSize()
ndof = all_distros["total"].GetNbinsX() - 1 - n_free_params
reduced_chi2 = chi2 / ndof if ndof > 0 else 0

# # change minimum to 0.1
# if args.region == "region1":
#     frame.SetMinimum(0.1)
# elif args.region == "region2":
#     frame.SetMinimum(10)
# elif args.region == "region0":
#     frame.SetMinimum(1)

# change minimum to 0.1
if args.region == "region1":
    frame.SetMinimum(10)
elif args.region == "region2":
    frame.SetMinimum(1)
elif args.region == "region0":
    frame.SetMinimum(1)

frame.SetMaximum(data_h.GetMaximum() * 5)

# Make legend
xmin = 0.5 if args.region == "region0" else 0.535 # if args.region == "region1" else 0.2
ymin = 0.15 if args.region == "region0" else 0.6 # if args.region == "region1" else 0.2
# yheight = 0.25 if args.region == "region1" else 0.35
yheight = 0.35 if args.region == "region0" else 0.25
legend = ROOT.TLegend(xmin, ymin, xmin + 0.3, ymin + yheight)
legend.SetFillStyle(0)
legend.SetBorderSize(0)
legend.SetTextSize(0.03)
legend.AddEntry(dataset, "Data", "p")
legend.AddEntry(all_distros["total"], f"#splitline{{Total S+B Fit = {all_norms['total']:.0f}}}{{chi2/ndof = {chi2:.2f} / {(all_distros['total'].GetNbinsX() - 1 - n_free_params):.0f} = {reduced_chi2:.2f}}}", "l")
for distro_label, (distro_name, norm) in zip(all_distro_labels, all_norms.items()):
    if distro_name != "total":
        legend.AddEntry(all_distros[distro_name], f"{distro_label} = {norm:.0f}", "l")
# legend.AddEntry(dy_bkg, f"DY bkg = {dy_n:.0f}", "l")
# legend.AddEntry(jpsi_bkg, f"J/psi bkg = {jpsi_n:.0f}", "l")
# legend.AddEntry(psi2s_bkg, f"psi(2S) bkg = {psi2s_n:.0f}", "l")
# legend.AddEntry(signal, f"Signal = {signal_n:.0f}", "l")
legend.Draw()

# Add CMS labels
latex2 = ROOT.TLatex()
latex2.SetNDC()
latex2.SetTextFont(42)
latex2.SetTextSize(0.045)

# CMS Preliminary label (top left)
latex_cms2 = ROOT.TLatex()
latex_cms2.SetNDC()
latex_cms2.SetTextFont(61)  # Bold font for "CMS"
latex_cms2.SetTextSize(0.05)
latex_cms2.DrawLatex(0.12, 0.91, "CMS")

latex_prelim2 = ROOT.TLatex()
latex_prelim2.SetNDC()
latex_prelim2.SetTextFont(52)  # Italic font for "Preliminary"
latex_prelim2.SetTextSize(0.04)
latex_prelim2.DrawLatex(0.20, 0.91, "Preliminary")

# Luminosity and energy label (top right)
latex2.SetTextAlign(31)  # Right align
latex2.DrawLatex(0.90, 0.91, f"{lumi:.2f}" + " fb^{-1} (13.6 TeV)")

c2.cd(2)
# compute pulls
pulls = ROOT.TGraphAsymmErrors()

for i in range(all_distros["total"].GetNbinsX()):
    x = all_distros["total"].GetBinCenter(i + 1)
    y = all_distros["total"].GetBinContent(i + 1)
    data_y = data_h.GetBinContent(i + 1)
    data_y_err = data_h.GetBinError(i + 1)

    # print(f"DEBUG: Bin {i+1}: x = {x}, y = {y}, data_y = {data_y}, data_y_err = {data_y_err}", flush = True)

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

# CLOSE ALL FILES
f1.Close()
if args.binned:
    f2.Close()