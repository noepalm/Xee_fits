import argparse
from pathlib import Path
import matplotlib.pyplot as plt
import mplhep as hep
import numpy as np
import uproot

hep.style.use("CMS")
cms_palette = [
    "#5790fc",
    "#f89c20",
    "#e42536",
    "#964a8b",
    "#9c9ca1",
    "#7a21dd",
]

BKG_FUNCTION_LABELS = ["Chebyshev", "Bernstein", "PolyExp"]
REGION_BOUNDS = {
    "region0": (0.5, 2.2),
    "region1": (1.8, 4.4),
    "region2": (4.0, 10.8),
}

def mass_in_selected_regions(mass, regions):
    for region in regions:
        low, high = REGION_BOUNDS[region]
        if low <= mass <= high:
            return True
    return False


def read_toy_r_triplet(root_path):
    """Return per-toy (r, r_up, r_down) arrays with shared filtering logic.

    For FitDiagnostics output, reads from 'limit' field:
    - Central values: quantileExpected == 0.5
    - Up (68% CI): quantileExpected == 0.15999
    - Down (68% CI): quantileExpected == 0.83999
    
    This applies the same filtering logic used for bias summary computations.
    Handles negative r values correctly.
    """
    with uproot.open(root_path) as f:
        if "limit" not in f:
            return None
        arr = f["limit"].arrays()
        if "quantileExpected" not in arr.fields or "limit" not in arr.fields:
            return None

        q = np.array(arr["quantileExpected"], dtype=float)
        lim = np.array(arr["limit"], dtype=float)

        # Select quantiles for central, up, and down values
        central_mask = np.abs(q - 0.5) < 0.01
        up_mask = np.abs(q - 0.83999) < 0.01
        down_mask = np.abs(q - 0.15999) < 0.01

        vals = lim[central_mask]
        r_up = lim[up_mask]
        r_down = lim[down_mask]

        if vals.size == 0 or r_up.size == 0 or r_down.size == 0:
            return None

        # Defensively align arrays in case combine output order/size differs.
        n_common = min(vals.size, r_up.size, r_down.size)
        vals = vals[:n_common]
        r_up = r_up[:n_common]
        r_down = r_down[:n_common]

        # scrap toys in which r_up is essentially zero (fit failed)
        failed_up_mask = np.abs(r_up) < 1e-15
        vals = vals[~failed_up_mask]
        r_down = r_down[~failed_up_mask]
        r_up = r_up[~failed_up_mask]

        # Sanity checks: r_up should be >= r and r_down should be <= r (works for negative values)
        failed_r_mask = r_up < vals
        if np.any(failed_r_mask):
            print(f"Warning: found {np.sum(failed_r_mask)} toys with r_up < r, skipping these")
            print("  r values for failed toys:", vals[failed_r_mask])
            print("  r_up values for failed toys:", r_up[failed_r_mask])
            print("  r_down values for failed toys:", r_down[failed_r_mask])
            vals = vals[~failed_r_mask]
            r_down = r_down[~failed_r_mask]
            r_up = r_up[~failed_r_mask]

        failed_r_mask_down = r_down > vals
        if np.any(failed_r_mask_down):
            print(f"Warning: found {np.sum(failed_r_mask_down)} toys with r_down > r, skipping these")
            print("  r values for failed toys:", vals[failed_r_mask_down])
            print("  r_up values for failed toys:", r_up[failed_r_mask_down])
            print("  r_down values for failed toys:", r_down[failed_r_mask_down])
            vals = vals[~failed_r_mask_down]
            r_down = r_down[~failed_r_mask_down]
            r_up = r_up[~failed_r_mask_down]

        if vals.size == 0:
            return None

        return vals, r_up, r_down


def read_limit_mean_std(root_path):
    selected = read_toy_r_triplet(root_path)
    if selected is None:
        return None

    vals, r_up, r_down = selected

    return float(np.mean(vals)), np.mean((r_up - r_down) / 2), np.mean(r_up - vals), np.mean(vals - r_down)


def read_r_values(root_path):
    """Read per-toy r values using the same toy-selection logic as summary stats."""
    selected = read_toy_r_triplet(root_path)
    if selected is None:
        return np.array([], dtype=float)
    vals, _, _ = selected
    return vals


