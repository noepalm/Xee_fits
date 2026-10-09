#!/usr/bin/env python3
import argparse
import math
import subprocess
from pathlib import Path

import ROOT

CMS_PALETTE = [
    "#5790fc",
    "#f89c20",
    "#e42536",
]


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


def _normalize_toy_index(selector):
    selector = str(selector).strip()
    if not selector:
        return None
    if selector == "asimov":
        return selector
    if selector.isdigit():
        idx = int(selector)
        if idx < 1:
            return None
        return str(idx)
    return None


def extract_single_toy(input_file, output_file, toy_selector):
    ROOT.TH1.AddDirectory(False)

    f_in = ROOT.TFile.Open(str(input_file), "READ")
    if not f_in or f_in.IsZombie():
        return None

    toys_dir = f_in.Get("toys")
    if toys_dir is None:
        f_in.Close()
        return None

    toy_names = [k.GetName() for k in toys_dir.GetListOfKeys() if k.GetName().startswith("toy_")]
    if not toy_names:
        f_in.Close()
        return None

    selector = _normalize_toy_index(toy_selector)
    if selector is None:
        f_in.Close()
        return None

    toy_name = f"toy_{selector}"
    if toy_name not in toy_names:
        f_in.Close()
        return None

    toy_key = toys_dir.GetKey(toy_name)
    if toy_key is None:
        f_in.Close()
        return None

    toy = toy_key.ReadObj()
    if toy is None or not toy.InheritsFrom("RooAbsData"):
        f_in.Close()
        return None

    toy.SetName("toy_1")
    toy_clone = toy.Clone("toy_1")

    f_out = ROOT.TFile.Open(str(output_file), "RECREATE")
    if not f_out or f_out.IsZombie():
        f_in.Close()
        return None

    d_out = f_out.mkdir("toys")
    d_out.cd()
    toy_clone.Write("toy_1", ROOT.TObject.kOverwrite)

    f_out.Close()
    f_in.Close()
    return toy_name


def resolve_fit_specific_workspace(workdir, root_file, fit_name):
    mass_dir = Path(workdir).resolve()
    ee_dir = mass_dir.parent
    cards_dir = ee_dir.parent
    cards_name = cards_dir.name
    token = "_envelope_"
    if token not in cards_name:
        return None

    fit_cards_name = cards_name.replace(token, f"_altbkg_{fit_name}_")
    fit_cards_dir = cards_dir.parent / fit_cards_name
    fit_root = fit_cards_dir / "ee" / mass_dir.name / root_file
    return str(fit_root.resolve())


def get_graph_yerr(graph, idx):
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


def _best_fit_r_param(tf):
    for obj_name in ("fit_s", "fit_mdf", "fit_b"):
        fit_result = tf.Get(obj_name)
        if fit_result is None:
            continue

        try:
            params = fit_result.floatParsFinal()
            r_var = params.find("r")
            if r_var is None:
                continue
            return r_var
        except Exception:
            continue

    return None


def _round_to_significant_digits(value, significant_digits=2):
    value = abs(float(value))
    if value <= 0.0 or not math.isfinite(value):
        return 0

    exponent = math.floor(math.log10(value))
    return max(0, significant_digits - 1 - exponent)


def get_best_fit_r_label(tf):
    r_var = _best_fit_r_param(tf)
    if r_var is None:
        return None

    try:
        r_value = float(r_var.getVal())
    except Exception:
        return None

    r_err_hi = None
    r_err_lo = None
    for method_name in ("getErrorHi", "getAsymErrorHi"):
        if hasattr(r_var, method_name):
            try:
                r_err_hi = float(getattr(r_var, method_name)())
                break
            except Exception:
                pass
    for method_name in ("getErrorLo", "getAsymErrorLo"):
        if hasattr(r_var, method_name):
            try:
                r_err_lo = float(getattr(r_var, method_name)())
                break
            except Exception:
                pass

    try:
        sym_err = float(r_var.getError())
    except Exception:
        sym_err = 0.0

    if r_err_hi is None:
        r_err_hi = sym_err
    if r_err_lo is None:
        r_err_lo = -sym_err

    err_for_digits = max(abs(r_err_lo), abs(r_err_hi))
    decimals = _round_to_significant_digits(err_for_digits)
    r_value_str = f"{r_value:.{decimals}f}"
    r_err_hi_str = f"{abs(r_err_hi):.{decimals}f}"
    r_err_lo_str = f"{abs(r_err_lo):.{decimals}f}"
    return f"r = {r_value_str}^{{+{r_err_hi_str}}}_{{-{r_err_lo_str}}}"


