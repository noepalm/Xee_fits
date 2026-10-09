#!/usr/bin/env python3
import argparse
import datetime
import math
import os
import pickle
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Optional

import numpy as np
import scipy.stats as stats

DEFAULT_ERAS = ["allYears"]
REGIONS = ["region0", "region1", "region2"]

lumis = {
    "allYears": 58.6,
    "2022": 7.73,
    "2022EE": 26.62,
    "2023": 14.54,
    "2023BPix": 9.68,
}

eras = ["2022", "2022EE", "2023", "2023BPix"]

# 1. Parameter ranges [0, 10]
param_ranges = ":".join(
    [f"t{i}_{era}_envelope=0,10" for i in range(15) for era in eras]
    + [f"a{i}_{era}_envelope=0,10" for i in range(15) for era in eras]
)

# 2. Initial values
set_params = ",".join(
    [f"t{i}_{era}_envelope=0.001" for i in range(2) for era in eras]
    + [f"t{i}_{era}_envelope=0" for i in range(2, 15) for era in eras]
    + [f"a{i}_{era}_envelope=0.001" for i in range(3) for era in eras]
    + [f"a{i}_{era}_envelope=0" for i in range(3, 15) for era in eras]
    + [f"CMS_EXO25020_bkgEnvelopeIdx_{era}=1" for era in eras]
)

# 3. Freeze higher orders
freeze_params = ",".join(
    [f"t{i}_{era}_envelope" for i in range(2, 15) for era in eras]
    + [f"a{i}_{era}_envelope" for i in range(3, 15) for era in eras]
    + [f"CMS_EXO25020_bkgEnvelopeIdx_{era}" for era in eras]
)

COMMON_EXTRA_ARGS = [
    "--cminDefaultMinimizerStrategy", "0",
    "--setParameters", set_params,
    "--setParameterRanges", param_ranges,
    "--freezeParameters", freeze_params,
]


def cards_folder(folder_tag: str, fit_tag: str, region: str, mass: str) -> str:
    return (
        f"/eos/home-n/npalmeri/DiEleAnalyzer/Xee_fits/sensitivity_scan/cards/{folder_tag}"
        f"/cards_{region}_data_envelope_{fit_tag}_binned/ee/{mass}"
    )


def outfolder(folder_tag: str, fit_tag: str) -> Path:
    return Path(
        f"/eos/home-n/npalmeri/www/DiElectron/sensitivity/{folder_tag}"
        f"/fitDiagnostics_grid_data_envelope_{fit_tag}_binned/mu0/pvalue/global"
    )


def input_name_for_era(template: str, era: str) -> str:
    return template.format(era=era)


def collect_points(
    folder_tag: str,
    fit_tag: str,
    era: str,
    input_template: str,
    r_range: tuple[int, int],
) -> list[tuple[str, str, tuple[int, int]]]:
    points = []
    input_name = input_name_for_era(input_template, era)
    for region in REGIONS:
        folder = cards_folder(folder_tag, fit_tag, region, "")
        if not os.path.isdir(folder):
            continue
        for mass_folder in os.listdir(folder):
            if not mass_folder.replace(".", "").isdigit():
                continue
            root_path = os.path.join(folder, mass_folder, input_name)
            if os.path.isfile(root_path):
                points.append((region, mass_folder, r_range))
    return sorted(points, key=lambda x: (x[0], float(x[1])))


def generate_region_toys(
    folder_tag: str,
    fit_tag: str,
    era: str,
    input_template: str,
    region: str,
    ref_mass: str,
    ntoys: int,
    seed: int,
    toys_dir: Path,
) -> str:
    folder = cards_folder(folder_tag, fit_tag, region, ref_mass)
    input_name = input_name_for_era(input_template, era)
    workspace_path = os.path.join(folder, input_name)

    toy_filename = f"higgsCombine.bkg_toys_{region}_{era}.GenerateOnly.mH120.{seed}.root"
    target_path = toys_dir / toy_filename

    if target_path.exists():
        print(f"[{region}] Using existing toys file: {target_path}")
        return str(target_path)

    print(f"[{region}] Generating {ntoys} background-only toys using {workspace_path} (seed {seed})...")
    cmd = [
        "combine", "-M", "GenerateOnly",
        workspace_path,
        "-t", str(ntoys),
        "--toysFrequentist",
        "--saveToys",
        "-s", str(seed),
        "-n", f".bkg_toys_{region}_{era}",
        "-v", "0",
        *COMMON_EXTRA_ARGS,
    ]

    env = os.environ.copy()
    env["OMP_NUM_THREADS"] = "1"
    subprocess.run(cmd, cwd=str(toys_dir), env=env, check=True)
    return str(target_path)


