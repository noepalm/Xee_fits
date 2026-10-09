import ROOT
import argparse
import os
from math import sqrt
from pathlib import Path

# ==============================================================================
# CONFIGURATION: Custom Bounds
# ==============================================================================
# CUSTOM_XMIN = 1.7   # e.g. 1.8
# CUSTOM_XMAX = 2.2   # e.g. 2.2

CUSTOM_XMIN = 7.5   # e.g. 1.8
CUSTOM_XMAX = 10   # e.g. 2.2

# Manual per-era Y-bounds (None enables automatic computation)
ERA_Y_BOUNDS = {
    "2022":     None,
    "2022EE":   None,
    "2023":     None,
    "2023BPix": None,
    "allYears": None,
}

AUTO_YMAX_FACTOR = 1.2  # buffer above highest point in [xmin, xmax]
AUTO_YMIN_FACTOR = 0.8  # buffer below lowest non-zero point in [xmin, xmax]
ABS_YMIN_FLOOR   = 0.5   # absolute positive floor (log scale)

PULL_YMIN = -4.5
PULL_YMAX =  4.5
# ==============================================================================

parser = argparse.ArgumentParser()
parser.add_argument('-i', '--input', type=str, default='Xee_ee_4_2023.root', help='File containing input dataset and models')
parser.add_argument('--basefolder', type=str, default='.', help='Base folder for input files')
parser.add_argument('-f', '--fit_file', type=str, default='fitDiagnosticsTest.root', help='File containing fit results')
parser.add_argument('-o', '--output_folder', type=str, default='plots', help='Output folder')
parser.add_argument('-m', '--mass', type=float, default=3.0, help='Mass value to plot')
parser.add_argument('-c', '--cat_id', type=int, default=4, help='Category ID to plot')
parser.add_argument('-r', '--region', type=str, default='region1', choices=["region0", "region1", "region2"])
parser.add_argument('--era', type=str, default='2023', choices=["2022", "2022EE", "2023", "2023BPix", "allYears"])
parser.add_argument('--binned', type=bool, default=False, help='Use binned dataset for plotting')
parser.add_argument('--tag', type=str, default='', help='Tag to append to output filename')
args = parser.parse_args()

ROOT.gROOT.SetBatch(True)
ROOT.gStyle.SetOptStat(0)

# Load workspace and variable
f_ws = ROOT.TFile.Open(str(Path(args.basefolder) / f"{args.mass:.1f}" / args.input), "READ")
if not f_ws or f_ws.IsZombie():
    raise FileNotFoundError(f"Failed to open input workspace: {args.input}")

ws = f_ws.Get("w")
m = ws.var("mass")
m.setUnit("GeV")
m_min = CUSTOM_XMIN if CUSTOM_XMIN is not None else m.getMin()
m_max = CUSTOM_XMAX if CUSTOM_XMAX is not None else m.getMax()

# Retrieve dataset and luminosity
lumi = 6.68
if args.binned:
    common_path = Path(args.basefolder) / f"common/Xee_ee_{args.era}.input.root"
    f_in = ROOT.TFile.Open(str(common_path), "READ")
    if f_in and not f_in.IsZombie():
        ws_in = f_in.Get("w")
        dataset = ws_in.data("data_obs")
        lumi_var = ws_in.var(f"luminosity_{args.era}")
        if lumi_var:
            lumi = lumi_var.getVal()
    else:
        dataset = ws.data("data_obs")
else:
    dataset = ws.data("data_obs")

error_type = ROOT.RooAbsData.Poisson if (args.binned and "data" not in args.tag) else ROOT.RooAbsData.SumW2

# Load fit diagnostics file
f_fit = ROOT.TFile.Open(str(Path(args.basefolder) / f"{args.mass:.1f}" / args.fit_file), "READ")
if not f_fit or f_fit.IsZombie():
    raise FileNotFoundError(f"Failed to open fit file: {args.fit_file}")

channel_name = f"Xee_ee_{args.cat_id}_{args.era}"

# Retrieve shapes
bkg_total = f_fit.Get(f"shapes_fit_b/{channel_name}/total_background")
bkg_s     = f_fit.Get(f"shapes_fit_s/{channel_name}/total_background")
sb_total  = f_fit.Get(f"shapes_fit_s/{channel_name}/total")
sig_shape = f_fit.Get(f"shapes_fit_s/{channel_name}/Zd")

if not bkg_total or not sb_total:
    raise ValueError(f"Could not load shapes for {channel_name} from {args.fit_file}")

