#!/usr/bin/env python3
import argparse
import ast
import codecs
import datetime
import os
import re
import shutil
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Iterable, Optional

DEFAULT_FOLDER_TAG = "260828"
# ALL_ERAS = ["2022", "2022EE", "2023", "2023BPix"]
ALL_ERAS = ["2023BPix"]

FOLDER_TEMPLATE_RAW = "/eos/home-n/npalmeri/DiEleAnalyzer/Xee_fits/sensitivity_scan/cards/{folder_tag}/cards_{region}_data_envelope_allCorrections_binned/ee/{mass}"
PLOT_DIR_BASE_TEMPLATE = "/eos/home-n/npalmeri/www/DiElectron/sensitivity/{folder_tag}/fitDiagnostics_grid_data_envelope_allCorrections_binned/mu0/nll_scans"

POINTS = {
    "allYears" : [
        ### OBSERVED, UNBLINDED
        # ("region0", "1.2", (-20, 5)),
        ("region0", "2.1", (-5, 10)),
        # ("region0", "2.0", (-20, 20)),
        # ("region1", "3.3", (-0.4, 0.1)), #(-1,1)
        # ("region1", "4.8", (-0.05, 0.36)),
        # ("region1", "5.8", (-0.1, 0.6)),
        # ("region2", "7.1", (0.001, 0.15)),
        # ("region2", "9.1", (-0.1, 10)),
        # ("region2", "9.8", (-10, 2)),
    ],
    "2022" : [
        ("region0", "1.2", (-50, 10)),
        ("region0", "2.1", (-15, 10)),
        ("region1", "3.3", (-1,1)),
        ("region1", "4.8", (-1,1)),
        ("region1", "5.8", (-1,1)),
        ("region2", "7.1", (-1,1)),
        ("region2", "9.1", (-10,10)),
        ("region2", "9.8", (-10,10)),
    ],
    "2022EE" : [
        # ("region0", "1.2", (-50, 10)),
        # ("region0", "2.1", (-15, 10)),
        ("region0", "1.9", (-20, 20)),
        ("region0", "2.0", (-20, 20)),
        # ("region1", "3.3", (-1,1)),
        # ("region1", "4.8", (-1,1)),
        # ("region1", "5.8", (-1,1)),
        # ("region2", "7.1", (-1,1)),
        # ("region2", "9.1", (-2, 10)),
        # ("region2", "9.8", (-10,10)),
    ],
    "2023" : [
        ("region0", "1.2", (-50, 30)),
        ("region0", "2.1", (-14, 4)),
        ("region1", "3.3", (-1,1)),
        ("region1", "4.8", (-1,1)),
        ("region1", "5.8", (-1,1)),
        ("region2", "7.1", (-1,1)),
        ("region2", "9.1", (-10,10)),
        ("region2", "9.8", (-20,7)),
    ],
    "2023BPix" : [
        ("region0", "1.2", (-50, 30)),
        ("region0", "2.1", (-14, 4)),
        ("region1", "3.3", (-1,1)),
        ("region1", "4.8", (-1,1)),
        ("region1", "5.8", (-1,1)),
        ("region2", "7.1", (-1,1)),
        ("region2", "9.1", (-10,10)),
        ("region2", "9.8", (-20,7)),
    ],
}

def cmd_to_string(cmd: list[str]) -> str:
    return " ".join(subprocess.list2cmdline([arg]) for arg in cmd)

def format_duration(seconds: float) -> str:
    total = int(round(seconds))
    hours, rem = divmod(total, 3600)
    minutes, secs = divmod(rem, 60)
    return f"{hours}:{minutes:02d}:{secs:02d}"


