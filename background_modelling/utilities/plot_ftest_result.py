import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import mplhep as hep
import numpy as np
from scipy.stats import f

import ROOT
import matplotlib.pyplot as plt

hep.style.use(hep.style.CMS)

cms_color_palette = [
    "#3f90da",
    "#ffa90e",
    "#bd1f01",
    "#94a4a2",
    "#832db6",
    "#a96b59",
    "#e76300",
    "#b9ac70",
    "#717581",
    "#92dadd",
]

lumi = {
    "2022" : 7.73,
    "2022EE" : 26.62,
    "2023" : 14.54,
    "2023BPix" : 9.68,
}

def compute_f_critical(p_n: int, p_np1: int, n_bins: int, alpha: float = 0.05) -> Optional[float]:
    """Compute critical F-value at given alpha significance level."""
    d1 = p_np1 - p_n
    d2 = n_bins - p_np1
    if d1 <= 0 or d2 <= 0:
        return None
    return float(f.ppf(1 - alpha, d1, d2))


def parse_orders(raw_orders: str) -> List[int]:
    """Parse a comma-separated list of integer function orders."""
    tokens = [tok.strip() for tok in raw_orders.split(",") if tok.strip()]
    if not tokens:
        raise ValueError("No function orders were provided")
    try:
        orders = sorted({int(tok) for tok in tokens})
    except ValueError as exc:
        raise ValueError("Orders must be integers (example: 4,5,6,7)") from exc
    if len(orders) < 2:
        raise ValueError("At least two orders are needed to compute F-scores")
    return orders


def get_mass_var(workspace: ROOT.RooWorkspace, dataset: ROOT.RooAbsData) -> ROOT.RooRealVar:
    """Retrieve the mass variable used by the dataset/PDF."""
    mass = workspace.var("mass")
    if mass:
        return mass

    row = dataset.get(0)
    if not row:
        raise RuntimeError("Dataset has no entries; cannot retrieve mass variable")

    var = row.first()
    if not var:
        raise RuntimeError("Could not retrieve a RooRealVar from dataset")
    return var


def compute_chi2_and_npar(
    workspace_path: Path,
    dataset_name: str,
    pdf_name: str,
    npar_offset: int = 0,
) -> Tuple[float, int, int]:
    """Open one workspace and compute chi2, free parameter count, and number of bins."""
    root_file = ROOT.TFile.Open(str(workspace_path))
    if not root_file or root_file.IsZombie():
        raise RuntimeError(f"Cannot open ROOT file: {workspace_path}")

    workspace = root_file.Get("w")
    if not workspace:
        root_file.Close()
        raise RuntimeError(f"Workspace 'w' not found in file: {workspace_path}")

    data = workspace.data(dataset_name)
    if not data:
        root_file.Close()
        raise RuntimeError(f"Dataset '{dataset_name}' not found in: {workspace_path}")

    pdf = workspace.pdf(pdf_name)
    if not pdf:
        root_file.Close()
        raise RuntimeError(f"PDF '{pdf_name}' not found in: {workspace_path}")

    mass = get_mass_var(workspace, data)
    frame = mass.frame()
    data.plotOn(frame, ROOT.RooFit.Name("data"))
    pdf.plotOn(frame, ROOT.RooFit.Name("pdf"))

    data_hist = frame.findObject("data")
    n_bins = int(data_hist.GetN()) if data_hist else 350

    n_free_raw = pdf.getParameters(data).selectByAttrib("Constant", False).getSize()
    n_free = n_free_raw + npar_offset
    
    # RooPlot::chiSquare returns REDUCED chi2 (chi2 / (nbins - npar))
    chi2_red = frame.chiSquare("pdf", "data", n_free)
    
    workspace.Delete()
    root_file.Close()
    return chi2_red, n_free, n_bins


def compute_fscore(chi2_red_n: float, chi2_red_np1: float, p_n: int, p_np1: int, n_bins: int) -> Optional[float]:
    """Compute F_n = ((chi2_n - chi2_n+1)/(p_n+1 - p_n)) / (chi2_n+1/(n_bins - p_n+1))."""
    
    # Convert RooFit's reduced chi2 back into absolute chi2 for the standard F-test
    chi2_n = chi2_red_n * (n_bins - p_n)
    chi2_np1 = chi2_red_np1 * (n_bins - p_np1)
    
    delta_p = p_np1 - p_n
    denom_dof = n_bins - p_np1

    if delta_p <= 0 or denom_dof <= 0 or chi2_np1 == 0:
        return None

    numerator = (chi2_n - chi2_np1) / float(delta_p)
    denominator = chi2_np1 / float(denom_dof)
    if denominator == 0:
        return None
    return numerator / denominator


