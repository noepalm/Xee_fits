#!/usr/bin/env python3

import argparse
import os
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import uproot


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


LOG_MAX_BYTES = 500 * 1024
LOG_HEAD_LINES = 10


def write_log_with_head_tail(path, text, max_bytes=LOG_MAX_BYTES, head_lines=LOG_HEAD_LINES):
    """Write log text, keeping full file when small and head+tail when large."""
    data = text.encode("utf-8", errors="replace")
    if len(data) <= max_bytes:
        with open(path, "wb") as f:
            f.write(data)
        return

    lines = text.splitlines(keepends=True)
    head_text = "".join(lines[:head_lines])
    head = head_text.encode("utf-8", errors="replace")
    tail = data[-max_bytes:]
    marker = b"\n[... log trimmed; keeping first lines and tail ...]\n"

    with open(path, "wb") as f:
        f.write(head)
        f.write(marker)
        f.write(tail)


def trim_file_to_head_tail(path, max_bytes=LOG_MAX_BYTES, head_lines=LOG_HEAD_LINES):
    """Trim an existing log file in-place to first N lines + last max_bytes."""
    if not os.path.exists(path):
        return
    size = os.path.getsize(path)
    if size <= max_bytes:
        return

    with open(path, "rb") as f:
        head_parts = []
        for _ in range(head_lines):
            line = f.readline()
            if not line:
                break
            head_parts.append(line)
        head = b"".join(head_parts)

    with open(path, "rb") as f:
        f.seek(-max_bytes, os.SEEK_END)
        tail = f.read()

    marker = b"\n[... log trimmed; keeping first lines and tail ...]\n"
    with open(path, "wb") as f:
        f.write(head)
        f.write(marker)
        f.write(tail)


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


# ============================================================================
# Job execution
# ============================================================================


def run_gof_job(job, mode, n_toys):
    workdir = str(Path(job["workdir"]).resolve())
    txt_file = job["txt_file"]
    root_file = job["root_file"]
    cat_id = job["cat_id"]
    cat_name = job["cat_name"]
    era = job["era"]
    region = job["region"]
    mass = job["mass"]
    mass_label = job["mass_label"]
    min_mass = job["min_mass"]
    max_mass = job["max_mass"]
    fit_tag_label = job["fit_tag_label"]
    outfolder = job["outfolder"]
    basedir = job["basedir"]
    use_binned = job["use_binned"]
    caching = job.get("caching", True)
    job_log_name = f"gof_job_{cat_name}{fit_tag_label}_{era}_{region}.log"
    job_log_path = os.path.join(workdir, job_log_name)
    job_log_sections = []
    dest_mass_dir = Path(outfolder) / f"{cat_name}_{era}" / f"M{mass}"

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

    def flush_job_log():
        if not job_log_sections:
            return
        write_log_with_head_tail(job_log_path, "".join(job_log_sections))

    def copy_job_log_to_output():
        dest_mass_dir.mkdir(parents=True, exist_ok=True)
        if os.path.exists(job_log_path):
            shutil.copy2(job_log_path, str(dest_mass_dir))

    root_path = os.path.join(workdir, root_file)
    if not os.path.exists(root_path):
        try:
            capture_and_buffer(["text2workspace.py", txt_file], cwd=workdir)
        except subprocess.CalledProcessError:
            flush_job_log()
            copy_job_log_to_output()
            return (False, f"text2workspace failed for {cat_name} M{mass} ({era}, {region}); see {job_log_path}")
    else:
        job_log_sections.append(f"SKIP: workspace exists, not running text2workspace: {root_path}\n")

    gof_log = os.path.join(workdir, f"gof_{cat_name}{fit_tag_label}_{era}_{region}_{mode}.log")
    gof_name = f"_{cat_name}{fit_tag_label}_{era}_{region}_{mode}"
    gof_cmd = [
        "combine",
        "-M", "GoodnessOfFit",
        "--algo", "saturated",
        "--cminDefaultMinimizerStrategy", "0",
        root_file,
        "--setParameterRanges", f"mass={min_mass},{max_mass}",
        "-n", gof_name,
        "-m", str(mass_label),
        "-v", "1",
    ]
    if mode == "toys":
        gof_cmd.extend(["-t", str(n_toys), "--toysFreq"])

    gof_out = os.path.join(
        workdir,
        f"higgsCombine{gof_name}.GoodnessOfFit.mH{mass_label}.root",
    )
    gof_out_glob = f"higgsCombine{gof_name}.GoodnessOfFit.mH*.root"
    if caching and os.path.exists(gof_out):
        job_log_sections.append(f"SKIP: cached GoF output exists: {gof_out}\n")
    else:
        job_log_sections.append(f"Output file {gof_out} not found. Running GoodnessOfFit.")
        try:
            with open(gof_log, "w") as f:
                subprocess.run(gof_cmd, stdout=f, stderr=subprocess.STDOUT, check=True, cwd=workdir)
            trim_file_to_head_tail(gof_log)
        except subprocess.CalledProcessError:
            trim_file_to_head_tail(gof_log)
            flush_job_log()
            copy_job_log_to_output()
            return (False, f"GoodnessOfFit failed for {cat_name} M{mass} ({era}, {region})")

    combine_logger = os.path.join(workdir, "combine_logger.out")
    dest_mass_dir.mkdir(parents=True, exist_ok=True)
    if os.path.exists(combine_logger):
        shutil.copy2(
            combine_logger,
            str(dest_mass_dir / f"combine_logger_gof_{cat_name}{fit_tag_label}_{era}_{region}.out"),
        )

    files_to_copy = [
        os.path.join(workdir, gof_log),
        os.path.join(workdir, txt_file),
        gof_out,
    ]
    gof_candidates = list(Path(workdir).glob(gof_out_glob))
    files_to_copy.extend([str(p) for p in gof_candidates])

    for src in files_to_copy:
        if os.path.exists(src):
            shutil.copy2(src, str(dest_mass_dir))

    flush_job_log()
    copy_job_log_to_output()

    return (True, f"OK: GoF {mode} {cat_name} M{mass_label} ({era}, {region})")