def decode_output(out) -> str:
    """Ensure output is always a decoded string with real newlines."""
    if out is None:
        return ""
    if isinstance(out, bytes):
        return out.decode("utf-8", errors="replace")
    if isinstance(out, str):
        # Handle stringified bytes like b'...' or b"..."
        if (out.startswith("b'") and out.endswith("'")) or (out.startswith('b"') and out.endswith('"')):
            try:
                val = ast.literal_eval(out)
                if isinstance(val, bytes):
                    return val.decode("utf-8", errors="replace")
            except Exception:
                inner = out[2:-1]
                try:
                    return codecs.decode(inner, "unicode_escape")
                except Exception:
                    return inner
        elif out.startswith("b'") or out.startswith('b"'):
            inner = out[2:]
            if inner.endswith("'") or inner.endswith('"'):
                inner = inner[:-1]
            try:
                return codecs.decode(inner, "unicode_escape")
            except Exception:
                return inner
        return out
    return str(out)


LOG_MAX_BYTES = 800 * 1024

HEADER_PATTERN = re.compile(
    r"^(?:(?:SKIP:[^\n]*|#.*)\r?\n)*(={40,}\r?\n.*?\r?\n={40,}\r?\n)",
    re.DOTALL,
)


def split_header_and_body(text: str):
    """Split log text into leading header (with banners) and output body."""
    m = HEADER_PATTERN.match(text)
    if m:
        header = m.group(0)
        body = text[len(header):]
        return header, body
    return "", text