def _run_point_toys(
    folder_tag: str,
    fit_tag: str,
    era: str,
    input_template: str,
    region: str,
    mass: str,
    r_range: tuple[int, int],
    toys_file: str,
    ntoys: int,
    combine_tag: str,
) -> tuple[bool, str]:
    folder = cards_folder(folder_tag, fit_tag, region, mass)
    if not os.path.isdir(folder):
        return False, f"Folder does not exist: {folder}"

    input_name = input_name_for_era(input_template, era)
    log_path = os.path.join(folder, f"global_pvalue_{combine_tag}.log")

    base_args = [
        "combine", "-M", "Significance",
        "-d", input_name,
        "--redefineSignalPOIs", "r",
        "--rMin", str(r_range[0]),
        "--rMax", str(r_range[1]),
        "--pvalue",
        "--toysFile", toys_file,
        "-t", str(ntoys),
        "-n", f".{combine_tag}",
        "-v", "0",
        *COMMON_EXTRA_ARGS,
    ]

    env = os.environ.copy()
    env["OMP_NUM_THREADS"] = "1"

    t0 = time.perf_counter()
    try:
        with open(log_path, "w") as f:
            subprocess.run(base_args, cwd=folder, stdout=f, stderr=subprocess.STDOUT, check=True, env=env)
        elapsed = time.perf_counter() - t0
        return True, f"OK: {region} M{mass} [{elapsed:.1f}s]"
    except Exception as e:
        return False, f"FAILED: {region} M{mass} -> {e} (see {log_path})"


def find_local_peaks(masses: np.ndarray, z_scores: np.ndarray, z_threshold: float = 3.0):
    """Find peak mass points where Z >= z_threshold, grouping continuous clusters into one peak."""
    peaks = []
    in_peak = False
    current_cluster = []

    for i in range(len(masses)):
        if z_scores[i] >= z_threshold:
            in_peak = True
            current_cluster.append(i)
        else:
            if in_peak:
                # Find maximum inside this cluster
                best_idx = current_cluster[np.argmax(z_scores[current_cluster])]
                peaks.append(best_idx)
                current_cluster = []
                in_peak = False

    if in_peak and current_cluster:
        best_idx = current_cluster[np.argmax(z_scores[current_cluster])]
        peaks.append(best_idx)

    return peaks


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run parallel global significance scans using background toys.")
    parser.add_argument("--nproc", type=int, default=os.cpu_count() or 1, help="Parallel worker jobs (default: cpu_count)")
    parser.add_argument("--folder-tag", default="260828", help="Folder tag under sensitivity outputs (default: 260828)")
    parser.add_argument("--fit-tag", default="allCorrections", help="Fit tag used in cards/output paths")
    parser.add_argument("--eras", nargs="+", default=DEFAULT_ERAS, help="Eras to process")
    parser.add_argument("--input-name-template", default="Xee_ee_4_{era}.root", help="Input workspace template")
    parser.add_argument("--r-min", type=int, default=-50, help="Minimum r range")
    parser.add_argument("--r-max", type=int, default=50, help="Maximum r range")
    parser.add_argument("--ntoys", type=int, default=500, help="Number of background-only toys to evaluate (default: 500)")
    parser.add_argument("--seed", type=int, default=123456, help="Random seed for toy generation")
    parser.add_argument("--obs-pkl", type=str, default=None, help="Path to observed p-value pickle file")
    parser.add_argument("--u0", type=float, default=1.0, help="Reference level for Gross-Vitells upcrossings (default: 1.0 -> 1 sigma)")
    parser.add_argument("--no-plot", action="store_true", help="Skip running plot_pvalue_scan.py on the global p-values")
    return parser.parse_args()