def extract_overlay_points(
    workspace_path: Path,
    dataset_name: str,
    pdf_name: str,
) -> Tuple[List[Tuple[float, float, float, float, float, float]], List[Tuple[float, float]]]:
    """Extract data points and fitted PDF curve points from a workspace for matplotlib overlay."""
    root_file = ROOT.TFile.Open(str(workspace_path))
    if not root_file or root_file.IsZombie():
        raise RuntimeError(f"Cannot open ROOT file: {workspace_path}")

    workspace = root_file.Get("w")
    if not workspace:
        root_file.Close()
        raise RuntimeError(f"Workspace 'w' not found in file: {workspace_path}")

    data = workspace.data(dataset_name)
    if not data:
        root_file.Close()
        raise RuntimeError(f"Dataset '{dataset_name}' not found in: {workspace_path}")

    pdf = workspace.pdf(pdf_name)
    if not pdf:
        root_file.Close()
        raise RuntimeError(f"PDF '{pdf_name}' not found in: {workspace_path}")

    mass = get_mass_var(workspace, data)
    frame = mass.frame()
    data.plotOn(frame, ROOT.RooFit.Name("data"))
    pdf.plotOn(frame, ROOT.RooFit.Name("pdf"))

    data_hist = frame.findObject("data")
    pdf_curve = frame.findObject("pdf")
    if not data_hist or not pdf_curve:
        root_file.Close()
        raise RuntimeError(f"Could not retrieve RooPlot objects for {workspace_path}")

    data_points: List[Tuple[float, float, float, float, float, float]] = []
    for i in range(int(data_hist.GetN())):
        x = float(data_hist.GetPointX(i))
        y = float(data_hist.GetPointY(i))
        exl = float(data_hist.GetErrorXlow(i))
        exh = float(data_hist.GetErrorXhigh(i))
        eyl = float(data_hist.GetErrorYlow(i))
        eyh = float(data_hist.GetErrorYhigh(i))
        data_points.append((x, y, exl, exh, eyl, eyh))

    pdf_points: List[Tuple[float, float]] = []
    for i in range(int(pdf_curve.GetN())):
        x = float(pdf_curve.GetPointX(i))
        y = float(pdf_curve.GetPointY(i))
        pdf_points.append((x, y))

    workspace.Delete()
    root_file.Close()
    return data_points, pdf_points


def interpolate_curve_at_x(pdf_points: List[Tuple[float, float]], xvals: List[float]) -> List[float]:
    """Interpolate model curve values at arbitrary x points."""
    if not pdf_points:
        return [0.0 for _ in xvals]

    x_curve = np.array([p[0] for p in pdf_points], dtype=float)
    y_curve = np.array([p[1] for p in pdf_points], dtype=float)
    order = np.argsort(x_curve)
    x_curve = x_curve[order]
    y_curve = y_curve[order]

    y_interp = np.interp(xvals, x_curve, y_curve, left=y_curve[0], right=y_curve[-1])
    return [float(y) for y in y_interp]