def write_log_with_tail(path, text, max_bytes=LOG_MAX_BYTES):
    """Write log text, preserving header and keeping tail of output when exceeding max_bytes."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    if isinstance(text, bytes):
        text_str = decode_output(text)
    else:
        text_str = decode_output(str(text))

    data = text_str.encode("utf-8", errors="replace")
    if len(data) <= max_bytes:
        with open(path, "wb") as f:
            f.write(data)
        return

    header, body = split_header_and_body(text_str)
    prefix = b"[... log trimmed; showing tail only ...]\n"

    if header:
        header_bytes = header.encode("utf-8")
        body_bytes = body.encode("utf-8", errors="replace")
        tail_budget = max(0, max_bytes - len(header_bytes) - len(prefix))
        if tail_budget > 0:
            tail = body_bytes[-tail_budget:]
            tail_str = tail.decode("utf-8", errors="replace")
            if "\n" in tail_str:
                parts = tail_str.split("\n", 1)
                if parts[1]:
                    tail_str = parts[1]
            trimmed = header_bytes + prefix + tail_str.encode("utf-8")
        else:
            trimmed = header_bytes + prefix
    else:
        tail_budget = max(0, max_bytes - len(prefix))
        if tail_budget > 0:
            tail = data[-tail_budget:]
            tail_str = tail.decode("utf-8", errors="replace")
            if "\n" in tail_str:
                parts = tail_str.split("\n", 1)
                if parts[1]:
                    tail_str = parts[1]
            trimmed = prefix + tail_str.encode("utf-8")
        else:
            trimmed = prefix

    with open(path, "wb") as f:
        f.write(trimmed)


# eras = ALL_ERAS

# # 1. Parameter ranges [0, 10] separated by colons
# param_ranges = ":".join(
#     [f"t{i}_{era}_envelope=0,10" for i in range(15) for era in eras]
#     + [f"a{i}_{era}_envelope=0,10" for i in range(15) for era in eras]
# )

# # 2. Initial values (low orders = 0.001, higher orders = 0)
# set_params = ",".join(
#     # [f"t{i}_{era}_envelope=0.001" for i in range(5) for era in eras]
#     [f"t{i}_{era}_envelope=0" for i in range(4, 15) for era in eras]
#     # + [f"a{i}_{era}_envelope=0.001" for i in range(7) for era in eras]
#     + [f"a{i}_{era}_envelope=0" for i in range(6, 15) for era in eras]
#     # + [f"CMS_EXO25020_bkgEnvelopeIdx_{era}=1" for era in eras]
# )

# # 3. Freeze higher orders
# freeze_params = ",".join(
#     [f"t{i}_{era}_envelope" for i in range(4, 15) for era in eras]
#     + [f"a{i}_{era}_envelope" for i in range(6, 15) for era in eras]
#     # + [f"CMS_EXO25020_bkgEnvelopeIdx_{era}" for era in eras]
# )


def build_common_args(rmin, rmax, input_root="Xee_ee_4_allYears.root") -> list[str]:
    return [
        "combine",
        "-M", "MultiDimFit",
        input_root,
        "--algo", "grid",
        "--rMin", f"{rmin}",
        "--rMax", f"{rmax}",
        "--points", "50",
        "--cminDefaultMinimizerStrategy", "0",
        # "--robustFit", "1",
        "--X-rtd", "MINIMIZER_freezeDisassociatedParams",
        # "--setParameters", set_params,
        # "--freezeParameters", freeze_params,
        "--saveNLL",
        # "--saveToys", #NOTE: good for tests, doesn't work for plot1DScan.py (expects no toys?)
        "-v", "0",
    ]


def run_point(
    region: str,
    mass: str,
    r_range: tuple[float, float],
    folder_template: str,
    plot_dir: str,
    asimov_mode: Optional[str] = None,
    expect_signal: Optional[float] = None,
    envelope_scan: bool = False,
    breakdown: bool = False,
    era: Optional[str] = None,
) -> tuple[bool, str]:

    t_start_point = time.perf_counter()
    folder = folder_template.format(region=region, mass=mass)

    if not os.path.isdir(folder):
        return False, f"Folder does not exist: {folder}"

    eras_to_use = [era] if era else ALL_ERAS
    input_root_file = f"Xee_ee_4_{era}.root" if era else "Xee_ee_4_allYears.root"

    # Determine tags, snapshot requirements, and input dataset based on mode
    ### NOTE: these params are NOT used everywhere.
    envelope_set_params = ",".join([f"CMS_EXO25020_bkgEnvelopeIdx_{year}=0" for year in eras_to_use])
    envelope_freeze_params = ",".join([f"CMS_EXO25020_bkgEnvelopeIdx_{year}" for year in eras_to_use])

    era_tag_suffix = f"_{era}" if era else ""
    log_name = f"nll_scan_{region}_M{mass}{era_tag_suffix}.log"
    log_path = os.path.join(plot_dir, log_name)
    sections: list[str] = []

    def capture_and_buffer(cmd: list[str], cwd: str, timeout: Optional[int] = 600) -> None:
        start_dt = datetime.datetime.now()
        t0 = time.perf_counter()
        timed_out = False
        try:
            proc = subprocess.run(
                cmd,
                cwd=cwd,
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=timeout,
            )
            elapsed = time.perf_counter() - t0
            end_dt = datetime.datetime.now()
            ret = proc.returncode
            output = decode_output(proc.stdout if proc.stdout is not None else "")
        except subprocess.TimeoutExpired as e:
            elapsed = time.perf_counter() - t0
            end_dt = datetime.datetime.now()
            ret = "TIMEOUT"
            output = decode_output(e.stdout if e.stdout is not None else "")
            timed_out = True

        header = "=" * 80
        meta = (
            f"START:   {start_dt.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"END:     {end_dt.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"ELAPSED: {elapsed:.2f}s ({format_duration(elapsed)})\n"
            f"CWD:     {cwd}\n"
            f"CMD:     {' '.join(cmd)}\n"
            f"RET:     {ret}\n"
        )
        if output and not output.endswith("\n"):
            output += "\n"
        sections.append(f"{header}\n{meta}{header}\n{output}")

        if timed_out:
            raise subprocess.CalledProcessError(-1, cmd, output=output)
        if ret != 0:
            raise subprocess.CalledProcessError(ret, cmd, output=output)

    def flush_log():
        write_log_with_tail(log_path, "".join(sections))

    try:
        if asimov_mode is None:
            # Observed mode
            scan_input_root = input_root_file
            n_scan_tag = f".nll_scan_sb{era_tag_suffix}"
            scan_extra_args = []
            plot_out_name = f"nll_scan_SB_{region}_M{mass}{era_tag_suffix}"

        elif asimov_mode == "bonly":
            # PRE-STEP: run B-only fit to generate B+injected signal Asimov (but from B-only best fit params)
            bonly_tag = f".bonly_postfit{era_tag_suffix}"
            capture_and_buffer([
                "combine", "-M", "MultiDimFit", input_root_file,
                "--saveWorkspace", "-n", bonly_tag,
                "--cminDefaultMinimizerStrategy", "0",
                # "--robustFit", "1",
                # "--setParameters", f"r=0,{envelope_set_params}",
                # "--freezeParameters", f"r,{envelope_freeze_params}",
                "--setParameters", f"r=0",
                "--freezeParameters", f"r",
                "--keepFailures",
                "-v", "0",
            ], cwd=folder)

            scan_input_root = f"higgsCombine{bonly_tag}.MultiDimFit.mH120.root"
            scan_extra_args = [
                "--snapshotName", "MultiDimFit",
                "-t", "-1",
                "--toysFrequentist",
            ]
            if expect_signal is not None:
                scan_extra_args.extend(["--expectSignal", str(expect_signal)])
                sig_label = f"mu{float(expect_signal):.2g}".replace(".", "p")
                n_scan_tag = f".nll_scan_asimovBonly_{sig_label}{era_tag_suffix}"
                plot_out_name = f"nll_scan_asimovBonly_{sig_label}_{region}_M{mass}{era_tag_suffix}"
            else:
                n_scan_tag = f".nll_scan_asimovBonly{era_tag_suffix}"
                plot_out_name = f"nll_scan_asimovBonly_{region}_M{mass}{era_tag_suffix}"
                scan_extra_args.extend(["--expectSignal", "0"])

        elif asimov_mode == "sb":
            # Pre-step: Run S+B fit to generate snapshot
            sb_tag = f".sb_postfit{era_tag_suffix}"
            capture_and_buffer([
                "combine", "-M", "MultiDimFit", input_root_file,
                "--saveWorkspace", "-n", sb_tag,
                "--cminDefaultMinimizerStrategy", "0", 
                # "--robustFit", "1",
                "--rMin", f"{r_range[0]}", "--rMax", f"{r_range[1]}",
                # "--setParameters", envelope_set_params,
                # "--freezeParameters", envelope_freeze_params,
                "--keepFailures",
                "-v", "0",
            ], cwd=folder)

            scan_input_root = f"higgsCombine{sb_tag}.MultiDimFit.mH120.root"
            scan_extra_args = [
                "--snapshotName", "MultiDimFit",
                "-t", "-1",
                "--toysFrequentist",
            ]
            if expect_signal is not None:
                scan_extra_args.extend(["--expectSignal", str(expect_signal)])
                sig_label = f"mu{float(expect_signal):.2g}".replace(".", "p")
                n_scan_tag = f".nll_scan_asimovSB_{sig_label}{era_tag_suffix}"
                plot_out_name = f"nll_scan_asimovSB_{sig_label}_{region}_M{mass}{era_tag_suffix}"
            else:
                n_scan_tag = f".nll_scan_asimovSB{era_tag_suffix}"
                plot_out_name = f"nll_scan_asimovSB_{region}_M{mass}{era_tag_suffix}"
        else:
            raise ValueError(f"Unknown asimov mode: {asimov_mode}")

        base_args = build_common_args(r_range[0], r_range[1], input_root=scan_input_root)

        if envelope_scan:
            tag_suffix_parts = []
            if asimov_mode == "bonly":
                tag_suffix_parts.append(f"asimovBonly_{sig_label}" if expect_signal is not None else "asimovBonly")
            elif asimov_mode == "sb":
                tag_suffix_parts.append(f"asimovSB_{sig_label}" if expect_signal is not None else "asimovSB")
            if era:
                tag_suffix_parts.append(era)

            tag_suffix = "_".join(tag_suffix_parts)
            tag_opt = f"_{tag_suffix}" if tag_suffix else ""

            # 1. Nominal scan with floating envelope (no background index frozen)
            n_scan_floating = f".nll_scan_bkgEnvelope{tag_opt}"
            capture_and_buffer(
                base_args + scan_extra_args 
                + ["-n", n_scan_floating] 
                + ["--X-rtd", "REMOVE_CONSTANT_ZERO_POINT=1"]
                + ["--X-rtd", "MINIMIZER_freezeDisassociatedParams"]
                + ["--cminRunAllDiscreteCombinations"]
                + ["--setParameters", ",".join([f"CMS_EXO25020_bkgEnvelopeIdx_{year}=1" for year in eras_to_use])], # just for init
                cwd=folder,
            )

            # 2. Fit with bkg index frozen to 0 (Bernstein)
            set_params_idx0 = ",".join([f"CMS_EXO25020_bkgEnvelopeIdx_{year}=0" for year in eras_to_use])
            freeze_params_idx0 = ",".join([f"CMS_EXO25020_bkgEnvelopeIdx_{year}" for year in eras_to_use])
            n_scan_idx0 = f".nll_scan_bkgEnvelope_idx0{tag_opt}"
            capture_and_buffer(
                base_args
                + scan_extra_args
                + [
                    "--setParameters", set_params_idx0,
                    "--freezeParameters", freeze_params_idx0,
                    "--X-rtd", "REMOVE_CONSTANT_ZERO_POINT=1",
                    "--X-rtd", "MINIMIZER_freezeDisassociatedParams",
                    "-n", n_scan_idx0,
                ],
                cwd=folder,
            )

            # 3. Fit with bkg index frozen to 1 (Chebyshev)
            set_params_idx1 = ",".join([f"CMS_EXO25020_bkgEnvelopeIdx_{year}=1" for year in eras_to_use])
            freeze_params_idx1 = ",".join([f"CMS_EXO25020_bkgEnvelopeIdx_{year}" for year in eras_to_use])
            n_scan_idx1 = f".nll_scan_bkgEnvelope_idx1{tag_opt}"
            capture_and_buffer(
                base_args
                + scan_extra_args
                + [
                    "--setParameters", set_params_idx1,
                    "--freezeParameters", freeze_params_idx1,
                    "--X-rtd", "REMOVE_CONSTANT_ZERO_POINT=1",
                    "--X-rtd", "MINIMIZER_freezeDisassociatedParams",
                    "-n", n_scan_idx1,
                ],
                cwd=folder,
            )

            # Output plot name
            plot_out_name = f"{plot_out_name}_envelopeComparison"
            era_title = f", {era}" if era else ""
            plot_title = f"Envelope NLL Scan ({region}, M{mass}{era_title})"

            # Call custom plot_nll_scan.py script (without --deltaNLL to preserve envelope constant offsets)
            plot_cmd = [
                "python3",
                f"{os.getcwd()}/scripts/utilities/plot_nll_scan.py",
                "-o", f"{plot_out_name}.png",
                "--title", plot_title,
            ]
            if tag_suffix:
                plot_cmd.extend(["--tag", tag_suffix])

            capture_and_buffer(plot_cmd, cwd=folder)

        else:
            # Default single scan (Total uncertainty: Stat + Syst)
            capture_and_buffer(
                base_args
                + scan_extra_args
                + [
                    # "--setParameters",
                    # envelope_set_params,
                    # "--freezeParameters",
                    # envelope_freeze_params,
                    ### TEST: freeze scale systematic to verify shift in best-fit r value is due to that
                    # "--freezeParameters",
                    # "CMS_scale_e",
                    "-n", n_scan_tag,
                ],
                cwd=folder,
            )
            scan_root_file = f"higgsCombine{n_scan_tag}.MultiDimFit.mH120.root"

            if breakdown:
                # Run second scan freezing allConstrainedNuisances (Stat-only)
                n_scan_tag_stat = f"{n_scan_tag}_freezeSysts"
                freeze_params_stat = f"allConstrainedNuisances"
                capture_and_buffer(
                    base_args
                    + scan_extra_args
                    + [
                        # "--setParameters",
                        # envelope_set_params,
                        "--freezeParameters",
                        freeze_params_stat,
                        "-n", n_scan_tag_stat,
                    ],
                    cwd=folder,
                )
                stat_root_file = f"higgsCombine{n_scan_tag_stat}.MultiDimFit.mH120.root"
                plot_out_name = f"{plot_out_name}_breakdown"

                # Overlapped plot using plot1DScan.py native overlay
                capture_and_buffer(
                    [
                        "plot1DScan.py", scan_root_file,
                        "--others", f"{stat_root_file}:Stat:2",
                        "-o", plot_out_name,
                    ],
                    cwd=folder,
                )
            else:
                capture_and_buffer(
                    [
                        "plot1DScan.py", scan_root_file,
                        "-o", plot_out_name,
                    ],
                    cwd=folder,
                )

        # Move generated plots to target plot_dir
        src_png = os.path.join(folder, f"{plot_out_name}.png")
        dst_png = os.path.join(plot_dir, f"{plot_out_name}.png")
        if os.path.exists(src_png):
            shutil.move(src_png, dst_png)

        src_pdf = os.path.join(folder, f"{plot_out_name}.pdf")
        dst_pdf = os.path.join(plot_dir, f"{plot_out_name}.pdf")
        if os.path.exists(src_pdf):
            shutil.move(src_pdf, dst_pdf)

        flush_log()
        elapsed_point = time.perf_counter() - t_start_point
        era_label = f" ({era})" if era else ""
        return True, f"OK: {region} M{mass}{era_label} [{elapsed_point:.1f}s]"

    except Exception as e:
        flush_log()
        era_label = f" ({era})" if era else ""
        return False, f"FAILED: {region} M{mass}{era_label} ({e}); see {log_path}"

def main():
    parser = argparse.ArgumentParser(description="Run NLL scans across multiple mass points in parallel.")
    parser.add_argument(
        "--folder-tag",
        default=DEFAULT_FOLDER_TAG,
        help=f"Tag for input cards and output directories (default: {DEFAULT_FOLDER_TAG})",
    )
    parser.add_argument(
        "--asimov",
        choices=["bonly", "sb"],
        default=None,
        help="Run Asimov scan using either 'bonly' or 'sb' snapshot (default: observed fit)",
    )
    parser.add_argument(
        "--expectSignal",
        type=float,
        default=None,
        help="Injected signal strength for Asimov scan (e.g., 0, 0.1, 1, 10)",
    )
    parser.add_argument(
        "--envelope-scan",
        action="store_true",
        help="Perform envelope comparison scan (floating envelope vs. idx 0 vs. idx 1) and plot together",
    )
    parser.add_argument(
        "--breakdown",
        "--uncertainty-breakdown",
        action="store_true",
        help="Run uncertainty breakdown (Total vs. Stat-only by freezing allConstrainedNuisances)",
    )
    parser.add_argument(
        "--by-era",
        nargs="*",
        default=None,
        choices=["2022", "2022EE", "2023", "2023BPix"],
        help="Split scan per individual era instead of using allYears. Optionally specify a list of eras.",
    )
    parser.add_argument(
        "--jobs",
        type=int,
        default=None,
        help="Number of parallel workers across mass points",
    )
    args = parser.parse_args()

    # Determine list of eras to run over
    if args.by_era is not None:
        eras_to_run = args.by_era if len(args.by_era) > 0 else ALL_ERAS
    else:
        eras_to_run = [None]  # Combined allYears run

    plot_dir_base = PLOT_DIR_BASE_TEMPLATE.format(folder_tag=args.folder_tag)
    folder_template = FOLDER_TEMPLATE_RAW.format(folder_tag=args.folder_tag, region="{region}", mass="{mass}")

    for era in eras_to_run:
        # 1. Base scan mode path (observed, asimov_postfit_bonly, asimov_postfit_sb)
        if args.asimov is None:
            plot_dir = os.path.join(plot_dir_base, "observed")
        elif args.asimov == "bonly":
            if args.expectSignal is not None:
                sig_label = f"r{float(args.expectSignal):.2g}".replace(".", "p")
                plot_dir = os.path.join(plot_dir_base, f"asimov_postfit_bonly_{sig_label}")
            else:
                plot_dir = os.path.join(plot_dir_base, "asimov_postfit_bonly")
        elif args.asimov == "sb":
            if args.expectSignal is not None:
                sig_label = f"r{float(args.expectSignal):.2g}".replace(".", "p")
                plot_dir = os.path.join(plot_dir_base, f"asimov_postfit_sb_{sig_label}")
            else:
                plot_dir = os.path.join(plot_dir_base, "asimov_postfit_sb")

        # 2. Append feature subfolders in hierarchy (envelope_scan -> breakdown)
        if args.envelope_scan:
            plot_dir = os.path.join(plot_dir, "envelope_scan")
        if args.breakdown:
            plot_dir = os.path.join(plot_dir, "breakdown")

        # 3. Append by_era/<era> as the terminal folder
        if era is not None:
            plot_dir = os.path.join(plot_dir, "by_era", era)

        os.makedirs(plot_dir, exist_ok=True)

        mode_label = "Observed" if args.asimov is None else f"Asimov ({args.asimov})"
        if args.expectSignal is not None:
            mode_label += f" [mu={args.expectSignal}]"
        if args.envelope_scan:
            mode_label += " [Envelope Comparison Scan]"
        if args.breakdown:
            mode_label += " [Uncertainty Breakdown]"
        if era is not None:
            mode_label += f" [Era={era}]"

        print("=" * 80)
        print(f"RUNNING NLL SCANS: Mode={mode_label} | Folder Tag={args.folder_tag}")
        print(f"Output directory: {plot_dir}")
        print("=" * 80)

        points = POINTS[era] if era else POINTS["allYears"]

        max_workers = args.jobs or min(len(points), os.cpu_count() or 1)
        print(f"Running NLL scans for {len(points)} points on {max_workers} parallel workers")

        completed = 0
        failed = 0
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(
                    run_point,
                    region,
                    mass,
                    r_range,
                    folder_template,
                    plot_dir,
                    args.asimov,
                    args.expectSignal,
                    args.envelope_scan,
                    args.breakdown,
                    era,
                ): (region, mass)
                for region, mass, r_range in points
            }
            for future in as_completed(futures):
                region, mass = futures[future]
                try:
                    success, msg = future.result()
                    if success:
                        completed += 1
                        print(f"[{completed + failed}/{len(points)}] {msg}")
                    else:
                        failed += 1
                        print(f"[{completed + failed}/{len(points)}] {msg}")
                except Exception as e:
                    failed += 1
                    era_str = f" [{era}]" if era else ""
                    print(f"[{completed + failed}/{len(points)}] EXCEPTION: {region} M{mass}{era_str}: {e}")

        print("\n" + "=" * 80)
        era_title = f" ({era})" if era else ""
        print(f"NLL SCANS COMPLETE{era_title}: {completed} succeeded, {failed} failed")
        print("=" * 80)

        if failed > 0:
            raise SystemExit(1)


if __name__ == "__main__":
    main()