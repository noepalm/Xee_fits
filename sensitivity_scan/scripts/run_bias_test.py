#!/usr/bin/env python3

import argparse
import glob
import os
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path


# ============================================================================
# Configuration and utilities
# ============================================================================


def get_category_label(cat_name):
    mapping = {
        "etaHigh": "etap0p6",
        "etaLow": "etam0p6",
        "dRHigh": "dRp0p3",
        "dRLow": "dRm0p3",
        "inclusive": "inclusive",
    }
    return mapping.get(cat_name, "unknown")


def get_category_name(cat_id):
    mapping = {
        0: "etaHigh",
        1: "etaLow",
        2: "dRHigh",
        3: "dRLow",
        4: "inclusive",
    }
    return mapping.get(cat_id, "unknown")


def get_all_category_ids(category_type):
    if category_type == "eta":
        return [0, 1]
    if category_type == "dR":
        return [2, 3]
    if category_type == "inclusive":
        return [4]
    return []


def get_mass_range(region):
    # ranges = {
    #     "region0": {"min": 0.3, "min_limit": 0.5, "max": 2.4, "max_limit": 2.2},
    #     "region1": {"min": 1.6, "min_limit": 1.8, "max": 4.6, "max_limit": 4.4},
    #     "region2": {"min": 3.8, "min_limit": 4.0, "max": 11.0, "max_limit": 10.8},
    # }
    # ranges = {
    #     "region0": {"min": 0.3, "min_limit": 0.5, "max": 2.4, "max_limit": 2.2},
    #     "region1": {"min": 1.6, "min_limit": 1.8, "max": 6.0, "max_limit": 5.6},
    #     "region2": {"min": 4.9, "min_limit": 5.4, "max": 10.5, "max_limit": 10},
    # }
    ranges = {
        "region0": {"min": 0.3, "min_limit": 0.5, "max": 2.4, "max_limit": 2.2},
        "region1": {"min": 1.6, "min_limit": 1.8, "max": 5.3, "max_limit": 4.9},
        "region2": {"min": 4.5, "min_limit": 4.9, "max": 10.5, "max_limit": 10},
    }
    return ranges.get(region, {})


def format_duration(seconds):
    total = int(round(seconds))
    hours, rem = divmod(total, 3600)
    minutes, secs = divmod(rem, 60)
    return f"{hours}:{minutes:02d}:{secs:02d}"


def get_run_mode_label(expect_signal):
    """Return run label used in output folders and filenames."""
    if abs(float(expect_signal)) <= 1e-12:
        return "no_signal"
    if expect_signal < 1:
        return f"signal_injected_mu{float(expect_signal):.2f}"
    else:        
        return f"signal_injected_mu{float(expect_signal):.0f}"


LOG_MAX_BYTES = 800 * 1024


def write_log_with_tail(path, text, max_bytes=LOG_MAX_BYTES):
    """Write log text, keeping only tail when it exceeds max_bytes."""
    data = text.encode("utf-8", errors="replace")
    if len(data) <= max_bytes:
        with open(path, "wb") as f:
            f.write(data)
        return

    prefix = b"[... log trimmed; showing tail only ...]\n"
    tail_budget = max(0, max_bytes - len(prefix))
    tail = data[-tail_budget:] if tail_budget > 0 else b""
    with open(path, "wb") as f:
        f.write(prefix + tail)


def trim_file_to_tail(path, max_bytes=LOG_MAX_BYTES):
    """Trim an existing log file in-place to tail when it exceeds max_bytes."""
    if not os.path.exists(path):
        return
    size = os.path.getsize(path)
    if size <= max_bytes:
        return

    prefix = b"[... log trimmed; showing tail only ...]\n"
    tail_budget = max(0, max_bytes - len(prefix))
    with open(path, "rb") as f:
        if tail_budget > 0:
            f.seek(-tail_budget, os.SEEK_END)
            tail = f.read()
        else:
            tail = b""

    with open(path, "wb") as f:
        f.write(prefix + tail)


def parse_mass_selector(selector):
    """Parse mass selection syntax.

    Supported syntax:
      - "min:max" for an inclusive mass range
      - "m1,m2,m3" for an explicit list of mass points
      - "m" for a single mass point
    """
    if not selector:
        return None

    s = selector.strip()
    if not s:
        return None

    if ":" in s:
        parts = [p.strip() for p in s.split(":")]
        if len(parts) != 2 or not parts[0] or not parts[1]:
            raise ValueError(f"Invalid mass range syntax: '{selector}'. Expected 'min:max'.")
        m_min = float(parts[0])
        m_max = float(parts[1])
        if m_min > m_max:
            m_min, m_max = m_max, m_min
        return {
            "mode": "range",
            "min": m_min,
            "max": m_max,
        }

    if "," in s:
        values = [v.strip() for v in s.split(",") if v.strip()]
        if not values:
            raise ValueError(f"Invalid mass list syntax: '{selector}'.")
        points = sorted({float(v) for v in values})
        return {
            "mode": "list",
            "points": points,
        }

    return {
        "mode": "list",
        "points": [float(s)],
    }


def mass_is_selected(mass, selector):
    """Return True if mass passes the optional selector."""
    if not selector:
        return True

    if selector["mode"] == "range":
        return selector["min"] <= mass <= selector["max"]

    eps = 1e-6
    return any(abs(mass - p) < eps for p in selector["points"])


def make_mass_key(mass):
    """Stable string key for mass-point dictionary lookups."""
    return f"{float(mass):.12g}"


# Background function index → name mapping (matches combine pdf_index parameter).
BKG_FUNCTION_NAMES = {0: "chebyshev", 1: "bernstein", 2: "polyexp"}
BKG_FUNCTION_LABELS = {"chebyshev": "Chebyshev", "bernstein": "Bernstein", "polyexp": "PolyExp"}
# BKG_FUNCTION_NAMES = {0: "chebyshev", 1: "bernstein"}
# BKG_FUNCTION_LABELS = {"chebyshev": "Chebyshev", "bernstein": "Bernstein"}


def resolve_fit_specific_workspace(workdir, root_file, fit_name):
        """Resolve fit-specific workspace path from sibling altbkg card folders.

        Example mapping for a workdir under cards_*_envelope_.../ee/<mass>:
            fit_name='bernstein' -> cards_*_altbkg_bernstein_.../ee/<mass>/<root_file>

        Returns absolute path to the fit-specific root file, or None if not resolvable.
        """
        mass_dir = Path(workdir).resolve()
        ee_dir = mass_dir.parent
        cards_dir = ee_dir.parent
        cards_name = cards_dir.name
        token = "_envelope_"
        if token not in cards_name:
                return None

        fit_cards_name = cards_name.replace(token, f"_altbkg_{fit_name}_")
        fit_cards_dir = cards_dir.parent / fit_cards_name
        fit_root = fit_cards_dir / "ee" / mass_dir.name / root_file
        return str(fit_root.resolve())