# Retrieve norms
bkg_total_norm = f_fit.Get("norm_fit_b").selectByName(f"{channel_name}/total_background").first().getValV()
bkg_s_norm_obj = f_fit.Get("norm_fit_s").selectByName(f"{channel_name}/total_background").first()
bkg_s_norm     = bkg_s_norm_obj.getValV() if bkg_s_norm_obj else 0.0
sb_total_norm  = f_fit.Get("norm_fit_s").selectByName(f"{channel_name}/total").first().getValV()
sig_norm_obj   = f_fit.Get("norm_fit_s").selectByName(f"{channel_name}/Zd").first()
sig_norm       = sig_norm_obj.getValV() if sig_norm_obj else 0.0

# Retrieve best-fit signal strength r
fit_tree = f_fit.Get("tree_fit_sb")
if fit_tree and fit_tree.GetEntries() > 0:
    fit_tree.GetEntry(0)
    signal_r, r_hi, r_lo = fit_tree.r, fit_tree.rHiErr, fit_tree.rLoErr
else:
    signal_r, r_hi, r_lo = 0.0, 0.0, 0.0

# ----------------- Retrieve Post-Fit Nuisances & Parameters -----------------
fit_result_s = f_fit.Get("fit_s")
fit_params = fit_result_s.floatParsFinal() if fit_result_s else None

# 1. Format mass parameter name (e.g. 9.6 -> 9p6)
mass_str = f"{args.mass:.1f}".replace('.', 'p')
mean_var_name = f"mean_test_M{mass_str}_{args.era}"

mean_val, mean_err = None, None
if fit_params:
    mean_param = fit_params.find(mean_var_name)
    if mean_param:
        mean_val = mean_param.getVal()
        mean_err = mean_param.getError()

# Fallback: check workspace if it was kept constant or not floated
if mean_val is None:
    ws_mean_param = ws.obj(mean_var_name)
    # also retrieve scale value and set to post-fit; only par left floating in the RooFormula
    ws_scale_param = ws.obj(f"CMS_scale_e")
    ws_postfit_scale = fit_params.find(f"CMS_scale_e") #post-fit value
    ws_postfit_scale_val = None
    try:
        ws_postfit_scale_val = ws_postfit_scale.getVal()
    except:
        print("DEBUG: Could not retrieve post-fit scale value for CMS_scale_e. Setting to 0")
        ws_postfit_scale_val = 0.0
    ws_scale_param.setVal(ws_postfit_scale_val)  # set to post-fit value
    if ws_mean_param:
        mean_val = ws_mean_param.getVal()
        # mean_err = ws_mean_param.getError()

print("DEBUG: found mean parameter:", mean_var_name, "=", mean_val, ", with scale = ", ws_scale_param.getVal())

# 2. Retrieve CMS_scale_e post-fit value
scale_e_val, scale_e_err = None, None
if fit_params:
    # Try multiple naming conventions
    possible_scale_names = [
        "CMS_scale_e",
        f"CMS_scale_e_{args.era}",
        "CMS_scale_e_13TeV",
        f"CMS_scale_e_{args.region}"
    ]
    for name in possible_scale_names:
        scale_param = fit_params.find(name)
        if scale_param:
            scale_e_val = scale_param.getVal()
            scale_e_err = scale_param.getError()
            break

# Scale histograms by bin width to match event counts
bin_width = bkg_total.GetBinWidth(1)
for h in [bkg_total, bkg_s, sb_total, sig_shape]:
    if h:
        h.Scale(bin_width)

# Style distributions
bkg_total.SetLineColor(ROOT.kAzure + 1)
bkg_total.SetLineWidth(2)
bkg_total.SetLineStyle(2)

if bkg_s:
    bkg_s.SetLineColor(ROOT.kTeal + 2)
    bkg_s.SetLineWidth(2)
    bkg_s.SetLineStyle(3)

sb_total.SetLineColor(ROOT.kRed + 1)
sb_total.SetLineWidth(2)

if sig_shape:
    sig_shape.SetLineColor(ROOT.kBlack)
    sig_shape.SetLineWidth(2)

# Build data histogram
nbins = bkg_total.GetNbinsX()
data_h = dataset.createHistogram("data_hist", m, ROOT.RooFit.Binning(nbins))

# ==============================================================================
# AUTOMATIC OR OVERRIDDEN Y-BOUND DETERMINATION
# ==============================================================================
era_override = ERA_Y_BOUNDS.get(args.era, None)

if era_override is not None and era_override[0] is not None and era_override[1] is not None:
    y_min, y_max = era_override
