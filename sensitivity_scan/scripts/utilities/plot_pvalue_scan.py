import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import mplhep as hep
import numpy as np
import pickle
import ROOT


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plot p-value scan from a pickle file.")
    parser.add_argument("--input-pkl", required=True, help="Input pickle with masses and p-values.")
    parser.add_argument("--outfolder", required=True, help="Output folder for plots.")
    parser.add_argument("--out-tag", required=True, help="Tag for output plot filenames.")
    parser.add_argument("--lumi", type=float, default=6.8, help="Luminosity label (default: 6.8).")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    hep.set_style("CMS")

    with open(args.input_pkl, "rb") as f:
        data = pickle.load(f)

    masses = data["masses"]
    pvalues = data["pvalues"]

    sorted_indices = np.argsort(masses)
    masses = masses[sorted_indices]
    pvalues = pvalues[sorted_indices]

    fig, ax = plt.subplots(figsize=(14, 10))
    ax.plot(masses, pvalues, marker="o", linestyle="-", color="black")
    ax.set_xlabel("$M(Z_D)$ [GeV]")
    ax.set_ylabel("p-value")
    ax.set_yscale("log")
    ax.set_ylim(1e-8, 1.1)

    sigma_levels = [1, 2, 3, 4, 5]
    for sigma in sigma_levels:
        pval = ROOT.Math.normal_cdf_c(sigma)
        ax.axhline(pval, color="red", linestyle="--")
        ax.text(
            1.02,
            pval,
            f"{sigma}$\\sigma$",
            color="red",
            va="center",
            transform=ax.get_yaxis_transform(),
        )

    ax.grid()
    hep.cms.label(loc=0, data=True, label="Preliminary", com=13.6, ax=ax, lumi=args.lumi)

    output_dir = Path(args.outfolder)
    output_dir.mkdir(parents=True, exist_ok=True)
    for ext in ["png", "pdf"]:
        fig.savefig(output_dir / f"pvalue_scan_{args.out_tag}.{ext}")


if __name__ == "__main__":
    main()