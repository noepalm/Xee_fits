#!/usr/bin/env python3
import argparse
import os
import ROOT
from functools import partial
import HiggsAnalysis.CombinedLimit.util.plotting as plot

ROOT.PyConfig.IgnoreCommandLineOptions = True
ROOT.gROOT.SetBatch(ROOT.kTRUE)

# Enlarge canvas and expand left/bottom margins to clear axis titles
plot.ModTDRStyle(width=800, height=600, l=0.16, b=0.12, r=0.05, t=0.08)
ROOT.gStyle.SetNdivisions(510, "XYZ")

NAMECOUNTER = 0

LABELS = {
    "envelope": "Envelope",
    "idx0": "Bernstein (idx 0)",
    "idx1": "Chebyshev (idx 1)",
    "idx2": "PolyExp (idx 2)",
    "dCB": "Double Crystal Ball",
    "gaussian": "Gaussian",
}

# Standard CMS categorical palette
COLORS = {
    "envelope": ROOT.kBlack,
    "idx0": ROOT.TColor.GetColor("#1f77b4"),     # Muted Blue
    "idx1": ROOT.TColor.GetColor("#d62728"),     # Muted Red / Orange-Red
    "idx2": ROOT.TColor.GetColor("#2ca02c"),     # Green
    "dCB": ROOT.TColor.GetColor("#1f77b4"),
    "gaussian": ROOT.TColor.GetColor("#d62728"),
}


def read_envelope_tree(filepath: str, poi: str, delta_nll_only: bool = False) -> ROOT.TGraph:
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Input file not found: {filepath}")
    tfile = ROOT.TFile.Open(filepath)
    if not tfile or tfile.IsZombie():
        raise RuntimeError(f"Cannot open ROOT file: {filepath}")

    tree = tfile.Get("limit")
    if not tree:
        raise RuntimeError(f"Could not find 'limit' tree in {filepath}")

    r_vals = []
    y_vals = []

    for idx, entry in enumerate(tree):
        if idx == 0:
            continue  # Skip best-fit snapshot row
        r_vals.append(getattr(entry, poi))
        if delta_nll_only:
            y_vals.append(2.0 * entry.deltaNLL)
        else:
            y_vals.append(2.0 * (entry.deltaNLL + entry.nll + entry.nll0))

    tfile.Close()

    if len(r_vals) == 0:
        raise RuntimeError(f"Zero points extracted from {filepath}")

    graph = ROOT.TGraph(len(r_vals))
    for i, (rx, yv) in enumerate(zip(r_vals, y_vals)):
        graph.SetPoint(i, rx, yv)

    graph.Sort()
    plot.RemoveGraphXDuplicates(graph)
    return graph


def Eval(obj, x, params):
    return obj.Eval(x[0])


def build_scan_from_graph(graph: ROOT.TGraph, key: str, color: int, ycut: float = None):
    if ycut is not None:
        plot.RemoveGraphYAbove(graph, ycut)
    if graph.GetN() <= 1:
        raise RuntimeError("TGraph has zero or one point remaining after processing")

    graph.SetMarkerColor(color)
    graph.SetLineColor(color)

    # Empty open circles for envelope, solid small markers for sub-fits
    if key == "envelope":
        graph.SetMarkerStyle(24)  # Open circle
        graph.SetMarkerSize(1.2)
        graph.SetLineWidth(2)
    else:
        graph.SetMarkerStyle(20)  # Filled circle
        graph.SetMarkerSize(0.7)
        graph.SetLineWidth(2)

    global NAMECOUNTER
    spline = ROOT.TSpline3(f"spline3_{NAMECOUNTER}", graph)
    func_method = partial(Eval, spline)
    func = ROOT.TF1(
        f"splinefn_{NAMECOUNTER}",
        func_method,
        graph.GetX()[0],
        graph.GetX()[graph.GetN() - 1],
        1,
    )
    func._method = func_method
    func.SetLineColor(color)
    func.SetLineWidth(2)
    if key == "envelope":
        func.SetLineWidth(3)
        func.SetLineStyle(1)
    else:
        func.SetLineStyle(2)

    NAMECOUNTER += 1

    return {
        "graph": graph,
        "spline": spline,
        "func": func,
    }