def pick_sparse_masses(masses, fraction=0.1):
    """Pick approximately fraction of masses, evenly spaced, at least one point."""
    if not masses:
        return []
    masses = sorted(masses)
    n = len(masses)
    n_pick = max(1, int(round(n * fraction)))
    if n_pick >= n:
        return masses
    idxs = np.linspace(0, n - 1, n_pick).round().astype(int)
    idxs = sorted(set(int(i) for i in idxs))
    return [masses[i] for i in idxs]


def make_summary_grid_plot(output_dir, era, truth_results, regions, extra_tag, nominal_r, name_suffix=""):
    """Render one 2x3 summary grid.

    Columns are truth background functions.
    Top row shows r with std error bars.
    Bottom row shows pulls with unit error bars.
    """
    region_tag = "_".join(regions)
    fig, axes = plt.subplots(2, len(BKG_FUNCTION_LABELS), figsize=(25, 13), sharex=False)
    plotted_any = False
    all_r_vals = []

    def decorate_region_spans(ax):
        if len(regions) <= 1:
            return
        for i, region in enumerate(regions):
            low, high = REGION_BOUNDS[region]
            # ax.axvspan(low, high, color=f"C{i+3}", alpha=0.03)
            ax.axvline(low, color=f"C{i+3}", alpha=0.3, linestyle="--")
            ax.axvline(high, color=f"C{i+3}", alpha=0.3, linestyle="--")

    for col_idx, truth_label in enumerate(BKG_FUNCTION_LABELS):
        ax_r = axes[0, col_idx]
        ax_pull = axes[1, col_idx]
        fit_results = truth_results[truth_label]

        decorate_region_spans(ax_r)
        decorate_region_spans(ax_pull)

        for fit_label, color in zip(BKG_FUNCTION_LABELS, cms_palette[:len(BKG_FUNCTION_LABELS)]):
            mass_map = fit_results[fit_label]
            selected_masses = sorted([m for m in mass_map if mass_in_selected_regions(m, regions)])
            if not selected_masses:
                continue

            means = np.array([mass_map[m][0] for m in selected_masses], dtype=float)
            stds = np.array([mass_map[m][1] for m in selected_masses], dtype=float)
            err_up = np.array([mass_map[m][2] for m in selected_masses], dtype=float)
            err_down = np.array([mass_map[m][3] for m in selected_masses], dtype=float)

            # compute real std based on whether means - nominal is > 0 (use err_down) or < 0 (use err_up)
            errors = np.where(means - nominal_r > 0, err_down, err_up)
            pulls = np.divide(means - nominal_r, errors, out=np.full_like(means, np.nan, dtype=float), where=errors != 0)
    
            ax_r.errorbar(
                selected_masses,
                means,
                yerr = [err_down, err_up],
                fmt="o",
                color=color,
                alpha=0.8,
                label=f"Fit {fit_label}",
            )
            ax_pull.errorbar(
                selected_masses,
                pulls,
                yerr=np.ones_like(pulls),
                fmt="o",
                color=color,
                alpha=0.8,
                label=f"Fit {fit_label}",
            )

            all_r_vals.extend(list(means[np.isfinite(means)]))
            plotted_any = True

        ax_r.set_title(f"Truth {truth_label}")
        ax_r.grid(alpha=0.3)
        ax_pull.grid(alpha=0.3)
        ax_pull.set_xlabel("Mass [GeV]")

        if len(regions) == 1:
            low, high = REGION_BOUNDS[regions[0]]
            ax_r.set_xlim(low, high)
            ax_pull.set_xlim(low, high)

    if not plotted_any:
        plt.close(fig)
        return False

    axes[0, 0].set_ylabel(r"$r_{fit}$")
    axes[1, 0].set_ylabel(r"$(r_{fit} - r_{injected})/(0.5 * (\sigma(r)_{up} + \sigma(r)_{down}))$")

    if all_r_vals:
        for col_idx in range(len(BKG_FUNCTION_LABELS)):
            axes[0, col_idx].set_ylim(-5, 5)
    for col_idx in range(len(BKG_FUNCTION_LABELS)):
        axes[1, col_idx].set_ylim(-3, 3)

    # hep.cms.label("Preliminary", ax=axes[0, 0], com=13.6, data=True, year=era)

    handles, labels = axes[0, 0].get_legend_handles_labels()
    if handles:
        fig.legend(handles, labels, loc="upper center", ncol=3, frameon=False, bbox_to_anchor=(0.5, 0.98))

    fig.suptitle(f"Bias test summary ({region_tag}, {era})", y=0.995)
    fig.tight_layout(rect=[0.02, 0.03, 1.0, 0.94])

    out_base = output_dir / f"bias_test_{region_tag}{name_suffix}{extra_tag}"
    plt.savefig(f"{out_base}.png")
    plt.savefig(f"{out_base}.pdf")
    plt.close(fig)
    print(f"Saved plots: {out_base}.png/.pdf")
    return True


