import ROOT
import argparse

parser = argparse.ArgumentParser(description="Plot FitDiagnostics shapes with S+B overlay and ratio/pull/diff panels")
parser.add_argument("-i", "--input", required=True, help="Input fitDiagnostics.root file")
parser.add_argument("--ch", default="ch1", help="Channel name inside ROOT file (e.g., ch1, bin1)")
parser.add_argument("-o", "--output", default="fit_plot.pdf", help="Output filename")
parser.add_argument("--mode", choices=["ratio", "pull", "diff"], default="pull", help="Data representation in the bottom pad")
args = parser.parse_args()

ROOT.gROOT.SetBatch(True)
ROOT.gStyle.SetOptStat(0)

f = ROOT.TFile(args.input)
if not f or f.IsZombie():
    raise RuntimeError(f"Could not open {args.input}")

data_graph = f.Get(f"shapes_fit_b/{args.ch}/data")
bg_only_hist = f.Get(f"shapes_fit_b/{args.ch}/total_background")
sb_total_hist = f.Get(f"shapes_fit_s/{args.ch}/total")

if not data_graph or not bg_only_hist or not sb_total_hist:
    raise RuntimeError(f"Could not find data, fit_b, or fit_s objects for channel {args.ch}")

c = ROOT.TCanvas("c", "c", 800, 800)

# Top pad
pad1 = ROOT.TPad("pad1", "pad1", 0, 0.3, 1, 1.0)
pad1.SetBottomMargin(0.02)
pad1.SetLeftMargin(0.15)
pad1.Draw()

# Bottom pad
pad2 = ROOT.TPad("pad2", "pad2", 0, 0.0, 1, 0.3)
pad2.SetTopMargin(0.02)
pad2.SetBottomMargin(0.3)
pad2.SetLeftMargin(0.15)
pad2.Draw()

# Build Top Pad
pad1.cd()
pad1.SetLogy()

bg_only_hist.SetTitle("")
bg_only_hist.SetLineColor(ROOT.kBlue)
bg_only_hist.SetLineWidth(2)
bg_only_hist.GetYaxis().SetTitle("Events")
bg_only_hist.GetYaxis().SetTitleSize(0.05)
bg_only_hist.GetYaxis().SetLabelSize(0.04)
bg_only_hist.SetMaximum(bg_only_hist.GetMaximum() * 50)
bg_only_hist.SetMinimum(max(1e-8, bg_only_hist.GetMinimum() * 0.1))
# bg_only_hist.SetMinimum(1e2)

bg_error = bg_only_hist.Clone("bg_error")
bg_error.SetFillColor(ROOT.kBlack)
bg_error.SetFillStyle(3004)
bg_error.SetMarkerSize(0)

# Configure S+B line
sb_total_hist.SetLineColor(ROOT.kRed)
sb_total_hist.SetLineWidth(2)
sb_total_hist.SetLineStyle(2) # Dashed line

# 1. Draw the background histogram FIRST just to set up the axes and frame
bg_only_hist.Draw("AXIS")

# 2. Draw the data points
data_graph.SetMarkerStyle(20)
data_graph.SetMarkerSize(0.6) # Make them slightly smaller if they are dense
data_graph.SetMarkerColor(ROOT.kBlack)
data_graph.SetLineColor(ROOT.kBlack)
data_graph.Draw("PZ SAME")

# 3. Draw the uncertainty band (if you kept it)
# bg_error.Draw("E2 SAME") 

# 4. Draw the fit curves ON TOP of the data
bg_only_hist.Draw("HIST SAME")
sb_total_hist.Draw("HIST SAME")

# 5. Redraw the axes so they aren't covered by the histograms
ROOT.gPad.RedrawAxis()

legend = ROOT.TLegend(0.55, 0.65, 0.88, 0.88)
legend.AddEntry(data_graph, "Data (or Toy)", "pe")
legend.AddEntry(bg_only_hist, "Post-Fit Background Only", "l")
legend.AddEntry(sb_total_hist, "Post-Fit S+B", "l")
legend.AddEntry(bg_error, "B-Only Uncertainty", "f")
legend.SetBorderSize(0)
legend.Draw()

# Build Bottom Pad
pad2.cd()

bottom_graph = ROOT.TGraphAsymmErrors(data_graph.GetN())
sb_line_bottom = bg_only_hist.Clone("sb_line_bottom")
sb_line_bottom.Reset()
sb_line_bottom.SetLineColor(ROOT.kRed)
sb_line_bottom.SetLineWidth(2)
sb_line_bottom.SetLineStyle(2)

