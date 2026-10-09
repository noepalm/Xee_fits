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
    
BKG_FUNCTION_LABELS = ["Chebyshev", "Bernstein"]

REGION_BOUNDS = {
    "region0": (0.5, 2.2),
    # "region1": (1.8, 5.3),
    # "region1": (1.8, 7.0),
    "region1": (2.2, 7.0),
    # "region2": (4.5, 10.5),
    "region2": (6.0, 11.0),
}

def mass_in_selected_regions(mass, regions):
    for region in regions:
        low, high = REGION_BOUNDS[region]
        if low <= mass <= high:
            return True
    return False

def read_toy_r_triplet(root_path):
    """Return per-toy (r, r_up, r_down) arrays with shared filtering logic.
    Supports either tree_fit_sb (from fitDiagnostics*.root) or limit (from higgsCombine*.root).
    """
    with uproot.open(root_path) as f:
        if "tree_fit_sb" in f:
            t = f["tree_fit_sb"]
            arr = t.arrays(["r", "rLoErr", "rHiErr"], library="np")
            vals = np.array(arr["r"], dtype=float)
            err_up = np.array(arr["rHiErr"], dtype=float)
            err_down = np.array(arr["rLoErr"], dtype=float)
            r_up = vals + err_up
            r_down = vals - err_down
        elif "limit" in f:
            arr = f["limit"].arrays()
            if "quantileExpected" not in arr.fields or "limit" not in arr.fields:
                return None

            q = np.array(arr["quantileExpected"], dtype=float)
            lim = np.array(arr["limit"], dtype=float)

            central_mask = np.abs(q - 0.5) < 0.01
            up_mask = np.abs(q - 0.83999) < 0.01
            down_mask = np.abs(q - 0.15999) < 0.01

            vals = lim[central_mask]
            r_up = lim[up_mask]
            r_down = lim[down_mask]
        else:
            return None

        if vals.size == 0 or r_up.size == 0 or r_down.size == 0:
            return None

        n_common = min(vals.size, r_up.size, r_down.size)
        vals = vals[:n_common]
        r_up = r_up[:n_common]
        r_down = r_down[:n_common]

        failed_up_mask = np.abs(r_up) < 1e-15
        vals = vals[~failed_up_mask]
        r_down = r_down[~failed_up_mask]
        r_up = r_up[~failed_up_mask]

        # rmax can be +-5, +-10, +-15, +-20, +-25, +-30, +-50 or +-400 depending on mass
        BOUNDARY_THRESHOLDS = np.array([5, 10, 15, 20, 25, 30, 50, 400])

        failed_boundary_up_mask = (np.abs(r_up[..., np.newaxis] - BOUNDARY_THRESHOLDS) < 1e-3).any(axis=-1)
        failed_boundary_down_mask = (np.abs(r_down[..., np.newaxis] + BOUNDARY_THRESHOLDS) < 1e-3).any(axis=-1)
        # Also filter toys where fit uncertainty collapsed onto boundary (e.g. err_up or err_down < 1e-3)
        failed_zero_err_mask = (np.abs(r_up - vals) < 1e-3) | (np.abs(vals - r_down) < 1e-3)

        failed_boundary_mask = failed_boundary_up_mask | failed_boundary_down_mask | failed_zero_err_mask
        if np.any(failed_boundary_mask):
            print(f"Warning: found {np.sum(failed_boundary_mask)} toys with r_up/r_down at boundary, skipping these")
        vals = vals[~failed_boundary_mask]
        r_up = r_up[~failed_boundary_mask]
        r_down = r_down[~failed_boundary_mask]

        failed_r_mask = r_up < vals
        if np.any(failed_r_mask):
            print(f"Warning: found {np.sum(failed_r_mask)} toys with r_up < r, skipping these.")
            vals = vals[~failed_r_mask]
            r_down = r_down[~failed_r_mask]
            r_up = r_up[~failed_r_mask]

        failed_r_mask_down = r_down > vals
        if np.any(failed_r_mask_down):
            print(f"Warning: found {np.sum(failed_r_mask_down)} toys with r_down > r, skipping these")
            vals = vals[~failed_r_mask_down]
            r_down = r_down[~failed_r_mask_down]
            r_up = r_up[~failed_r_mask_down]

        if vals.size == 0:
            return None

        return vals, r_up, r_down

