#!/usr/bin/env python3
import argparse
from pathlib import Path
import ROOT
cms_palette = [
    "#5790fc",
    "#f89c20",
    "#e42536",
    "#964a8b",
    "#9c9ca1",
    "#7a21dd",
]


BKG_FUNCTIONS = [
    ("chebyshev", "Chebyshev", cms_palette[0]),
    ("bernstein", "Bernstein", cms_palette[1]),
    ("polyexp", "PolyExp", cms_palette[2]),
]

# REGION_BOUNDS = {
#     "region0": (0.5, 2.2),
#     "region1": (1.8, 4.4),
#     "region2": (4.0, 10.8),
# }
# REGION_BOUNDS = {
#     "region0": (0.5, 2.2),
#     "region1": (1.8, 6.0),
#     "region2": (4.9, 10.5),
# }   
REGION_BOUNDS = {
    "region0": (0.5, 2.2),
    "region1": (1.8, 5.3),
    "region2": (4.5, 10.5),
}

def open_workspace(path):
    tf = ROOT.TFile.Open(str(path), "READ")
    if not tf or tf.IsZombie():
        return None, None

    ws = tf.Get("w")
    if ws is None:
        tf.Close()
        return None, None

    return tf, ws


def main():
    parser = argparse.ArgumentParser(description="Overlay B-only post-fit models on the same dataset")
    parser.add_argument("-i", "--bkg_fits_dir", required=True, help="Input ee/bkg_fits directory")
    parser.add_argument("-o", "--output_folder", required=True, help="Output folder")
    parser.add_argument("-c", "--category", required=True, help="Category name (e.g. inclusive)")
    parser.add_argument("--era", required=True, help="Era (e.g. 2022)")
    parser.add_argument("-r", "--region", required=True, choices=["region0", "region1", "region2"], help="Region name")
    parser.add_argument("-t", "--tag", default="", help="Optional fit tag used in B-only filenames")
    args = parser.parse_args()

    ROOT.gROOT.SetBatch(True)
    ROOT.gStyle.SetOptStat(0)

    in_dir = Path(args.bkg_fits_dir)
    out_dir = Path(args.output_folder)
    out_dir.mkdir(parents=True, exist_ok=True)

    tag_label = f"_{args.tag}" if args.tag else ""

    files = []
    for bkg_key, bkg_label, color in BKG_FUNCTIONS:
        fpath = in_dir / f"higgsCombine_{args.category}{tag_label}_{bkg_key}_{args.era}_Bonly.MultiDimFit.mH120.root"
        files.append((bkg_key, bkg_label, color, fpath))

    opened = []
    for bkg_key, bkg_label, color, fpath in files:
        if not fpath.exists():
            print(f"WARNING: Missing B-only workspace for {bkg_label}: {fpath}")
            continue

        tf, ws = open_workspace(fpath)
        if ws is None:
            print(f"WARNING: Invalid ROOT workspace for {bkg_label}: {fpath}")
            continue

        opened.append((tf, ws, bkg_label, color))

    if not opened:
        print("ERROR: No valid B-only workspace files found; nothing to plot")
        return 1

    data_ws = opened[0][1]
    dataset = data_ws.data("data_obs")
    mass = data_ws.var("mass")
    cat = data_ws.cat("CMS_channel")

    if dataset is None or mass is None:
        print("ERROR: Missing data_obs dataset or mass variable in workspace")
        for tf, _, _, _ in opened:
            tf.Close()
        return 1

    x_min, x_max = mass.getMin(), mass.getMax()
    frame = mass.frame(ROOT.RooFit.Range(x_min, x_max), ROOT.RooFit.Bins(350))
    frame.SetTitle("")
    frame.GetXaxis().SetTitle("m(ee) [GeV]")
    frame.GetYaxis().SetTitle("Events")
    frame.GetXaxis().SetLabelSize(0)

    dataset.plotOn(
        frame,
        ROOT.RooFit.Name("data_obs"),
        ROOT.RooFit.MarkerStyle(20),
        ROOT.RooFit.MarkerSize(0.8),
        ROOT.RooFit.DataError(ROOT.RooAbsData.Poisson),
    )

    plotted_models = []
    for _, ws, bkg_label, color in opened:
        model_b = ws.pdf("model_b")
        if model_b is None:
            print(f"WARNING: Missing model_b for {bkg_label}; skipping")
            continue
        model_name = f"model_{bkg_label}"
        opts = [
            ROOT.RooFit.Name(model_name),
            ROOT.RooFit.LineColor(ROOT.TColor.GetColor(color)),
            ROOT.RooFit.LineWidth(3),
        ]
        if cat is not None:
            opts.insert(0, ROOT.RooFit.ProjWData(cat, dataset))
        model_b.plotOn(frame, *opts)
        plotted_models.append((bkg_label, color, model_name))

    if not plotted_models:
        print("ERROR: No model_b curves were plotted; nothing to plot")
        for tf, _, _, _ in opened:
            tf.Close()
        return 1

    canvas = ROOT.TCanvas("c", "c", 900, 900)
    canvas.Divide(1, 2)
    top_pad = canvas.cd(1)
    top_pad.SetPad(0, 0.3, 1, 1)
    top_pad.SetBottomMargin(0.02)
    top_pad.SetGrid()
    top_pad.SetLogy()
    frame.Draw()

    x_width = 0.38
    y_width = 0.26
    legend_coordinates = {
        "region0" : (0.50, 0.2, 0.50 + x_width, 0.2 + y_width),
        "region1" : (0.50, 0.62, 0.50 + x_width, 0.62 + y_width),
        "region2" : (0.20, 0.1, 0.20 + x_width, 0.1 + y_width),
    }
    legend = ROOT.TLegend(*legend_coordinates[args.region])
    # legend = ROOT.TLegend(0.58, 0.68, 0.88, 0.88)
    legend.SetFillStyle(0)
    legend.SetBorderSize(0)
    legend.AddEntry(frame.findObject("data_obs"), "Data", "pe")

    for bkg_label, _, model_name in plotted_models:
        obj = frame.findObject(model_name)
        if obj:
            legend.AddEntry(obj, f"B-only {bkg_label}", "l")

    legend.Draw()

    title = f"B-only fit ({args.category}, {args.region}, {args.era})"
    frame.SetTitle(title)

    cms = ROOT.TLatex()
    cms.SetNDC()
    cms.SetTextFont(61)
    cms.SetTextSize(0.045)
    cms.DrawLatex(0.12, 0.92, "CMS")

    prelim = ROOT.TLatex()
    prelim.SetNDC()
    prelim.SetTextFont(52)
    prelim.SetTextSize(0.035)
    prelim.DrawLatex(0.21, 0.92, "Preliminary")

    meta = ROOT.TLatex()
    meta.SetNDC()
    meta.SetTextFont(42)
    meta.SetTextSize(0.035)
    meta.SetTextAlign(31)
    meta.DrawLatex(0.90, 0.92, f"13.6 TeV, {args.era}")

    # change y-axis range to 1.1 of max, 0.9 of min
    y_max = frame.GetMaximum() * 1.3
    y_min = frame.GetMinimum() * 0.9
    frame.SetMaximum(y_max)

    if args.region == "region1":
        y_min = 30
    if args.region == "region0":
        y_min = 5
    frame.SetMinimum(max(y_min, 0.1))  # avoid going to zero

    # Bottom pad: pull distributions for each model.
    bottom_pad = canvas.cd(2)
    bottom_pad.SetPad(0, 0, 1, 0.3)
    bottom_pad.SetTopMargin(0.03)
    bottom_pad.SetBottomMargin(0.30)
    bottom_pad.SetGrid()

    pull_frame = mass.frame(ROOT.RooFit.Range(x_min, x_max), ROOT.RooFit.Bins(350))        
    pull_frame.SetTitle("")
    pull_frame.GetXaxis().SetTitle("m(ee) [GeV]")
    pull_frame.GetXaxis().SetLabelSize(0.2)
    pull_frame.GetXaxis().SetTitleSize(0.22)
    pull_frame.GetYaxis().SetLabelSize(0.2)
    pull_frame.GetYaxis().SetTitleSize(0.22)
    pull_frame.GetYaxis().SetNdivisions(505)
    pull_frame.SetMinimum(-5.0)
    pull_frame.SetMaximum(5.0)

    for idx, (bkg_label, color, model_name) in enumerate(plotted_models):
        pull_hist = frame.pullHist("data_obs", model_name)
        if not pull_hist:
            continue
        pull_hist.SetName(f"pull_{bkg_label}_{idx}")
        root_color = ROOT.TColor.GetColor(color)
        pull_hist.SetMarkerColor(root_color)
        pull_hist.SetLineColor(root_color)
        pull_hist.SetMarkerStyle(20)
        pull_hist.SetMarkerSize(0.7)

        pull_hist.SetTitle("")
        pull_hist.GetXaxis().SetTitle("m(ee) [GeV]")
        pull_hist.GetYaxis().SetTitle("Pull")
        pull_hist.GetXaxis().SetLabelSize(0.10)
        pull_hist.GetXaxis().SetTitleSize(0.11)
        pull_hist.GetXaxis().SetTitleOffset(1.0)
        pull_hist.GetYaxis().SetLabelSize(0.09)
        pull_hist.GetYaxis().SetTitleSize(0.10)
        pull_hist.GetYaxis().SetTitleOffset(0.45)

        draw_opt = "AP" if idx == 0 else "P"
        pull_frame.addPlotable(pull_hist, draw_opt)

    pull_frame.Draw()
    zero = ROOT.TLine(x_min, 0.0, x_max, 0.0)
    zero.SetLineColor(ROOT.kGray + 1)
    zero.SetLineStyle(2)
    zero.Draw("same")

    out_tag = f"_{args.tag}" if args.tag else ""
    out_base = out_dir / f"bonly_overlay_{args.category}_{args.region}_{args.era}{out_tag}"
    canvas.SaveAs(f"{out_base}.png")
    canvas.SaveAs(f"{out_base}.pdf")
    print(f"Saved: {out_base}.png/.pdf")

    for tf, _, _, _ in opened:
        tf.Close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