def main() -> int:
    parser = argparse.ArgumentParser(description="Plot F-test results by mass region")
    parser.add_argument(
        "--family",
        required=True,
        help="Label for function family (example: chebyshev, polyexp, bernstein)",
    )
    parser.add_argument(
        "--orders",
        required=True,
        help="Comma-separated list of orders to compare (example: 4,5,6,7)",
    )
    parser.add_argument(
        "--input-folder",
        required=True,
        help="Folder containing input workspace ROOT files",
    )
    parser.add_argument(
        "--output-folder",
        required=True,
        help="Folder where output plot is saved",
    )
    parser.add_argument(
        "--era",
        default="2022",
        help="Era to process (default: 2022)",
    )
    parser.add_argument(
        "--workspace-template",
        default="dataset_data_{region}_binned_data_altbkg_{family}{order}_withScaleSyst_IDSF_triggerSF_finerBinning_tighterCuts_Ftest_{era}_full.root",
        help="Template used to build workspace file names.",
    )
    parser.add_argument(
        "--dataset-name-template",
        default="data_obs",
        help="Dataset name template inside the workspace.",
    )
    parser.add_argument(
        "--pdf-name-template",
        default="full_bkg_model_{era}",
        help="PDF name template inside the workspace.",
    )
    parser.add_argument(
        "--alpha",
        default=0.05,
        type=float,
        help="Alpha significance level for F-test threshold (default: 0.05)",
    )
    parser.add_argument(
        "--output-name",
        default="",
        help="Optional output file name (default: ftest_{family}_{era}.png)",
    )
    parser.add_argument(
        "--overlay-output-name",
        default="",
        help="Optional overlay plot file name (default: fits_overlay_{family}_{era}.png)",
    )
    parser.add_argument(
        "--unblinded",
        action="store_true",
        help="If set, unblinded data will be used for plotting (default: False)"
    )
    args = parser.parse_args()

    ROOT.gROOT.SetBatch(True)
    ROOT.RooMsgService.instance().setGlobalKillBelow(ROOT.RooFit.WARNING)

    orders = parse_orders(args.orders)
    input_folder = Path(args.input_folder)
    output_folder = Path(args.output_folder)
    output_folder.mkdir(parents=True, exist_ok=True)

    regions = ["region0", "region1", "region2"]

    # Now storing n_bins as well: (order, chi2_red, n_params, n_bins)
    chi2_results: Dict[str, List[Tuple[int, float, int, int]]] = {region: [] for region in regions}
    overlay_data: Dict[str, Optional[List[Tuple[float, float, float, float, float, float]]]] = {
        region: None for region in regions
    }
    overlay_curves: Dict[str, List[Tuple[int, List[Tuple[float, float]], float]]] = {
        region: [] for region in regions
    }

    print("=" * 72)
    print("Computing chi2 and free parameters for each region/order")
    print("=" * 72)

    for region in regions:
        print(f"\n[{region}]")
        for order in orders:
            workspace_name = args.workspace_template.format(
                region=region,
                family=args.family,
                order=order,
                era=args.era,
            )
            workspace_path = input_folder / workspace_name
            dataset_name = args.dataset_name_template.format(
                region=region,
                family=args.family,
                order=order,
                era=args.era,
            )
            pdf_name = args.pdf_name_template.format(
                region=region,
                family=args.family,
                order=order,
                era=args.era,
            )

            if not workspace_path.exists():
                print(f"  [missing] order {order}: {workspace_path}")
                continue

            try:
                npar_offset = 12 if region == "region1" else 12 if region == "region0" else 0
                chi2_red, npar, n_bins = compute_chi2_and_npar(
                    workspace_path,
                    dataset_name,
                    pdf_name,
                    npar_offset=npar_offset,
                )
                chi2_results[region].append((order, chi2_red, npar, n_bins))
                
                data_points, pdf_points = extract_overlay_points(
                    workspace_path,
                    dataset_name,
                    pdf_name,
                )
                if overlay_data[region] is None:
                    overlay_data[region] = data_points
                overlay_curves[region].append((order, pdf_points, chi2_red))
                
                ndof = n_bins - npar
                print(f"  order {order}: chi2/ndf={chi2_red:.6f}, npar={npar}, ndof={ndof} (nbins={n_bins})")
            except Exception as exc:
                print(f"  [error] order {order}: {exc}")

    fscore_results: Dict[str, List[Tuple[int, float, float]]] = {region: [] for region in regions}

    print("\n" + "=" * 72)
    print("Computing F-scores and critical values between consecutive available orders")
    print("=" * 72)

    for region in regions:
        entries = sorted(chi2_results[region], key=lambda x: x[0])
        print(f"\n[{region}]")
        if len(entries) < 2:
            print("  Not enough points to compute F-scores")
            continue

        for i in range(len(entries) - 1):
            order_n, chi2_red_n, p_n, n_bins_n = entries[i]
            order_np1, chi2_red_np1, p_np1, n_bins_np1 = entries[i + 1]
            
            if order_np1 != order_n + 1:
                print(f"  skipping pair ({order_n}, {order_np1}) - not consecutive")
                continue

            # Ensure we use the dynamic bin count retrieved from the dataset
            fscore = compute_fscore(chi2_red_n, chi2_red_np1, p_n, p_np1, n_bins_np1)
            fcrit = compute_f_critical(p_n, p_np1, n_bins_np1, alpha=args.alpha)
            
            if fscore is None or fcrit is None:
                print(f"  F_{order_n}: invalid (chi2/p/n_bins combination)")
                continue

            fscore_results[region].append((order_n, fscore, fcrit))
            status = "ACCEPT n+1" if fscore >= fcrit else "KEEP n"
            print(f"  F_{order_n}->{order_np1} (p_n={p_n}, p_np1={p_np1}): score={fscore:.4f}, fcrit={fcrit:.4f} [{status}]")

    # Plot F-scores, critical threshold, and reduced chi2
    fig, axes = plt.subplots(1, 3, figsize=(21, 8), sharey=False)
    for idx, region in enumerate(regions):
        ax = axes[idx]
        ax2 = None
        points = sorted(fscore_results[region], key=lambda x: x[0])
        
        all_orders = sorted(chi2_results[region], key=lambda x: x[0])
        xvals_chi2 = [p[0] for p in all_orders]
        chi2_vals = [p[1] for p in all_orders]

        if points:
            xvals = [p[0] for p in points]
            f_vals = [p[1] for p in points]
            fcrit_vals = [p[2] for p in points]

            # Primary Axis (F-score)
            line_fcrit = ax.plot(xvals, fcrit_vals, marker="s", linestyle="--", color="#e42536", linewidth=1.5, label=f"$F_{{crit}}$ ($\\sim{fcrit_vals[0]:.2f}$)")
            line_f = ax.plot(xvals, f_vals, marker="o", linestyle="-", color="#3f90da", linewidth=2.0, label="$F$-score")

        else:
            ax.text(0.5, 0.5, "No valid F-scores", transform=ax.transAxes, ha="center", va="center")

        # Secondary Axis (Reduced Chi2) - Plot across full range of 'n'
        if all_orders:
            ax2 = ax.twinx()
            line_chi2 = ax2.plot(xvals_chi2, chi2_vals, marker="^", linestyle=":", color="#832db6", linewidth=2.0, label=r"$\chi^2/\text{ndof}$")
            
            ax2.axhline(1.0, linestyle="-.", linewidth=1.0, color="gray", alpha=0.6)
            ax2.set_ylabel(r"$\chi^2/\text{ndof}$")
            ax2.set_ylim(bottom=max(0.5, min(chi2_vals) - 0.2), top=max(chi2_vals) + 0.3)

        ax.set_title("Region " + region[-1], pad=40)
        ax.set_xlabel("n (order pair $n \\rightarrow n+1$)")
        ax.set_xticks(xvals_chi2 if all_orders else orders[:-1])
        ax.axhline(0.0, linestyle="--", linewidth=1.0, color="black", alpha=0.6)
        ax.grid(True, alpha=0.4)
        
        # Combine legends from both axes
        handles, labels = ax.get_legend_handles_labels()
        if ax2:
            handles2, labels2 = ax2.get_legend_handles_labels()
            handles.extend(handles2)
            labels.extend(labels2)
            
        if handles:
            ax.legend(handles, labels, loc="upper right", fontsize=12)

    axes[0].set_ylabel("F-score")
    fig.suptitle(f"F-test evaluation by region, {args.family} background (era={args.era})")
    fig.tight_layout()

    output_name = args.output_name if args.output_name else f"ftest_{args.family}_{args.era}.png"
    output_path = output_folder / output_name
    fig.savefig(output_path, dpi=150)
    print("\nSaved plot:", output_path)

    # Plot overlays of all orders (data + all fit functions) per region with pull panels.
    fig_overlay = plt.figure(figsize=(35, 13))
    grid = fig_overlay.add_gridspec(2, 3, height_ratios=[3.3, 1.3], hspace=0.03, wspace=0.2)
    axes_overlay_top = [fig_overlay.add_subplot(grid[0, i]) for i in range(3)]
    axes_overlay_pull = [fig_overlay.add_subplot(grid[1, i], sharex=axes_overlay_top[i]) for i in range(3)]
    
    # Map ndof values by order for straightforward extraction in the plot labels
    ndof_maps = {region: {entry[0]: entry[3] - entry[2] for entry in chi2_results[region]} for region in regions}

    for idx, region in enumerate(regions):
        ax = axes_overlay_top[idx]
        ax_pull = axes_overlay_pull[idx]
        ndof_map = ndof_maps[region]

        data_points = overlay_data[region]
        if data_points and args.unblinded:
            x_data = [p[0] for p in data_points]
            y_data = [p[1] for p in data_points]
            ey_low = [p[4] for p in data_points]
            ey_high = [p[5] for p in data_points]
            ax.errorbar(
                x_data,
                y_data,
                yerr=[ey_low, ey_high],
                fmt="o",
                markersize=2,
                linewidth=1.0,
                color="black",
                label="data",
            )

        curves = sorted(overlay_curves[region], key=lambda x: x[0])
        for i_curve, (order, pdf_points, chi2) in enumerate(curves):
            x_curve = [p[0] for p in pdf_points]
            y_curve = [p[1] for p in pdf_points]
            curve_color = cms_color_palette[i_curve % len(cms_color_palette)]
            ndof_val = ndof_map.get(order, "N/A")
            ax.plot(
                x_curve,
                y_curve,
                linewidth=3,
                label=f"n={order}, $\\chi^2/n$={chi2:.2f}",# (npar={450 - ndof_val})",
                zorder=999,
                alpha=0.8,
                color=curve_color,
            )

            if data_points:
                x_data = [p[0] for p in data_points]
                y_data = [p[1] for p in data_points]
                ey_low = [p[4] for p in data_points]
                ey_high = [p[5] for p in data_points]
                y_model_at_data = interpolate_curve_at_x(pdf_points, x_data)
                pull_vals = []
                for y_obs, y_mod, err_low, err_high in zip(y_data, y_model_at_data, ey_low, ey_high):
                    den = err_high if y_obs >= y_mod else err_low
                    if den <= 0:
                        pull_vals.append(np.nan)
                    else:
                        pull_vals.append((y_obs - y_mod) / den)
                ax_pull.errorbar(
                    x_data,
                    pull_vals,
                    yerr=np.ones(len(pull_vals)),
                    fmt="o",
                    markersize=2,
                    linestyle="None",
                    elinewidth=1.0,
                    capsize=2,
                    alpha=0.85,
                    color=curve_color,
                )

        if not data_points and not curves:
            ax.text(0.5, 0.5, "No valid data/functions", transform=ax.transAxes, ha="center", va="center")

        ax.set_title("Region" + region[-1], pad=40)
        ax.set_xlabel("")
        ax.grid(True, alpha=0.4)
        ax.legend(loc="best")
        ax.set_yscale("log")
        hep.cms.label(loc=0, data=True, label="Preliminary", lumi=lumi[args.era], com=13.6, year=str(args.era), ax=ax)

        positive_data_low = []
        positive_data_high = []
        if data_points:
            for _, y, _, _, eyl, eyh in data_points:
                low = y - eyl
                high = y + eyh
                if low > 0:
                    positive_data_low.append(low)
                if high > 0:
                    positive_data_high.append(high)

        if positive_data_low and positive_data_high:
            y_min_ref = min(positive_data_low)
            y_max_ref = max(positive_data_high)
        else:
            positive_curve_vals = [y for _, pts, _ in curves for _, y in pts if y > 0]
            if positive_curve_vals:
                y_min_ref = min(positive_curve_vals)
                y_max_ref = max(positive_curve_vals)
            else:
                y_min_ref = None
                y_max_ref = None

        if y_min_ref is not None and y_max_ref is not None and y_max_ref > y_min_ref:
            log_min = ROOT.TMath.Log10(y_min_ref)
            log_max = ROOT.TMath.Log10(y_max_ref)
            ymin = 10 ** (log_min - 0.2)
            ymax = 10 ** (log_max + 0.3)
            if ymin > 0 and ymax > ymin:
                ax.set_ylim(ymin, ymax)

        ax_pull.axhline(0.0, linestyle="-", linewidth=1.0, color="black", alpha=0.7)
        ax_pull.axhline(3.0, linestyle="--", linewidth=0.8, color="gray", alpha=0.7)
        ax_pull.axhline(-3.0, linestyle="--", linewidth=0.8, color="gray", alpha=0.7)
        ax_pull.set_ylabel("Pulls")
        ax_pull.set_xlabel("m(ee) [GeV]")
        ax_pull.set_ylim(-6, 6)
        ax_pull.grid(True, alpha=0.3)
        plt.setp(ax.get_xticklabels(), visible=False)

    axes_overlay_top[0].set_ylabel("Events / bin")
    fig_overlay.suptitle(f"{args.family.capitalize()} fit functions (era = {args.era})")
    fig_overlay.tight_layout()

    overlay_name = args.overlay_output_name if args.overlay_output_name else f"fits_overlay_{args.family}_{args.era}.png"
    overlay_path = output_folder / overlay_name
    fig_overlay.savefig(overlay_path, dpi=150)
    
    pdf_overlay_path = overlay_path.with_suffix(".pdf")
    fig_overlay.savefig(pdf_overlay_path)
    print("Saved overlay plot:", overlay_path)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())