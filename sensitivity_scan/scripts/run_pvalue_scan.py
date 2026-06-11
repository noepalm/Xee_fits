import argparse
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pickle
import ROOT

DEFAULT_ERAS = ["allYears", "2022", "2022EE", "2023", "2023BPix"]
REGIONS = ["region0", "region1", "region2"]

# Add global extra options here (example values shown but commented out):
COMMON_EXTRA_ARGS = [
    # "--setParameters", "signal_model_index_2023=0,signal_model_index_2022=0,signal_model_index_2022EE=0,signal_model_index_2023BPix=0,pdf_index_2022_envelope=0,pdf_index_2022EE_envelope=0,pdf_index_2023_envelope=0,pdf_index_2023BPix_envelope=0",
    # "--freezeParameters", "signal_model_index_2023,signal_model_index_2022,signal_model_index_2022EE,signal_model_index_2023BPix,pdf_index_2022_envelope,pdf_index_2022EE_envelope,pdf_index_2023_envelope,pdf_index_2023BPix_envelope",
    "--setParameters", "pdf_index_2022_envelope=0,pdf_index_2022EE_envelope=0,pdf_index_2023_envelope=0,pdf_index_2023BPix_envelope=0",
    "--freezeParameters", "pdf_index_2022_envelope,pdf_index_2022EE_envelope,pdf_index_2023_envelope,pdf_index_2023BPix_envelope",
]

def cmd_to_string(cmd: list[str]) -> str:
    return " ".join(subprocess.list2cmdline([arg]) for arg in cmd)

def run_command(cmd: list[str], cwd: str) -> None:
    print(f"\n>>> [{cwd}] {cmd_to_string(cmd)}")
    subprocess.run(cmd, check=True, cwd=cwd)


def format_expect_signal(value: float) -> str:
    text = f"{value:g}"
    return text.replace("-", "m").replace(".", "p")


def build_mode_tag(mode: str, expect_signal: float) -> str:
    if mode == "observed":
        return "observed"
    signal_tag = format_expect_signal(expect_signal)
    return f"toys_r{signal_tag}"


def cards_folder(folder_tag: str, fit_tag: str, region: str, mass: str) -> str:
    return (
        f"/eos/home-n/npalmeri/DiEleAnalyzer/Xee_fits/sensitivity_scan/cards/{folder_tag}"
        f"/cards_{region}_data_envelope_{fit_tag}_binned/ee/{mass}"
    )


