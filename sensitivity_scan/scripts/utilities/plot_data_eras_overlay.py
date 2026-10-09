#!/usr/bin/env python3
import ROOT
import argparse
import os
import sys
from math import sqrt

# ==============================================================================
# CONFIGURATION
# ==============================================================================
CUSTOM_XMIN = 1.7   # e.g. 1.8 (or None to auto-detect from dataset bounds)
CUSTOM_XMAX = 2.2   # e.g. 2.2
CUSTOM_YMIN = None   # None for auto, or e.g. 1e-5 (log-scale floor)
CUSTOM_YMAX = None   # None for auto (2.5 * max density)

RATIO_YMIN  = 0.8    # Bottom pad minimum ratio
RATIO_YMAX  = 1.2    # Bottom pad maximum ratio

ERA_COLORS = {
    "2022":     ROOT.TColor.GetColor("#3f90da"),
    "2022EE":   ROOT.TColor.GetColor("#ffa90e"),
    "2023":     ROOT.TColor.GetColor("#bd1f01"),
    "2023BPix": ROOT.TColor.GetColor("#832db6"),
    "allYears": ROOT.kBlack,
}

ERA_MARKERS = {
    "2022":     20,  # Full circle
    "2022EE":   21,  # Full square
    "2023":     22,  # Full triangle up
    "2023BPix": 33,  # Full diamond
    "allYears": 24,
}
# ==============================================================================

parser = argparse.ArgumentParser(description="Plot normalized density data spectra and ratio wrt first era")
parser.add_argument('-b', '--basedir', type=str, default='.', help='Base directory of repo')
parser.add_argument('-m', '--mass', type=float, default=2.0, help='Nominal mass directory')
parser.add_argument('-c', '--cat_id', type=int, default=4, help='Category ID (4 for inclusive)')
parser.add_argument('-r', '--region', type=str, default='region0', choices=["region0", "region1", "region2"])
parser.add_argument('--folder_tag', type=str, default='260828', help='Folder tag')
parser.add_argument('--tag', type=str, default='envelope_allCorrections_binned', help='Card tag')
parser.add_argument('--binned', action='store_true', default=True, help='Read binned dataset')
parser.add_argument('-o', '--output_folder', type=str, default='plots/data_overlay', help='Output folder')
parser.add_argument('--eras', nargs='+', default=["2022", "2022EE", "2023", "2023BPix"], help='Eras to include')
args = parser.parse_args()

ROOT.gROOT.SetBatch(True)
ROOT.gStyle.SetOptStat(0)

os.makedirs(args.output_folder, exist_ok=True)
log_file_path = os.path.join(args.output_folder, f"data_density_overlay_M{args.mass:.1f}_{args.region}.log")

class Logger(object):
    def __init__(self, filename):
        self.terminal = sys.stdout
        self.log = open(filename, "w")
    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)
    def flush(self):
        self.terminal.flush()
        self.log.flush()

sys.stdout = Logger(log_file_path)
sys.stderr = sys.stdout

print("=" * 80)
print(f"Starting Density Data + Ratio Overlay Plot for M={args.mass:.2f} ({args.region})")
print(f"Log written to: {log_file_path}")
print("=" * 80)

# 1. Resolve mass folder
cards_dir = os.path.join(args.basedir, f"cards/{args.folder_tag}/cards_{args.region}_data_{args.tag}/ee")
mass_dir = None
if os.path.exists(cards_dir):
    for entry in os.listdir(cards_dir):
        full_p = os.path.join(cards_dir, entry)
        if os.path.isdir(full_p):
            try:
                if abs(float(entry) - args.mass) < 1e-3:
                    mass_dir = full_p
                    break
            except ValueError:
                continue

if not mass_dir:
    raise FileNotFoundError(f"Could not locate mass folder for M={args.mass} in {cards_dir}")

print(f"[+] Found Mass Folder: {mass_dir}")

# 2. Extract dataset for each era, convert to TH1D, and normalize by integral
loaded_hists = {}
m_min_global, m_max_global = float('inf'), float('-inf')