def main():
    args = _parse_args()
    output_dir = outfolder(args.folder_tag, args.fit_tag)
    output_dir.mkdir(parents=True, exist_ok=True)
    toys_dir = output_dir / "toys"
    toys_dir.mkdir(parents=True, exist_ok=True)

    r_range = (args.r_min, args.r_max)

    for era in args.eras:
        points = collect_points(
            args.folder_tag,
            args.fit_tag,
            era,
            args.input_name_template,
            r_range,
        )
        print("=" * 80)
        print(f"[{era}] GLOBAL SIGNIFICANCE SCAN: {len(points)} mass points across {len(REGIONS)} regions")
        print(f"Evaluating {args.ntoys} toys on {args.nproc} workers | Output: {output_dir}")
        print("=" * 80)

        if not points:
            continue

        region_toy_files = {}
        for region in REGIONS:
            region_points = [p for p in points if p[0] == region]
            if not region_points:
                continue
            ref_mass = region_points[len(region_points) // 2][1]
            toy_file = generate_region_toys(
                args.folder_tag,
                args.fit_tag,
                era,
                args.input_name_template,
                region,
                ref_mass,
                args.ntoys,
                args.seed,
                toys_dir,
            )
            region_toy_files[region] = toy_file

        combine_tag = f"global_toys_{args.ntoys}_s{args.seed}"

        completed = 0
        failed = 0
        with ThreadPoolExecutor(max_workers=args.nproc) as executor:
            futures = {
                executor.submit(
                    _run_point_toys,
                    args.folder_tag,
                    args.fit_tag,
                    era,
                    args.input_name_template,
                    region,
                    mass,
                    r_range,
                    region_toy_files[region],
                    args.ntoys,
                    combine_tag,
                ): (region, mass)
                for region, mass, r_range in points
            }
            for future in as_completed(futures):
                success, msg = future.result()
                if success:
                    completed += 1
                else:
                    failed += 1
                print(f"[{completed + failed}/{len(points)}] {msg}")

        import ROOT

        print("\nHarvesting toy outputs...")
        mass_labels = []
        pvalue_matrix = []

        for region, mass, _ in points:
            folder = cards_folder(args.folder_tag, args.fit_tag, region, mass)
            infile = os.path.join(folder, f"higgsCombine.{combine_tag}.Significance.mH120.{args.seed}.root")
            if not os.path.isfile(infile):
                infile = os.path.join(folder, f"higgsCombine.{combine_tag}.Significance.mH120.root")

            if not os.path.isfile(infile):
                print(f"WARNING: Output missing for {region} M{mass}: {infile}")
                continue

            rf = ROOT.TFile.Open(infile)
            tree = rf.Get("limit")
            if not tree or tree.GetEntries() == 0:
                print(f"WARNING: Empty tree for {region} M{mass}")
                rf.Close()
                continue

            point_pvals = [entry.limit for entry in tree]
            rf.Close()

            if len(point_pvals) < args.ntoys:
                print(f"WARNING: {region} M{mass} only has {len(point_pvals)}/{args.ntoys} entries")
                continue

            pvalue_matrix.append(point_pvals[: args.ntoys])
            mass_labels.append(float(mass))

        pvalue_matrix = np.array(pvalue_matrix).T  # (ntoys, n_masses)
        mass_labels = np.array(mass_labels)

        # Compute significance Z per toy
        eps = 1e-15
        pvalue_clamped = np.clip(pvalue_matrix, eps, 0.5)
        z_matrix = stats.norm.ppf(1.0 - pvalue_clamped)

        # Max significance per toy
        max_z_per_toy = np.max(z_matrix, axis=1)

        # Upcrossings for Gross-Vitells
        q0_matrix = z_matrix**2
        u0 = args.u0
        upcrossings_per_toy = []
        for i_toy in range(args.ntoys):
            q0_curve = q0_matrix[i_toy, :]
            below = q0_curve[:-1] < u0
            above = q0_curve[1:] >= u0
            upcrossings_per_toy.append(np.sum(below & above))

        mean_n_u0 = float(np.mean(upcrossings_per_toy))
        err_n_u0 = float(np.std(upcrossings_per_toy) / math.sqrt(args.ntoys))

        # Save summary dataset
        summary_pkl = output_dir / f"global_toys_summary_{era}.pkl"
        out_data = {
            "masses": mass_labels,
            "max_z_per_toy": max_z_per_toy,
            "mean_n_u0": mean_n_u0,
            "err_n_u0": err_n_u0,
            "u0": u0,
            "ntoys": args.ntoys,
        }
        with open(summary_pkl, "wb") as f:
            pickle.dump(out_data, f)
        print(f"Saved global toy results to {summary_pkl}")

        # Resolve Observed p-value pickle
        obs_pkl_path = args.obs_pkl
        if obs_pkl_path is None:
            candidate = output_dir.parent / "lowOrders" / f"pvalues_observed_{era}.pkl"
            if candidate.exists():
                obs_pkl_path = str(candidate)

        print("\n" + "=" * 90)
        print(f"GLOBAL SIGNIFICANCE EVALUATION SUMMARY ({era})")
        print("=" * 90)
        print(f"Toys Evaluated:              {args.ntoys}")
        print(f"Mass Points Scanned:         {len(mass_labels)}")
        print(f"GV <N_u0> (u0 = {u0:.1f}):         {mean_n_u0:.2f} +/- {err_n_u0:.2f}")

        if obs_pkl_path and os.path.isfile(obs_pkl_path):
            with open(obs_pkl_path, "rb") as f:
                obs_data = pickle.load(f)

            obs_masses = np.array(obs_data["masses"])
            obs_raw_pvals = np.array(obs_data["pvalues"])
            obs_pvals_clamped = np.clip(obs_raw_pvals, eps, 0.5)
            obs_z = stats.norm.ppf(1.0 - obs_pvals_clamped)
            obs_q0 = obs_z**2

            # ------------------------------------------------------------------
            # 1. Full-spectrum Gross-Vitells adjusted p-value curve
            # ------------------------------------------------------------------
            # p_global(m) = p_local(m) + <N_u0> * exp(-(q0(m) - u0) / 2)
            lee_factors = mean_n_u0 * np.exp(-(obs_q0 - u0) / 2.0)
            global_pvals_gv = obs_raw_pvals + lee_factors
            global_pvals_gv = np.clip(global_pvals_gv, obs_raw_pvals, 1.0)

            # Dump GV-adjusted pickle for plot_pvalue_scan.py
            gv_pkl_path = output_dir / f"pvalues_global_GV_{era}.pkl"
            with open(gv_pkl_path, "wb") as f:
                pickle.dump({"masses": obs_masses, "pvalues": global_pvals_gv}, f)
            print(f"Saved Gross-Vitells global p-values pickle: {gv_pkl_path}")

            # Plot GV-adjusted scan using existing plot utility
            if not args.no_plot:
                plot_script = Path(__file__).resolve().parent / "utilities" / "plot_pvalue_scan.py"
                if plot_script.exists():
                    print("\nPlotting Gross-Vitells global p-value scan...")
                    plot_cmd = [
                        sys.executable,
                        str(plot_script),
                        "--input-pkl", str(gv_pkl_path),
                        "--outfolder", str(output_dir),
                        "--out-tag", f"global_GV_{era}",
                        "--lumi", str(lumis.get(era, 58.6)),
                    ]
                    env = os.environ.copy()
                    env["OMP_NUM_THREADS"] = "1"
                    subprocess.run(plot_cmd, cwd=str(Path(__file__).resolve().parent), env=env, check=False)

            # ------------------------------------------------------------------
            # 2. Detailed reporting for all local excesses >= 3 sigma
            # ------------------------------------------------------------------
            peak_indices = find_local_peaks(obs_masses, obs_z, z_threshold=3.0)

            print("\n" + "-" * 90)
            print("CANDIDATE EXCESSES WITH LOCAL SIGNIFICANCE >= 3.0 sigma:")
            print("-" * 90)
            if not peak_indices:
                print("  No local excesses observed with Z_local >= 3.0 sigma.")
                # Show the absolute maximum peak as a fallback reference
                abs_max_idx = int(np.argmax(obs_z))
                peak_indices = [abs_max_idx]
                print(f"  (Showing overall maximum observed peak instead: M = {obs_masses[abs_max_idx]:.3f} GeV)")

            print(f"{'Mass [GeV]':<12} | {'Local Z':<10} | {'Local p':<12} | {'Global p (GV)':<15} | {'Global Z (GV)':<14} | {'Toys Exceeding':<16}")
            print("-" * 90)

            for idx in peak_indices:
                m_val = obs_masses[idx]
                z_loc = obs_z[idx]
                p_loc = obs_raw_pvals[idx]
                q0_val = obs_q0[idx]

                # GV calculation
                p_glob_gv = p_loc + mean_n_u0 * math.exp(-(q0_val - u0) / 2.0)
                p_glob_gv = min(max(p_glob_gv, p_loc), 1.0)
                z_glob_gv = stats.norm.ppf(1.0 - p_glob_gv) if p_glob_gv < 1.0 else 0.0

                # Direct counting calculation
                n_exceed = int(np.sum(max_z_per_toy >= z_loc))
                if n_exceed > 0:
                    p_cnt = n_exceed / float(args.ntoys)
                    toys_str = f"{n_exceed}/{args.ntoys} ({p_cnt:.3e})"
                else:
                    toys_str = f"0/{args.ntoys} (< {1.0/args.ntoys:.3e})"

                print(f"{m_val:<12.3f} | {z_loc:<10.2f} | {p_loc:<12.3e} | {p_glob_gv:<15.3e} | {z_glob_gv:<14.2f} | {toys_str:<16}")

            print("-" * 90)

        else:
            print(f"\nObserved pickle not found at {obs_pkl_path}. Run with --obs-pkl to evaluate observed peaks.")
        print("=" * 90)


if __name__ == "__main__":
    main()