def infer_expected_bins(input_root, cat_name, cat_id):
    if not input_root.exists():
        return None

    try:
        with uproot.open(input_root) as f:
            keys = [k.split(";")[0] for k in f.keys(recursive=True)]
            data_obs_keys = [k for k in keys if "data_obs" in k]
            if not data_obs_keys:
                return None

            preferred = [
                k
                for k in data_obs_keys
                if cat_name in k or f"cat{cat_id}" in k or f"cat_{cat_id}" in k
            ]
            candidates = preferred if preferred else data_obs_keys
            candidates.sort(key=len)
            hist = f[candidates[0]]
            _, edges = hist.to_numpy()
            return len(edges) - 1
    except Exception:
        return None


def get_region_boundaries(regions):
    ordered = [r for r in ["region0", "region1", "region2"] if r in regions]
    boundaries = []
    for region in ordered[:-1]:
        r_range = get_mass_range(region)
        boundary = r_range.get("max_limit") or r_range.get("max")
        if boundary is not None:
            boundaries.append(boundary)
    return boundaries


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
    parser.add_argument("--jobs", type=int, default=-1, help="Number of parallel jobs")
    parser.add_argument("--no_caching", action="store_false", dest="caching", help="Disable caching")
    parser.add_argument("--plot_only", action="store_true", help="Only generate summary plots")
    parser.add_argument("--observed_only", action="store_true", help="Run only observed GoF")
    parser.add_argument("--toys_only", action="store_true", help="Run only toy GoF")
    parser.add_argument("--toys", type=int, default=500, help="Number of toys per mass point")
    parser.add_argument(
        "--gof_expected",
        default="",
        help="Expected GoF value for summary plots (leave empty to auto-derive)",
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

    if args.observed_only and args.toys_only:
        print("ERROR: --observed_only and --toys_only cannot be used together.")
        return 2

    run_observed = not args.toys_only
    run_toys = not args.observed_only
    if args.plot_only:
        run_observed = False
        run_toys = False

    # if --jobs not provided, use nproc as #parallel workers
    if args.jobs <= 0:
        args.jobs = os.cpu_count() or 1

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
    print(f"  Observed only: {args.observed_only}")
    print(f"  Toys only: {args.toys_only}")
    print(f"  Toys per mass: {args.toys}")
    print(f"  Exclude resonant backgrounds: {args.no_res}")
    print(f"  Caching enabled: {args.caching}")
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
            outfolder += "/mu0"

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
            cat_dir = Path(outfolder) / f"{cat_name}_{era}"
            (cat_dir / "s").mkdir(parents=True, exist_ok=True)
            (cat_dir / "b").mkdir(parents=True, exist_ok=True)

        input_root = Path(config["input_folder"]) / "ee" / "common" / f"Xee_ee_{era}.input.root"
        if input_root.exists():
            subprocess.run(["cp", str(input_root), str(Path(outfolder))])

    all_jobs = []
    successful_jobs = []
    failed = 0
    if args.plot_only:
        print("\n" + "=" * 80)
        print("PHASE 1: Skipped (--plot_only enabled)")
        print("=" * 80)
        phase_durations["phase1_collect"] = 0.0
    else:
        # ========================================================================
        # PHASE 1: Collect GoF jobs
        # ========================================================================
        print("\n" + "=" * 80)
        print("PHASE 1: Collecting GoF jobs")
        print("=" * 80)
        phase1_start = time.perf_counter()

        for config_idx, config in enumerate(configs, 1):
            era = config["era"]
            region = config["region"]
            input_folder = config["input_folder"]
            outfolder = config["outfolder"]

            print(f"\n--- Processing config {config_idx}/{len(configs)}: {era}, {region} ---")
            ee_dir = Path(input_folder) / "ee"
            if not ee_dir.exists():
                print(f"  WARNING: Input directory does not exist: {ee_dir}")
                continue

            mass_range = get_mass_range(region)
            mass_dirs = [
                d
                for d in ee_dir.iterdir()
                if d.is_dir() and d.name.replace(".", "").replace("-", "").isdigit()
            ]
            mass_dirs = sorted(mass_dirs, key=lambda d: float(d.name))
            print(f"  Found {len(mass_dirs)} mass directories")

            jobs_before = len(all_jobs)
            for mass_dir in mass_dirs:
                mass = float(mass_dir.name)
                if mass < mass_range["min_limit"] or mass > mass_range["max_limit"]:
                    continue
                if not mass_is_selected(mass, mass_selector):
                    continue

                for cat_id in get_all_category_ids(args.category):
                    cat_name = get_category_name(cat_id)
                    txt_file = f"Xee_ee_{cat_id}_{era}.txt"
                    root_file = txt_file.replace(".txt", ".root")
                    txt_path = mass_dir / txt_file
                    if not txt_path.exists():
                        continue

                    all_jobs.append(
                        {
                            "workdir": str(mass_dir.resolve()),
                            "txt_file": txt_file,
                            "root_file": root_file,
                            "cat_id": cat_id,
                            "cat_name": cat_name,
                            "era": era,
                            "region": region,
                            "mass": mass,
                            "mass_label": mass_dir.name,
                            "min_mass": mass_range["min"],
                            "max_mass": mass_range["max"],
                            "fit_tag": args.fit_tag,
                            "fit_tag_label": fit_tag_label,
                            "outfolder": outfolder,
                            "basedir": basedir,
                            "use_binned": args.binned,
                            "no_resonant_bkgs": int(args.no_res),
                            "plot_only": args.plot_only,
                            "caching": args.caching,
                        }
                    )

            print(f"  Added {len(all_jobs) - jobs_before} jobs from this config")

        phase_durations["phase1_collect"] = time.perf_counter() - phase1_start
        print(f"PHASE 1 elapsed: {format_duration(phase_durations['phase1_collect'])}")

        if not all_jobs:
            print("No diagnostics jobs to run!")
            return 0

    # ========================================================================
    # PHASE 2: Run GoodnessOfFit jobs in parallel
    # ========================================================================
    completed = 0
    if args.plot_only:
        print("\n" + "=" * 80)
        print("PHASE 2: Skipped (--plot_only enabled)")
        print("=" * 80 + "\n")
        phase_durations["phase2_gof"] = 0.0
    else:
        print("\n" + "=" * 80)
        modes = []
        if run_observed:
            modes.append("obs")
        if run_toys:
            modes.append("toys")
        print(
            f"PHASE 2: Running GoodnessOfFit ({', '.join(modes)}) for {len(all_jobs)} jobs on {args.jobs} workers"
        )
        print("=" * 80 + "\n")
        phase2_start = time.perf_counter()
        successful_jobs = []

        tasks = []
        for job in all_jobs:
            if run_observed:
                tasks.append((job, "obs"))
            if run_toys:
                tasks.append((job, "toys"))

        with ThreadPoolExecutor(max_workers=args.jobs) as executor:
            futures = {executor.submit(run_gof_job, job, mode, args.toys): (job, mode) for job, mode in tasks}
            for future in as_completed(futures):
                job, mode = futures[future]
                try:
                    success, msg = future.result()
                    if success:
                        completed += 1
                        successful_jobs.append(job)
                        if completed % 10 == 0:
                            print(
                                f"Progress: {completed} completed, {failed} failed (of {len(tasks)})"
                            )
                    else:
                        failed += 1
                        print(f"FAILED: {msg}")
                except Exception as e:
                    failed += 1
                    print(
                        f"EXCEPTION: {mode} {job['cat_name']} M{job['mass']} ({job['era']}, {job['region']}): {e}"
                    )

        print(f"\nGoodnessOfFit complete: {completed} completed, {failed} failed")
        phase_durations["phase2_gof"] = time.perf_counter() - phase2_start
        print(f"PHASE 2 elapsed: {format_duration(phase_durations['phase2_gof'])}")

    # ========================================================================
    # PHASE 3: Generate summary plots
    # ========================================================================
    print("\n" + "=" * 80)
    print("PHASE 3: Generating summary plots")
    print("=" * 80 + "\n")
    phase3_start = time.perf_counter()

    eras_to_plot = sorted({cfg["era"] for cfg in configs})
    regions_to_plot = sorted({cfg["region"] for cfg in configs})

    for era in eras_to_plot:
        print(f"Generating GoF summary plots for era {era}")
        region_boundaries = get_region_boundaries(regions_to_plot)
        input_root = None
        for cfg in configs:
            if cfg["era"] == era:
                input_root = Path(cfg["input_folder"]) / "ee" / "common" / f"Xee_ee_{era}.input.root"
                break
        for cat_id in get_all_category_ids(args.category):
            cat_name = get_category_name(cat_id)
            expected_bins = None
            if not args.gof_expected and input_root is not None:
                expected_bins = infer_expected_bins(input_root, cat_name, cat_id)
            if expected_bins is None:
                expected_bins = float(args.gof_expected) if args.gof_expected else 350.0
            plot_cmd = [
                "python3",
                f"{basedir}/scripts/utilities/plot_gof_summary.py",
                "--outfolder",
                # f"{configs[0]['outfolder']}/{cat_name}_{era}",
                f"{configs[0]['outfolder']}",
                "--era",
                era,
                "--cat",
                cat_name,
                "--regions",
            ] + regions_to_plot

            if args.fit_tag:
                plot_cmd.extend(["--fit-tag", args.fit_tag])
            if expected_bins is not None:
                plot_cmd.extend(["--expected", str(expected_bins)])

            log_path = f"{configs[0]['outfolder']}/{cat_name}_{era}/gof_summary_{era}{fit_tag_label}.log"
            with open(log_path, "w") as f:
                subprocess.run(plot_cmd, stdout=f, stderr=subprocess.STDOUT)
            trim_file_to_head_tail(log_path)

            pvalue_cmd = [
                "python3",
                f"{basedir}/scripts/utilities/plot_gof_pvalues.py",
                "--outfolder",
                # f"{configs[0]['outfolder']}/{cat_name}_{era}",
                f"{configs[0]['outfolder']}",
                "--era",
                era,
                "--cat",
                cat_name,
                "--regions",
            ] + regions_to_plot

            if region_boundaries:
                pvalue_cmd.extend(["--region-boundaries"] + [str(b) for b in region_boundaries])
            if args.fit_tag:
                pvalue_cmd.extend(["--fit-tag", args.fit_tag])

            pvalue_log = f"{configs[0]['outfolder']}/{cat_name}_{era}/gof_pvalues_{era}{fit_tag_label}.log"
            with open(pvalue_log, "w") as f:
                subprocess.run(pvalue_cmd, stdout=f, stderr=subprocess.STDOUT)
            trim_file_to_head_tail(pvalue_log)

    phase_durations["phase3_summary_plots"] = time.perf_counter() - phase3_start
    print(f"PHASE 3 elapsed: {format_duration(phase_durations['phase3_summary_plots'])}")

    total_elapsed = time.perf_counter() - run_start
    phase_durations["total"] = total_elapsed

    print("\n" + "=" * 80)
    print("ALL PHASES COMPLETE")
    print(f"  Processed {len(configs)} (era, region) combinations")
    print(f"  Total jobs: {len(all_jobs)}")
    print(f"  GoodnessOfFit failures: {failed}")
    print("=" * 80)
    print("TIMING SUMMARY")
    print(f"  Phase 1 (collect):            {format_duration(phase_durations['phase1_collect'])}")
    print(f"  Phase 2 (gof):                {format_duration(phase_durations['phase2_gof'])}")
    print(f"  Phase 3 (summary plots):      {format_duration(phase_durations['phase3_summary_plots'])}")
    print(f"  Total runtime:                {format_duration(phase_durations['total'])}")
    print("=" * 80)

    return 1 if failed > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