for era in args.eras:
    dataset = None
    lumi = None
    
    common_path = os.path.join(cards_dir, "common", f"Xee_ee_{era}.input.root")
    src_file = None
    
    if args.binned and os.path.exists(common_path):
        f = ROOT.TFile.Open(common_path, "READ")
        if f and not f.IsZombie():
            w = f.Get("w")
            if w and w.data("data_obs"):
                dataset = w.data("data_obs")
                m_var = w.var("mass")
                lumi_var = w.var(f"luminosity_{era}")
                lumi = lumi_var.getVal() if lumi_var else None
                src_file = common_path

    if not dataset:
        ws_file = os.path.join(mass_dir, f"Xee_ee_{args.cat_id}_{era}.root")
        if os.path.exists(ws_file):
            f = ROOT.TFile.Open(ws_file, "READ")
            if f and not f.IsZombie():
                w = f.Get("w")
                if w and w.data("data_obs"):
                    dataset = w.data("data_obs")
                    m_var = w.var("mass")
                    src_file = ws_file

    if not dataset:
        print(f"[-] WARNING: Could not find data_obs for era {era}!")
        continue

    print(f"[+] Loaded era {era} from: {src_file}")
    
    m_min = m_var.getMin()
    m_max = m_var.getMax()
    m_min_global = min(m_min_global, m_min)
    m_max_global = max(m_max_global, m_max)

    # Convert to independent TH1D
    h_name = f"h_data_{era}"
    h = dataset.createHistogram(h_name, m_var)
    h.SetDirectory(0)

    raw_entries = dataset.sumEntries()

    # Normalize by Integral (density)
    integral = h.Integral()
    if integral > 0:
        h.Scale(1.0 / integral)
    else:
        print(f"[-] WARNING: Integral for era {era} is 0!")

    loaded_hists[era] = {
        "hist": h,
        "entries": raw_entries,
        "lumi": lumi,
    }
    f.Close()

if not loaded_hists:
    raise RuntimeError("No datasets were successfully loaded. Aborting.")

# 3. Establish limits
xmin = CUSTOM_XMIN if CUSTOM_XMIN is not None else m_min_global
xmax = CUSTOM_XMAX if CUSTOM_XMAX is not None else m_max_global

global_max = 0.0
global_min = float('inf')

for era, item in loaded_hists.items():
    h = item["hist"]
    for i in range(1, h.GetNbinsX() + 1):
        x = h.GetBinCenter(i)
        if xmin <= x <= xmax:
            val = h.GetBinContent(i)
            err = h.GetBinError(i)
            if (val + err) > global_max:
                global_max = val + err
            if 0 < val < global_min:
                global_min = val

if global_min == float('inf'):
    global_min = 1e-4

ymin = CUSTOM_YMIN if CUSTOM_YMIN is not None else global_min * 0.8
ymax = CUSTOM_YMAX if CUSTOM_YMAX is not None else global_max * 1.2
print(f"[+] Setting Ranges: X = [{xmin}, {xmax}], Y = [{ymin:.2e}, {ymax:.2e}]")

# Reference era is the first successfully loaded era
ref_era = list(loaded_hists.keys())[0]
ref_hist = loaded_hists[ref_era]["hist"]
print(f"[+] Using '{ref_era}' as baseline for ratio comparison.")

# 4. Canvas Layout (Two pads: 70% top, 30% bottom)
c = ROOT.TCanvas("c_data_ratio_overlay", "Data Density and Ratio Eras Overlay", 800, 800)
c.Divide(1, 2)

# Top pad (Densities)
c.cd(1)
ROOT.gPad.SetPad(0, 0.3, 1, 1)
ROOT.gPad.SetBottomMargin(0.001)
ROOT.gPad.SetLeftMargin(0.12)
ROOT.gPad.SetRightMargin(0.05)
ROOT.gPad.SetLogy()

main_frame = ref_hist.Clone("main_frame")
main_frame.Reset()
main_frame.SetTitle("")
main_frame.GetXaxis().SetRangeUser(xmin, xmax)
main_frame.GetXaxis().SetLabelSize(0)
main_frame.GetXaxis().SetTitleSize(0)

main_frame.GetYaxis().SetTitle("Density (a.u.)")
main_frame.GetYaxis().SetTitleSize(0.045)
main_frame.GetYaxis().SetTitleOffset(1.2)
main_frame.GetYaxis().SetLabelSize(0.04)
main_frame.SetMinimum(ymin)
main_frame.SetMaximum(ymax)
main_frame.Draw("HIST")

# Legend
leg = ROOT.TLegend(0.50, 0.65, 0.92, 0.90)
leg.SetBorderSize(0)
leg.SetFillStyle(0)
leg.SetTextFont(42)
leg.SetTextSize(0.032)

for era, item in loaded_hists.items():
    h = item["hist"]
    color = ERA_COLORS.get(era, ROOT.kBlack)
    marker = ERA_MARKERS.get(era, 20)

    h.SetMarkerStyle(marker)
    h.SetMarkerSize(0.6)
    h.SetMarkerColor(color)
    h.SetLineColor(color)
    h.Draw("E1 P SAME")

    lumi_str = f" ({item['lumi']:.2f} fb^{{-1}})" if item['lumi'] else ""
    leg.AddEntry(h, f"{era}{lumi_str} [N={item['entries']:.0f}]", "pe")