else:
    window_max = 0.0
    window_min = float('inf')

    for i in range(1, nbins + 1):
        x_center = data_h.GetBinCenter(i)
        if m_min <= x_center <= m_max:
            d_val = data_h.GetBinContent(i)
            d_err = data_h.GetBinError(i)
            b_val = bkg_total.GetBinContent(i)
            sb_val = sb_total.GetBinContent(i)

            current_max = max(d_val + d_err, b_val, sb_val)
            if current_max > window_max:
                window_max = current_max

            positive_candidates = [val for val in (d_val - d_err, d_val, b_val, sb_val) if val > 0]
            if positive_candidates:
                current_min = min(positive_candidates)
                if current_min < window_min:
                    window_min = current_min

    if window_min == float('inf'):
        window_min = ABS_YMIN_FLOOR

    y_max = window_max * AUTO_YMAX_FACTOR
    y_min = max(window_min * AUTO_YMIN_FACTOR, ABS_YMIN_FLOOR)

# Compute chi2 for S+B manually
chi2 = 0.0
for i in range(1, nbins + 1):
    obs = data_h.GetBinContent(i)
    exp = sb_total.GetBinContent(i)
    err = data_h.GetBinError(i)
    if err > 0:
        chi2 += ((obs - exp) / err) ** 2

n_free_params = ws.pdf("model_s").getParameters(ws.data("data_obs")).selectByAttrib("Constant", False).getSize()
ndof = max(nbins - 1 - n_free_params, 1)
reduced_chi2 = chi2 / ndof

# ----------------- Canvas Setup -----------------
c = ROOT.TCanvas("c", "c", 800, 800)
c.Divide(1, 2)

# Top pad (Main plot)
c.cd(1)
ROOT.gPad.SetPad(0, 0.3, 1, 1)
ROOT.gPad.SetBottomMargin(0.001)
ROOT.gPad.SetLeftMargin(0.12)
ROOT.gPad.SetRightMargin(0.05)
ROOT.gPad.SetLogy()

frame = m.frame(m_min, m_max)
frame.SetTitle("")
frame.GetXaxis().SetTitle("m(ee) [GeV]")
frame.GetXaxis().SetLabelSize(0)
frame.GetXaxis().SetTitleSize(0)
frame.GetYaxis().SetTitle(f"Events / {round(bin_width, 4)} GeV")
frame.GetYaxis().SetTitleSize(0.045)
frame.GetYaxis().SetTitleOffset(1.2)

dataset.plotOn(frame, ROOT.RooFit.DataError(error_type), ROOT.RooFit.MarkerSize(0.5))
frame.Draw()

bkg_total.Draw("same hist")
if bkg_s:
    bkg_s.Draw("same hist")
sb_total.Draw("same hist")
if sig_shape:
    sig_shape.Draw("same hist")

frame.GetXaxis().SetRangeUser(m_min, m_max)
frame.SetMinimum(y_min)
frame.SetMaximum(y_max)

# ----------------- Legend Setup -----------------
xmin = 0.48 if args.region == "region0" else 0.50
ymin = 0.10 if args.region == "region0" else 0.46
yheight = 0.44 if args.region == "region0" else 0.42

legend = ROOT.TLegend(xmin, ymin, xmin + 0.45, ymin + yheight)
legend.SetFillStyle(0)
legend.SetBorderSize(0)
legend.SetTextFont(42)
legend.SetTextSize(0.028)
legend.AddEntry(dataset, "Data", "p")
legend.AddEntry(sb_total, f"#splitline{{Total S+B Fit = {sb_total_norm:.0f}}}{{#chi^2/ndof = {chi2:.2f} / {ndof} = {reduced_chi2:.2f}}}", "l")
if bkg_s:
    legend.AddEntry(bkg_s, f"B component (S+B fit) = {bkg_s_norm:.0f}", "l")
legend.AddEntry(bkg_total, f"Total B Fit (B-only) = {bkg_total_norm:.0f}", "l")

if sig_shape:
    # Build informative signal label with r, mean, and scale_e
    sig_line1 = f"Signal = {sig_norm:.0f} (r = {signal_r:.2g}^{{+{r_hi:.2g}}}_{{-{r_lo:.2g}}})"
    
    sub_lines = []
    if mean_val is not None:
        sub_lines.append(f"#mu = {mean_val:.4f}")
    if scale_e_val is not None:
        sub_lines.append(f"#delta_{{scale}} = {scale_e_val:+.2f} #pm {scale_e_err:.2f}")

    if sub_lines:
        sig_line2 = ", ".join(sub_lines)
        sig_label = f"#splitline{{{sig_line1}}}{{{sig_line2}}}"
    else:
        sig_label = sig_line1

    legend.AddEntry(sig_shape, sig_label, "l")

legend.Draw()

# CMS Headings
latex_cms = ROOT.TLatex()
latex_cms.SetNDC()
latex_cms.SetTextFont(61)
latex_cms.SetTextSize(0.05)
latex_cms.DrawLatex(0.12, 0.92, "CMS")

latex_prelim = ROOT.TLatex()
latex_prelim.SetNDC()
latex_prelim.SetTextFont(52)
latex_prelim.SetTextSize(0.04)
latex_prelim.DrawLatex(0.20, 0.92, "Preliminary")