def open_fitdiag_shapes(path, channel_name):
    tf = ROOT.TFile.Open(str(path), "READ")
    if not tf or tf.IsZombie():
        return None, None, None, None, None

    base = f"shapes_fit_s/{channel_name}"
    data = tf.Get(f"{base}/data")
    total = tf.Get(f"{base}/total")
    total_bkg = tf.Get(f"{base}/total_background")

    print(f"DEBUG: opened {path}: data={data}, total={total}, total_bkg={total_bkg}")

    if total is None:
        tf.Close()
        return None, None, None, None, None

    return tf, data, total, total_bkg, get_best_fit_r_label(tf)


def build_pull_graph(data_graph, fit_hist, name, color):
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


def infer_r_range(mass, run_mode_label):
    if mass < 2.0:
        if run_mode_label == "no_signal":
            return -400, 400
        return -10, 10

    if run_mode_label == "no_signal":
        return -50, 50
    return -10, 10


def run_fitdiagnostics(
    fit_root_file,
    toy_file,
    out_dir,
    n_label,
    pdf_param,
    pdf_param_new,
    fit_idx,
    r_min,
    r_max,
    log_path,
):
    cmd = [
        "combine",
        "-M",
        "FitDiagnostics",
        fit_root_file,
        "--setParameters",
        f"{pdf_param}={fit_idx},{pdf_param_new}={fit_idx}",
        "--freezeParameters",
        f"{pdf_param},{pdf_param_new}",
        "--rMin",
        str(r_min),
        "--rMax",
        str(r_max),
        "-t",
        "1",
        "-n",
        n_label,
        "--toysFile",
        toy_file,
        "--cminDefaultMinimizerStrategy",
        "0",
        "--robustFit",
        "1",
        "--saveWorkspace",
        "--saveShapes",
        "--saveNormalizations",
        "-v",
        "3",
    ]

    proc = subprocess.run(
        cmd,
        cwd=str(out_dir),
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    with open(log_path, "w") as f:
        f.write("=" * 80 + "\n")
        f.write("CMD: " + " ".join(cmd) + "\n")
        f.write(f"RET: {proc.returncode}\n")
        f.write("=" * 80 + "\n")
        f.write(proc.stdout or "")
        if proc.stdout and not proc.stdout.endswith("\n"):
            f.write("\n")

    if proc.returncode != 0:
        raise subprocess.CalledProcessError(proc.returncode, cmd, output=proc.stdout)


def main():
    parser = argparse.ArgumentParser(
        description="Extract one toy, rerun FitDiagnostics on it for each fit model, then plot the resulting shapes"
    )
    parser.add_argument("--toy-file", required=True, help="GenerateOnly toys ROOT file")
    parser.add_argument(
        "--toy-index",
        default="1",
        help="Toy to plot, either an exact toy name like toy_asimov or a 1-based toy number like 2",
    )
    parser.add_argument("--mass-dir", required=True, help="Mass-point directory containing the channel ROOT file")
    parser.add_argument("--category", required=True)
    parser.add_argument("--era", required=True)
    parser.add_argument("--region", required=True)
    parser.add_argument("--mass", required=True, type=float)
    parser.add_argument("--truth-label", required=True)
    parser.add_argument("--run-label", default="")
    parser.add_argument("--fit-labels", nargs=2, default=["Bernstein", "Chebyshev"], help="Fit labels")
    parser.add_argument("-o", "--output-folder", required=True)
    parser.add_argument("-t", "--tag", default="")
    args = parser.parse_args()

    ROOT.gROOT.SetBatch(True)
    ROOT.gStyle.SetOptStat(0)

    toy_selector = _normalize_toy_index(args.toy_index)
    if toy_selector is None:
        print(f"ERROR: Invalid toy index '{args.toy_index}'. Expected a positive integer or 'asimov'.")
        return 1

    toy_name_for_paths = f"toy_{toy_selector}"

    out_dir = Path(args.output_folder)
    out_dir.mkdir(parents=True, exist_ok=True)
    rerun_dir = out_dir / "rerun_fitdiagnostics"
    rerun_dir.mkdir(parents=True, exist_ok=True)

    channel_name = get_channel_name(args.category, args.era)
    if channel_name is None:
        print(f"ERROR: Unsupported category '{args.category}'")
        return 1

    fit_names = [label.lower() for label in args.fit_labels]
    pdf_param = f"pdf_index_{args.era}_envelope"
    pdf_param_new = f"CMS_EXO25020_bkgEnvelopeIdx_{args.era}"
    run_mode_label = args.run_label if args.run_label else "no_signal"
    r_min, r_max = infer_r_range(float(args.mass), run_mode_label)

    root_file = f"Xee_ee_{category_to_cat_id(args.category)}_{args.era}.root"

    toy_workdir = rerun_dir / toy_name_for_paths
    toy_workdir.mkdir(parents=True, exist_ok=True)

    toy_extract_path = toy_workdir / f"single_toy_truth{args.truth_label}_{toy_name_for_paths}.root"
    original_toy_name = extract_single_toy(args.toy_file, toy_extract_path, toy_selector)
    if original_toy_name is None:
        print(f"ERROR: Could not extract toy '{toy_name_for_paths}' from {args.toy_file}")
        return 1
    print(f"DEBUG: extracted source toy '{original_toy_name}' to '{toy_extract_path}'")

    opened_fitdiag = []
    for fit_idx, fit_name in enumerate(fit_names):
        fit_root_file = resolve_fit_specific_workspace(args.mass_dir, root_file, fit_name)
        if fit_root_file is None:
            print(
                f"ERROR: Could not resolve fit-specific workspace from mass dir '{args.mass_dir}' for fit '{fit_name}'"
            )
            for tf_open, _, _, _, _ in opened_fitdiag:
                tf_open.Close()
            return 1

        if not Path(fit_root_file).exists():
            print(f"ERROR: Missing fit workspace: {fit_root_file}")
            for tf_open, _, _, _, _ in opened_fitdiag:
                tf_open.Close()
            return 1

        fit_label = args.fit_labels[fit_idx]
        n_label = (
            f".toyfit_truth{args.truth_label}_fit{fit_label}_{args.category}_{args.era}_{run_mode_label}"
            f"_{toy_name_for_paths}_rerun"
        )
        log_path = toy_workdir / f"fitDiagnostics_truth{args.truth_label}_{fit_label}.log"

        try:
            run_fitdiagnostics(
                fit_root_file=fit_root_file,
                toy_file=str(toy_extract_path),
                out_dir=toy_workdir,
                n_label=n_label,
                pdf_param=pdf_param,
                pdf_param_new=pdf_param_new,
                fit_idx=fit_idx,
                r_min=r_min,
                r_max=r_max,
                log_path=log_path,
            )
        except subprocess.CalledProcessError:
            print(f"ERROR: FitDiagnostics failed for {fit_label}; see {log_path}")
            for tf_open, _, _, _, _ in opened_fitdiag:
                tf_open.Close()
            return 1

        fitdiag_path = toy_workdir / f"fitDiagnostics{n_label}.root"
        tf, data_g, total_h, bkg_h, r_label = open_fitdiag_shapes(fitdiag_path, channel_name)
        if total_h is None:
            print(f"ERROR: Could not read shapes from {fitdiag_path}")
            for tf_open, _, _, _, _ in opened_fitdiag:
                tf_open.Close()
            return 1

        opened_fitdiag.append((tf, data_g, total_h, bkg_h, r_label))

    plotted_labels = []
    data_graph = None
    for idx, (fit_label, (_, data_g, total_hist, bkg_hist, r_label)) in enumerate(zip(args.fit_labels, opened_fitdiag)):
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
            bkg_clone.SetLineStyle(2)
            bkg_clone.SetLineWidth(2)

        plotted_labels.append((fit_label, r_label, total_hist, bkg_clone))

    if not plotted_labels:
        print("ERROR: No valid FitDiagnostics inputs to plot")
        for tf_open, _, _, _, _ in opened_fitdiag:
            tf_open.Close()
        return 1

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

    axis_hist = plotted_labels[0][2].Clone("axis_hist")
    axis_hist.SetDirectory(0)
    axis_hist.Reset("ICES")
    axis_hist.SetTitle("")
    axis_hist.GetXaxis().SetTitle("m(ee) [GeV]")
    axis_hist.GetYaxis().SetTitle("Event density")
    axis_hist.GetXaxis().SetLabelSize(0)

    y_max = max(*[h.GetMaximum() for _, _, h, _ in plotted_labels], data_graph.GetMaximum())
    y_min = max(*[h.GetMinimum() for _, _, h, _ in plotted_labels], data_graph.GetMinimum())
    print("DEBUG: y_min =", y_min, "y_max =", y_max)
    axis_hist.SetMinimum(max(y_min * 0.8, 1e-3))
    axis_hist.SetMaximum(y_max * 1.2)

    top_pad.cd()
    axis_hist.Draw("axis")

    if data_graph is not None:
        data_graph.SetMarkerStyle(20)
        data_graph.SetMarkerSize(0.8)
        data_graph.Draw("P same")
    for _, _, total_hist, bkg_hist in plotted_labels:
        total_hist.Draw("hist same")
        if bkg_hist is not None:
            bkg_hist.Draw("hist same")

    x_width = 0.38
    y_width = 0.26
    legend_coordinates = {
        "region0": (0.50, 0.2, 0.50 + x_width, 0.2 + y_width),
        "region1": (0.50, 0.62, 0.50 + x_width, 0.62 + y_width),
        "region2": (0.10, 0.20, 0.10 + x_width, 0.2 + y_width),
    }
    legend = ROOT.TLegend(*legend_coordinates[args.region])
    legend.SetFillStyle(0)
    legend.SetBorderSize(0)
    legend.AddEntry(data_graph, f"Toy {original_toy_name}", "pe")

    for fit_label, r_label, total_hist, bkg_hist in plotted_labels:
        label_text = fit_label if not r_label else f"{fit_label}, {r_label}"
        legend.AddEntry(total_hist, label_text, "l")
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

    pull_graphs = []
    for idx, (_, _, total_hist, _) in enumerate(plotted_labels):
        color = ROOT.TColor.GetColor(CMS_PALETTE[idx])
        pull_graph = build_pull_graph(data_graph, total_hist, f"pull_{idx}", color)
        pull_graphs.append(pull_graph)
        pull_graph.Draw("P same")

    extra = f"_{args.tag}" if args.tag else ""
    run_suffix = f"_{args.run_label}" if args.run_label else ""
    out_base = out_dir / (
        f"toy_fit_{args.category}_{args.region}_{args.era}_M{args.mass}"
        f"_truth{args.truth_label}_{toy_name_for_paths}{run_suffix}{extra}"
    )

    top_pad.SetGrid()
    bottom_pad.SetGrid()
    top_pad.Update()
    bottom_pad.Update()

    canvas.SaveAs(f"{out_base}.png")
    canvas.SaveAs(f"{out_base}.pdf")
    print(f"Saved: {out_base}.png/.pdf")
    print(f"Rerun FitDiagnostics outputs kept in: {toy_workdir}")

    for tf_open, _, _, _, _ in opened_fitdiag:
        tf_open.Close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())