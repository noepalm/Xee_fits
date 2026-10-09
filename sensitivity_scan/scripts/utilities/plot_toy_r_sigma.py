#!/usr/bin/env python3

import argparse
import sys
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable
import uproot


def parse_combine_limit_tree(file_path):
    """
    Parses the 'limit' tree from a Combine FitDiagnostics output file.
    Reshapes the tree entries into per-toy best-fit r and relative 1-sigma uncertainties.
    """
    with uproot.open(file_path) as f:
        if "limit" not in f:
            raise KeyError(f"Tree 'limit' not found in file: {file_path}")
        
        tree = f["limit"]
        data = tree.arrays(["limit", "quantileExpected"], library="np")

    limits = data["limit"]
    quantiles = data["quantileExpected"]

    num_entries = len(limits)
    if num_entries % 6 != 0:
        print(f"WARNING: Total entries ({num_entries}) is not a multiple of 6. "
              "Some toys might be incomplete or malformed.")

    n_toys = num_entries // 6

    r_fit = []
    sigma_down = []
    sigma_up = []

    for i in range(n_toys):
        sub_limits = limits[i*6 : (i+1)*6]
        sub_quantiles = quantiles[i*6 : (i+1)*6]

        try:
            r_val = sub_limits[np.isclose(sub_quantiles, 0.5)][0]
            r_lo = sub_limits[np.isclose(sub_quantiles, 0.16)][0]
            r_hi = sub_limits[np.isclose(sub_quantiles, 0.84)][0]

            if r_hi > 45 or r_lo < -45:
                # Skip unphysical boundary values
                continue

            s_down = r_val - r_lo
            s_up = r_hi - r_val

            r_fit.append(r_val)
            sigma_down.append(s_down)
            sigma_up.append(s_up)
        except IndexError:
            continue

    return np.array(r_fit), np.array(sigma_down), np.array(sigma_up)


