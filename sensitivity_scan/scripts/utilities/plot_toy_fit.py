#!/usr/bin/env python3

import argparse
from pathlib import Path

import ROOT


CMS_PALETTE = [
    "#5790fc",
    "#f89c20",
    "#e42536",
]


def open_fitdiag_shapes(path, channel_name):
    tf = ROOT.TFile.Open(str(path), "READ")
    if not tf or tf.IsZombie():
        return None, None, None, None

    base = f"shapes_fit_s/{channel_name}"
    data = tf.Get(f"{base}/data")
    total = tf.Get(f"{base}/total")
    total_bkg = tf.Get(f"{base}/total_background")

    if total is None:
        tf.Close()
        return None, None, None, None

    return tf, data, total, total_bkg


def category_to_cat_id(category):
    mapping = {
        "etaHigh": 0,
        "etaLow": 1,
        "dRHigh": 2,
        "dRLow": 3,
        "inclusive": 4,
    }
    return mapping.get(category)


def get_channel_name(category, era):
    cat_id = category_to_cat_id(category)
    if cat_id is None:
        return None
    return f"Xee_ee_{cat_id}_{era}"


def open_toy_dataset(toy_file, toy_index):
    tf = ROOT.TFile.Open(str(toy_file), "READ")
    if not tf or tf.IsZombie():
        return None, None, None

    toys_dir = tf.Get("toys")
    if toys_dir is None:
        tf.Close()
        return None, None, None

    toy_names = sorted([k.GetName() for k in toys_dir.GetListOfKeys() if k.GetName().startswith("toy_")])
    if not toy_names:
        tf.Close()
        return None, None, None

    idx = toy_index
    if idx < 0:
        idx = 0
    if idx >= len(toy_names):
        idx = len(toy_names) - 1

    toy_name = toy_names[idx]
    ds = toys_dir.Get(toy_name)
    if ds is None:
        tf.Close()
        return None, None, None

    return tf, ds, toy_name

def get_graph_yerr(graph, idx):
    """Return a positive y-error from either TGraphErrors or TGraphAsymmErrors."""
    try:
        err = float(graph.GetErrorY(idx))
        if err > 0:
            return err
    except Exception:
        pass

    err_low = 0.0
    err_high = 0.0
    try:
        err_low = float(graph.GetErrorYlow(idx))
    except Exception:
        pass
    try:
        err_high = float(graph.GetErrorYhigh(idx))
    except Exception:
        pass

    err = 0.5 * (max(0.0, err_low) + max(0.0, err_high))
    return err if err > 0 else 0.0


def build_pull_graph(data_graph, fit_hist, name, color):
    """Build pull graph: (data - fit) / sigma_data for each data point."""
    pull = ROOT.TGraphErrors()
    pull.SetName(name)

    n = data_graph.GetN() if data_graph is not None else 0
    ip = 0
    for i in range(n):
        x = float(data_graph.GetX()[i])
        y = float(data_graph.GetY()[i])
        err = get_graph_yerr(data_graph, i)
        if err <= 0:
            continue

        fit_y = float(fit_hist.GetBinContent(fit_hist.FindBin(x)))
        pull_y = (y - fit_y) / err
        pull.SetPoint(ip, x, pull_y)
        pull.SetPointError(ip, 0.0, 1.0)
        ip += 1

    pull.SetMarkerColor(color)
    pull.SetLineColor(color)
    pull.SetMarkerStyle(20)
    pull.SetMarkerSize(0.55)
    return pull