def is_sb_job_fully_cached(job):
    """Check if all S+B fit outputs already exist for this job.
    
    Returns True only if all truth/fit combinations have cached results.
    """
    if not job.get("caching", True):
        return False
    
    cat_name = job["cat_name"]
    era = job["era"]
    mass = job["mass"]
    fit_tag_label = job["fit_tag_label"]
    outfolder = job["outfolder"]
    expect_signal = float(job.get("expect_signal", 0.0))
    run_mode_label = get_run_mode_label(expect_signal)
    
    dest_mass_dir = Path(outfolder) / f"{cat_name}_{era}" / run_mode_label / f"M{mass}"
    
    # Check if all truth/fit combinations have output files
    for truth_idx, truth_name in BKG_FUNCTION_NAMES.items():
        truth_label = BKG_FUNCTION_LABELS[truth_name]
        for fit_idx, fit_name in BKG_FUNCTION_NAMES.items():
            fit_label = BKG_FUNCTION_LABELS[fit_name]
            n_label = f".bias_truth{truth_label}_fit{fit_label}_{cat_name}_{era}_{run_mode_label}_alt"
            combine_out = dest_mass_dir / f"higgsCombine{n_label}.FitDiagnostics.mH120.123456.root"
            fitdiag_out = dest_mass_dir / f"fitDiagnostics{n_label}.root"
            if not combine_out.exists() or not fitdiag_out.exists():
                return False
    
    return True


# ============================================================================
# Job execution
# ============================================================================

def run_bkg_fits_job(job):
    """Run B-only MultiDimFit for each background function (pdf_index 0-2).

    One job per (era, region, category). Workspace files are written to
    bkg_fits_dir (the ee/bkg_fits/ folder above the mass-point directories)
    so all mass points can use them in downstream steps.
    """
    workdir = str(Path(job["workdir"]).resolve())
    bkg_fits_dir = job["bkg_fits_dir"]
    txt_file = job["txt_file"]
    root_file = job["root_file"]
    cat_name = job["cat_name"]
    era = job["era"]
    region = job["region"]
    mass = job["mass"]
    min_mass = job["min_mass"]
    max_mass = job["max_mass"]
    fit_tag_label = job["fit_tag_label"]
    caching = job.get("caching", True)
    expect_signal = float(job.get("expect_signal", 0.0))
    mass_dependent = abs(expect_signal) > 1e-12
    run_mode_label = job.get("run_mode_label", "no_signal")
    job_log_path = os.path.join(workdir, f"bias_bkg_fits_{cat_name}{fit_tag_label}_{era}_{run_mode_label}.log")
    job_log_sections = []

    def capture_and_buffer(cmd, *, cwd=None):
        proc = subprocess.run(
            cmd,
            cwd=cwd,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        header = "=" * 80
        output = proc.stdout if proc.stdout is not None else ""
        section = f"{header}\nCMD: {' '.join(cmd)}\nRET: {proc.returncode}\n{header}\n{output}\n"
        job_log_sections.append(section)
        if proc.returncode != 0:
            raise subprocess.CalledProcessError(proc.returncode, cmd)

    def flush_and_copy_log():
        write_log_with_tail(job_log_path, "".join(job_log_sections))
        if os.path.exists(job_log_path) and not mass_dependent:
            shutil.copy2(job_log_path, bkg_fits_dir)

    if not mass_dependent:
        Path(bkg_fits_dir).mkdir(parents=True, exist_ok=True)

    # Build workspace from the chosen mass-point card.
    root_path = os.path.join(workdir, root_file)
    if not os.path.exists(root_path) and caching:
        try:
            capture_and_buffer(["text2workspace.py", txt_file], cwd=workdir)
        except subprocess.CalledProcessError:
            flush_and_copy_log()
            return (False, f"text2workspace failed for {cat_name} M{mass} ({era}, {region}); see {job_log_path}")
    else:
        job_log_sections.append(f"SKIP: workspace exists, not running text2workspace: {root_path}\n")

    # Run B-only MultiDimFit for pdf_index = 0, 1, 2.
    for pdf_idx, bkg_name in BKG_FUNCTION_NAMES.items():
        pdf_param = f"pdf_index_{era}_envelope"
        n_suffix = f"_{cat_name}{fit_tag_label}_{bkg_name}_{era}_Bonly"
        fit_log = os.path.join(
            workdir,
            f"fitMultiDimFit_Bonly_{cat_name}{fit_tag_label}_{bkg_name}_{era}_{run_mode_label}.log",
        )
        if mass_dependent:
            ws_dst = str(
                Path(workdir) / f"higgsCombine_{cat_name}{fit_tag_label}_{bkg_name}_{era}_Bonly.MultiDimFit.mH120.root"
            )
        else:
            ws_dst = str(
                Path(bkg_fits_dir) / f"higgsCombine_{cat_name}{fit_tag_label}_{bkg_name}_{era}_Bonly.MultiDimFit.mH120.root"
            )

        if caching and os.path.exists(ws_dst):
            job_log_sections.append(
                f"SKIP: cached B-only workspace exists for {bkg_name}: {ws_dst}\n"
            )
            continue

        cmd = [
            "combine", "-M", "MultiDimFit",
            root_file,
            "--saveWorkspace",
            "--setParameters", f"r=0,{pdf_param}={pdf_idx}",
            "--freezeParameters", f"r,{pdf_param}",
            "--setParameterRanges", f"mass={min_mass},{max_mass}",
            "--rMin", "-10",
            "--rMax", "10",
            "--cminDefaultMinimizerStrategy", "0",
            "--robustFit", "1",
            "-n", n_suffix,
            "-v", "3",  # increase to 3 for debugging
        ]

        try:
            with open(fit_log, "w") as f:
                subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, check=True, cwd=workdir)
            trim_file_to_tail(fit_log)
        except subprocess.CalledProcessError:
            trim_file_to_tail(fit_log)
            flush_and_copy_log()
            return (False, f"MultiDimFit B-only ({bkg_name}) failed for {cat_name} M{mass} ({era}, {region})")

        # Copy workspace and fit log to bkg_fits_dir for downstream access.
        # combine outputs higgsCombine<n_suffix>.MultiDimFit.mH120.root
        ws_src = os.path.join(workdir, f"higgsCombine{n_suffix}.MultiDimFit.mH120.root")
        if os.path.exists(ws_src) and os.path.abspath(ws_src) != os.path.abspath(ws_dst):
            shutil.copy2(ws_src, ws_dst)
        if os.path.exists(fit_log) and not mass_dependent:
            shutil.copy2(fit_log, bkg_fits_dir)

    flush_and_copy_log()
    return (True, f"OK: {cat_name} ({era}, {region})")