def plot_limit_vs_uncertainty(r_fit, sigma_down, sigma_up, output_filename="limit_vs_sigma_r.png"):
    # Calculate piecewise pull vector
    sigma_chosen = np.where(r_fit >= 0, sigma_up, sigma_down)
    
    with np.errstate(divide='ignore', invalid='ignore'):
        pulls = np.where(sigma_chosen > 0, r_fit / sigma_chosen, np.nan)
    
    valid_mask = ~np.isnan(pulls)
    r_fit = r_fit[valid_mask]
    sigma_down = sigma_down[valid_mask]
    sigma_up = sigma_up[valid_mask]
    pulls = pulls[valid_mask]

    # Global binning definitions to guarantee unified scales across rows
    n_bins = 50
    r_bins = np.linspace(np.min(r_fit) - 0.2, np.max(r_fit) + 0.2, n_bins)
    s_down_bins = np.linspace(0, np.percentile(sigma_down, 99) * 1.2, n_bins)
    s_up_bins = np.linspace(0, np.percentile(sigma_up, 99) * 1.2, n_bins)
    pull_bins = np.linspace(np.percentile(pulls, 1), np.percentile(pulls, 99), n_bins)

    # Set up standardized figure
    fig, axes = plt.subplots(3, 2, figsize=(14, 15), dpi=120)

    # Helper function to append colorbars without resizing the parent axis
    def add_color_bar(im, ax, label="Toy Count"):
        divider = make_axes_locatable(ax)
        cax = divider.append_axes("right", size="5%", pad=0.08)
        cbar = fig.colorbar(im, cax=cax)
        cbar.set_label(label, fontsize=10)

    # ------------------------------------------------------------------------
    # ROW 1: 2D Histograms
    # ------------------------------------------------------------------------
    # Top-Left: r vs sigma_r (down)
    h1 = axes[0, 0].hist2d(r_fit, sigma_down, bins=[r_bins, s_down_bins], cmap="viridis", cmin=1)
    axes[0, 0].scatter(r_fit, sigma_down, color="black", alpha=0.3, s=6)
    axes[0, 0].set_xlabel(r"Best-fit $r$", fontsize=11)
    axes[0, 0].set_ylabel(r"$\sigma_{r, \text{down}}$ ($r_{\text{fit}} - r_{16\%}$)", fontsize=11)
    axes[0, 0].set_title(r"2D: Best-fit $r$ vs $\sigma_{r, \text{down}}$", fontsize=12)
    axes[0, 0].grid(True, linestyle="--", alpha=0.5)
    add_color_bar(h1[3], axes[0, 0])

    # Top-Right: r vs sigma_r (up)
    h2 = axes[0, 1].hist2d(r_fit, sigma_up, bins=[r_bins, s_up_bins], cmap="viridis", cmin=1)
    axes[0, 1].scatter(r_fit, sigma_up, color="black", alpha=0.3, s=6)
    axes[0, 1].set_xlabel(r"Best-fit $r$", fontsize=11)
    axes[0, 1].set_ylabel(r"$\sigma_{r, \text{up}}$ ($r_{84\%} - r_{\text{fit}}$)", fontsize=11)
    axes[0, 1].set_title(r"2D: Best-fit $r$ vs $\sigma_{r, \text{up}}$", fontsize=12)
    axes[0, 1].grid(True, linestyle="--", alpha=0.5)
    add_color_bar(h2[3], axes[0, 1])

    # ------------------------------------------------------------------------
    # ROW 2: 1D Histograms
    # ------------------------------------------------------------------------
    # Middle-Left: 1D r & sigma_r (down)
    ax_ml1 = axes[1, 0]
    ax_ml2 = ax_ml1.twinx()
    ax_ml1.hist(r_fit, bins=r_bins, color="royalblue", alpha=0.6, label=r"Best-fit $r$", edgecolor="blue")
    ax_ml2.hist(sigma_down, bins=s_down_bins, color="crimson", alpha=0.5, label=r"$\sigma_{r, \text{down}}$", edgecolor="red")
    ax_ml1.set_xlabel("Value", fontsize=11)
    ax_ml1.set_ylabel(r"Count ($r$)", color="royalblue", fontsize=11)
    ax_ml2.set_ylabel(r"Count ($\sigma_{r, \text{down}}$)", color="crimson", fontsize=11)
    ax_ml1.set_title(r"1D: Distribution of Best-fit $r$ and $\sigma_{r, \text{down}}$", fontsize=12)
    ax_ml1.grid(True, linestyle="--", alpha=0.5)
    
    lines_1, labels_1 = ax_ml1.get_legend_handles_labels()
    lines_2, labels_2 = ax_ml2.get_legend_handles_labels()
    ax_ml1.legend(lines_1 + lines_2, labels_1 + labels_2, loc="upper right", fontsize=10)

    # Middle-Right: 1D r & sigma_r (up)
    ax_mr1 = axes[1, 1]
    ax_mr2 = ax_mr1.twinx()
    ax_mr1.hist(r_fit, bins=r_bins, color="royalblue", alpha=0.6, label=r"Best-fit $r$", edgecolor="blue")
    ax_mr2.hist(sigma_up, bins=s_up_bins, color="darkorange", alpha=0.5, label=r"$\sigma_{r, \text{up}}$", edgecolor="darkred")
    ax_mr1.set_xlabel("Value", fontsize=11)
    ax_mr1.set_ylabel(r"Count ($r$)", color="royalblue", fontsize=11)
    ax_mr2.set_ylabel(r"Count ($\sigma_{r, \text{up}}$)", color="darkorange", fontsize=11)
    ax_mr1.set_title(r"1D: Distribution of Best-fit $r$ and $\sigma_{r, \text{up}}$", fontsize=12)
    ax_mr1.grid(True, linestyle="--", alpha=0.5)

    lines_3, labels_3 = ax_mr1.get_legend_handles_labels()
    lines_4, labels_4 = ax_mr2.get_legend_handles_labels()
    ax_mr1.legend(lines_3 + lines_4, labels_3 + labels_4, loc="upper right", fontsize=10)

    # ------------------------------------------------------------------------
    # ROW 3: Pull Distribution & Correlation
    # ------------------------------------------------------------------------
    # Bottom-Left: Pull Histogram
    axes[2, 0].hist(pulls, bins=pull_bins, color="teal", alpha=0.7, edgecolor="darkslategray")
    axes[2, 0].axvline(0, color="black", linestyle="--", linewidth=1)
    axes[2, 0].set_xlabel(r"Pull ($r / \sigma_{r}$)", fontsize=11)
    axes[2, 0].set_ylabel("Toy Count", fontsize=11)
    axes[2, 0].set_title(r"1D: Pull Distribution ($r / \sigma_{r, \text{up/down}}$)", fontsize=12)
    axes[2, 0].grid(True, linestyle="--", alpha=0.5)

    mean_pull = np.mean(pulls)
    std_pull = np.std(pulls)
    stats_text = f"Entries: {len(pulls)}\nMean: {mean_pull:.3f}\nStd Dev: {std_pull:.3f}"
    axes[2, 0].text(0.05, 0.92, stats_text, transform=axes[2, 0].transAxes,
                    fontsize=10, verticalalignment="top",
                    bbox=dict(boxstyle="round", facecolor="white", alpha=0.8))

    # Bottom-Right: 2D Pull vs Best-Fit r
    h3 = axes[2, 1].hist2d(r_fit, pulls, bins=[r_bins, pull_bins], cmap="plasma", cmin=1)
    axes[2, 1].set_xlabel(r"Best-fit $r$", fontsize=11)
    axes[2, 1].set_ylabel(r"Pull ($r / \sigma_{r}$)", fontsize=11)
    axes[2, 1].set_title(r"2D: Pull vs Best-fit $r$", fontsize=12)
    axes[2, 1].grid(True, linestyle="--", alpha=0.5)
    add_color_bar(h3[3], axes[2, 1])

    # Enforce regular grid geometry across all plots
    plt.tight_layout()
    plt.savefig(output_filename)
    print(f"Regularized plot saved successfully to: {output_filename}")
    plt.close()


def main():
    parser = argparse.ArgumentParser(description="Plot regularized structure of Best-Fit r, Uncertainties, and Pulls.")
    parser.add_argument("file_path", help="Path to input ROOT file")
    parser.add_argument("-o", "--output", default="limit_vs_sigmar_regularized.png", help="Output plot image filename")
    args = parser.parse_args()

    try:
        r_fit, sigma_down, sigma_up = parse_combine_limit_tree(args.file_path)
        print(f"Extracted {len(r_fit)} valid toy fits (excluding boundary hits).")
        
        if len(r_fit) == 0:
            print("ERROR: No valid toys could be parsed from the file.")
            sys.exit(1)

        plot_limit_vs_uncertainty(r_fit, sigma_down, sigma_up, output_filename=args.output)

    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()