#!/usr/bin/env python3
"""
plot_resolution_interp_variations.py

Compute and plot the relative signal mass resolution uncertainty (fit interpolation uncertainty)
over mass across Run 3 eras.

The resolution model is linearly interpolated:
    sigma_nominal(m) = sigma_fit_par0 + sigma_fit_par1 * m

The 1-sigma uncertainty on resolution induced by the fit covariance matrix is:
    Delta_sigma(m) = sqrt( (sigma_fit_par0_err)^2 + (sigma_fit_par1_err * m)^2 + 2 * m * sigma_fit_par01_cov )

The relative resolution uncertainty plotted is:
    Delta_sigma(m) / sigma_nominal(m)  [%]

Uses the exact same plotting style as the scale-only plot:
    - Overlapped curves for all eras
    - No symmetrized mirror line
    - No shaded bands
    - No resonance data points
    - CMS color palette & styling
"""

import argparse
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import mplhep as hep
import ROOT

# CMS Recommended Color Palette
ERA_COLORS = {
    "2022": "#5790fc",
    "2022EE": "#f89c20",
    "2023": "#e42536",
    "2023BPix": "#964a8b",
}


def retrieve_resolution_parameters(workspace, era):
    """
    Retrieve resolution fit parameters and covariance from the RooFit workspace.

    Variables:
        sigma_fit_par0_<era>
        sigma_fit_par1_<era>
        sigma_fit_par0_err_<era>
        sigma_fit_par1_err_<era>
        sigma_fit_par01_cov_<era>
    """
    var_names = {
        "p0": f"sigma_fit_par0_{era}",
        "p1": f"sigma_fit_par1_{era}",
        "err0": f"sigma_fit_par0_err_{era}",
        "err1": f"sigma_fit_par1_err_{era}",
        "cov01": f"sigma_fit_par01_cov_{era}",
    }

    params = {}
    for key, name in var_names.items():
        var = workspace.var(name)
        if not var:
            raise ValueError(f"Variable '{name}' not found in workspace for era {era}")
        params[key] = var.getVal()

    return params


def compute_relative_resolution_uncertainty(masses, params):
    """
    Compute relative resolution uncertainty Delta_sigma / sigma_nominal [%].

    formula:
        sigma_nominal = p0 + p1 * m
        Delta_sigma   = sqrt(err0^2 + (err1 * m)^2 + 2 * m * cov01)
        rel_unc       = Delta_sigma / sigma_nominal * 100.0
    """
    m = np.asarray(masses, dtype=float)
    sigma_nominal = params["p0"] + params["p1"] * m

    variance = (
        (params["err0"]) ** 2
        + (params["err1"] * m) ** 2
        + 2.0 * m * params["cov01"]
    )
    # Numerical safeguard
    variance = np.maximum(variance, 0.0)
    delta_sigma = np.sqrt(variance)

    rel_uncertainty_percent = (delta_sigma / sigma_nominal) * 100.0
    return {
        "sigma_nominal": sigma_nominal,
        "delta_sigma": delta_sigma,
        "rel_percent": rel_uncertainty_percent,
    }