def main():
    parser = argparse.ArgumentParser(description="Plot one toy with S+B fits for all three background functions")
    parser.add_argument("--toy-file", required=True, help="GenerateOnly toys ROOT file")
    parser.add_argument("--sb-files", nargs=3, required=True, help="Three fitDiagnostics.<label>.root files")
    parser.add_argument("--fit-labels", nargs=3, default=["Chebyshev", "Bernstein", "PolyExp"], help="Labels for fit functions")
    parser.add_argument("--toy-index", type=int, default=0, help="Toy index to plot")
    parser.add_argument("--category", required=True)
    parser.add_argument("--era", required=True)
    parser.add_argument("--region", required=True)
    parser.add_argument("--mass", required=True)
    parser.add_argument("--truth-label", required=True)
    parser.add_argument("--run-label", default="")
    parser.add_argument("-o", "--output-folder", required=True)
    parser.add_argument("-t", "--tag", default="")
    args = parser.parse_args()
    
    print("Arguments:")
    for arg_name, arg_value in vars(args).items():
        print(f"  {arg_name}: {arg_value}")

    ROOT.gROOT.SetBatch(True)
    ROOT.gStyle.SetOptStat(0)

    out_dir = Path(args.output_folder)
    out_dir.mkdir(parents=True, exist_ok=True)

    channel_name = get_channel_name(args.category, args.era)
    if channel_name is None:
        print(f"ERROR: Unsupported category '{args.category}'")
        return 1

    toy_tf, toy_ds, toy_name = open_toy_dataset(args.toy_file, args.toy_index)
    if toy_ds is None:
        toy_name = f"toy_{args.toy_index}"

    opened_fitdiag = []
    for fitdiag_file in args.sb_files:
        tf, data_g, total_h, bkg_h = open_fitdiag_shapes(fitdiag_file, channel_name)
        if total_h is None:
            print(
                f"ERROR: Could not open shapes from {fitdiag_file} at "
                f"shapes_fit_s/{channel_name}/{{data,total,total_background}}"
            )
            if toy_tf:
                toy_tf.Close()
            for tf_open, _, _, _ in opened_fitdiag:
                tf_open.Close()
            return 1
        opened_fitdiag.append((tf, data_g, total_h, bkg_h))

    plotted_labels = []
    data_graph = None
    for idx in range(3):
        fitdiag_file = args.sb_files[idx]
        fit_label = args.fit_labels[idx]
        _, data_g, total_hist, bkg_hist = opened_fitdiag[idx]

        if data_graph is None and data_g is not None:
            data_graph = data_g.Clone("toy_data_graph")

        color = ROOT.TColor.GetColor(CMS_PALETTE[idx])
        total_hist = total_hist.Clone(f"total_{fit_label}_{idx}")
        total_hist.SetDirectory(0)
        total_hist.SetLineColor(color)
        total_hist.SetLineWidth(3)

        bkg_clone = None
        if bkg_hist is not None:
            bkg_clone = bkg_hist.Clone(f"bkg_{fit_label}_{idx}")
            bkg_clone.SetDirectory(0)
            bkg_clone.SetLineColor(color)
            bkg_clone.SetLineStyle(9)
            bkg_clone.SetLineWidth(2)

        plotted_labels.append((fit_label, total_hist, bkg_clone))

    canvas = ROOT.TCanvas("c_toyfit", "c_toyfit", 900, 900)
    canvas.Divide(1, 2)
    top_pad = canvas.cd(1)
    top_pad.SetPad(0.0, 0.30, 1.0, 1.0)
    top_pad.SetBottomMargin(0.02)
    top_pad.SetGrid()
    top_pad.SetLogy()

    bottom_pad = canvas.cd(2)
    bottom_pad.SetPad(0.0, 0.0, 1.0, 0.30)
    bottom_pad.SetTopMargin(0.03)
    bottom_pad.SetBottomMargin(0.30)
    bottom_pad.SetGrid()

    if not plotted_labels:
        print("ERROR: No valid fitDiagnostics inputs to plot")
        if toy_tf:
            toy_tf.Close()
        for tf_open, _, _, _ in opened_fitdiag:
            tf_open.Close()
        return 1

    axis_hist = plotted_labels[0][1].Clone("axis_hist")
    axis_hist.SetDirectory(0)
    axis_hist.Reset("ICES")
    axis_hist.SetTitle("")
    axis_hist.GetXaxis().SetTitle("m(ee) [GeV]")
    axis_hist.GetYaxis().SetTitle("Events")
    axis_hist.GetXaxis().SetLabelSize(0)

    y_max = max(*[h.GetMaximum() for _, h, _ in plotted_labels], data_graph.GetMaximum())
    y_min = max(*[h.GetMinimum() for _, h, _ in plotted_labels], data_graph.GetMinimum())
    axis_hist.SetMinimum(max(y_min * 0.8, 1e-3))
    axis_hist.SetMaximum(y_max * 1.2)

    top_pad.cd()
    axis_hist.Draw("axis")

    if data_graph is not None:
        data_graph.SetMarkerStyle(20)
        data_graph.SetMarkerSize(0.8)
        data_graph.Draw("P same")
    for _, total_hist, bkg_hist in plotted_labels:
        total_hist.Draw("hist same")
        if bkg_hist is not None:
            bkg_hist.Draw("hist same")

    # change legend position based on region
    x_width = 0.38
    y_width = 0.26
    legend_coordinates = {
        "region0" : (0.50, 0.2, 0.50 + x_width, 0.2 + y_width),
        "region1" : (0.50, 0.62, 0.50 + x_width, 0.62 + y_width),
        "region2" : (0.20, 0.20, 0.20 + x_width, 0.62 + y_width),
    }
    legend = ROOT.TLegend(*legend_coordinates[args.region])
    legend.SetFillStyle(0)
    legend.SetBorderSize(0)
    if data_graph is not None:
        legend.AddEntry(data_graph, f"Toy {toy_name}", "pe")

    for fit_label, total_hist, bkg_hist in plotted_labels:
        legend.AddEntry(total_hist, fit_label, "l")
        if bkg_hist is not None:
            legend.AddEntry(bkg_hist, f"{fit_label} (bkg only)", "l")

    legend.Draw()

    title = ROOT.TLatex()
    title.SetNDC()
    title.SetTextFont(42)
    title.SetTextSize(0.03)
    title.DrawLatex(
        0.12,
        0.965,
        f"Toy + S+B fits ({args.category}, {args.region}, {args.era}, M{args.mass}, truth {args.truth_label})",
    )

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

    # Pull panel: one pull graph per total S+B model.
    bottom_pad.cd()
    pull_axis = axis_hist.Clone("pull_axis")
    pull_axis.Reset("ICES")
    pull_axis.SetTitle("")
    pull_axis.GetXaxis().SetTitle("m(ee) [GeV]")
    pull_axis.GetYaxis().SetTitle("Pull")
    pull_axis.GetXaxis().SetLabelSize(0.10)
    pull_axis.GetXaxis().SetTitleSize(0.11)
    pull_axis.GetXaxis().SetTitleOffset(1.0)
    pull_axis.GetYaxis().SetLabelSize(0.09)
    pull_axis.GetYaxis().SetTitleSize(0.10)
    pull_axis.GetYaxis().SetTitleOffset(0.45)
    pull_axis.SetMinimum(-5.0)
    pull_axis.SetMaximum(5.0)
    pull_axis.Draw("axis")

    line0 = ROOT.TLine(pull_axis.GetXaxis().GetXmin(), 0.0, pull_axis.GetXaxis().GetXmax(), 0.0)
    line0.SetLineStyle(2)
    line0.SetLineColor(ROOT.kGray + 2)
    line0.Draw("same")

    for idx, (_, total_hist, _) in enumerate(plotted_labels):
        color = ROOT.TColor.GetColor(CMS_PALETTE[idx])
        pull_graph = build_pull_graph(data_graph, total_hist, f"pull_{idx}", color)
        pull_graph.Draw("P same")

    extra = f"_{args.tag}" if args.tag else ""
    run_suffix = f"_{args.run_label}" if args.run_label else ""
    out_base = out_dir / (
        f"toy_fit_{args.category}_{args.region}_{args.era}_M{args.mass}"
        f"_truth{args.truth_label}_toy{args.toy_index}{run_suffix}{extra}"
    )

    canvas.SaveAs(f"{out_base}.png")
    canvas.SaveAs(f"{out_base}.pdf")
    print(f"Saved: {out_base}.png/.pdf")

    if toy_tf:
        toy_tf.Close()
    for tf_open, _, _, _ in opened_fitdiag:
        tf_open.Close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
