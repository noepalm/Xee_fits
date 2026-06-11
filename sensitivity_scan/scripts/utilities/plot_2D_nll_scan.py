import ROOT
import array
import argparse

parser = argparse.ArgumentParser(description="Plot 2D NLL scan using TProfile2D")
parser.add_argument("-i", "--input", type=str, default="higgsCombineScan_2D_Trigger.MultiDimFit.mH120.root", help="Input ROOT file")
parser.add_argument("-o", "--output", type=str, default="scan_2d.pdf", help="Output filename")
parser.add_argument("--pois", 
                    nargs="+",
                    default=["r", "triggerSF_syst"],                    
                    help="Names of the parameters of interest (POIs)")
parser.add_argument("--bins", 
                    type=int, 
                    default=20, 
                    help="Number of bins per axis. Should be roughly sqrt(points). E.g., for --points 400, use 20.")

args = parser.parse_args()

if len(args.pois) < 2:
    raise ValueError("You must specify at least two POIs for a 2D scan.")

poi_x = args.pois[0]
poi_y = args.pois[1]

ROOT.gROOT.SetBatch(True)

f = ROOT.TFile(args.input)
t = f.Get("limit")

x_min = t.GetMinimum(poi_x)
x_max = t.GetMaximum(poi_x)
y_min = t.GetMinimum(poi_y)
y_max = t.GetMaximum(poi_y)

c = ROOT.TCanvas("c", "c", 800, 600)
c.SetRightMargin(0.15)
ROOT.gStyle.SetOptStat(0)

# Use the dynamic bin size from the arguments
hist_def = f"h({args.bins}, {x_min}, {x_max}, {args.bins}, {y_min}, {y_max})"
draw_cmd = f"2*deltaNLL:{poi_y}:{poi_x}>>{hist_def}"
cut_cmd = "deltaNLL < 10 && deltaNLL >= 0"

t.Draw(draw_cmd, cut_cmd, "prof colz")
h2 = ROOT.gROOT.FindObject("h")

h2.SetName("g2NLL")
h2.SetTitle(f"2D Likelihood Scan;{poi_x};{poi_y};-2#DeltalogL")

t.Draw(f"{poi_y}:{poi_x}", "deltaNLL == 0", "P same")
best_fit = ROOT.gROOT.FindObject("Graph")

if best_fit:
    best_fit.SetMarkerSize(3)
    best_fit.SetMarkerStyle(34) 
    best_fit.SetMarkerColor(ROOT.kBlack)
    best_fit.Draw("P same")

# 1-sigma contour (68% CL)
h68 = h2.Clone("h68")
h68.SetContour(1)
h68.SetContourLevel(0, 2.30)
h68.SetLineWidth(3)
h68.SetLineColor(ROOT.kBlack)
h68.Draw("CONT3 same")

# # 2-sigma contour (95% CL)
# h95 = h2.Clone("h95")
# h95.SetContour(1)
# h95.SetContourLevel(0, 5.99)
# h95.SetLineWidth(3)
# h95.SetLineStyle(2) 
# h95.SetLineColor(ROOT.kBlack)
# h95.Draw("CONT3 same")

c.SaveAs(args.output)