max_val = -999999
min_val = 999999

for i in range(data_graph.GetN()):
    x = data_graph.GetPointX(i)
    y_data = data_graph.GetPointY(i)
    err_up = data_graph.GetErrorYhigh(i)
    err_low = data_graph.GetErrorYlow(i)
    
    bin_idx = bg_only_hist.FindBin(x)
    y_bg = bg_only_hist.GetBinContent(bin_idx)
    y_sb = sb_total_hist.GetBinContent(bin_idx)
    
    diff_data = y_data - y_bg
    diff_sb = y_sb - y_bg
    
    if args.mode == "ratio":
        val_data = (y_data / y_bg) if y_bg > 0 else 0
        val_sb = (y_sb / y_bg) if y_bg > 0 else 0
        e_up = (err_up / y_bg) if y_bg > 0 else 0
        e_low = (err_low / y_bg) if y_bg > 0 else 0
    elif args.mode == "pull":
        sigma = err_low if diff_data < 0 else err_up
        val_data = (diff_data / sigma) if sigma > 0 else 0
        # Calculate the S+B pull using the data's error bar for a direct visual comparison
        val_sb = (diff_sb / sigma) if sigma > 0 else 0
        e_up = 0 
        e_low = 0
    elif args.mode == "diff":
        val_data = diff_data
        val_sb = diff_sb
        e_up = err_up
        e_low = err_low
        
    bottom_graph.SetPoint(i, x, val_data)
    bottom_graph.SetPointError(i, 0, 0, e_low, e_up)
    sb_line_bottom.SetBinContent(bin_idx, val_sb)
    
    if val_data + e_up > max_val: max_val = val_data + e_up
    if val_data - e_low < min_val: min_val = val_data - e_low

# Configure Axes based on Mode
x_min = bg_only_hist.GetXaxis().GetXmin()
x_max = bg_only_hist.GetXaxis().GetXmax()
bottom_axis = ROOT.TH1F("bottom_axis", "", 1, x_min, x_max)

if args.mode == "ratio":
    bottom_axis.SetMinimum(0.8)
    bottom_axis.SetMaximum(1.2)
    bottom_axis.GetYaxis().SetTitle("Data / B-Only")
    center_val = 1.0
elif args.mode == "pull":
    bottom_axis.SetMinimum(-5.0)
    bottom_axis.SetMaximum(5.0)
    bottom_axis.GetYaxis().SetTitle("Pull (#sigma)")
    center_val = 0.0
elif args.mode == "diff":
    margin = (max_val - min_val) * 0.1 if (max_val - min_val) > 0 else 10
    bottom_axis.SetMinimum(min_val - margin)
    bottom_axis.SetMaximum(max_val + margin)
    bottom_axis.GetYaxis().SetTitle("Data - B-Only")
    center_val = 0.0

bottom_axis.GetYaxis().SetNdivisions(505)
bottom_axis.GetYaxis().SetTitleSize(0.12)
bottom_axis.GetYaxis().SetLabelSize(0.1)
bottom_axis.GetYaxis().SetTitleOffset(0.5)

bottom_axis.GetXaxis().SetTitle("m_{ee} (GeV)")
bottom_axis.GetXaxis().SetTitleSize(0.12)
bottom_axis.GetXaxis().SetLabelSize(0.1)
bottom_axis.GetXaxis().SetTitleOffset(1.0)

bottom_axis.Draw("AXIS")

# Zero / Unity Line
line = ROOT.TLine(x_min, center_val, x_max, center_val)
line.SetLineStyle(2)
line.SetLineColor(ROOT.kBlack)
line.Draw("SAME")

# One and Two Sigma Bands (for Pulls only)
if args.mode == "pull":
    band2 = ROOT.TBox(x_min, -2, x_max, 2)
    band2.SetFillColorAlpha(ROOT.kYellow, 0.3)
    band2.Draw("SAME")
    band1 = ROOT.TBox(x_min, -1, x_max, 1)
    band1.SetFillColorAlpha(ROOT.kGreen, 0.3)
    band1.Draw("SAME")
    line.Draw("SAME")

# Draw the S+B line in the bottom pad
sb_line_bottom.Draw("HIST SAME")

bottom_graph.SetMarkerStyle(20)
bottom_graph.SetMarkerSize(0.8)
bottom_graph.Draw("PZ SAME")

c.SaveAs(args.output)
print(f"Saved {args.output} (Mode: {args.mode})")