def run_generate_toys_job(job):
    """Generate toys from B-only snapshots for each true background function."""
    workdir = str(Path(job["workdir"]).resolve())
    bkg_fits_dir = str(Path(job["bkg_fits_dir"]).resolve())
    
    cat_name = job["cat_name"]
    era = job["era"]
    region = job["region"]
    mass = job["mass"]
    fit_tag_label = job["fit_tag_label"]
    n_toys = int(job.get("n_toys", 10))
    caching = job.get("caching", True)
    expect_signal = float(job.get("expect_signal", 0.0))
    mass_dependent = abs(expect_signal) > 1e-12
    run_mode_label = get_run_mode_label(expect_signal)

    toy_workdir = workdir if mass_dependent else bkg_fits_dir
    job_log = Path(toy_workdir) / f"generate_toys_{cat_name}{fit_tag_label}_{era}_{run_mode_label}.log"
    sections = []

    def capture_and_buffer(cmd, logger_suffix=""):
        proc = subprocess.run(
            cmd,
            cwd=toy_workdir,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        header = "=" * 80
        output = proc.stdout if proc.stdout is not None else ""
        sections.append(f"{header}\nCMD: {' '.join(cmd)}\nRET: {proc.returncode}\n{header}\n{output}\n")
        combine_logger = Path(toy_workdir) / "combine_logger.out"
        if combine_logger.exists():
            suffix = f"_{logger_suffix}" if logger_suffix else ""
            combine_logger_copy = Path(toy_workdir) / f"combine_logger_{cat_name}{fit_tag_label}_{era}_{run_mode_label}{suffix}.out"
            shutil.copy2(str(combine_logger), str(combine_logger_copy))
        if proc.returncode != 0:
            raise subprocess.CalledProcessError(proc.returncode, cmd)

    Path(toy_workdir).mkdir(parents=True, exist_ok=True)

    for bkg_name in BKG_FUNCTION_NAMES.values():
        ws_name = f"higgsCombine_{cat_name}{fit_tag_label}_{bkg_name}_{era}_Bonly.MultiDimFit.mH120.root"
        ws_dir = Path(workdir) if mass_dependent else Path(bkg_fits_dir)
        ws_path = ws_dir / ws_name
        if not ws_path.exists():
            write_log_with_tail(job_log, "".join(sections))
            return (False, f"Missing B-only workspace for toys: {ws_path}")

        truth_label = BKG_FUNCTION_LABELS[bkg_name]
        if mass_dependent:
            n_label = f".toys_true{truth_label}_{cat_name}_{era}_{run_mode_label}"
            toys_pattern = str(Path(toy_workdir) / f"higgsCombine{n_label}.GenerateOnly.mH120.*.root")
        else:
            n_label = f".toys_true{truth_label}_{cat_name}_{era}_{run_mode_label}"
            toys_pattern = str(Path(toy_workdir) / f"higgsCombine{n_label}.GenerateOnly.mH120.*.root")

        if caching and glob.glob(toys_pattern):
            if mass_dependent:
                sections.append(f"SKIP: cached toys exist for {truth_label} at M{mass}: {toys_pattern}\n")
            else:
                sections.append(f"SKIP: cached toys exist for {truth_label}: {toys_pattern}\n")
            continue

        if mass_dependent:
            print(f"Generating toys for truth background function: {truth_label} (M{mass}, {run_mode_label})")
        else:
            print(f"Generating toys for truth background function: {truth_label}")

        gen_cmd = [
            "combine",
            "-M", "GenerateOnly",
            str(ws_path),
            "-t", str(n_toys),
            "-n", n_label,
            "--expectSignal", str(expect_signal),
            "--saveToys",
            "--snapshotName", "MultiDimFit",
            "-v", "0",
        ]
        try:
            capture_and_buffer(gen_cmd, logger_suffix=f"truth{truth_label}")
        except subprocess.CalledProcessError:
            write_log_with_tail(job_log, "".join(sections))
            return (
                False,
                (
                    f"GenerateOnly failed for true {truth_label} ({cat_name}, {era}, {region}, M{mass}, {run_mode_label}); "
                    f"see {job_log}"
                ),
            )

    write_log_with_tail(job_log, "".join(sections))
    if mass_dependent:
        return (True, f"OK toys: {cat_name} ({era}, {region}, M{mass}, {run_mode_label})")
    return (True, f"OK toys: {cat_name} ({era}, {region})")


def run_sb_bias_fit_job(job):
    """Run S+B fits on toys for all truth/fit background combinations."""
    workdir = str(Path(job["workdir"]).resolve())
    bkg_fits_dir = str(Path(job["bkg_fits_dir"]).resolve())
    root_file = job["root_file"]
    cat_name = job["cat_name"]
    era = job["era"]
    region = job["region"]
    mass = job["mass"]
    fit_tag_label = job["fit_tag_label"]
    fit_toys = int(job["fit_toys"])
    outfolder = job["outfolder"]
    caching = job.get("caching", True)
    expect_signal = float(job.get("expect_signal", 0.0))
    mass_dependent = abs(expect_signal) > 1e-12
    single_toy_only = bool(job.get("single_toy_only", False))
    run_mode_label = get_run_mode_label(expect_signal)

    pdf_param = f"pdf_index_{era}_envelope"
    job_log = os.path.join(workdir, f"bias_sb_fits_{cat_name}{fit_tag_label}_{era}_{run_mode_label}.log")
    sections = []

    dest_mass_dir = Path(outfolder) / f"{cat_name}_{era}" / run_mode_label / f"M{mass}"
    dest_mass_dir.mkdir(parents=True, exist_ok=True)

    # Resolve generated toys files once, by truth model.
    toys_by_truth = {}
    for truth_name in BKG_FUNCTION_NAMES.values():
        truth_label = BKG_FUNCTION_LABELS[truth_name]
        if mass_dependent:
            pattern = os.path.join(
                workdir,
                f"higgsCombine.toys_true{truth_label}_{cat_name}_{era}_{run_mode_label}.GenerateOnly.mH120.*.root",
            )
        else:
            pattern = os.path.join(
                bkg_fits_dir,
                f"higgsCombine.toys_true{truth_label}_{cat_name}_{era}_{run_mode_label}.GenerateOnly.mH120.*.root",
            )
        candidates = sorted(glob.glob(pattern), key=os.path.getmtime, reverse=True)
        if not candidates:
            write_log_with_tail(job_log, "".join(sections))
            if mass_dependent:
                return (False, f"Missing toys file for truth {truth_label} in {workdir}")
            return (False, f"Missing toys file for truth {truth_label} in {bkg_fits_dir}")
        toys_by_truth[truth_name] = os.path.abspath(candidates[0])

    def capture_and_buffer(cmd, logger_suffix=""):
        proc = subprocess.run(
            cmd,
            cwd=workdir,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        header = "=" * 80
        output = proc.stdout if proc.stdout is not None else ""
        sections.append(f"{header}\nCMD: {' '.join(cmd)}\nRET: {proc.returncode}\n{header}\n{output}\n")
        combine_logger = Path(workdir) / "combine_logger.out"
        if combine_logger.exists():
            suffix = f"_{logger_suffix}" if logger_suffix else ""
            combine_logger_copy = Path(workdir) / f"combine_logger_{cat_name}{fit_tag_label}_{era}_{run_mode_label}{suffix}.out"
            shutil.copy2(str(combine_logger), str(combine_logger_copy))
        if proc.returncode != 0:
            raise subprocess.CalledProcessError(proc.returncode, cmd)

    files_to_copy = []
    for truth_idx, truth_name in BKG_FUNCTION_NAMES.items():
        truth_label = BKG_FUNCTION_LABELS[truth_name]
        toys_file = toys_by_truth[truth_name]

        for fit_idx, fit_name in BKG_FUNCTION_NAMES.items():
            fit_label = BKG_FUNCTION_LABELS[fit_name]
            fit_root_file = resolve_fit_specific_workspace(workdir, root_file, fit_name)
            if fit_root_file is None:
                write_log_with_tail(job_log, "".join(sections))
                return (
                    False,
                    (
                        f"Could not resolve fit-specific cards folder from workdir '{workdir}'. "
                        "Expected folder name containing '_altbkg_envelope_'."
                    ),
                )
            if not os.path.exists(fit_root_file):
                write_log_with_tail(job_log, "".join(sections))
                return (
                    False,
                    (
                        f"Missing fit-specific workspace for fit {fit_label}: {fit_root_file}"
                    ),
                )

            # Keep requested base naming, and append cat/era for collision safety.
            n_label = f".bias_truth{truth_label}_fit{fit_label}_{cat_name}_{era}_{run_mode_label}_alt"
            # r_min = -2 if run_mode_label == "no_signal" else -10
            # r_max = 2 if run_mode_label == "no_signal" else 10
            r_min = -10 if run_mode_label == "no_signal" else -10
            r_max = 10 if run_mode_label == "no_signal" else 10

            cmd = [
                "combine",
                "-M", "FitDiagnostics",
                fit_root_file,
                "--setParameters", f"{pdf_param}={fit_idx}",
                "--freezeParameters", pdf_param,
                "--rMin", str(r_min),
                "--rMax", str(r_max),
                "--robustFit", "1",
                "-t", str(fit_toys),
                "-n", n_label,
                "--toysFile", toys_file,
                "--cminDefaultMinimizerStrategy", "0",
                "--saveWorkspace",
                "--skipBOnlyFit",
                "-v", "1",
            ]

            out_name = f"higgsCombine{n_label}.FitDiagnostics.mH120.123456.root"
            out_path = os.path.join(workdir, out_name)
            out_dst = str(dest_mass_dir / out_name)
            fitdiag_name = f"fitDiagnostics{n_label}.root"
            fitdiag_path = os.path.join(workdir, fitdiag_name)
            fitdiag_dst = str(dest_mass_dir / fitdiag_name)

            n_label_toy = f".toyfit_truth{truth_label}_fit{fit_label}_{cat_name}_{era}_{run_mode_label}_alt"
            cmd_toy = [
                "combine",
                "-M", "FitDiagnostics",
                fit_root_file,
                "--setParameters", f"{pdf_param}={fit_idx}",
                "--freezeParameters", pdf_param,
                "--rMin", str(r_min),
                "--rMax", str(r_max),
                "-t", "1",
                "-n", n_label_toy,
                "--toysFile", toys_file,
                "--cminDefaultMinimizerStrategy", "0",
                "--robustFit", "1",
                "--saveWorkspace",
                "--saveShapes",
                "--saveNormalizations",
                "-v", "1",
            ]
            toy_out_name = f"higgsCombine{n_label_toy}.FitDiagnostics.mH120.123456.root"
            toy_out_path = os.path.join(workdir, toy_out_name)
            toy_out_dst = str(dest_mass_dir / toy_out_name)
            toy_fitdiag_name = f"fitDiagnostics{n_label_toy}.root"
            toy_fitdiag_path = os.path.join(workdir, toy_fitdiag_name)
            toy_fitdiag_dst = str(dest_mass_dir / toy_fitdiag_name)

            if not single_toy_only:
                if caching and os.path.exists(out_dst) and os.path.exists(fitdiag_dst):
                    sections.append(f"SKIP: cached S+B fit exists: {out_dst}\n")
                    files_to_copy.append(out_path)
                    files_to_copy.append(fitdiag_path)
                elif caching and os.path.exists(out_dst) and os.path.exists(fitdiag_path):
                    sections.append(
                        f"SKIP: combine output cached and local fitDiagnostics present; only copying fitDiagnostics: {fitdiag_path}\n"
                    )
                    files_to_copy.append(out_path)
                    files_to_copy.append(fitdiag_path)
                else:
                    try:
                        capture_and_buffer(cmd, logger_suffix=f"truth{truth_label}_fit{fit_label}")
                    except subprocess.CalledProcessError:
                        write_log_with_tail(job_log, "".join(sections))
                        return (
                            False,
                            (
                                f"S+B fit failed for truth {truth_label}, fit {fit_label}, "
                                f"{cat_name} M{mass} ({era}, {region}); see {job_log}"
                            ),
                        )

                    if os.path.exists(out_path):
                        files_to_copy.append(out_path)
                    if os.path.exists(fitdiag_path):
                        files_to_copy.append(fitdiag_path)

            # Always ensure the single-toy fit (with shapes) exists for toy-plotting.
            if caching and os.path.exists(toy_fitdiag_dst):
                sections.append(f"SKIP: cached toy-plot fit exists: {toy_fitdiag_dst}\n")
                files_to_copy.append(toy_fitdiag_path)
                files_to_copy.append(toy_out_path)
                continue

            if caching and os.path.exists(toy_fitdiag_path):
                sections.append(f"SKIP: local toy-plot fitDiagnostics exists; copying: {toy_fitdiag_path}\n")
                files_to_copy.append(toy_fitdiag_path)
                files_to_copy.append(toy_out_path)
                continue

            try:
                capture_and_buffer(cmd_toy, logger_suffix=f"toyplot_truth{truth_label}_fit{fit_label}")
            except subprocess.CalledProcessError:
                write_log_with_tail(job_log, "".join(sections))
                return (
                    False,
                    (
                        f"Toy-plot S+B fit failed for truth {truth_label}, fit {fit_label}, "
                        f"{cat_name} M{mass} ({era}, {region}); see {job_log}"
                    ),
                )

            if os.path.exists(toy_out_path):
                files_to_copy.append(toy_out_path)
            if os.path.exists(toy_fitdiag_path):
                files_to_copy.append(toy_fitdiag_path)

    write_log_with_tail(job_log, "".join(sections))

    if os.path.exists(job_log):
        shutil.copy2(job_log, str(dest_mass_dir))
    for src in files_to_copy:
        if os.path.exists(src):
            shutil.copy2(src, str(dest_mass_dir))

    mode_note = "single-toy" if single_toy_only else "full"
    return (True, f"OK sb-fits ({mode_note}): {cat_name} M{mass} ({era}, {region})")


# ============================================================================
# Main execution
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="Run FitDiagnostics in parallel with Python")
    parser.add_argument("--tag", default="", help="Tag appended to input/output folders")
    parser.add_argument("--fit_tag", default="", help="Tag appended to output filenames only")
    parser.add_argument("--folder_tag", default="", help="Folder tag for input directory")
    parser.add_argument("--category", "--cat", default="eta", choices=["eta", "dR", "inclusive"])
    parser.add_argument(
        "--regions",
        nargs="+",
        default=[],
        choices=["region0", "region1", "region2"],
        help="One or more regions to process",
    )
    parser.add_argument("--region", dest="regions", action="append", help="Deprecated: use --regions instead")
    parser.add_argument("--no_reweight", action="store_true", help="Do not use reweighting")
    parser.add_argument("--plot_only", action="store_true", help="Only generate plots")
    parser.add_argument("--data", action="store_true", help="Run on data instead of MC")
    parser.add_argument("--binned", action="store_true", help="Use binned datasets")
    parser.add_argument("--no_res", action="store_true", help="Exclude resonant backgrounds")
    parser.add_argument(
        "--eras",
        nargs="+",
        default=[],
        choices=["2022", "2022EE", "2023", "2023BPix"],
        help="One or more eras to process",
    )
    parser.add_argument("--era", dest="eras", action="append", help="Deprecated: use --eras instead")
    parser.add_argument("--jobs", type=int, default=8, help="Number of parallel jobs")
    parser.add_argument("--no_caching", action="store_false", dest="caching", help="Disable caching")
    parser.add_argument(
        "--expectSignal",
        type=float,
        default=0.0,
        help="Signal strength injected during toy generation",
    )
    parser.add_argument(
        "--n_toys",
        "--ntoys",
        type=int,
        default=10,
        help="Number of toys per true background function",
    )
    parser.add_argument(
        "--mass_selector",
        default="",
        help=(
            "Optional mass selector: 'min:max' for range, or 'm1,m2,m3' for explicit points "
            "(single value 'm' is also accepted). Only selected masses are queued."
        ),
    )

    args = parser.parse_args()
    run_start = time.perf_counter()
    phase_durations = {}

    try:
        mass_selector = parse_mass_selector(args.mass_selector)
    except ValueError as e:
        print(f"ERROR: {e}")
        return 2

    if args.regions:
        regions = [r for r in args.regions if r in ["region0", "region1", "region2"]]
    else:
        regions = ["region1"]

    if args.eras:
        eras = [e for e in args.eras if e in ["2022", "2022EE", "2023", "2023BPix"]]
    else:
        eras = ["2023"]

    # Preserve the original input naming logic used in run_diagnostics_parallel.sh.
    # INPUT_FOLDER starts at cards/{folder_tag}cards_{region}, then optionally appends
    # _noReweight, _data, and _{tag} in that order.
    folder_path = f"{args.folder_tag}/" if args.folder_tag else ""
    fit_tag_label = f"_{args.fit_tag}" if args.fit_tag else ""
    run_mode_label = get_run_mode_label(args.expectSignal)
    basedir = os.getcwd()

    print("=" * 80)
    print("GLOBAL CONFIGURATION")
    print("=" * 80)
    print(f"  Use data: {args.data}")
    print(f"  Using binned datasets: {args.binned}")
    print(f"  Use reweighting: {not args.no_reweight}")
    print(f"  Tag: {args.tag if args.tag else '(none)'}")
    print(f"  Fit tag: {args.fit_tag if args.fit_tag else '(none)'}")
    print(f"  Eras: {', '.join(eras)}")
    print(f"  Regions: {', '.join(regions)}")
    print(f"  Category type: {args.category}")
    print(f"  Categories: {get_all_category_ids(args.category)}")
    print(f"  Plot only: {args.plot_only}")
    print(f"  Exclude resonant backgrounds: {args.no_res}")
    print(f"  Caching enabled: {args.caching}")
    print(f"  Injected signal strength: {args.expectSignal}")
    print(f"  Toys per true function: {args.n_toys}")
    if mass_selector:
        if mass_selector["mode"] == "range":
            print(f"  Mass selection: range [{mass_selector['min']}, {mass_selector['max']}]")
        else:
            print(f"  Mass selection: explicit points {mass_selector['points']}")
    else:
        print("  Mass selection: full region range")
    print(f"  Parallel jobs: {args.jobs}")
    print(f"  Total (era,region) combinations: {len(eras) * len(regions)}")

    configs = []
    for era in eras:
        for region in regions:
            input_folder = f"cards/{folder_path}cards_{region}"
            if args.no_reweight:
                input_folder += "_noReweight"
            if args.data:
                input_folder += "_data"
            if args.tag:
                input_folder += f"_{args.tag}"

            outfolder = f"/eos/home-n/npalmeri/www/DiElectron/sensitivity/{folder_path}fitDiagnostics_grid"
            if args.data:
                outfolder += "_data"
            elif not args.no_reweight:
                outfolder += "_reweight_categories"
            else:
                outfolder += "_noReweight"
            if args.tag:
                outfolder += f"_{args.tag}"
            outfolder += "/bias_test"

            config = {
                "era": era,
                "region": region,
                "input_folder": input_folder,
                "outfolder": outfolder,
            }
            configs.append(config)
            print(f"Config {len(configs)}: era={era}, region={region}")
            print(f"  Input:  {input_folder}")
            print(f"  Output: {outfolder}")

    for config in configs:
        outfolder = config["outfolder"]
        era = config["era"]
        for cat_id in get_all_category_ids(args.category):
            cat_name = get_category_name(cat_id)
            Path(outfolder, f"{cat_name}_{era}").mkdir(parents=True, exist_ok=True)

    def run_plot_phase():
        def pick_representative_masses(mass_values, n_points=5):
            """Pick approximately evenly spaced masses from a sorted list."""
            if len(mass_values) <= n_points:
                return mass_values
            if n_points <= 1:
                return [mass_values[len(mass_values) // 2]]
            idxs = sorted({round(i * (len(mass_values) - 1) / (n_points - 1)) for i in range(n_points)})
            return [mass_values[i] for i in idxs]

        def latest_match(pattern):
            matches = sorted(glob.glob(pattern), key=os.path.getmtime, reverse=True)
            return matches[0] if matches else None

        print("\n" + "=" * 80)
        print("PHASE 5: Generating bias summary, B-only overlays, and toy+S+B plots")
        print("=" * 80 + "\n")
        phase5_start = time.perf_counter()

        era_to_outfolder = {}
        for cfg in configs:
            era_to_outfolder.setdefault(cfg["era"], cfg["outfolder"])

        for era in eras:
            outfolder = era_to_outfolder[era]
            print(f"Plotting summaries for era {era} and regions {regions}")
            for cat_id in get_all_category_ids(args.category):
                cat_name = get_category_name(cat_id)
                cat_out = f"{outfolder}/{cat_name}_{era}/{run_mode_label}"
                Path(cat_out).mkdir(parents=True, exist_ok=True)
                plot_cmd = [
                    "python3",
                    f"{basedir}/scripts/utilities/plot_bias_test_result.py",
                    "-i", cat_out,
                    "-o", cat_out,
                    "-c", cat_name,
                    "--era", era,
                    "--nominal_r", str(args.expectSignal),
                    "-r",
                ] + regions

                if args.fit_tag:
                    plot_cmd.extend(["--tag", args.fit_tag])

                log_path = f"{cat_out}/bias_summary_{'_'.join(regions)}{fit_tag_label}.log"
                with open(log_path, "w") as f:
                    subprocess.run(plot_cmd, stdout=f, stderr=subprocess.STDOUT)

        # B-only overlay plots are region-specific and use ee/bkg_fits workspaces.
        for cfg in configs:
            era = cfg["era"]
            region = cfg["region"]
            input_folder = cfg["input_folder"]
            outfolder = cfg["outfolder"]
            bkg_fits_dir = str((Path(input_folder) / "ee" / "bkg_fits").resolve())
            ee_input_dir = (Path(input_folder) / "ee").resolve()

            for cat_id in get_all_category_ids(args.category):
                cat_name = get_category_name(cat_id)
                cat_out = f"{outfolder}/{cat_name}_{era}/{run_mode_label}"
                Path(cat_out).mkdir(parents=True, exist_ok=True)

                overlay_cmd = [
                    "python3",
                    f"{basedir}/scripts/utilities/plot_bonly_overlay.py",
                    "-i", bkg_fits_dir,
                    "-o", cat_out,
                    "-c", cat_name,
                    "--era", era,
                    "-r", region,
                ]
                if args.fit_tag:
                    overlay_cmd.extend(["--tag", args.fit_tag])

                overlay_log = f"{cat_out}/bonly_overlay_{region}{fit_tag_label}.log"
                with open(overlay_log, "w") as f:
                    subprocess.run(overlay_cmd, stdout=f, stderr=subprocess.STDOUT)

        # Toy + S+B fit plots for representative masses
        for cfg in configs:
            era = cfg["era"]
            region = cfg["region"]
            input_folder = cfg["input_folder"]
            outfolder = cfg["outfolder"]
            bkg_fits_dir = str((Path(input_folder) / "ee" / "bkg_fits").resolve())

            for cat_id in get_all_category_ids(args.category):
                cat_name = get_category_name(cat_id)
                cat_out = f"{outfolder}/{cat_name}_{era}/{run_mode_label}/toy_fits"
                cat_out_path = Path(cat_out)

                # make output folder if it does not exist
                if not cat_out_path.exists():
                    print(f"Creating output folder for toy+fit plots: {cat_out}")
                    cat_out_path.mkdir(parents=True, exist_ok=True)

                # Get mass directories from input cards folder
                ee_input_dir = Path(input_folder) / "ee"
                input_mass_dirs = [d for d in ee_input_dir.iterdir() if d.is_dir() and d.name.replace(".", "").replace("-", "").isdigit()]
                input_mass_dirs = sorted(input_mass_dirs, key=lambda d: float(d.name))
                
                mass_pairs = []
                region_range = get_mass_range(region)
                for d in input_mass_dirs:
                    try:
                        mval = float(d.name)
                        if mval < region_range["min_limit"] or mval > region_range["max_limit"]:
                            continue
                        mass_pairs.append((mval, d))
                    except ValueError:
                        continue
                mass_pairs.sort(key=lambda x: x[0])
                selected_masses = pick_representative_masses([m for m, _ in mass_pairs], n_points=7)

                selected_txt = cat_out_path / f"toy_fit_selected_masses_{region}{fit_tag_label}.txt"
                with open(selected_txt, "w") as sf:
                    sf.write(f"Run mode: {run_mode_label}\n")
                    sf.write(f"Category: {cat_name}\n")
                    sf.write(f"Era: {era}\n")
                    sf.write(f"Region: {region}\n")
                    sf.write("Selected masses for toy+fit plotting:\n")
                    for m in selected_masses:
                        sf.write(f"  - M{m:g}\n")

                if selected_masses:
                    print(
                        f"Toy+fit example masses for {cat_name} {era} {region} ({run_mode_label}): "
                        + ", ".join([f"M{m:g}" for m in selected_masses])
                    )
                    print(f"Saved mass-point selection to: {selected_txt}")
                else:
                    print(f"No mass points found for toy+fit plotting in {cat_out_path}")

                for sel_mass in selected_masses:
                    mass_str = f"{sel_mass:g}"

                    # Build output mass directory path for S+B fit results
                    mass_dir = Path(outfolder) / f"{cat_name}_{era}" / run_mode_label / f"M{mass_str}"

                    local_mass_dir = None
                    for d in ee_input_dir.iterdir():
                        if not d.is_dir():
                            continue
                        try:
                            d_mass = float(d.name)
                        except ValueError:
                            continue
                        if abs(d_mass - sel_mass) < 1e-9:
                            local_mass_dir = d
                            break
                    if local_mass_dir is None:
                        print(f"WARNING: Could not find local mass directory for M{mass_str} in {ee_input_dir}; skipping toy+fit plots for this mass point.")
                        continue

                    for truth_name in BKG_FUNCTION_NAMES.values():
                        truth_label = BKG_FUNCTION_LABELS[truth_name]

                        if abs(args.expectSignal) > 1e-12:
                            toy_pattern = str(
                                local_mass_dir
                                / f"higgsCombine.toys_true{truth_label}_{cat_name}_{era}_{run_mode_label}.GenerateOnly.mH120.*.root"
                            )
                        else:
                            toy_pattern = str(
                                Path(bkg_fits_dir)
                                / f"higgsCombine.toys_true{truth_label}_{cat_name}_{era}_{run_mode_label}.GenerateOnly.mH120.*.root"
                            )

                        toy_file = latest_match(toy_pattern)
                        if toy_file is None:
                            continue

                        sb_files = []
                        missing_inputs = False
                        missing_details = []
                        for fit_name in BKG_FUNCTION_NAMES.values():
                            fit_label = BKG_FUNCTION_LABELS[fit_name]
                            sb_file = (
                                local_mass_dir
                                / (
                                    f"fitDiagnostics.toyfit_truth{truth_label}_fit{fit_label}_{cat_name}_{era}_{run_mode_label}_alt.root"
                                )
                            )
                            if not sb_file.exists():
                                missing_details.append(f"missing SB file: {sb_file}")
                                missing_inputs = True
                            if missing_inputs:
                                break
                            sb_files.append(str(sb_file))

                        if missing_inputs:
                            continue

                        # print("DEBUG: for region", region, ", mass ", mass_str, ": toy files = ", toy_file, "SB files = ", sb_files)

                        toy_plot_cmd = [
                            "python3",
                            f"{basedir}/scripts/utilities/plot_toy_fit.py",
                            "--toy-file", str(toy_file),
                            "--sb-files",
                        ] + sb_files + [
                            "--fit-labels", "Chebyshev", "Bernstein", "PolyExp",
                            "--toy-index", "0",
                            "--category", cat_name,
                            "--era", era,
                            "--region", region,
                            "--mass", mass_str,
                            "--truth-label", truth_label,
                            "--run-label", run_mode_label,
                            "-o", cat_out,
                        ]

                        if args.fit_tag:
                            toy_plot_cmd.extend(["--tag", args.fit_tag])

                        toy_plot_log = (
                            f"{cat_out}/toy_fit_{region}_M{mass_str}_truth{truth_label}_{run_mode_label}{fit_tag_label}.log"
                        )
                        proc = subprocess.run(
                            toy_plot_cmd,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT,
                            text=True,
                        )
                        output_text = proc.stdout if proc.stdout is not None else ""
                        with open(toy_plot_log, "w") as f:
                            f.write(output_text)

                        if proc.returncode == 0:
                            print(
                                f"Saved toy+fit plot for {cat_name} {era} {region} M{mass_str} truth {truth_label} "
                                f"under {cat_out}"
                            )
                        else:
                            print(
                                f"Toy+fit plotting failed for {cat_name} {era} {region} M{mass_str} truth {truth_label}; "
                                f"see {toy_plot_log}"
                            )

        phase_durations["phase5_plots"] = time.perf_counter() - phase5_start
        print(f"PHASE 5 elapsed: {format_duration(phase_durations['phase5_plots'])}")

    if args.plot_only:
        print("Plot-only mode: skipping fit/toy phases")
        run_plot_phase()
        total_elapsed = time.perf_counter() - run_start
        print("\n" + "=" * 80)
        print("PLOTTING COMPLETE")
        print(f"  Total runtime: {format_duration(total_elapsed)}")
        print("=" * 80)
        return 0

    # ========================================================================
    # PHASE 1: Collect B-only fit jobs (one per era x region x category)
    # ========================================================================
    print("\n" + "=" * 80)
    print("PHASE 1: Collecting B-only fit jobs")
    print("=" * 80)
    phase1_start = time.perf_counter()

    all_jobs = []
    for config_idx, config in enumerate(configs, 1):
        era = config["era"]
        region = config["region"]
        input_folder = config["input_folder"]

        print(f"\n--- Processing config {config_idx}/{len(configs)}: {era}, {region} ---")
        ee_dir = Path(input_folder) / "ee"
        if not ee_dir.exists():
            print(f"  WARNING: Input directory does not exist: {ee_dir}")
            continue

        # bkg_fits_dir lives at the ee/ level so all mass points can access it.
        bkg_fits_dir = str((ee_dir / "bkg_fits").resolve())

        mass_range = get_mass_range(region)
        mass_dirs = [d for d in ee_dir.iterdir() if d.is_dir() and d.name.replace(".", "").replace("-", "").isdigit()]
        mass_dirs = sorted(mass_dirs, key=lambda d: float(d.name))
        print(f"  Found {len(mass_dirs)} mass directories")

        jobs_before = len(all_jobs)
        if abs(args.expectSignal) > 1e-12:
            # In signal-injected mode, B-only snapshots must be produced per mass point.
            for cat_id in get_all_category_ids(args.category):
                cat_name = get_category_name(cat_id)
                txt_file = f"Xee_ee_{cat_id}_{era}.txt"
                root_file = txt_file.replace(".txt", ".root")

                added_for_cat = 0
                for mass_dir in mass_dirs:
                    mass = float(mass_dir.name)
                    if mass < mass_range["min_limit"] or mass > mass_range["max_limit"]:
                        continue
                    if not mass_is_selected(mass, mass_selector):
                        continue
                    if not (mass_dir / txt_file).exists():
                        continue

                    all_jobs.append({
                        "workdir": str(mass_dir.resolve()),
                        "bkg_fits_dir": bkg_fits_dir,
                        "txt_file": txt_file,
                        "root_file": root_file,
                        "cat_id": cat_id,
                        "cat_name": cat_name,
                        "era": era,
                        "region": region,
                        "mass": mass,
                        "min_mass": mass_range["min"],
                        "max_mass": mass_range["max"],
                        "fit_tag_label": fit_tag_label,
                        "run_mode_label": run_mode_label,
                        "n_toys": args.n_toys,
                        "caching": args.caching,
                        "expect_signal": args.expectSignal,
                    })
                    added_for_cat += 1

                if added_for_cat == 0:
                    print(f"  WARNING: No valid mass points found for {cat_name} ({era}, {region})")

            print(
                f"  Injected mode: added {len(all_jobs) - jobs_before} mass-dependent jobs from this config"
            )
        else:
            for cat_id in get_all_category_ids(args.category):
                cat_name = get_category_name(cat_id)
                txt_file = f"Xee_ee_{cat_id}_{era}.txt"
                root_file = txt_file.replace(".txt", ".root")

                # Pick the first valid mass point that has the required card.
                # The B-only fit is mass-independent; any point works.
                chosen_dir = None
                chosen_mass = None
                for mass_dir in mass_dirs:
                    mass = float(mass_dir.name)
                    if mass < mass_range["min_limit"] or mass > mass_range["max_limit"]:
                        continue
                    if not mass_is_selected(mass, mass_selector):
                        continue
                    if (mass_dir / txt_file).exists():
                        chosen_dir = mass_dir
                        chosen_mass = mass
                        break

                if chosen_dir is None:
                    print(f"  WARNING: No valid mass point found for {cat_name} ({era}, {region})")
                    continue

                print(f"  Using M{chosen_mass} for {cat_name}")
                all_jobs.append({
                    "workdir": str(chosen_dir.resolve()),
                    "bkg_fits_dir": bkg_fits_dir,
                    "txt_file": txt_file,
                    "root_file": root_file,
                    "cat_id": cat_id,
                    "cat_name": cat_name,
                    "era": era,
                    "region": region,
                    "mass": chosen_mass,
                    "min_mass": mass_range["min"],
                    "max_mass": mass_range["max"],
                    "fit_tag_label": fit_tag_label,
                    "run_mode_label": run_mode_label,
                    "n_toys": args.n_toys,
                    "caching": args.caching,
                    "expect_signal": args.expectSignal,
                })

            print(f"  Added {len(all_jobs) - jobs_before} jobs from this config")

    phase_durations["phase1_collect"] = time.perf_counter() - phase1_start
    print(f"PHASE 1 elapsed: {format_duration(phase_durations['phase1_collect'])}")

    if not all_jobs: 
        print("No diagnostics jobs to run!")
        return 0

    # ========================================================================
    # PHASE 2: Run B-only fits (3 background functions) in parallel
    # ========================================================================
    print("\n" + "=" * 80)
    print(f"PHASE 2: Running {len(all_jobs)} jobs ({len(BKG_FUNCTION_NAMES)} bkg functions each) on {args.jobs} workers")
    print("=" * 80 + "\n")
    phase2_start = time.perf_counter()

    completed = 0
    failed = 0
    successful_jobs = []

    with ThreadPoolExecutor(max_workers=args.jobs) as executor:
        futures = {executor.submit(run_bkg_fits_job, job): job for job in all_jobs}
        for future in as_completed(futures):
            job = futures[future]
            try:
                success, msg = future.result()
                if success:
                    completed += 1
                    successful_jobs.append(job)
                    if completed % 10 == 0:
                        print(f"Progress: {completed} completed, {failed} failed (of {len(all_jobs)})")
                else:
                    failed += 1
                    print(f"FAILED: {msg}")
            except Exception as e:
                failed += 1
                print(
                    f"EXCEPTION: {job['cat_name']} M{job['mass']} ({job['era']}, {job['region']}): {e}"
                )

    print(f"\nB-only fits complete: {completed} completed, {failed} failed")
    phase_durations["phase2_bkg_fits"] = time.perf_counter() - phase2_start
    print(f"PHASE 2 elapsed: {format_duration(phase_durations['phase2_bkg_fits'])}")

    # ========================================================================
    # PHASE 3: Produce toys for each true background function
    # ========================================================================
    print("\n" + "=" * 80)
    if abs(args.expectSignal) > 1e-12:
        print("PHASE 3: Generating toys (mass-dependent for injected signal)")
    else:
        print("PHASE 3: Generating toys (fast shared mode, not mass-dependent)")
    print("=" * 80 + "\n")
    phase3_start = time.perf_counter()

    # Build a fast lookup of successful (era, region, category) jobs from Phase 2.
    if abs(args.expectSignal) > 1e-12:
        successful_lookup = {
            (job["era"], job["region"], job["cat_name"], make_mass_key(job["mass"])): job
            for job in successful_jobs
        }
    else:
        successful_lookup = {
            (job["era"], job["region"], job["cat_name"]): job
            for job in successful_jobs
        }

    toy_jobs = []
    if abs(args.expectSignal) > 1e-12:
        for config_idx, config in enumerate(configs, 1):
            era = config["era"]
            region = config["region"]
            input_folder = config["input_folder"]

            print(f"Collecting toy jobs for config {config_idx}/{len(configs)}: {era}, {region}")
            ee_dir = Path(input_folder) / "ee"
            if not ee_dir.exists():
                print(f"  WARNING: Input directory does not exist: {ee_dir}")
                continue

            mass_range = get_mass_range(region)
            mass_dirs = [d for d in ee_dir.iterdir() if d.is_dir() and d.name.replace(".", "").replace("-", "").isdigit()]
            mass_dirs = sorted(mass_dirs, key=lambda d: float(d.name))

            for mass_dir in mass_dirs:
                mass = float(mass_dir.name)
                if mass < mass_range["min_limit"] or mass > mass_range["max_limit"]:
                    continue
                if not mass_is_selected(mass, mass_selector):
                    continue

                for cat_id in get_all_category_ids(args.category):
                    cat_name = get_category_name(cat_id)
                    key = (era, region, cat_name, make_mass_key(mass))
                    if key not in successful_lookup:
                        continue

                    seed_job = successful_lookup[key]
                    toy_jobs.append(
                        {
                            "workdir": str(mass_dir.resolve()),
                            "bkg_fits_dir": seed_job["bkg_fits_dir"],
                            "cat_name": cat_name,
                            "era": era,
                            "region": region,
                            "mass": mass,
                            "fit_tag_label": fit_tag_label,
                            "n_toys": args.n_toys,
                            "caching": args.caching,
                            "expect_signal": args.expectSignal,
                        }
                    )
    else:
        for job in successful_jobs:
            toy_jobs.append(
                {
                    "workdir": job["workdir"],
                    "bkg_fits_dir": job["bkg_fits_dir"],
                    "cat_name": job["cat_name"],
                    "era": job["era"],
                    "region": job["region"],
                    "mass": job["mass"],
                    "fit_tag_label": fit_tag_label,
                    "n_toys": args.n_toys,
                    "caching": args.caching,
                    "expect_signal": args.expectSignal,
                }
            )

    print(f"Total toy jobs queued: {len(toy_jobs)} ({args.n_toys} toys per truth model, mu={args.expectSignal})")

    toys_completed = 0
    toys_failed = 0

    with ThreadPoolExecutor(max_workers=args.jobs) as executor:
        futures = {executor.submit(run_generate_toys_job, job): job for job in toy_jobs}
        for future in as_completed(futures):
            job = futures[future]
            try:
                success, msg = future.result()
                if success:
                    toys_completed += 1
                    if toys_completed % 10 == 0:
                        print(
                            f"Toys progress: {toys_completed} completed, {toys_failed} failed (of {len(toy_jobs)})"
                        )
                else:
                    toys_failed += 1
                    print(f"FAILED: {msg}")
            except Exception as e:
                toys_failed += 1
                print(
                    f"EXCEPTION: toys {job['cat_name']} ({job['era']}, {job['region']}): {e}"
                )

    print(f"\nToy generation complete: {toys_completed} completed, {toys_failed} failed")
    phase_durations["phase3_toys"] = time.perf_counter() - phase3_start
    print(f"PHASE 3 elapsed: {format_duration(phase_durations['phase3_toys'])}")

    # ========================================================================
    # PHASE 4: S+B fit with all truth/fit background function combinations
    # ========================================================================
    print("\n" + "=" * 80)
    print("PHASE 4: Running S+B fits on toys (mass-dependent)")
    print("=" * 80 + "\n")
    phase4_start = time.perf_counter()

    sb_jobs = []
    for config_idx, config in enumerate(configs, 1):
        era = config["era"]
        region = config["region"]
        input_folder = config["input_folder"]
        outfolder = config["outfolder"]

        print(f"Collecting S+B jobs for config {config_idx}/{len(configs)}: {era}, {region}")
        ee_dir = Path(input_folder) / "ee"
        if not ee_dir.exists():
            print(f"  WARNING: Input directory does not exist: {ee_dir}")
            continue

        mass_range = get_mass_range(region)
        mass_dirs = [d for d in ee_dir.iterdir() if d.is_dir() and d.name.replace(".", "").replace("-", "").isdigit()]
        mass_dirs = sorted(mass_dirs, key=lambda d: float(d.name))

        for mass_dir in mass_dirs:
            mass = float(mass_dir.name)
            if mass < mass_range["min_limit"] or mass > mass_range["max_limit"]:
                continue
            if not mass_is_selected(mass, mass_selector):
                continue

            for cat_id in get_all_category_ids(args.category):
                cat_name = get_category_name(cat_id)
                if abs(args.expectSignal) > 1e-12:
                    key = (era, region, cat_name, make_mass_key(mass))
                else:
                    key = (era, region, cat_name)
                if key not in successful_lookup:
                    continue

                root_file = f"Xee_ee_{cat_id}_{era}.root"
                if not (mass_dir / root_file).exists():
                    continue

                seed_job = successful_lookup[key]
                sb_jobs.append(
                    {
                        "workdir": str(mass_dir.resolve()),
                        "bkg_fits_dir": seed_job["bkg_fits_dir"],
                        "root_file": root_file,
                        "cat_name": cat_name,
                        "era": era,
                        "region": region,
                        "mass": mass,
                        "fit_tag_label": fit_tag_label,
                        "fit_toys": args.n_toys,
                        "outfolder": outfolder,
                        "caching": args.caching,
                        "expect_signal": args.expectSignal,
                    }
                )

    print(f"Total S+B jobs queued: {len(sb_jobs)}")

    # Pre-check caching: separate jobs into cached and to_run
    sb_cached_jobs = []
    sb_jobs_to_run = []
    for job in sb_jobs:
        if is_sb_job_fully_cached(job):
            sb_cached_jobs.append(job)
        else:
            sb_jobs_to_run.append(job)

    if sb_cached_jobs:
        print(f"  {len(sb_cached_jobs)} jobs using cached results")
    if sb_jobs_to_run:
        print(f"  {len(sb_jobs_to_run)} jobs to compute")

    sb_completed = 0
    sb_failed = 0
    sb_cached = len(sb_cached_jobs)
    sb_toyplot_completed = 0
    sb_toyplot_failed = 0
    
    if sb_jobs_to_run:
        with ThreadPoolExecutor(max_workers=args.jobs) as executor:
            futures = {executor.submit(run_sb_bias_fit_job, job): job for job in sb_jobs_to_run}
            for future in as_completed(futures):
                job = futures[future]
                try:
                    success, msg = future.result()
                    if success:
                        sb_completed += 1
                        if sb_completed % 10 == 0:
                            print(f"S+B progress: {sb_completed} completed, {sb_failed} failed (of {len(sb_jobs_to_run)})")
                    else:
                        sb_failed += 1
                        print(f"FAILED: {msg}")
                except Exception as e:
                    sb_failed += 1
                    print(
                        f"EXCEPTION: sb-fits {job['cat_name']} M{job['mass']} ({job['era']}, {job['region']}): {e}"
                    )

    # For fully cached jobs, still run the single-toy fit pass used by toy+S+B plotting.
    if sb_cached_jobs:
        sb_toyplot_jobs = []
        for job in sb_cached_jobs:
            toy_job = dict(job)
            toy_job["single_toy_only"] = True
            sb_toyplot_jobs.append(toy_job)

        with ThreadPoolExecutor(max_workers=args.jobs) as executor:
            futures = {executor.submit(run_sb_bias_fit_job, job): job for job in sb_toyplot_jobs}
            for future in as_completed(futures):
                job = futures[future]
                try:
                    success, msg = future.result()
                    if success:
                        sb_toyplot_completed += 1
                    else:
                        sb_toyplot_failed += 1
                        print(f"FAILED: {msg}")
                except Exception as e:
                    sb_toyplot_failed += 1
                    print(
                        f"EXCEPTION: toyplot sb-fits {job['cat_name']} M{job['mass']} ({job['era']}, {job['region']}): {e}"
                    )

    print(f"\nS+B fit phase complete: {sb_completed} computed, {sb_cached} cached, {sb_failed} failed")
    if sb_cached_jobs:
        print(
            f"  Single-toy plotting fits on cached jobs: {sb_toyplot_completed} completed, {sb_toyplot_failed} failed"
        )
    phase_durations["phase4_sb_fits"] = time.perf_counter() - phase4_start
    print(f"PHASE 4 elapsed: {format_duration(phase_durations['phase4_sb_fits'])}")

    # ========================================================================
    # PHASE 5: Generate summary plots
    # ========================================================================

    run_plot_phase()

    # ========================================================================
    # SUMMARY
    # ========================================================================

    total_elapsed = time.perf_counter() - run_start
    phase_durations["total"] = total_elapsed

    print("\n" + "=" * 80)
    print("ALL PHASES COMPLETE")
    print(f"  Processed {len(configs)} (era, region) combinations")
    print(f"  Phase 2 (B-only fits): {len(all_jobs)} jobs, {failed} failed")
    print(f"  Phase 3 (toy generation): {toys_completed + toys_failed} jobs, {toys_failed} failed")
    print(f"  Phase 4 (S+B fits): {len(sb_jobs)} jobs ({sb_completed} computed, {sb_cached} cached, {sb_failed} failed)")
    print("=" * 80)
    print("TIMING SUMMARY")
    print(f"  Phase 1 (collect):   {format_duration(phase_durations['phase1_collect'])}")
    print(f"  Phase 2 (bkg fits):  {format_duration(phase_durations['phase2_bkg_fits'])}")
    # print(f"  Phase 3 (toys):      {format_duration(phase_durations['phase3_toys'])}")
    # print(f"  Phase 4 (sb fits):   {format_duration(phase_durations['phase4_sb_fits'])}")
    print(f"  Phase 5 (plots):     {format_duration(phase_durations['phase5_plots'])}")
    print(f"  Total runtime:       {format_duration(phase_durations['total'])}")
    print("=" * 80)

    # return 1 if (failed > 0 or toys_failed > 0 or sb_failed > 0) else 0


if __name__ == "__main__":
    sys.exit(main())