def read_limit_mean_std(root_path, nominal_r):
    """Calculates per-toy pulls and returns the array statistics."""
    selected = read_toy_r_triplet(root_path)
    if selected is None:
        return None

    vals, r_up, r_down = selected
    
    err_up = r_up - vals
    err_down = vals - r_down

    if np.mean(err_down) < 0.5 and np.mean(err_up) > 3:
        print("DEBUG: err_up = ", err_up, "; err_down = ", err_down)
        print("DEBUG: err_up mean = ", np.mean(err_up), "; err_down mean = ", np.mean(err_down))
    
    # Calculate per-toy pull with asymmetric errors:
    # When vals > nominal_r, the true value lies BELOW the fit, so the relevant uncertainty
    # covering the truth is the lower error (err_down / rLoErr).
    # When vals <= nominal_r, the true value lies ABOVE the fit, so the relevant uncertainty
    # covering the truth is the upper error (err_up / rHiErr).
    # This ensures that |pull| <= 1 corresponds exactly to [r - err_down, r + err_up] covering nominal_r.
    sigma_i = np.where(vals > nominal_r, err_down, err_up)
    pulls = np.divide(vals - nominal_r, sigma_i, out=np.full_like(vals, np.nan, dtype=float), where=sigma_i != 0)
    pulls = pulls[np.isfinite(pulls)]

    return (
        float(np.mean(vals)),       # 0
        float(np.mean(err_up)),     # 1 
        float(np.mean(err_down)),   # 2
        float(np.std(vals)),        # 3
        float(np.mean(pulls)),      # 4: Exact Mean of Pulls
        float(np.std(pulls))        # 5: Exact Std Dev of Pulls
    )

def read_toy_distributions(root_path, nominal_r):
    """Read per-toy r values and per-toy pull values."""
    selected = read_toy_r_triplet(root_path)
    if selected is None:
        return np.array([], dtype=float), np.array([], dtype=float)
        
    vals, r_up, r_down = selected
    
    err_up = r_up - vals
    err_down = vals - r_down
    sigma_i = np.where(vals > nominal_r, err_down, err_up)
    pulls = np.divide(vals - nominal_r, sigma_i, out=np.full_like(vals, np.nan, dtype=float), where=sigma_i != 0)
    
    valid = np.isfinite(pulls)
    return vals[valid], pulls[valid]

def pick_sparse_masses(masses, fraction=0.1):
    if not masses:
        return []
    masses = sorted(masses)
    n = len(masses)
    n_pick = max(1, int(round(n * fraction)))
    if n_pick >= n:
        return masses
    idxs = np.linspace(0, n - 1, n_pick).round().astype(int)
    idxs = sorted(set(int(i) for i in idxs))
    
    # TEMPORARY: for excess debugging, always add these masses 
    for extra_mass in [1.8, 1.9, 2.0, 2.1, 8.7, 8.8, 8.9, 9.0, 9.1, 9.2]:
        if extra_mass in masses and extra_mass not in [masses[i] for i in idxs]:
            idxs.append(masses.index(extra_mass))
    idxs = sorted(set(idxs))
    
    print("DEBUG: pick_sparse_masses selected masses: ", [masses[i] for i in idxs])
    return [masses[i] for i in idxs]

def get_fixed_r_range(nominal_r):
    """Return fixed (r_min, r_max) based on injected signal:
    - -5/+5 for mu=0 (shifted accordingly for mu=0.1 to -4.9/+5.1)
    - -4/+6 for mu=1
    - -5/+20 for mu=10
    """
    if np.isclose(nominal_r, 10.0, atol=1e-3):
        return -5.0, 20.0
    elif nominal_r >= 5.0:
        return nominal_r - 15.0, nominal_r + 10.0
    else:
        return nominal_r - 5.0, nominal_r + 5.0