def outfolder(folder_tag: str, fit_tag: str) -> Path:
    return Path(
        f"/eos/home-n/npalmeri/www/DiElectron/sensitivity/{folder_tag}"
        f"/fitDiagnostics_grid_data_envelope_{fit_tag}_binned/mu0/pvalue"
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
    return points

def _run_point(
    folder_tag: str,
    fit_tag: str,
    era: str,
    input_template: str,
    mode: str,
    expect_signal: float,
    region: str,
    mass: str,
    r_range: tuple[int, int],
    combine_tag: str,
) -> None:
    folder = cards_folder(folder_tag, fit_tag, region, mass)
    if not os.path.isdir(folder):
        raise FileNotFoundError(f"Folder does not exist: {folder}")

    input_name = input_name_for_era(input_template, era)
    base_args = [
        "combine",
        "-M",
        "Significance",
        "-d",
        input_name,
        "--cminDefaultMinimizerStrategy",
        "0",
        "--redefineSignalPOIs",
        "r",
        "--rMin",
        f"{r_range[0]}",
        "--rMax",
        f"{r_range[1]}",
        "--cminDefaultMinimizerTolerance",
        "0.0001",  # needed for Asimov; variations are too small
        "--pvalue",
        "-n",
        f".{combine_tag}",
        "-v",
        "0",
        *COMMON_EXTRA_ARGS,
    ]

    if mode == "toys":
        base_args.extend(["-t", "-1", "--expectSignal", f"{expect_signal}"])

    run_command(base_args, cwd=folder)

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run combine p-value scan in parallel.")
    parser.add_argument(
        "--nproc",
        type=int,
        default=os.cpu_count() or 1,
        help="Number of parallel jobs (default: cpu count).",
    )
    parser.add_argument(
        "--folder-tag",
        default="260602",
        help="Folder tag under sensitivity outputs (default: 260602).",
    )
    parser.add_argument(
        "--fit-tag",
        default="allCorrections",
        help="Fit tag used in cards/output paths (default: allCorrections).",
    )
    parser.add_argument(
        "--eras",
        nargs="+",
        default=DEFAULT_ERAS,
        help="Eras to process (default: allYears 2022 2022EE 2023 2023BPix).",
    )
    parser.add_argument(
        "--input-name-template",
        default="Xee_ee_4_{era}.root",
        help="Input workspace name template (default: Xee_ee_4_{era}.root).",
    )
    parser.add_argument(
        "--r-min",
        type=int,
        default=-50,
        help="Minimum r value (default: -50).",
    )
    parser.add_argument(
        "--r-max",
        type=int,
        default=50,
        help="Maximum r value (default: 50).",
    )
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--observed",
        action="store_true",
        help="Run observed p-values (default).",
    )
    mode_group.add_argument(
        "--toys",
        action="store_true",
        help="Run Asimov toys and compute expected p-values.",
    )
    parser.add_argument(
        "--expect-signal",
        type=float,
        default=0.0,
        help="Injected signal strength for toys (default: 0.0).",
    )
    parser.add_argument(
        "--no-plot",
        action="store_true",
        help="Skip plotting step.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    mode = "toys" if args.toys else "observed"
    if mode == "observed" and args.expect_signal not in (0.0, -0.0):
        raise ValueError("--expect-signal is only supported with --toys")

    output_dir = outfolder(args.folder_tag, args.fit_tag)
    os.makedirs(output_dir, exist_ok=True)
    if args.nproc < 1:
        raise ValueError("--nproc must be >= 1")

    r_range = (args.r_min, args.r_max)
    for era in args.eras:
        points = collect_points(
            args.folder_tag,
            args.fit_tag,
            era,
            args.input_name_template,
            r_range,
        )
        if not points:
            print(f"Warning: no mass points found for era {era}")
            continue

        combine_tag = build_mode_tag(mode, args.expect_signal)
        with ThreadPoolExecutor(max_workers=args.nproc) as executor:
            futures = [
                executor.submit(
                    _run_point,
                    args.folder_tag,
                    args.fit_tag,
                    era,
                    args.input_name_template,
                    mode,
                    args.expect_signal,
                    region,
                    mass,
                    r_range,
                    combine_tag,
                )
                for region, mass, r_range in points
            ]
            for future in as_completed(futures):
                future.result()

        # harvest step: take p-value from each processed mass and save them to pickle
        pvalues = []
        masses = []
        for region, mass, _ in points:
            folder = cards_folder(args.folder_tag, args.fit_tag, region, mass)
            infile = os.path.join(
                folder,
                f"higgsCombine.{combine_tag}.Significance.mH120.root",
            )
            if not os.path.isfile(infile):
                print(f"Warning: output file not found for region {region}, mass {mass}: {infile}")
                continue

            root_file = ROOT.TFile.Open(infile)
            tree = root_file.Get("limit")
            if tree is None:
                print(f"Warning: 'limit' tree not found in file {infile}")
                continue
            tree.GetEntry(0)
            pvalue = tree.limit
            pvalues.append(pvalue)
            masses.append(float(mass))

        pvalues = np.array(pvalues)
        masses = np.array(masses)
        print(f"P-values ({era}): {pvalues}")
        mode_tag = build_mode_tag(mode, args.expect_signal)
        output_pickle = output_dir / f"pvalues_{mode_tag}_{era}.pkl"
        with open(output_pickle, "wb") as f:
            pickle.dump({"masses": masses, "pvalues": pvalues}, f)
        print(f"Saved p-values and masses to {output_pickle}")

        if not args.no_plot:
            plot_script = Path(__file__).resolve().parent / "utilities" / "plot_pvalue_scan.py"
            plot_tag = f"{mode_tag}_{era}"
            plot_cmd = [
                sys.executable,
                str(plot_script),
                "--input-pkl",
                str(output_pickle),
                "--outfolder",
                str(output_dir),
                "--out-tag",
                plot_tag,
            ]
            run_command(plot_cmd, cwd=str(Path(__file__).resolve().parent))

if __name__ == "__main__":
    main()