import argparse
import re
from pathlib import Path

import matplotlib.pyplot as plt
import mplhep as hep
import numpy as np
import uproot

def extract_mass_region_kind(path):
    name = path.name
    mass_match = re.search(r"\.mH([0-9]+\.?[0-9]*)(?:\.[0-9]+)?\.root$", name)
    kind_match = re.search(r"_(region[0-9]+)_(obs|toys)\.GoodnessOfFit", name)
    if not mass_match or not kind_match:
        return None, None, None
    return float(mass_match.group(1)), kind_match.group(1), kind_match.group(2)


def read_gof_scores(root_path):
    with uproot.open(root_path) as f:
        tree = f["limit"]
        values = tree["limit"].array(library="np")
        return values


def collect_scores(outfolder, era, regions):
    scores = {region: {"obs": [], "toys": []} for region in regions}
    root_files = list((Path(outfolder) / f"inclusive_{era}").rglob("higgsCombine*.GoodnessOfFit.mH*.root"))
    for root_path in root_files:
        mass, region, kind = extract_mass_region_kind(root_path)
        if region not in scores or kind is None:
            continue
        values = read_gof_scores(root_path)
        if values.size == 0:
            continue
        if kind == "obs":
            scores[region]["obs"].append((mass, float(values[0])))
        else:
            scores[region]["toys"].extend([float(v) for v in values])

    for region in scores:
        scores[region]["obs"] = [
            s for _, s in sorted(scores[region]["obs"], key=lambda x: x[0])
        ]

    return scores


def main():
    parser = argparse.ArgumentParser(description="Plot GoodnessOfFit summary histograms")
    parser.add_argument("--outfolder", required=True, help="Output folder for a single cat+era")
    parser.add_argument("--era", required=True, help="Era label")
    parser.add_argument("--cat", required=True, help="Category label")
    parser.add_argument("--regions", nargs="+", required=True, help="Regions to include")
    parser.add_argument("--fit-tag", default="", help="Optional fit tag for output name")
    parser.add_argument(
        "--expected",
        type=float,
        default=350.0,
        help="Expected GoF value for the reference line",
    )
    args = parser.parse_args()

    hep.style.use("CMS")
    scores = collect_scores(args.outfolder, args.era, args.regions)

    fig, axes = plt.subplots(1, len(args.regions), figsize=(6.2 * len(args.regions), 6), sharey=True)
    if len(args.regions) == 1:
        axes = [axes]

    max_values = []
    for region in scores:
        max_values.extend(scores[region]["obs"])
        max_values.extend(scores[region]["toys"])
    max_score = max(max_values) if max_values else 1

    for ax, region in zip(axes, args.regions):
        region_obs = [s for s in scores.get(region, {}).get("obs", []) if s >= 0]
        region_toys = [s for s in scores.get(region, {}).get("toys", []) if s >= 0]
        print(f"Region {region}: obs={len(region_obs)}, toys={len(region_toys)} entries")
        if region_obs or region_toys:
            counts, edges = np.histogram(
                region_toys + region_obs,
                bins=60,
                range=(args.expected * 0.8, max_score * 1.1),
            )
            if region_toys:
                ax.hist(
                    region_toys,
                    bins=edges,
                    histtype="stepfilled",
                    color="#5790fc",
                    alpha=0.6,
                    density=True,
                    label="Toys",
                )
            if region_obs:
                ax.hist(
                    region_obs,
                    bins=edges,
                    histtype="step",
                    color="#000000",
                    density=True,
                    linewidth=1.6,
                    label="Observed",
                )
            if args.expected is not None:
                ax.axvline(
                    args.expected,
                    color="#e42536",
                    linestyle="--",
                    linewidth=1.6,
                    label="Expected",
                )
        ax.set_title("Region " + region.split("region")[-1], pad=18)
        ax.set_xlabel("GoF score")
        if ax == axes[0]:
            ax.set_ylabel("Entries")
        ax.text(
            0.9,
            0.7,
            f"Nobs={len(region_obs)}\nNtoys={len(region_toys)}",
            transform=ax.transAxes,
            ha="right",
            va="top",
            fontsize=11,
        )
        if region == args.regions[0]:
            ax.legend(loc="upper right", fontsize=11, frameon=False)

    # hep.cms.label("Preliminary", loc=0, ax=axes[0])
    # fig.suptitle(f"Goodness of Fit summary - {args.cat}, {args.era}", y=0.98)
    fig.subplots_adjust(wspace=0.18, top=0.86, bottom=0.12)

    out_dir = Path(args.outfolder) # / "s"
    out_dir.mkdir(parents=True, exist_ok=True)
    fit_tag = f"_{args.fit_tag}" if args.fit_tag else ""
    out_path = out_dir / f"gof_summary_{args.era}{fit_tag}.png"
    fig.savefig(out_path)


if __name__ == "__main__":
    main()
