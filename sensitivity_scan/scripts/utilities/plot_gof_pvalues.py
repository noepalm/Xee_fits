#!/usr/bin/env python3

import argparse
import re
from pathlib import Path

import matplotlib.pyplot as plt
import mplhep as hep
import numpy as np
import uproot


def parse_file_info(path):
    name = path.name
    mass_match = re.search(r"\.mH([0-9]+\.?[0-9]*)(?:\.[0-9]+)?\.root$", name)
    kind_match = re.search(r"_(region[0-9]+)_(obs|toys)\.GoodnessOfFit", name)
    if not mass_match or not kind_match:
        return None, None, None
    return float(mass_match.group(1)), kind_match.group(1), kind_match.group(2)


def read_limit_values(root_path):
    with uproot.open(root_path) as f:
        tree = f["limit"]
        return tree["limit"].array(library="np")


def collect_gof(outfolder, era, regions):
    obs_map = {}
    toys_map = {}
    root_files = list((Path(outfolder) / f"inclusive_{era}").rglob("higgsCombine*.GoodnessOfFit.mH*.root"))
    for root_path in root_files:
        mass, region, kind = parse_file_info(root_path)
        if region not in regions or kind is None:
            continue
        values = read_limit_values(root_path)
        if values.size == 0:
            continue
        key = (region, mass)
        if kind == "obs":
            obs_map[key] = float(values[0])
        else:
            toys_map[key] = values.astype(float)

    return obs_map, toys_map


def compute_pvalues(obs_map, toys_map, regions):
    pvals = {region: [] for region in regions}
    gof_obs = {region: [] for region in regions}

    for (region, mass), obs in obs_map.items():
        if region not in regions:
            continue
        toys = toys_map.get((region, mass))
        if toys is None or toys.size == 0:
            continue
        print(f"DEBUG: Region: {region}, Mass: {mass}, Obs: {obs}, Number of toys: {toys.size}")
        print(f"DEBUG: obs vs toys: obs={obs}, toys mean={toys.mean()}, toys std={toys.std()}")
        pval = float(np.sum(toys > obs)) / float(toys.size)
        pvals[region].append((mass, pval))
        gof_obs[region].append((mass, obs))
    
    print("DEBUG: p-values by region:")
    for region in regions:
        print(f"  {region}:")
        for mass, pval in pvals[region]:
            print(f"    Mass: {mass}, p-value: {pval}")

    for region in regions:
        pvals[region] = sorted(pvals[region], key=lambda x: x[0])
        gof_obs[region] = sorted(gof_obs[region], key=lambda x: x[0])

    return pvals, gof_obs


def plot_curves(ax, data_by_region, regions, ylabel, region_boundaries, colors):
    for idx, region in enumerate(regions):
        masses = [m for m, _ in data_by_region.get(region, [])]
        values = [v for _, v in data_by_region.get(region, [])]
        if not masses:
            continue
        ax.plot(
            masses,
            values,
            marker="o",
            linestyle="-",
            linewidth=1.5,
            markersize=4,
            color=colors[idx % len(colors)],
            label=f"Region {region.split('region')[-1]}",
        )

    for boundary in region_boundaries:
        ax.axvline(boundary, color="#666666", linestyle="--", linewidth=1.0)
    ax.set_xlabel("Mass")
    ax.set_ylabel(ylabel)
    ax.legend(frameon=False)


def main():
    parser = argparse.ArgumentParser(description="Plot GoF p-values and observed GoF vs mass")
    parser.add_argument("--outfolder", required=True, help="Output folder for a single cat+era")
    parser.add_argument("--era", required=True, help="Era label")
    parser.add_argument("--cat", required=True, help="Category label")
    parser.add_argument("--regions", nargs="+", required=True, help="Regions to include")
    parser.add_argument("--fit-tag", default="", help="Optional fit tag for output name")
    parser.add_argument(
        "--region-boundaries",
        nargs="*",
        type=float,
        default=[],
        help="Optional mass boundaries between regions",
    )
    args = parser.parse_args()

    hep.style.use("CMS")
    obs_map, toys_map = collect_gof(args.outfolder, args.era, args.regions)
    pvals, gof_obs = compute_pvalues(obs_map, toys_map, args.regions)

    colors = ["#5790fc", "#f89c20", "#e42536"]

    fig, ax = plt.subplots(figsize=(10,10))
    plot_curves(ax, gof_obs, args.regions, "Observed GoF", args.region_boundaries, colors)
    hep.cms.label("Preliminary", loc=0, ax=ax)
    # ax.set_title(f"Observed GoF vs Mass - {args.cat}, {args.era}")
    fig.tight_layout()

    out_dir = Path(args.outfolder)
    # out_dir = Path(args.outfolder) / "s"
    out_dir.mkdir(parents=True, exist_ok=True)
    fit_tag = f"_{args.fit_tag}" if args.fit_tag else ""
    gof_path = out_dir / f"gof_vs_mass_{args.era}{fit_tag}.png"
    # fig.savefig(gof_path)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10,10))
    plot_curves(ax, pvals, args.regions, "GoF p-value", args.region_boundaries, colors)
    ax.set_ylim(1e-9, 1.0)
    ax.set_yscale("log")

    hep.cms.label("Preliminary", loc=0, ax=ax)
    # ax.set_title(f"GoF p-value vs Mass - {args.cat}, {args.era}")
    ax.axhline(0.05, color="red", linestyle=":", linewidth=1.0, label="p-value = 5%")
    fig.tight_layout()

    pval_path = out_dir / f"gof_pvalue_vs_mass_{args.era}{fit_tag}.png"
    fig.savefig(pval_path)


if __name__ == "__main__":
    main()
