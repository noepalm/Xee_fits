#!/usr/bin/env python3
"""
plot_pt_vs_mass.py

Iterate over all signal samples used for the signal model / background modelling
(by default tag 260727 for background tag 260828), and plot:
  - Average dielectron pT
  - Average dielectron leading electron pT
  - Average dielectron subleading electron pT
vs signal mass.

Key features:
  - For each mass, a different color is assigned from a high-contrast palette.
  - At each mass, the three points are vertically aligned:
      pT(dielectron) >= pT(leading) >= pT(subleading).
  - Appropriate uncertainty bars describe the uncertainty on the MEAN value
    of the pT distributions (which are non-Gaussian: turn-on + exponential tail),
    computed via non-parametric weighted bootstrap (68.3% CI) as well as analytical SEM.
  - CMS plotting style (mplhep CMS style, CMS Simulation Preliminary label).
  - Saves both .png and .pdf to the PS_reweighting signal model subfolder.
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import mplhep as hep
import ROOT

# High-contrast categorical color palette for mass points
MASS_PALETTE = [
    "#5790fc",  # blue
    "#f89c20",  # amber/orange
    "#e42536",  # red
    "#964a8b",  # purple
    "#00a88f",  # teal
    "#7a21dd",  # deep purple
    "#e377c2",  # pink
    "#8c564b",  # brown
    "#17becf",  # cyan
    "#bcbd22",  # yellow-green
    "#ff7f0e",  # dark orange
    "#2ca02c",  # green
    "#393b79",  # navy
    "#637939",  # olive
]

# Era-specific colors for comparison plots
ERA_COLORS = {
    "2022": "#5790fc",
    "2022EE": "#f89c20",
    "2023": "#e42536",
    "2023BPix": "#964a8b",
}


def extract_mass_from_filename(filename: str) -> Optional[float]:
    """
    Extract the nominal mass in GeV from a signal root file name.
    Examples:
        HAHM_13p6TeV_M0p5.root -> 0.5
        HAHM_13p6TeV_M1.root   -> 1.0
        HAHM_13p6TeV_M3p1.root -> 3.1
        JPsiToEE.root          -> 3.097
        UpsilonToEE.root       -> 9.460
    """
    stem = Path(filename).stem
    if "JPsi" in stem:
        return 3.097
    elif "Upsilon" in stem:
        return 9.460
    elif "_M" in stem:
        mass_str = stem.split("_M")[-1].replace("p", ".")
        try:
            return float(mass_str)
        except ValueError:
            return None
    return None


def compute_pt_statistics(
    values: np.ndarray,
    weights: Optional[np.ndarray] = None,
    n_bootstrap: int = 1000,
    seed: int = 42,
) -> Dict[str, Any]:
    """
    Compute mean and uncertainty on the mean for a pT distribution.

    Since the underlying pT distribution is non-Gaussian (exponential turn-on with
    a resolution round-off), the uncertainty on the mean is evaluated via:
      1. Non-parametric weighted bootstrap: yields empirical 68.27% central
         confidence interval [mean - err_low, mean + err_high], capturing any skewness.
      2. Analytical standard error of the weighted mean:
         Var(mean) = sum(w_i^2 * (x_i - mean)^2) / (sum(w_i))^2

    Returns:
        Dictionary with:
            'mean': weighted mean
            'err_low': 68.3% lower error bar on the mean
            'err_high': 68.3% upper error bar on the mean
            'sem_analytical': analytical standard error of the mean
            'sem_boot': bootstrap standard deviation of the mean
            'std': sample standard deviation
            'n_events': total number of raw events
            'n_eff': effective number of entries (Kish)
    """
    x = np.asarray(values, dtype=float)
    n = len(x)
    if n == 0:
        return {
            "mean": 0.0,
            "err_low": 0.0,
            "err_high": 0.0,
            "sem_analytical": 0.0,
            "sem_boot": 0.0,
            "std": 0.0,
            "n_events": 0,
            "n_eff": 0.0,
        }

    if weights is None:
        w = np.ones(n, dtype=float)
    else:
        w = np.asarray(weights, dtype=float)
        # Handle zero or negative total weight
        if np.sum(w) <= 0:
            w = np.ones(n, dtype=float)

    sum_w = np.sum(w)
    sum_w2 = np.sum(w**2)
    n_eff = (sum_w**2) / sum_w2 if sum_w2 > 0 else float(n)

    mean = np.average(x, weights=w)
    variance_sample = np.average((x - mean) ** 2, weights=w)
    std_sample = np.sqrt(max(0.0, variance_sample))

    # Analytical variance of the weighted mean
    var_mean = np.sum((w**2) * ((x - mean) ** 2)) / (sum_w**2)
    sem_analytical = np.sqrt(max(0.0, var_mean))

    # Bootstrap for non-parametric asymmetric 68.3% confidence interval
    err_low = sem_analytical
    err_high = sem_analytical
    sem_boot = sem_analytical

    if n_bootstrap > 0 and n > 1:
        rng = np.random.default_rng(seed)
        boot_means = np.empty(n_bootstrap)
        for b in range(n_bootstrap):
            idx = rng.choice(n, size=n, replace=True)
            w_sample = w[idx]
            sum_w_sample = np.sum(w_sample)
            if sum_w_sample > 0:
                boot_means[b] = np.average(x[idx], weights=w_sample)
            else:
                boot_means[b] = np.mean(x[idx])

        q_low, q_high = np.percentile(boot_means, [15.865, 84.135])
        err_low = max(0.0, mean - q_low)
        err_high = max(0.0, q_high - mean)
        sem_boot = float(np.std(boot_means))

    return {
        "mean": float(mean),
        "err_low": float(err_low),
        "err_high": float(err_high),
        "sem_analytical": float(sem_analytical),
        "sem_boot": float(sem_boot),
        "std": float(std_sample),
        "n_events": int(n),
        "n_eff": float(n_eff),
    }


def retrieve_signal_pt_data(
    file_path: Path,
    use_weights: bool = True,
    n_bootstrap: int = 1000,
    seed: int = 42,
) -> Optional[Dict[str, Any]]:
    """
    Open a signal root file and extract pt distributions for:
      - dielectron pt: DiElectron_pt
      - leading electron pt: max(DiElectron_l1_postfit_pt, DiElectron_l2_postfit_pt)
      - subleading electron pt: min(DiElectron_l1_postfit_pt, DiElectron_l2_postfit_pt)

    Returns dictionary with statistics for each quantity.
    """
    if not file_path.exists():
        return None

    root_file = ROOT.TFile.Open(str(file_path))
    if not root_file or root_file.IsZombie():
        return None

    tree = root_file.Get("Events")
    if not tree or tree.GetEntries() == 0:
        root_file.Close()
        return None

    rdf = ROOT.RDataFrame(tree)
    colnames = [str(c) for c in rdf.GetColumnNames()]

    # Required branches
    needed = ["DiElectron_pt", "DiElectron_l1_postfit_pt", "DiElectron_l2_postfit_pt"]
    for col in needed:
        if col not in colnames:
            print(f"Warning: Branch '{col}' not found in {file_path}. Skipping.")
            root_file.Close()
            return None

    load_cols = list(needed)
    has_weights = ("weight" in colnames) and use_weights
    if has_weights:
        load_cols.append("weight")

    data_np = rdf.AsNumpy(load_cols)
    root_file.Close()

    # In zsnap candidate files, DiElectron branches are 1-element RVecs per event
    pt_diele = np.array([x[0] if hasattr(x, "__len__") else x for x in data_np["DiElectron_pt"]], dtype=float)
    pt_l1 = np.array([x[0] if hasattr(x, "__len__") else x for x in data_np["DiElectron_l1_postfit_pt"]], dtype=float)
    pt_l2 = np.array([x[0] if hasattr(x, "__len__") else x for x in data_np["DiElectron_l2_postfit_pt"]], dtype=float)

    # Strictly sorted: leading is max, subleading is min
    pt_lead = np.maximum(pt_l1, pt_l2)
    pt_sublead = np.minimum(pt_l1, pt_l2)

    weights = None
    if has_weights:
        weights = np.array(data_np["weight"], dtype=float)

    stats_diele = compute_pt_statistics(pt_diele, weights=weights, n_bootstrap=n_bootstrap, seed=seed)
    stats_lead = compute_pt_statistics(pt_lead, weights=weights, n_bootstrap=n_bootstrap, seed=seed)
    stats_sublead = compute_pt_statistics(pt_sublead, weights=weights, n_bootstrap=n_bootstrap, seed=seed)

    return {
        "diele": stats_diele,
        "lead": stats_lead,
        "sublead": stats_sublead,
        "raw_diele": pt_diele,
        "raw_lead": pt_lead,
        "raw_sublead": pt_sublead,
        "raw_weights": weights if weights is not None else np.ones_like(pt_diele),
    }


def load_era_signals(
    base_folder: Path,
    era: str,
    include_resonances: bool = False,
    use_weights: bool = True,
    n_bootstrap: int = 1000,
    min_mass: float = 0.0,
    max_mass: float = 100.0,
) -> List[Dict[str, Any]]:
    """
    Discover and process all signal samples in the snap folder for a given era.
    Path: {base_folder}/zsnap/era{era}/base_15_full/
    """
    snap_dir = base_folder / "zsnap" / f"era{era}" / "base_15_full"
    if not snap_dir.exists():
        print(f"Warning: Directory does not exist: {snap_dir}")
        return []

    root_files = sorted(snap_dir.glob("*.root"))
    samples_data = []

    for rf in root_files:
        fn = rf.name
        # Skip hidden files
        if fn.startswith("."):
            continue

        is_resonance = ("JPsi" in fn) or ("Upsilon" in fn)
        if is_resonance and not include_resonances:
            continue

        mass = extract_mass_from_filename(fn)
        if mass is None:
            continue

        # Always ignore extra BPix files (M0p15, M0p3, M0p4)
        if any(np.isclose(mass, ex, atol=1e-3) for ex in [0.15, 0.3, 0.4]):
            continue

        if not (min_mass <= mass <= max_mass):
            continue

        res = retrieve_signal_pt_data(
            rf,
            use_weights=use_weights,
            n_bootstrap=n_bootstrap,
            seed=42 + int(mass * 10),
        )
        if res is None:
            continue

        samples_data.append({
            "filename": fn,
            "sample_name": rf.stem,
            "mass": mass,
            "is_resonance": is_resonance,
            "diele": res["diele"],
            "lead": res["lead"],
            "sublead": res["sublead"],
            "raw_diele": res["raw_diele"],
            "raw_lead": res["raw_lead"],
            "raw_sublead": res["raw_sublead"],
            "raw_weights": res["raw_weights"],
        })

    # Sort strictly by mass
    samples_data.sort(key=lambda s: s["mass"])
    return samples_data


def plot_pt_vs_mass(
    samples_data: List[Dict[str, Any]],
    output_path: Path,
    era_label: Optional[str] = None,
    xlim: Optional[Tuple[float, float]] = None,
    ylim: Optional[Tuple[float, float]] = None,
):
    """
    Plot average leading and subleading electron pT vs mass.

    Styling requirements:
      - CMS style (mplhep)
      - For each mass, a different color
      - At each mass, leading and subleading points are vertically aligned:
          pT(leading) >= pT(subleading)
      - No connecting lines between different masses
      - Reference horizontal dashed gray lines at 5, 10, and 20 GeV (not in legend)
      - Non-parametric uncertainty bars describing the uncertainty on the mean
      - Clean borderless legend (frameon=False)
      - CMS Simulation Preliminary label
      - Saves both .png and .pdf
    """
    if not samples_data:
        print("Warning: No sample data to plot.")
        return

    fig, ax = plt.subplots(figsize=(10, 10))

    masses = [s["mass"] for s in samples_data]
    l_means = [s["lead"]["mean"] for s in samples_data]
    s_means = [s["sublead"]["mean"] for s in samples_data]

    # Assign distinct colors to each mass
    n_masses = len(masses)
    colors = [MASS_PALETTE[i % len(MASS_PALETTE)] for i in range(n_masses)]

    # Reference dashed gray lines at 5, 10, and 20 GeV (not added to legend)
    for y_ref in [5.0, 10.0, 20.0]:
        ax.axhline(
            y_ref,
            color="gray",
            linestyle="--",
            linewidth=1.3,
            alpha=0.6,
            zorder=0,
        )

    # Plot each mass point: vertically aligned leading and subleading markers with error bars
    for idx, (s, color) in enumerate(zip(samples_data, colors)):
        m = s["mass"]
        l = s["lead"]
        sub = s["sublead"]

        # Vertical connecting line between subleading and leading points
        ax.plot(
            [m, m],
            [sub["mean"], l["mean"]],
            linestyle=":",
            color=color,
            alpha=0.55,
            linewidth=1.8,
            zorder=2,
        )

        # 1. Leading electron pT (Triangle Up '^')
        ax.errorbar(
            m,
            l["mean"],
            yerr=[[l["err_low"]], [l["err_high"]]],
            fmt="^",
            markersize=9.0,
            color=color,
            ecolor=color,
            elinewidth=2.0,
            capsize=3.5,
            capthick=1.8,
            zorder=4,
        )

        # 2. Subleading electron pT (Triangle Down 'v')
        ax.errorbar(
            m,
            sub["mean"],
            yerr=[[sub["err_low"]], [sub["err_high"]]],
            fmt="v",
            markersize=9.0,
            color=color,
            ecolor=color,
            elinewidth=2.0,
            capsize=3.5,
            capthick=1.8,
            zorder=4,
        )

    # Legend for quantities (represented in black, no border)
    legend_handles = [
        Line2D(
            [0],
            [0],
            color="black",
            marker="^",
            markersize=9.0,
            linestyle="None",
            label=r"Leading electron $\langle p_T \rangle$",
        ),
        Line2D(
            [0],
            [0],
            color="black",
            marker="v",
            markersize=9.0,
            linestyle="None",
            label=r"Subleading electron $\langle p_T \rangle$",
        ),
    ]

    leg = ax.legend(
        handles=legend_handles,
        loc="upper left",
        fontsize=16,
        frameon=False,
    )
    leg.set_zorder(10)

    # Era / sample info box
    info_text = f"Era: {era_label}" if era_label else "Run 3 (Combined)"
    ax.text(
        0.045,
        0.80,
        info_text,
        transform=ax.transAxes,
        fontsize=17,
        fontweight="bold",
        verticalalignment="top",
        zorder=10,
    )

    ax.set_xlabel(r"$M(Z_D)$ [GeV]")
    ax.set_ylabel(r"$\langle p_T \rangle$ [GeV]")

    # X-axis limits and ticks
    if xlim:
        ax.set_xlim(xlim)
    else:
        min_m = min(masses)
        max_m = max(masses)
        ax.set_xlim(max(0.0, min_m - 0.5), max_m + 0.8)

    # Set x-ticks matching the sample masses with standard large font
    valid_ticks = [m for m in masses if (xlim is None or (xlim[0] <= m <= xlim[1]))]
    ax.set_xticks(valid_ticks)
    ax.set_xticklabels([f"{m:g}" for m in valid_ticks])
    ax.tick_params(axis="both", which="major", labelsize=18)

    # Y-axis limits
    if ylim:
        ax.set_ylim(ylim)
    else:
        max_y = max(l_means)
        ax.set_ylim(0.0, max_y * 1.35)

    ax.grid(True, linestyle="--", alpha=0.35)
    hep.cms.label(loc=0, data=False, label="Preliminary", com=13.6, ax=ax)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    for ext in ["png", "pdf"]:
        out_file = output_path.with_suffix(f".{ext}")
        fig.savefig(out_file, bbox_inches="tight")
        print(f"Plot saved: {out_file}")

    plt.close(fig)


def plot_era_comparison(
    era_samples_data: Dict[str, List[Dict[str, Any]]],
    output_path: Path,
    xlim: Optional[Tuple[float, float]] = None,
):
    """
    Plot comparison of leading and subleading electron pT across all eras.
    """
    fig, ax = plt.subplots(figsize=(10, 10))

    # Reference dashed gray lines at 5, 10, and 20 GeV (not in legend)
    for y_ref in [5.0, 10.0, 20.0]:
        ax.axhline(
            y_ref,
            color="gray",
            linestyle="--",
            linewidth=1.3,
            alpha=0.6,
            zorder=0,
        )

    era_handles = []
    for era, samples in era_samples_data.items():
        if not samples:
            continue
        color = ERA_COLORS.get(era, "black")

        # Draw markers for each mass without connecting lines between different masses
        for s in samples:
            m = s["mass"]
            # Vertical connector between sublead and lead
            ax.plot(
                [m, m],
                [s["sublead"]["mean"], s["lead"]["mean"]],
                linestyle=":",
                color=color,
                alpha=0.45,
                linewidth=1.5,
                zorder=2,
            )
            ax.errorbar(
                m, s["lead"]["mean"],
                yerr=[[s["lead"]["err_low"]], [s["lead"]["err_high"]]],
                fmt="^", markersize=7.5, color=color, ecolor=color, elinewidth=1.6, capsize=3.0,
                zorder=4,
            )
            ax.errorbar(
                m, s["sublead"]["mean"],
                yerr=[[s["sublead"]["err_low"]], [s["sublead"]["err_high"]]],
                fmt="v", markersize=7.5, color=color, ecolor=color, elinewidth=1.6, capsize=3.0,
                zorder=4,
            )

        era_handles.append(Line2D([0], [0], color=color, marker="o", markersize=7, linestyle="None", label=era))

    # Proxy entries for quantities
    style_handles = [
        Line2D([0], [0], color="black", marker="^", markersize=8, linestyle="None", label=r"Leading $e$ $\langle p_T \rangle$"),
        Line2D([0], [0], color="black", marker="v", markersize=8, linestyle="None", label=r"Subleading $e$ $\langle p_T \rangle$"),
    ]

    all_handles = era_handles + [Line2D([0], [0], color="none", label="")] + style_handles
    ax.legend(handles=all_handles, loc="upper left", fontsize=14, frameon=False)

    ax.set_xlabel(r"$M(Z_D)$ [GeV]")
    ax.set_ylabel(r"$\langle p_T \rangle$ [GeV]")
    ax.tick_params(axis="both", which="major", labelsize=18)
    if xlim:
        ax.set_xlim(xlim)
    else:
        ax.set_xlim(0.0, 13.0)

    ax.set_ylim(0.0, 38.0)
    ax.grid(True, linestyle="--", alpha=0.35)
    hep.cms.label(loc=0, data=False, label="Preliminary", com=13.6, ax=ax)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    for ext in ["png", "pdf"]:
        out_file = output_path.with_suffix(f".{ext}")
        fig.savefig(out_file, bbox_inches="tight")
        print(f"Era comparison plot saved: {out_file}")

    plt.close(fig)


def combine_signals_across_eras(
    era_samples_data: Dict[str, List[Dict[str, Any]]],
    n_bootstrap: int = 1000,
) -> List[Dict[str, Any]]:
    """
    Combine events for each mass across all eras, weighting events appropriately.
    """
    combined_by_mass = {}

    for era, samples in era_samples_data.items():
        for s in samples:
            m = s["mass"]
            if m not in combined_by_mass:
                combined_by_mass[m] = {
                    "sample_name": s["sample_name"],
                    "mass": m,
                    "is_resonance": s["is_resonance"],
                    "diele_list": [],
                    "lead_list": [],
                    "sublead_list": [],
                    "weights_list": [],
                }
            combined_by_mass[m]["diele_list"].append(s["raw_diele"])
            combined_by_mass[m]["lead_list"].append(s["raw_lead"])
            combined_by_mass[m]["sublead_list"].append(s["raw_sublead"])
            combined_by_mass[m]["weights_list"].append(s["raw_weights"])

    combined_samples = []
    for m in sorted(combined_by_mass.keys()):
        item = combined_by_mass[m]
        all_diele = np.concatenate(item["diele_list"])
        all_lead = np.concatenate(item["lead_list"])
        all_sublead = np.concatenate(item["sublead_list"])
        all_w = np.concatenate(item["weights_list"])

        st_d = compute_pt_statistics(all_diele, weights=all_w, n_bootstrap=n_bootstrap, seed=int(m * 100))
        st_l = compute_pt_statistics(all_lead, weights=all_w, n_bootstrap=n_bootstrap, seed=int(m * 100) + 1)
        st_s = compute_pt_statistics(all_sublead, weights=all_w, n_bootstrap=n_bootstrap, seed=int(m * 100) + 2)

        combined_samples.append({
            "sample_name": item["sample_name"],
            "mass": m,
            "is_resonance": item["is_resonance"],
            "diele": st_d,
            "lead": st_l,
            "sublead": st_s,
        })

    return combined_samples


def format_summary_table(
    era_samples_data: Dict[str, List[Dict[str, Any]]],
    combined_samples: List[Dict[str, Any]],
) -> str:
    """
    Format a complete summary text table of the average leading and subleading pT values and uncertainties.
    """
    lines = []
    sep = "=" * 90
    sub_sep = "-" * 90

    lines.extend([
        sep,
        "AVERAGE LEADING AND SUBLEADING ELECTRON pT VS MASS SUMMARY",
        "  - Uncertainty bars represent 68.3% confidence interval on the mean via weighted bootstrap",
        "  - Analytical standard error on weighted mean: SEM = sqrt(sum(w_i^2 * (x_i - mean)^2)) / sum(w_i)",
        sep,
    ])

    for era, samples in era_samples_data.items():
        lines.extend([
            f"\nERA: {era}",
            sub_sep,
            f"{'Mass [GeV]':<11} {'Sample Name':<22} {'N_Events':<10} {'Leading <pT> [GeV]':<26} {'Subleading <pT> [GeV]':<26}",
            sub_sep,
        ])
        for s in samples:
            m = s["mass"]
            name = s["sample_name"]
            l = s["lead"]
            sub = s["sublead"]
            n_ev = l["n_events"]

            l_str = f"{l['mean']:.2f} +{l['err_high']:.2f}/-{l['err_low']:.2f} (SEM {l['sem_analytical']:.2f})"
            s_str = f"{sub['mean']:.2f} +{sub['err_high']:.2f}/-{sub['err_low']:.2f} (SEM {sub['sem_analytical']:.2f})"

            line = f"{m:<11.3f} {name:<22} {n_ev:<10} {l_str:<26} {s_str:<26}"
            lines.append(line)
        lines.append(sub_sep)

    if combined_samples:
        lines.extend([
            "\nRUN 3 COMBINED (ALL ERAS)",
            sub_sep,
            f"{'Mass [GeV]':<11} {'Sample Name':<22} {'N_Events':<10} {'Leading <pT> [GeV]':<26} {'Subleading <pT> [GeV]':<26}",
            sub_sep,
        ])
        for s in combined_samples:
            m = s["mass"]
            name = s["sample_name"]
            l = s["lead"]
            sub = s["sublead"]
            n_ev = l["n_events"]

            l_str = f"{l['mean']:.2f} +{l['err_high']:.2f}/-{l['err_low']:.2f} (SEM {l['sem_analytical']:.2f})"
            s_str = f"{sub['mean']:.2f} +{sub['err_high']:.2f}/-{sub['err_low']:.2f} (SEM {sub['sem_analytical']:.2f})"

            line = f"{m:<11.3f} {name:<22} {n_ev:<10} {l_str:<26} {s_str:<26}"
            lines.append(line)
        lines.append(sub_sep)

    lines.append(sep)
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Plot average dielectron pT, leading pT, and subleading pT vs mass for signal samples."
    )
    parser.add_argument(
        "--signal-tag",
        "--folder-tag",
        "--tag",
        type=str,
        default="260727",
        dest="signal_tag",
        help="Signal reprocessing tag (default: 260727, as used for background tag 260828)",
    )
    parser.add_argument(
        "--subfolder",
        type=str,
        default="signal_model_allCorrections",
        help="Signal subfolder name (default: signal_model_allCorrections)",
    )
    parser.add_argument(
        "--base-path",
        type=str,
        default="/eos/home-n/npalmeri/www/DiElectron/PS_reweighting/nanov15/per_subera",
        help="Base path for PS_reweighting signal files",
    )
    parser.add_argument(
        "--eras",
        nargs="+",
        default=["2022", "2022EE", "2023", "2023BPix"],
        help="List of eras to process (default: 2022 2022EE 2023 2023BPix)",
    )
    parser.add_argument(
        "--include-resonances",
        action="store_true",
        help="Include standard model resonances (JPsiToEE, UpsilonToEE) in the plot",
    )
    parser.add_argument(
        "--unweighted",
        action="store_true",
        help="Compute unweighted averages instead of using event weights",
    )
    parser.add_argument(
        "--n-bootstrap",
        type=int,
        default=1000,
        help="Number of bootstrap iterations for asymmetric mean uncertainty (default: 1000)",
    )
    parser.add_argument(
        "--min-mass",
        type=float,
        default=0.0,
        help="Minimum mass in GeV to include (default: 0.0)",
    )
    parser.add_argument(
        "--max-mass",
        type=float,
        default=100.0,
        help="Maximum mass in GeV to include (default: 100.0)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Custom output directory override (default: {base_path}/{signal_tag}/{subfolder})",
    )
    args = parser.parse_args()

    ROOT.gROOT.SetBatch(True)
    hep.style.use("CMS")

    base_signal_dir = Path(args.base_path) / args.signal_tag / args.subfolder
    if args.output_dir:
        out_parent_dir = Path(args.output_dir)
    else:
        out_parent_dir = base_signal_dir

    out_parent_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 80)
    print("PLOT AVERAGE DIELECTRON pT VS MASS")
    print(f"Signal base path: {base_signal_dir}")
    print(f"Output directory: {out_parent_dir}")
    print(f"Eras: {args.eras}")
    print(f"Use weights: {not args.unweighted}")
    print(f"Bootstrap iterations: {args.n_bootstrap}")
    print(f"Include resonances: {args.include_resonances}")
    print("=" * 80)

    era_samples_data = {}

    for era in args.eras:
        print(f"\nProcessing era: {era}...")
        samples = load_era_signals(
            base_folder=base_signal_dir,
            era=era,
            include_resonances=args.include_resonances,
            use_weights=(not args.unweighted),
            n_bootstrap=args.n_bootstrap,
            min_mass=args.min_mass,
            max_mass=args.max_mass,
        )
        if not samples:
            print(f"  No valid signal samples found for era {era}.")
            continue

        era_samples_data[era] = samples
        print(f"  Retrieved {len(samples)} signal samples for era {era}:")
        for s in samples:
            print(
                f"    M={s['mass']:<5.2f} GeV ({s['sample_name']}): "
                f"lead={s['lead']['mean']:.2f} +{s['lead']['err_high']:.2f}/-{s['lead']['err_low']:.2f}, "
                f"sublead={s['sublead']['mean']:.2f} +{s['sublead']['err_high']:.2f}/-{s['sublead']['err_low']:.2f}"
            )

        # Plot for this individual era in era folder and parent folder
        era_out_dir = out_parent_dir / f"era{era}"
        era_out_dir.mkdir(parents=True, exist_ok=True)

        plot_pt_vs_mass(
            samples_data=samples,
            output_path=era_out_dir / "dielectron_pt_vs_mass",
            era_label=era,
        )
        plot_pt_vs_mass(
            samples_data=samples,
            output_path=out_parent_dir / f"dielectron_pt_vs_mass_era{era}",
            era_label=era,
        )

    if not era_samples_data:
        print("\nError: No samples processed for any era.")
        sys.exit(1)

    # Combined Run 3 plot pooling events across eras
    combined_samples = combine_signals_across_eras(
        era_samples_data,
        n_bootstrap=args.n_bootstrap,
    )
    if combined_samples:
        print(f"\nGenerating Run 3 combined plot ({len(combined_samples)} mass points)...")
        plot_pt_vs_mass(
            samples_data=combined_samples,
            output_path=out_parent_dir / "dielectron_pt_vs_mass_all_eras",
            era_label=None,
        )

    # Multi-era overlay comparison plot
    if len(era_samples_data) > 1:
        print("\nGenerating multi-era comparison plot...")
        plot_era_comparison(
            era_samples_data=era_samples_data,
            output_path=out_parent_dir / "dielectron_pt_vs_mass_era_comparison",
        )

    # Save summary table
    summary_text = format_summary_table(era_samples_data, combined_samples)
    summary_file = out_parent_dir / "dielectron_pt_vs_mass_summary.txt"
    with open(summary_file, "w") as f:
        f.write(summary_text + "\n")
    print(f"\nSummary table saved to: {summary_file}")
    print("\n" + summary_text)

    print("\nAll tasks completed successfully!")


if __name__ == "__main__":
    main()