def plot_resolution_uncertainty_all_eras(
    masses,
    era_resolutions,
    ylabel,
    output_path,
    xlim=(0.6, 11.0),
):
    """
    Plot relative resolution uncertainty (% Delta sigma / sigma) across all eras:
    no bands/symmetrization, no resonances, single clean curve per era.
    """
    fig, ax = plt.subplots(figsize=(10, 10))

    ax.axhline(0, color="gray", linestyle=":", linewidth=1)

    for era, res_data in era_resolutions.items():
        color = ERA_COLORS.get(era, "black")
        vals = res_data["rel_percent"]

        ax.plot(
            masses,
            vals,
            color=color,
            linewidth=2.5,
            label=era,
        )

    ax.set_xlabel(r"$M(Z_D)$ [GeV]")
    ax.set_ylabel(ylabel)
    ax.set_xlim(xlim)
    ax.legend(loc="best", fontsize=16)
    ax.grid(True)
    hep.cms.label(loc=0, data=True, label="Preliminary", com=13.6, ax=ax)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    for ext in ["png", "pdf"]:
        fig.savefig(output_path.with_suffix(f".{ext}"))

    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(
        description="Plot signal mass resolution fit interpolation uncertainty over mass across eras."
    )
    parser.add_argument(
        "--folder-tag",
        "--data-tag",
        "--tag",
        type=str,
        default="260828",
        dest="folder_tag",
        help="Input folder tag for background dataset (default: 260828)",
    )
    parser.add_argument(
        "--signal-tag",
        type=str,
        default="260727",
        help="Signal model output tag (default: 260727)",
    )
    parser.add_argument(
        "--bkg-func",
        "--altbkg",
        type=str,
        default="bernstein",
        choices=["bernstein", "chebyshev"],
        help="Background function file to read workspace from (default: bernstein)",
    )
    parser.add_argument(
        "--eras",
        nargs="+",
        default=["2022", "2022EE", "2023", "2023BPix"],
        help="List of eras to process",
    )
    parser.add_argument(
        "--min-mass",
        type=float,
        default=0.6,
        help="Minimum mass in GeV (default: 0.6)",
    )
    parser.add_argument(
        "--max-mass",
        type=float,
        default=11.0,
        help="Maximum mass in GeV (default: 11.0)",
    )
    parser.add_argument(
        "--mass-step",
        type=float,
        default=0.1,
        help="Mass step in GeV (default: 0.1)",
    )
    args = parser.parse_args()

    ROOT.gROOT.SetBatch(True)
    hep.style.use("CMS")

    masses = np.round(
        np.arange(args.min_mass, args.max_mass + 0.5 * args.mass_step, args.mass_step),
        4,
    )

    all_era_resolutions = {}
    era_params = {}

    print("=" * 80)
    print("SIGNAL RESOLUTION INTERPOLATION UNCERTAINTY")
    print(f"Folder tag: {args.folder_tag}, Signal tag: {args.signal_tag}, bkg: {args.bkg_func}")
    print("=" * 80)

    for era in args.eras:
        input_file = (
            f"/eos/home-n/npalmeri/DiEleAnalyzer/Xee_fits/background_modelling/"
            f"datasets/{args.folder_tag}/{era}/"
            f"dataset_data_region0_binned_data_altbkg_{args.bkg_func}_allCorrections_{era}_full.root"
        )

        print(f"\nProcessing Era: {era}")
        print(f"  Input file: {input_file}")

        root_file = ROOT.TFile.Open(input_file)
        if not root_file or root_file.IsZombie():
            print(f"  Error: Could not open {input_file}, skipping era {era}.")
            continue

        workspace = root_file.Get("w")
        if not workspace:
            print(f"  Error: Workspace 'w' not found in {input_file}, skipping era {era}.")
            root_file.Close()
            continue

        try:
            params = retrieve_resolution_parameters(workspace, era)
        except ValueError as err:
            print(f"  Error: {err}")
            root_file.Close()
            continue

        era_params[era] = params
        print(f"  Retrieved resolution fit parameters:")
        print(f"    p0:       {params['p0']:+.6e}")
        print(f"    p1:       {params['p1']:+.6e}")
        print(f"    err0:     {params['err0']:.6e}")
        print(f"    err1:     {params['err1']:.6e}")
        print(f"    cov01:    {params['cov01']:+.6e}")

        res_data = compute_relative_resolution_uncertainty(masses, params)
        all_era_resolutions[era] = res_data

        vals = res_data["rel_percent"]
        print(
            f"  Relative resolution uncertainty range: "
            f"min={vals.min():.2f}%, max={vals.max():.2f}%, mean={vals.mean():.2f}%"
        )
        root_file.Close()

    # Output directory
    parent_outfolder = Path(
        f"/eos/home-n/npalmeri/www/DiElectron/signal_model/{args.signal_tag}/"
        f"use_reco_mass_allCorrections"
    )
    parent_outfolder.mkdir(parents=True, exist_ok=True)

    # Generate cumulative plot across all eras
    if len(all_era_resolutions) > 1:
        plot_name = "electron_resolution_interp_variation_all_eras_percent"
        out_plot_path = parent_outfolder / plot_name
        plot_resolution_uncertainty_all_eras(
            masses=masses,
            era_resolutions=all_era_resolutions,
            ylabel=r"$\Delta \sigma / \sigma$ [%]",
            output_path=out_plot_path,
            xlim=(args.min_mass, args.max_mass),
        )

        print("\n" + "=" * 80)
        print(f"All-eras resolution uncertainty plot saved to:")
        print(f"  {out_plot_path.with_suffix('.png')}")
        print(f"  {out_plot_path.with_suffix('.pdf')}")
        print("=" * 80)

    # Print summary table at benchmark masses
    benchmark_masses = [1.0, 2.0, 3.0, 5.0, 7.0, 9.0, 11.0]
    header = f"{'Mass [GeV]':<12} " + " ".join([f"{era + ' [%]':<14}" for era in args.eras if era in all_era_resolutions])
    sep = "=" * len(header)
    print("\n" + sep)
    print("RELATIVE RESOLUTION UNCERTAINTY Delta_sigma / sigma [%] AT BENCHMARK MASSES:")
    print(sep)
    print(header)
    print("-" * len(header))
    for bm in benchmark_masses:
        row = f"{bm:<12.1f} "
        for era in args.eras:
            if era not in all_era_resolutions:
                continue
            r = compute_relative_resolution_uncertainty([bm], era_params[era])
            val = r["rel_percent"][0]
            row += f"{val:<14.2f} "
        print(row)
    print(sep)

    # Save summary text file
    summary_path = parent_outfolder / "resolution_interp_summary.txt"
    with open(summary_path, "w") as f:
        f.write("=" * 80 + "\n")
        f.write("SIGNAL RESOLUTION FIT INTERPOLATION UNCERTAINTY SUMMARY\n")
        f.write("=" * 80 + "\n\n")
        f.write("RETRIEVED PARAMETERS:\n")
        f.write("-" * 80 + "\n")
        f.write(f"{'Era':<10} {'p0':<14} {'p1':<14} {'err0':<14} {'err1':<14} {'cov01':<14}\n")
        f.write("-" * 80 + "\n")
        for era, p in era_params.items():
            f.write(
                f"{era:<10} {p['p0']:<+14.6e} {p['p1']:<+14.6e} "
                f"{p['err0']:<14.6e} {p['err1']:<14.6e} {p['cov01']:<+14.6e}\n"
            )
        f.write("-" * 80 + "\n\n")
        f.write(sep + "\n")
        f.write("RELATIVE RESOLUTION UNCERTAINTY Delta_sigma / sigma [%] AT BENCHMARK MASSES:\n")
        f.write(sep + "\n")
        f.write(header + "\n")
        f.write("-" * len(header) + "\n")
        for bm in benchmark_masses:
            row = f"{bm:<12.1f} "
            for era in args.eras:
                if era not in all_era_resolutions:
                    continue
                r = compute_relative_resolution_uncertainty([bm], era_params[era])
                val = r["rel_percent"][0]
                row += f"{val:<14.2f} "
            f.write(row + "\n")
        f.write(sep + "\n")

    print(f"\nSummary table saved to: {summary_path}")
    print("\nDone!")


if __name__ == "__main__":
    main()