latex_lumi = ROOT.TLatex()
latex_lumi.SetNDC()
latex_lumi.SetTextFont(42)
latex_lumi.SetTextSize(0.045)
latex_lumi.SetTextAlign(31)
latex_lumi.DrawLatex(0.95, 0.92, f"{lumi:.2f}" + " fb^{#font[122]{\55}1} (13.6 TeV)")

# ----------------- Bottom Pad (Pulls) -----------------
c.cd(2)
ROOT.gPad.SetPad(0, 0, 1, 0.3)
ROOT.gPad.SetBottomMargin(0.25)
ROOT.gPad.SetTopMargin(0.02)
ROOT.gPad.SetLeftMargin(0.12)
ROOT.gPad.SetRightMargin(0.05)

pulls_sb = ROOT.TGraphAsymmErrors()
pulls_b = ROOT.TGraphAsymmErrors()

dx = bin_width * 0.12

for i in range(nbins):
    x = sb_total.GetBinCenter(i + 1)
    if not (m_min <= x <= m_max):
        continue

    data_y = data_h.GetBinContent(i + 1)
    data_y_err = data_h.GetBinError(i + 1)

    val_sb = (data_y - sb_total.GetBinContent(i + 1)) / data_y_err if data_y_err > 0 else 0.0
    val_b  = (data_y - bkg_total.GetBinContent(i + 1)) / data_y_err if data_y_err > 0 else 0.0

    idx = pulls_sb.GetN()
    pulls_sb.SetPoint(idx, x + dx, val_sb)
    pulls_sb.SetPointError(idx, 0, 0, 1, 1)

    pulls_b.SetPoint(idx, x - dx, val_b)
    pulls_b.SetPointError(idx, 0, 0, 1, 1)

# Pull formatting
pulls_sb.SetMarkerStyle(20)
pulls_sb.SetMarkerSize(0.5)
pulls_sb.SetMarkerColor(ROOT.kRed + 1)
pulls_sb.SetLineColor(ROOT.kRed + 1)

pulls_b.SetMarkerStyle(24)
pulls_b.SetMarkerSize(0.5)
pulls_b.SetMarkerColor(ROOT.kAzure + 1)
pulls_b.SetLineColor(ROOT.kAzure + 1)

pulls_sb.GetXaxis().SetLimits(m_min, m_max)
pulls_sb.GetXaxis().SetTitle("m(ee) [GeV]")
pulls_sb.GetXaxis().SetLabelSize(0.07)
pulls_sb.GetXaxis().SetTitleSize(0.1)
pulls_sb.GetYaxis().SetTitle("Pulls")
pulls_sb.GetYaxis().SetLabelSize(0.07)
pulls_sb.GetYaxis().SetTitleSize(0.1)
pulls_sb.GetYaxis().SetTitleOffset(0.4)
pulls_sb.GetYaxis().SetRangeUser(PULL_YMIN, PULL_YMAX)
pulls_sb.GetYaxis().SetNdivisions(505)

pulls_sb.Draw("AP E1")
pulls_b.Draw("P E1 SAME")

# Reference guide lines
line0 = ROOT.TLine(m_min, 0, m_max, 0)
line0.SetLineColor(ROOT.kGray + 2)
line0.SetLineStyle(2)
line0.Draw("same")

for y_band in [-2.0, 2.0]:
    line_band = ROOT.TLine(m_min, y_band, m_max, y_band)
    line_band.SetLineColor(ROOT.kGray + 1)
    line_band.SetLineStyle(3)
    line_band.Draw("same")

# Sub-legend for pulls
leg_pull = ROOT.TLegend(0.15, 0.76, 0.35, 0.94)
leg_pull.SetNColumns(2)
leg_pull.SetBorderSize(0)
leg_pull.SetFillStyle(0)
leg_pull.SetTextFont(42)
leg_pull.SetTextSize(0.065)
leg_pull.AddEntry(pulls_sb, "S+B", "pe")
leg_pull.AddEntry(pulls_b, "B-only", "pe")
leg_pull.Draw()

# ----------------- Save Outputs -----------------
tag_label = f"_{args.tag}" if args.tag else ""
out_dir = args.output_folder #os.path.join(args.output_folder, "overlay")
os.makedirs(out_dir, exist_ok=True)

for ext in ['png', 'pdf']:
    out_file = os.path.join(out_dir, f"fit_overlay_M{args.mass:.1f}{tag_label}_{args.era}.{ext}")
    c.SaveAs(out_file)

print(f"[OK] Saved plots to {out_dir}")

# Cleanup
f_ws.Close()
if args.binned and 'f_in' in locals() and f_in:
    f_in.Close()
f_fit.Close()