def make_r_distribution_plots(output_dir, era, category, regions, truth_files, truth_results, extra_tag, nominal_r):
    """Make sampled per-mass histogram plots of fitted r values.

        For each selected mass: 2x3 subplots (columns=truth model).
        Top row overlays fitted-r histograms for three fit hypotheses.
        Bottom row overlays pull histograms for three fit hypotheses.
        Pulls use asymmetric uncertainty selected from mean vs nominal_r:
            - mean > nominal_r -> use err_down
            - mean <= nominal_r -> use err_up
    """
    all_masses = set()
    for truth_label in BKG_FUNCTION_LABELS:
        for fit_label in BKG_FUNCTION_LABELS:
            all_masses.update(truth_files[truth_label][fit_label].keys())

    selected_masses = pick_sparse_masses([m for m in all_masses if mass_in_selected_regions(m, regions)], fraction=0.2)
    if not selected_masses:
        print("No masses available for r-distribution plots")
        return

    out_dir = output_dir / "fit_r_distribution"
    out_dir.mkdir(parents=True, exist_ok=True)
    region_tag = "_".join(regions)

    print(
        f"Making r-distribution plots for {len(selected_masses)}/{len(all_masses)} sampled masses in {out_dir}"
    )

    for mass in selected_masses:
        fig, axes = plt.subplots(2, len(BKG_FUNCTION_LABELS), figsize=(21, 10), sharex=False)
        plotted_any = False

        for col_idx, truth_label in enumerate(BKG_FUNCTION_LABELS):
            ax_r = axes[0, col_idx]
            ax_pull = axes[1, col_idx]
            ax_r.set_title(f"Truth {truth_label}")
            ax_r.grid(alpha=0.25)
            ax_pull.grid(alpha=0.25)

            for fit_label, color in zip(BKG_FUNCTION_LABELS, cms_palette[:len(BKG_FUNCTION_LABELS)]):
                file_map = truth_files[truth_label][fit_label]
                fpath = file_map.get(mass)
                if fpath is None:
                    continue

                stats = truth_results[truth_label][fit_label].get(mass)
                if stats is None:
                    continue

                mean_r = float(stats[0])
                err_up = float(stats[2])
                err_down = float(stats[3])
                pull_err = err_down if mean_r > nominal_r else err_up
                if abs(pull_err) < 1e-15:
                    continue

                r_vals = read_r_values(fpath)
                r_vals = r_vals[np.isfinite(r_vals)]
                if r_vals.size == 0:
                    continue

                pull_vals = (r_vals - nominal_r) / pull_err

                ax_r.hist(
                    r_vals,
                    bins=30,
                    histtype="step",
                    linewidth=1.8,
                    color=color,
                    label=f"Fit {fit_label}",
                    range=(-5, 5),
                )
                ax_pull.hist(
                    pull_vals,
                    bins=30,
                    histtype="step",
                    linewidth=1.8,
                    color=color,
                    label=f"Fit {fit_label}",
                    range=(-5, 5),
                )
                plotted_any = True

            ax_r.set_xlabel(r"$r_{fit}$")
            ax_pull.set_xlabel(r"Pull")
            if col_idx == 0:
                ax_r.set_ylabel("Entries")
                ax_pull.set_ylabel("Entries")

        if not plotted_any:
            plt.close(fig)
            continue

        handles, labels = axes[0, 0].get_legend_handles_labels()
        if handles:
            fig.legend(handles, labels, loc="upper center", ncol=3, frameon=False, bbox_to_anchor=(0.5, 1.02))

        fig.suptitle(f"r distributions ({region_tag}, {era}, {category}, M{mass:g})", y=1.06)
        fig.tight_layout()

        out_base = out_dir / f"fit_r_distribution_{region_tag}_M{mass:g}{extra_tag}"
        plt.savefig(f"{out_base}.png")
        plt.savefig(f"{out_base}.pdf")
        plt.close(fig)
        print(f"Saved r-distribution: {out_base}.png/.pdf")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--output_folder", type=str, required=True, help="Output folder for plots")
    parser.add_argument("-i", "--input", type=str, required=True, help="Input folder with M*/ outputs")
    parser.add_argument("-c", "--category", type=str, required=True, help="Category name (e.g. inclusive)")
    parser.add_argument("-t", "--tag", type=str, default="", help="Optional extra tag in output filename")
    parser.add_argument("--nominal_r", type=float, default=0.0, help="Nominal r value used in toys (for pull calculation)")
    parser.add_argument(
        "-r",
        "--regions",
        nargs="+",
        default=["region1"],
        choices=["region0", "region1", "region2"],
        help="Regions to include; when multiple are passed, they are stitched in one plot",
    )
    parser.add_argument("--era", type=str, default="2023", help="Era (e.g. 2023)")
    args = parser.parse_args()

    hep.style.use("CMS")

    input_dir = Path(args.input)
    output_dir = Path(args.output_folder)
    output_dir.mkdir(parents=True, exist_ok=True)

    truth_results = {truth: {fit: {} for fit in BKG_FUNCTION_LABELS} for truth in BKG_FUNCTION_LABELS}
    truth_files = {truth: {fit: {} for fit in BKG_FUNCTION_LABELS} for truth in BKG_FUNCTION_LABELS}

    mass_dirs = [d for d in input_dir.iterdir() if d.is_dir() and d.name.startswith("M")]
    mass_dirs = sorted(mass_dirs, key=lambda d: float(d.name[1:]))

    for mass_dir in mass_dirs:
        try:
            mass = float(mass_dir.name[1:])
        except ValueError:
            continue

        if not mass_in_selected_regions(mass, args.regions):
            continue
        
        print(f"Processing mass {mass}")

        for truth_label in BKG_FUNCTION_LABELS:
            for fit_label in BKG_FUNCTION_LABELS:
                pattern = (
                    f"higgsCombine.bias_truth{truth_label}_fit{fit_label}_{args.category}_{args.era}"
                    "*.FitDiagnostics.mH120.123456.root"
                )
                matches = sorted(mass_dir.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
                if not matches:
                    print(f"Warning: File not found for pattern: {mass_dir / pattern}, skipping")
                    continue
                fpath = matches[0]
                stats = read_limit_mean_std(fpath)
                if stats is None:
                    print(f"Warning: No valid stats for mass {mass}, truth {truth_label}, fit {fit_label}, skipping")
                    continue
                truth_results[truth_label][fit_label][mass] = stats
                truth_files[truth_label][fit_label][mass] = fpath

    extra_tag = f"_{args.tag}" if args.tag else ""

    ok = make_summary_grid_plot(
        output_dir=output_dir,
        era=args.era,
        truth_results=truth_results,
        regions=args.regions,
        extra_tag=extra_tag,
        nominal_r=args.nominal_r,
    )
    if not ok:
        print("No points found for selected regions, skipping plot")

    # # Also make one zoomed summary per region with the same 2x3 layout logic.
    # if len(args.regions) > 1:
    #     for region in args.regions:
    #         zoom_ok = make_summary_grid_plot(
    #             output_dir=output_dir,
    #             era=args.era,
    #             truth_results=truth_results,
    #             regions=[region],
    #             extra_tag=extra_tag,
    #             nominal_r=args.nominal_r,
    #             name_suffix="_zoom",
    #         )
    #         if not zoom_ok:
    #             print(f"No points found for {region}, skipping zoom plot")

    make_r_distribution_plots(
        output_dir=output_dir,
        era=args.era,
        category=args.category,
        regions=args.regions,
        truth_files=truth_files,
        truth_results=truth_results,
        extra_tag=extra_tag,
        nominal_r=args.nominal_r,
    )


if __name__ == "__main__":
    main()