def main():
    parser = argparse.ArgumentParser(description="Plot NLL scan results matching Combine plot1DScan style.")
    parser.add_argument("--signal", action="store_true", help="Plot signal-only NLL scan")
    parser.add_argument("-o", "--output", type=str, default="nll_scan_comparison.png", help="Output filename")
    parser.add_argument("-i", "--input", type=str, default=None, help="Input ROOT file")
    parser.add_argument("--deltaNLL", action="store_true", help="Plot 2*deltaNLL instead of 2*(deltaNLL + nll + nll0)")
    parser.add_argument("--year", type=str, default="", help="Year to process")
    parser.add_argument("--title", type=str, default="", help="Unused (kept for CLI compatibility)")
    parser.add_argument("--poi", type=str, default="r", help="POI name to plot on x-axis")
    parser.add_argument("--tag", type=str, default="", help="Tag suffix for filename resolution")
    parser.add_argument("--y-max", type=float, default=None, help="Optional y-axis maximum (auto-computed if omitted)")
    parser.add_argument("--y-cut", type=float, default=None, help="Optional cut on points above y-cut before spline interpolation")
    parser.add_argument("--logo", default="CMS")
    parser.add_argument("--logo-sub", default="Internal")
    args = parser.parse_args()

    if args.signal:
        keys = ["envelope", "dCB", "gaussian"]
    else:
        keys = ["envelope", "idx0", "idx1"]

    scans = {}
    for key in keys:
        suffix = "" if key == "envelope" else f"_{key}Only" if args.signal else f"_{key}"
        suffix = suffix + f"_{args.year}" if args.year else suffix
        suffix = suffix + f"_{args.tag}" if args.tag else suffix

        if args.input:
            filepath = args.input
        else:
            filepath = f"higgsCombine.nll_scan_{'signal' if args.signal else 'bkg'}Envelope{suffix}.MultiDimFit.mH120.root"

        graph = read_envelope_tree(filepath, args.poi, delta_nll_only=args.deltaNLL)
        scans[key] = build_scan_from_graph(graph, key, COLORS.get(key, ROOT.kBlack), ycut=args.y_cut)

    # Base Canvas setup
    out_base = os.path.splitext(args.output)[0]
    canv = ROOT.TCanvas(out_base, out_base, 800, 600)
    pads = plot.OnePad()

    main_scan = scans["envelope"]
    main_scan["graph"].Draw("AP")

    axishist = plot.GetAxisHist(pads[0])

    # Dynamic Y axis limits with adequate headroom
    all_ymin = min(min(s["graph"].GetY()) for s in scans.values())
    all_ymax = max(max(s["graph"].GetY()) for s in scans.values())
    y_range = all_ymax - all_ymin if (all_ymax > all_ymin) else 1.0

    y_min_target = all_ymin - 0.05 * y_range
    y_max_target = args.y_max if args.y_max is not None else (all_ymax + 0.28 * y_range)

    axishist.SetMinimum(y_min_target)
    axishist.SetMaximum(y_max_target)

    # Offset Y-axis label to avoid numerical overlap
    if args.deltaNLL:
        axishist.GetYaxis().SetTitle("- 2 #Delta ln L")
    else:
        axishist.GetYaxis().SetTitle("2 #times (#Delta ln L + ln L_{0})")

    axishist.GetYaxis().SetTitleOffset(1.4)
    axishist.GetXaxis().SetTitle(args.poi)
    axishist.GetXaxis().SetTitleOffset(1.1)

    # Global X bounds
    mins = [s["graph"].GetX()[0] for s in scans.values()]
    maxs = [s["graph"].GetX()[s["graph"].GetN() - 1] for s in scans.values()]
    axishist.GetXaxis().SetLimits(min(mins), max(maxs))

    # Draw individual function components first, then overlay the envelope on top
    for key in keys:
        if key != "envelope":
            scans[key]["graph"].Draw("PSAME")
            scans[key]["func"].Draw("SAME")

    scans["envelope"]["graph"].Draw("PSAME")
    scans["envelope"]["func"].Draw("SAME")

    pads[0].GetFrame().Draw()
    pads[0].RedrawAxis()

    # Draw CMS Logo outside above the frame (iPosX = 0)
    plot.DrawCMSLogo(pads[0], args.logo, args.logo_sub, 0, 0.1, 0.035, 1.2, cmsTextSize=0.9)

    # Legend Configuration
    legend = ROOT.TLegend(0.60, 0.72, 0.93, 0.90, "", "NBNDC")
    legend.SetTextFont(42)
    legend.SetTextSize(0.035)
    for key in keys:
        legend.AddEntry(scans[key]["graph"], LABELS.get(key, key), "LP")
    legend.Draw()

    # Save outputs
    canv.Print(out_base + ".png")
    canv.Print(out_base + ".pdf")


if __name__ == "__main__":
    main()