leg.Draw()

# CMS Headings
latex = ROOT.TLatex()
latex.SetNDC()
latex.SetTextFont(61)
latex.SetTextSize(0.05)
latex.DrawLatex(0.12, 0.92, "CMS")

latex.SetTextFont(52)
latex.SetTextSize(0.038)
latex.DrawLatex(0.20, 0.92, "Preliminary")

latex.SetTextAlign(31)
latex.SetTextFont(42)
latex.SetTextSize(0.04)
latex.DrawLatex(0.95, 0.92, "13.6 TeV")

# 5. Bottom pad (Ratios with error bars)
c.cd(2)
ROOT.gPad.SetPad(0, 0, 1, 0.3)
ROOT.gPad.SetBottomMargin(0.25)
ROOT.gPad.SetTopMargin(0.02)
ROOT.gPad.SetLeftMargin(0.12)
ROOT.gPad.SetRightMargin(0.05)

ratio_graphs = []
nbins = ref_hist.GetNbinsX()
bin_width = ref_hist.GetBinWidth(1)
dx_step = bin_width * 0.08  # small horizontal offset per era to prevent marker overlap

for idx, (era, item) in enumerate(list(loaded_hists.items())[1:]):
    h = item["hist"]
    color = ERA_COLORS.get(era, ROOT.kBlack)
    marker = ERA_MARKERS.get(era, 20)
    
    g_ratio = ROOT.TGraphAsymmErrors()
    g_ratio.SetName(f"ratio_{era}")
    shift = (idx - len(loaded_hists) / 2.0) * dx_step

    for i in range(1, nbins + 1):
        x = h.GetBinCenter(i)
        if not (xmin <= x <= xmax):
            continue

        y_val = h.GetBinContent(i)
        y_err = h.GetBinError(i)
        ref_val = ref_hist.GetBinContent(i)
        ref_err = ref_hist.GetBinError(i)

        if ref_val > 0 and y_val > 0:
            ratio = y_val / ref_val
            # Standard ratio error propagation
            ratio_err = ratio * sqrt((y_err / y_val)**2 + (ref_err / ref_val)**2)
        elif ref_val > 0 and y_val == 0:
            ratio = 0.0
            ratio_err = y_err / ref_val
        else:
            continue

        p_idx = g_ratio.GetN()
        g_ratio.SetPoint(p_idx, x + shift, ratio)
        g_ratio.SetPointError(p_idx, 0, 0, ratio_err, ratio_err)

    g_ratio.SetMarkerStyle(marker)
    g_ratio.SetMarkerSize(0.6)
    g_ratio.SetMarkerColor(color)
    g_ratio.SetLineColor(color)
    ratio_graphs.append(g_ratio)

# Base ratio frame configuration
first_graph = ratio_graphs[0]
first_graph.GetXaxis().SetLimits(xmin, xmax)
first_graph.GetXaxis().SetTitle("m(ee) [GeV]")
first_graph.GetXaxis().SetLabelSize(0.07)
first_graph.GetXaxis().SetTitleSize(0.1)

first_graph.GetYaxis().SetTitle(f"Ratio to {ref_era}")
first_graph.GetYaxis().SetLabelSize(0.07)
first_graph.GetYaxis().SetTitleSize(0.09)
first_graph.GetYaxis().SetTitleOffset(0.55)
first_graph.GetYaxis().SetRangeUser(RATIO_YMIN, RATIO_YMAX)
first_graph.GetYaxis().SetNdivisions(505)

first_graph.Draw("AP E1")
for g in ratio_graphs[1:]:
    g.Draw("P E1 SAME")

# Horizontal reference lines
line_one = ROOT.TLine(xmin, 1.0, xmax, 1.0)
line_one.SetLineColor(ROOT.kGray + 2)
line_one.SetLineStyle(1)
line_one.Draw("same")

for r_band in [0.8, 1.2]:
    line_band = ROOT.TLine(xmin, r_band, xmax, r_band)
    line_band.SetLineColor(ROOT.kGray + 1)
    line_band.SetLineStyle(3)
    line_band.Draw("same")

out_base = os.path.join(args.output_folder, f"data_density_ratio_overlay_M{args.mass:.1f}_{args.region}")
for ext in ["png", "pdf"]:
    c.SaveAs(f"{out_base}.{ext}")

print(f"[✓] Successfully generated: {out_base}.png/.pdf")