#!/usr/bin/env python3
import ROOT
import argparse
import os
from pathlib import Path

# Silence ROOT verbosity
ROOT.gROOT.SetBatch(True)
ROOT.RooMsgService.instance().setGlobalKillBelow(ROOT.RooFit.FATAL)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Extract and summarize best-fit signal strength r values across masses and eras."
    )
    parser.add_argument(
        "-m", "--masses",
        type=float,
        nargs="+",
        required=True,
        help="Space-separated list of mass points (e.g. 1.8 1.9 2.0 2.1)",
    )
    parser.add_argument(
        "-e", "--eras",
        type=str,
        nargs="+",
        required=True,
        help="Space-separated list of eras (e.g. 2022 2022EE 2023 2023BPix)",
    )
    parser.add_argument(
        "--basefolder",
        type=str,
        default=".",
        help="Base folder where mass subdirectories are stored (e.g. <basefolder>/<mass>/fitDiagnostics_inclusive_<era>.root)",
    )
    parser.add_argument(
        "-f", "--fit_file_pattern",
        type=str,
        default="fitDiagnostics_inclusive_{era}.root",
        help="Pattern for fit diagnostics root file (default: fitDiagnostics_inclusive_{era}.root)",
    )
    parser.add_argument(
        "-o", "--output_folder",
        type=str,
        default=None,
        help="Output folder where the report will be saved. If omitted, prints to stdout only.",
    )
    parser.add_argument(
        "--report_name",
        type=str,
        default="fit_results_r_summary.txt",
        help="Filename for the report (default: fit_results_r_summary.txt)",
    )
    return parser.parse_args()


def extract_r_values(file_path):
    """Retrieve best-fit r, rHiErr, and rLoErr from tree_fit_sb in fitDiagnostics root file."""
    if not os.path.exists(file_path):
        return None, None, None, f"File not found: {file_path}"

    f_fit = ROOT.TFile.Open(str(file_path), "READ")
    if not f_fit or f_fit.IsZombie():
        return None, None, None, f"Could not open file: {file_path}"

    fit_tree = f_fit.Get("tree_fit_sb")
    if not fit_tree or fit_tree.GetEntries() == 0:
        f_fit.Close()
        return None, None, None, "tree_fit_sb not found or empty"

    fit_tree.GetEntry(0)
    r_val = float(fit_tree.r)
    r_hi = float(fit_tree.rHiErr)
    r_lo = float(fit_tree.rLoErr)

    f_fit.Close()
    return r_val, r_hi, r_lo, None


def main():
    args = parse_args()
    basefolder = Path(args.basefolder)

    lines = []
    lines.append("=" * 80)
    lines.append(" FIT DIAGNOSTICS: BEST-FIT SIGNAL STRENGTH (r) SUMMARY REPORT")
    lines.append("=" * 80)
    lines.append(f"Base folder: {basefolder}")
    lines.append(f"Masses:      {' '.join(f'{m:.1f}' for m in args.masses)}")
    lines.append(f"Eras:        {' '.join(args.eras)}")
    lines.append("-" * 80)

    for mass in args.masses:
        mass_str = f"{mass:.1f}"
        lines.append(f"\n[ Mass = {mass_str} GeV ]")
        lines.append(f"  {'Era':<12} | {'Best-fit r':<14} | {'+Err (Hi)':<12} | {'-Err (Lo)':<12} | {'Formatted r':<24}")
        lines.append("  " + "-" * 74)

        for era in args.eras:
            filename = args.fit_file_pattern.format(era=era, mass=mass_str)
            file_path = basefolder / mass_str / filename

            r_val, r_hi, r_lo, err_msg = extract_r_values(file_path)

            if err_msg is not None:
                lines.append(f"  {era:<12} | ERROR: {err_msg}")
            else:
                formatted_r = f"{r_val:.3f} +{r_hi:.3f}/-{r_lo:.3f}"
                lines.append(
                    f"  {era:<12} | {r_val:>12.4f}   | {r_hi:>10.4f}   | {r_lo:>10.4f}   | {formatted_r:<24}"
                )

    lines.append("\n" + "=" * 80)
    full_report = "\n".join(lines) + "\n"

    # Print to console
    print(full_report)

    # Save to file if output folder is given
    if args.output_folder:
        out_dir = Path(args.output_folder)
        out_dir.mkdir(parents=True, exist_ok=True)
        report_path = out_dir / args.report_name
        with open(report_path, "w") as f:
            f.write(full_report)
        print(f"[OK] Saved summary report to: {report_path}")


if __name__ == "__main__":
    main()