def make_summary_grid_plot(output_dir, era, truth_results, regions, extra_tag, nominal_r, name_suffix=""):
    region_tag = "_".join(regions)
    fig, axes = plt.subplots(2, len(BKG_FUNCTION_LABELS), figsize=(25, 13), sharex=False)
    plotted_any = False
    all_r_vals = []

    def decorate_region_spans(ax):
        if len(regions) <= 1:
            return
        for i, region in enumerate(regions):
            low, high = REGION_BOUNDS[region]
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
            err_up = np.array([mass_map[m][1] for m in selected_masses], dtype=float)
            err_down = np.array([mass_map[m][2] for m in selected_masses], dtype=float)
            
            # Using the exact pull stats computed in read_limit_mean_std
            mean_pulls = np.array([mass_map[m][4] for m in selected_masses], dtype=float)
            std_pulls = np.array([mass_map[m][5] for m in selected_masses], dtype=float)
    
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
                mean_pulls,
                yerr=std_pulls,
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
    # Updated y-label to reflect exact formulation
    axes[1, 0].set_ylabel(r"$\langle (r_{fit} - r_{injected}) / \sigma_i \rangle$")

    if all_r_vals:
        r_min_grid, r_max_grid = get_fixed_r_range(nominal_r)
        for col_idx in range(len(BKG_FUNCTION_LABELS)):
            axes[0, col_idx].set_ylim(r_min_grid, r_max_grid)
    for col_idx in range(len(BKG_FUNCTION_LABELS)):
        axes[1, col_idx].set_ylim(-3, 3)

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

    # Fixed r range per injected signal:
    # -5/+5 for mu=0 (shifted accordingly for mu=0.1 to -4.9/+5.1)
    # -4/+6 for mu=1
    # -5/+20 for mu=10
    r_min, r_max = get_fixed_r_range(nominal_r)

    # r binning: 35 bins
    n_r_bins = 35
    r_bins = np.linspace(r_min, r_max, n_r_bins + 1)

    # pull binning: range [-5, 5] with an odd number of bins (35 bins) so that a bin straddles 0
    n_pull_bins = 35
    pull_bins = np.linspace(-5.0, 5.0, n_pull_bins + 1)

    print(
        f"Making r-distribution plots for {len(selected_masses)}/{len(all_masses)} sampled masses in {out_dir} "
        f"(fixed r range: [{r_min:g}, {r_max:g}], pull range: [-5, 5] with {n_pull_bins} bins)"
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
            ax_r.axvline(nominal_r, color="gray", linestyle="--", alpha=0.6, label="Injected r")
            ax_pull.axvline(0.0, color="gray", linestyle="--", alpha=0.6)
            ax_pull.axvline(1.0, color="gray", linestyle=":", alpha=0.35)
            ax_pull.axvline(-1.0, color="gray", linestyle=":", alpha=0.35)

            for fit_label, color in zip(BKG_FUNCTION_LABELS, cms_palette[:len(BKG_FUNCTION_LABELS)]):
                file_map = truth_files[truth_label][fit_label]
                fpath = file_map.get(mass)
                if fpath is None:
                    continue

                stats = truth_results[truth_label][fit_label].get(mass)
                if stats is None:
                    continue

                # Unpack the per-toy arrays directly
                r_vals, pull_vals = read_toy_distributions(fpath, nominal_r)
                if r_vals.size == 0:
                    continue

                ax_r.hist(
                    r_vals,
                    bins=r_bins,
                    histtype="step",
                    linewidth=1.8,
                    color=color,
                    label=f"Fit {fit_label} (entries = {len(r_vals)})",
                )
                ax_pull.hist(
                    pull_vals,
                    bins=pull_bins,
                    histtype="step",
                    linewidth=1.8,
                    color=color,
                    label=f"Fit {fit_label}",
                )
                plotted_any = True

            ax_r.set_xlim(r_min, r_max)
            ax_pull.set_xlim(-5, 5)
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
                    pattern_fitdiag = (
                        f"fitDiagnostics.bias_truth{truth_label}_fit{fit_label}_{args.category}_{args.era}*.root"
                    )
                    matches = sorted(mass_dir.glob(pattern_fitdiag), key=lambda p: p.stat().st_mtime, reverse=True)
                if not matches:
                    print(f"Warning: File not found for pattern: {mass_dir / pattern}, skipping")
                    continue
                fpath = matches[0]
                
                # Pass nominal_r to the stats extraction
                stats = read_limit_mean_std(fpath, args.nominal_r)
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