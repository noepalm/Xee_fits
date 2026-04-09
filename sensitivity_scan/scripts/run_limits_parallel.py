#!/usr/bin/env python3

import os
import argparse
import subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
import sys
import time

# ============================================================================
# Configuration and utilities
# ============================================================================

def get_category_label(cat_name):
    """Get category label from category name."""
    mapping = {
        "etaHigh": "etap0p6",
        "etaLow": "etam0p6",
        "dRHigh": "dRp0p3",
        "dRLow": "dRm0p3",
        "inclusive": "inclusive"
    }
    return mapping.get(cat_name, "unknown")

def get_category_name(cat_id):
    """Get category name from category ID."""
    mapping = {
        0: "etaHigh",
        1: "etaLow",
        2: "dRHigh",
        3: "dRLow",
        4: "inclusive"
    }
    return mapping.get(cat_id, "unknown")

def get_all_category_ids(category_type):
    """Get all category IDs for a given category type."""
    if category_type == "eta":
        return [0, 1]
    elif category_type == "dR":
        return [2, 3]
    elif category_type == "inclusive":
        return [4]
    else:
        return []

def get_points_for_mass(mass, region):
    """Get r points to scan based on mass value and region."""
    if region == "region0":
        # if mass < 0.65:
        if mass < 0.75:
            return [0.01, 0.05, 0.08, 0.1, 0.2, 0.25, 0.3, 0.35, 0.37, 0.39, 0.4, 0.45, 0.5, 0.55, 0.57, 0.6, 0.7, 
                    0.9, 1.0, 1.2, 1.5, 1.7, 2.0, 5.0, 10.0, 20.0, 30.0, 50.0, 80, 100, 150, 200, 400, 600, 800, 1200]
        elif mass < 0.9:
            # return [0.0005, 0.001, 0.002, 0.0025, 0.003, 0.0035, 0.005, 0.007, 0.009, 0.01, 0.015, 
            #         0.025, 0.05, 0.06, 0.08, 0.1, 0.2, 0.3, 0.5, 0.6, 0.9, 1.0, 2.0, 3.5, 5.0, 10, 20, 40, 60, 80, 100, 150, 200, 250, 300]
            return [0.2, 0.3, 0.5, 0.6, 0.9, 1.0, 2.0, 3.5, 5.0, 10, 20, 40, 60, 80, 100, 150, 200, 250, 300, 400, 500, 800, 1000, 1500]
        elif 0.95 <= mass <= 1.1:
            return [0.01, 0.05, 0.07, 0.1, 0.15, 0.2, 0.3, 0.37, 0.45, 0.7, 0.8, 0.9, 1.0, 1.25, 1.5, 2.0, 5.0, 10.0, 
                    12.5, 15.0, 17.5, 20.0, 30.0, 50, 80, 100, 150, 200, 250, 300, 400, 600, 800, 1000, 1200, 1500]
        else:
            return [0.007, 0.015, 0.02, 0.025, 0.04, 0.06, 0.075, 0.09, 0.1, 0.15, 0.2, 0.3, 0.37, 
                    0.45, 0.7, 0.8, 0.9, 1.0, 1.25, 1.5, 2.0, 5.0, 10.0, 15.0, 20.0, 30, 40, 50, 70, 80, 100, 150, 200, 300, 500, 700, 1000, 1300]
    
    elif region == "region1":
        if 3.05 <= mass <= 3.15:
            # return [0.01, 0.03, 0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 1.0, 1.5, 2.0, 2.5, 3.5, 4.0, 
            #         4.2, 4.3, 4.6, 4.7, 5.1, 5.4, 6.0, 7.0, 10.0, 20.0, 50.0, 70.0, 100.0, 200, 300]
            return [1.0, 1.5, 2.0, 2.5, 3.5, 4.0, 4.2, 4.3, 4.6, 4.7, 5.1, 5.4, 6.0, 7.0, 10.0, 20.0, 50.0, 70.0, 100.0, 200, 250, 300, 320, 350, 400, 500, 600, 750]
        elif 3.67 <= mass <= 3.73:
            return [0.01, 0.025, 0.05, 0.075, 0.1, 0.15, 0.2, 0.25, 0.27, 0.3, 0.35, 0.4, 0.5, 0.9, 1.0, 3, 5,
                    10.0, 20, 30, 40, 50]
        else:
            return [0.001, 0.005, 0.01, 0.0207, 0.0336, 0.0546, 0.0886, 0.1, 0.15, 0.2, 0.3, 0.4, 0.5, 0.6, 
                    0.7, 1.0, 2.5, 5.0, 10.0, 20.0, 40.0, 50.0, 70.0, 100.0]

    # if region == "region0":
    #     # if mass < 0.65:
    #     if mass < 0.75:
    #         return [10, 20, 50.0, 100, 200, 300, 400, 700, 800, 900, 1200, 1500, 1700, 2000, 2500, 3000, 3500]
    #     elif mass < 0.9:
    #         return [10, 20, 40, 60, 80, 100, 150, 200, 250, 300, 400, 500, 600, 800, 900, 1200, 1500, 1700, 2000, 2500, 3000, 3500]
    #     elif 0.95 <= mass <= 1.1:
    #         return [10, 20, 50, 80, 100, 150, 200, 250, 500, 800, 900, 1200, 1500, 1700, 2000, 2500, 3000, 3500]
    #     else:
    #         return [10, 20, 50, 100, 200, 300, 400, 700, 800, 900, 1000, 1500, 2000, 2500, 3000, 3500]
    
    # elif region == "region1":
    #     if 3.05 <= mass <= 3.15:
    #         return [50.0, 70.0, 100.0, 200, 300, 400, 500, 800, 1000, 1500, 2000, 2500, 3000, 3500]
    #     elif 3.67 <= mass <= 3.73:
    #         return [0.01, 0.025, 0.05, 0.075, 0.1, 0.15, 0.2, 0.25, 0.27, 0.3, 0.35, 0.4, 0.5, 0.9, 1.0, 3, 5,
    #                 10.0]
    #     else:
    #         return [10, 30, 50, 70, 100.0, 200, 300, 400, 600, 700, 800, 900, 1200, 1500, 2000, 3000, 3500]

    elif region == "region2":
        if 7 <= mass < 7.5:
            return [0.001, 0.005, 0.007, 0.01, 0.0162, 0.0264, 0.0379, 0.0546, 0.0695, 0.0886, 0.1, 0.2, 0.4, 0.6, 0.8, 1.0, 
                    2.0, 5.0, 10.0, 15.0, 20.0, 25.0, 30.0, 35.0, 40.0, 50.0, 60.0]
        elif 7.5 <= mass < 9.8:
            return [0.001, 0.005, 0.007, 0.01, 0.02, 0.03, 0.05, 0.06, 0.0785, 0.0886, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 
                    0.8, 0.9, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 10.0, 12.0, 15.0, 17.0, 20.0, 25.0, 30.0, 35.0, 
                    40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0, 120.0, 160.0, 200.0, 210.0, 270.0, 300.0, 350, 400, 500]
        elif 9.8 <= mass < 10:
            return [0.01, 0.02, 0.03, 0.05, 0.06, 0.0785, 0.0886, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 
                    0.8, 0.9, 1.0, 2.0, 3.0, 4.0, 4.5, 4.7, 4.9, 5.0, 5.5, 6.0, 7.0, 10.0, 20, 30, 40, 50, 60, 75, 90, 130, 150, 200, 250, 300, 400]
        elif 10 <= mass <= 12:
            return [0.5, 0.7, 0.9, 1.0, 2.0, 3.0, 3.2, 3.5, 3.7, 3.9, 4.0, 5.0, 5.5, 6.0, 7.0, 7.5, 8.0, 8.5, 9.0, 10.0, 
                    15.0, 20.0, 25.0, 35.0, 50.0, 60.0, 70.0, 85.0, 95, 115.0, 130.0, 150.0, 180.0, 
                    220.0, 250.0, 350.0, 500.0, 650.0, 800.0]
        else:
            return [0.001, 0.005, 0.007, 0.009, 0.01, 0.0144, 0.0207, 0.0298, 0.0483, 0.0616, 0.0695, 
                    0.0785, 0.09, 0.1, 0.2, 0.3, 0.6, 0.8, 1.2, 1.8, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 7.0, 
                    8.0, 9.0, 10.0]
    
    else:
        print("ERROR: Unknown region specified: ", region)
        return []

def get_rmin_rmax(mass, era):
    """Get rMin and rMax based on mass and era."""
    rmin = 0
    rmax = 10  # default
    
    # syntax: if M > <thresholds>, set rmin/rmax to value.
    era_settings = {
        "2022": {0: (0, 100), 1: (0,10), 9.0: (0, 40), 9.5: (0, 70), 10.0: (0, 140)},
        "2022EE": {0: (0, 100), 1: (0,10), 9.0: (0, 25), 9.5: (0, 45), 10.0: (0, 85)},
        "2023": {0: (0, 100), 1: (0,10), 9.0: (0, 20), 9.5: (0, 35), 10.0: (0, 70)},
        "2023BPix": {0: (0, 100), 1: (0,10), 9.0: (0, 40), 9.5: (0, 70), 10.0: (0, 135)},
        # "allYears": {0: (0, 100), 1: (0,10), 9.0: (0, 15), 9.5: (0, 25), 10.0: (0, 50)}
        # "allYears": {0: (0, 100), 1.25: (0,10), 9.0: (0, 15), 9.5: (0, 50), 10.0: (0, 50)}
        # "allYears": {1.25: (0,300), 2.0 : (0, 10), 9.0: (0, 15), 9.5: (0, 50), 10.0: (0, 50)}
        "allYears": {0 : (0, 3000), 1.25: (0,500), 2.0 : (0, 100), 3.0 : (0, 1000), 3.2 : (0, 100), 4.0 : (0, 10), 7.5: (0, 100)}
        # "allYears": {0: (0, 7000), 3.5: (0, 5000), 9.0: (0, 15), 9.5: (0, 50), 10.0: (0, 50)} #for 6p5 trigger test only
    }
    
    if era in era_settings:
        for threshold, (r_min, r_max) in sorted(era_settings[era].items()):
            if mass >= threshold:
                rmin = r_min
                rmax = r_max
    
    return rmin, rmax

def get_mass_range(region):
    """Get mass range limits for a given region."""
    # ranges = {
    #     "region0": {"min": 0.3, "min_limit": 0.5, "max": 2.4, "max_limit": 2.2},
    #     "region1": {"min": 1.6, "min_limit": 1.8, "max": 4.6, "max_limit": 4.4},
    #     "region2": {"min": 3.8, "min_limit": 4.0, "max": 11.0, "max_limit": 10.8}
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
    """Format elapsed seconds as H:MM:SS."""
    total = int(round(seconds))
    hours, rem = divmod(total, 3600)
    minutes, secs = divmod(rem, 60)
    return f"{hours}:{minutes:02d}:{secs:02d}"


LOG_MAX_BYTES = 500 * 1024
LOG_HEAD_LINES = 10


def write_log_with_head_tail(path, text, max_bytes=LOG_MAX_BYTES, head_lines=LOG_HEAD_LINES):
    """Write log text, keeping full file when small and head+tail when large."""
    data = text.encode('utf-8', errors='replace')
    if len(data) <= max_bytes:
        with open(path, 'wb') as f:
            f.write(data)
        return

    lines = text.splitlines(keepends=True)
    head_text = ''.join(lines[:head_lines])
    head = head_text.encode('utf-8', errors='replace')
    tail = data[-max_bytes:]
    marker = b"\n[... log trimmed; keeping first lines and tail ...]\n"

    with open(path, 'wb') as f:
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

    with open(path, 'rb') as f:
        head_parts = []
        for _ in range(head_lines):
            line = f.readline()
            if not line:
                break
            head_parts.append(line)
        head = b''.join(head_parts)

    with open(path, 'rb') as f:
        f.seek(-max_bytes, os.SEEK_END)
        tail = f.read()

    marker = b"\n[... log trimmed; keeping first lines and tail ...]\n"
    with open(path, 'wb') as f:
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

    # Explicit point list: allow tiny tolerance for float parsing differences.
    eps = 1e-6
    return any(abs(mass - p) < eps for p in selector["points"])

# ============================================================================
# Grid point computation (parallelizable)
# ============================================================================

def run_single_grid_point(args_dict):
    """
    Run combine for a single grid point.
    
    Args:
        args_dict: Dictionary containing all necessary parameters
    
    Returns:
        Tuple of (success, point, label, mass, log_path)
    """
    workdir = args_dict['workdir']
    input_root = args_dict['input_root']
    point = args_dict['point']
    label = args_dict['label']
    fit_tag_label = args_dict['fit_tag_label']
    rmin = args_dict['rmin']
    rmax = args_dict['rmax']
    cl_value = args_dict.get('cl')
    set_params = args_dict['set_params']
    freeze_params = args_dict['freeze_params']
    mass = args_dict['mass']
    era = args_dict['era']
    
    # Construct full paths (no chdir to avoid parallel conflicts)
    input_root_path = os.path.join(workdir, input_root)
    output_file = os.path.join(workdir, f"higgsCombine_{label}{fit_tag_label}_point_{point}.AsymptoticLimits.mH120.root")
    log_file = os.path.join(workdir, f"fitAsymptotic_{label}{fit_tag_label}_point_{point}.log")

    # Check if already computed (caching)
    if os.path.exists(output_file) and args_dict.get('caching', True):
        return (True, point, label, mass, None)
    
    # Build combine command - use relative path since we'll run in workdir
    cmd = [
        "combine", "-M", "AsymptoticLimits", input_root,
        "--rMin", str(rmin), "--rMax", str(rmax),
        "--singlePoint", str(point),
        "-n", f"_{label}{fit_tag_label}_point_{point}",
        "--cminDefaultMinimizerStrategy", "0"
    ]

    # cmd.extend(["--freezeParameters", "lumi_scale"])
    
    # # Add parameter settings for year combination or multi-era handling
    # if era == "allYears":
    #     cmd.extend([
    #         # "--setParameters", "pdf_index_2022EE=0,pdf_index_2023=0,pdf_index_2023BPix=0",
    #         # "--freezeParameters", "pdf_index_2022EE,pdf_index_2023,pdf_index_2023BPix",
    #         "--setParameters", "pdf_index_2022EE=0,pdf_index_2023=0,pdf_index_2023BPix=0,pdf_index_2022EE_envelope=0,pdf_index_2023_envelope=0,pdf_index_2023BPix_envelope=0",
    #         "--freezeParameters", "pdf_index_2022EE,pdf_index_2023,pdf_index_2023BPix,pdf_index_2022EE_envelope,pdf_index_2023_envelope,pdf_index_2023BPix_envelope"
    #     ])
    
    # Forward user-provided parameter settings directly to combine.
    if set_params:
        cmd.extend(["--setParameters", set_params])

    # Forward user-provided freeze list directly to combine.
    if freeze_params:
        cmd.extend(["--freezeParameters", freeze_params])

    # Forward user-provided confidence level directly to combine.
    if cl_value is not None:
        cmd.extend(["--cl", str(cl_value)])
    
    cmd.extend(["-v", "1"]) #3
    
    # Run combine
    try:
        with open(log_file, 'w') as f:
            result = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, timeout=1200, cwd=workdir)
        trim_file_to_head_tail(log_file)
        success = result.returncode == 0
        return (success, point, label, mass, log_file)
    except subprocess.TimeoutExpired:
        trim_file_to_head_tail(log_file)
        return (False, point, label, mass, log_file)
    except Exception as e:
        return (False, point, label, mass, str(e))

# ============================================================================
# Harvesting (requires all grid points)
# ============================================================================

def harvest_limits(workdir, label, fit_tag_label, points, input_root, rmin, rmax, outfolder, mass, cl=None):
    """
    Harvest grid results: merge grid files, compute final limit, copy outputs.
    
    Args:
        workdir: Working directory where grid files are located
        label: Target label (e.g., etaHigh_2023)
        fit_tag_label: Fit tag with underscore prefix
        points: List of r points that were computed
        input_root: Input ROOT file path (basename only)
        rmin: Minimum r value
        rmax: Maximum r value
        outfolder: Output folder for results
        mass: Mass value
    
    Returns:
        True if successful, False otherwise
    """
    # Construct full paths (no chdir to avoid parallel conflicts)
    input_root_path = os.path.join(workdir, input_root)
    
    # Collect grid files with full paths
    grid_files = [os.path.join(workdir, f"higgsCombine_{label}{fit_tag_label}_point_{point}.AsymptoticLimits.mH120.root") 
                  for point in points]
    
    # Check all files exist
    missing = [f for f in grid_files if not os.path.exists(f)]
    if missing:
        print(f"ERROR: Missing grid files for {label} M{mass}: {len(missing)}/{len(grid_files)} missing")
        return False
    
    # Merge grid - use relative paths since we'll run in workdir
    grid_output = f"limits_from_grid_{label}.root"
    grid_files_rel = [os.path.basename(f) for f in grid_files]
    hadd_cmd = ["hadd", "-f", grid_output] + grid_files_rel
    
    try:
        subprocess.run(hadd_cmd, check=True, capture_output=True, cwd=workdir)
    except subprocess.CalledProcessError as e:
        print(f"ERROR: hadd failed for {label} M{mass}: {e}")
        return False
    
    # Compute final limit from grid - use relative paths since we'll run in workdir
    final_log = f"fitAsymptotic_{label}{fit_tag_label}.log"
    combine_cmd = [
        "combine", "-M", "AsymptoticLimits", input_root,
        "--rMin", str(rmin), "--rMax", str(rmax),
        "--getLimitFromGrid", grid_output,
        "-n", f"_{label}{fit_tag_label}",
        "-v", "1" #3
    ]

    if cl is not None:
        combine_cmd.extend(["--cl", str(cl)])
    
    try:
        with open(os.path.join(workdir, final_log), 'w') as f:
            subprocess.run(combine_cmd, stdout=f, stderr=subprocess.STDOUT, check=True, timeout=300, cwd=workdir)
        trim_file_to_head_tail(os.path.join(workdir, final_log))
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        trim_file_to_head_tail(os.path.join(workdir, final_log))
        print(f"ERROR: Final limit extraction failed for {label} M{mass}: {e}")
        return False
    
    # Print last 10 lines of log
    print(f"\n=== Final limit results for {label} M{mass} ===")
    with open(os.path.join(workdir, final_log), 'r') as f:
        lines = f.readlines()
        for line in lines[-10:]:
            print(line.rstrip())
    
    # Copy outputs to destination
    dest_dir = Path(outfolder) / label / f"M{mass}"
    dest_dir.mkdir(parents=True, exist_ok=True)
    
    files_to_copy = [
        (os.path.join(workdir, final_log), os.path.basename(final_log)),
        (os.path.join(workdir, f"higgsCombine_{label}{fit_tag_label}.AsymptoticLimits.mH120.root"),
         f"higgsCombine_{label}{fit_tag_label}.AsymptoticLimits.mH120.root")
    ]
    
    combine_logger = os.path.join(workdir, "combine_logger.out")
    if os.path.exists(combine_logger):
        files_to_copy.append((combine_logger, f"combine_logger_{label}{fit_tag_label}.out"))
    
    for src_file, dest_name in files_to_copy:
        if os.path.exists(src_file):
            subprocess.run(["cp", src_file, str(dest_dir / dest_name)])
    
    return True

# ============================================================================
# Mass directory processing
# ============================================================================

def process_mass_directory(args):
    """
    Process a single mass directory: determine what needs to be computed,
    return list of grid point jobs, and harvesting parameters.
    
    Returns:
        Dictionary with 'grid_jobs' and 'harvest_params'
    """
    mass_dir, config = args
    
    mass = float(os.path.basename(mass_dir))
    mass_range = get_mass_range(config['region'])
    
    # Check if mass is in range
    if mass < mass_range['min_limit'] or mass > mass_range['max_limit']:
        return None

    # Optional user mass filter (queue-building only).
    if not mass_is_selected(mass, config.get('mass_selector')):
        return None
    
    print(f"Processing M{mass}")
    
    # Get points for this mass
    points = get_points_for_mass(mass, config['region'])
    rmin, rmax = get_rmin_rmax(mass, config['era'])
    
    # Determine targets based on combination settings
    # Each target is (label, cat_id_or_none, workdir, config)
    if config['run_combination']:
        targets = [(f"{config['category_type']}Combination_{config['era_suffix']}", 
                   None, mass_dir, config)]
    else:
        targets = []
        for cat_id in get_all_category_ids(config['category_type']):
            cat_name = get_category_name(cat_id)
            targets.append((f"{cat_name}_{config['era_suffix']}", cat_id, mass_dir, config))
    
    result = {
        'mass': mass,
        'mass_dir': mass_dir,
        'grid_jobs': [],
        'harvest_params': []
    }
    
    # For each target, prepare grid jobs and harvest parameters
    for label, cat_id, workdir, cfg in targets:
        # Determine input file
        if config['run_year_combination']:
            # Year combination logic - need per-category cards from all years
            if cat_id is None:
                print(f"ERROR: cat_id required for year combination")
                continue
            
            # Collect datacards from all years for this category
            all_years = ["2022", "2022EE", "2023", "2023BPix"]
            year_card_files = []
            for year in all_years:
                year_card = os.path.join(workdir, f"Xee_ee_{cat_id}_{year}.txt")
                if os.path.exists(year_card):
                    year_card_files.append(year_card)
            
            if not year_card_files:
                cat_name = get_category_name(cat_id)
                print(f"WARNING: No cards found for category {cat_name} (ID {cat_id}) across all years, skipping")
                continue
            
            txt_file = os.path.join(workdir, f"Xee_ee_{cat_id}_allYears.txt")
            root_file = txt_file.replace('.txt', '.root')
            
            # Combine cards from all years (do this now, not in parallel)
            print(f"  Combining all years for category {cat_id} into {os.path.basename(txt_file)}")
            combine_cards_cmd = ["combineCards.py"] + year_card_files
            try:
                with open(txt_file, 'w') as f:
                    subprocess.run(combine_cards_cmd, stdout=f, check=True)
            except subprocess.CalledProcessError:
                print(f"ERROR: Failed to combine year cards for cat_id {cat_id} at M{mass}")
                continue
            
            # Build workspace from combined datacard
            print(f"  Building workspace: {os.path.basename(root_file)}")
            
            # check if root file already exists
            if os.path.exists(root_file) and config['caching']:
                print(f"  -> Workspace already exists: {os.path.basename(root_file)}, skipping text2workspace")
            else:                
                text2workspace_cmd = ["text2workspace.py", txt_file]
                try:
                    subprocess.run(text2workspace_cmd, check=True, capture_output=True)
                except subprocess.CalledProcessError:
                    print(f"ERROR: Failed to build workspace for cat_id {cat_id} at M{mass}")
                    continue
        elif config['run_combination']:
            # Category combination
            card_files = []
            for cat_id in get_all_category_ids(config['category_type']):
                card_path = os.path.join(workdir, f"Xee_ee_{cat_id}_{config['era']}.txt")
                if os.path.exists(card_path):
                    card_files.append(card_path)
            
            if not card_files:
                print(f"WARNING: No datacards found for combination at M{mass}")
                continue
                
            txt_file = os.path.join(workdir, f"Xee_ee_{config['category_type']}Combination_{config['era']}.txt")
            root_file = txt_file.replace('.txt', '.root')
            
            # Combine cards (do this now, not in parallel)
            combine_cards_cmd = ["combineCards.py"] + card_files
            try:
                with open(txt_file, 'w') as f:
                    subprocess.run(combine_cards_cmd, stdout=f, check=True)
            except subprocess.CalledProcessError:
                print(f"ERROR: Failed to combine cards for M{mass}")
                continue
            
            # Build workspace from combined datacard
            print(f"  Building workspace: {os.path.basename(root_file)}")
            text2workspace_cmd = ["text2workspace.py", txt_file]
            try:
                subprocess.run(text2workspace_cmd, check=True, capture_output=True)
            except subprocess.CalledProcessError:
                print(f"ERROR: Failed to build workspace for M{mass}")
                continue
        else:
            # Individual category
            if cat_id is None:
                print(f"ERROR: cat_id required for individual category")
                continue
                
            txt_file = os.path.join(workdir, f"Xee_ee_{cat_id}_{config['era']}.txt")
            root_file = txt_file.replace('.txt', '.root')
        
        if not os.path.exists(root_file):
            print(f"WARNING: Input file not found: {root_file}")
            continue
        
        # Determine parameter passthrough for single-point combine calls.
        set_params = config.get('set_parameters', "")
        freeze_params = config.get('freeze_parameters', "")
        # Use just the filename since we'll chdir to workdir
        input_root = os.path.basename(root_file)
        
        # Create grid jobs for all points
        for point in points:
            job = {
                'workdir': workdir,
                'input_root': input_root,
                'point': point,
                'label': label,
                'fit_tag_label': config['fit_tag_label'],
                'rmin': rmin,
                'rmax': rmax,
                'cl': config.get('cl'),
                'set_params': set_params,
                'freeze_params': freeze_params,
                'mass': mass,
                'caching': config['caching'],
                'era': config['era']
            }
            result['grid_jobs'].append(job)
        
        # Store harvest parameters
        harvest_params = {
            'workdir': workdir,
            'label': label,
            'fit_tag_label': config['fit_tag_label'],
            'points': points,
            'input_root': input_root,
            'rmin': rmin,
            'rmax': rmax,
            'outfolder': config['outfolder'],
            'mass': mass,
            'cl': config.get('cl')
        }
        result['harvest_params'].append(harvest_params)
    
    return result

# ============================================================================
# Main execution
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description='Run combine limits in parallel with Python')
    parser.add_argument('--tag', default='', help='Tag appended to input/output folders')
    parser.add_argument('--fit_tag', default='', help='Tag appended to output filenames only')
    parser.add_argument('--folder_tag', default='', help='Folder tag for input directory')
    parser.add_argument('--category', '--cat', default='eta', choices=['eta', 'dR', 'inclusive'])
    parser.add_argument('--regions', nargs='+', default=[], 
                        choices=['region0', 'region1', 'region2'], 
                        help='One or more regions to process')
    parser.add_argument('--region', dest='regions', action='append',
                        help='Deprecated: use --regions instead')
    parser.add_argument('--no_reweight', action='store_true', help='Do not use reweighting')
    parser.add_argument('--plot_only', action='store_true', help='Only generate plots')
    parser.add_argument('--data', action='store_true', help='Run on data instead of MC')
    parser.add_argument(
        '--setParameters',
        default='',
        help=(
            "Comma-separated parameter assignments to pass to combine "
            "(forwarded as --setParameters to single-point AsymptoticLimits jobs)."
        ),
    )
    parser.add_argument(
        '--freezeParameters',
        default='',
        help=(
            "Comma-separated nuisance parameter names to freeze in combine (forwarded as "
            "--freezeParameters to single-point AsymptoticLimits jobs)."
        ),
    )
    parser.add_argument(
        '--cl',
        type=float,
        default=None,
        help=(
            "Confidence level for combine AsymptoticLimits."
        ),
    )
    parser.add_argument('--combination', action='store_true', help='Run category combination')
    parser.add_argument('--no_caching', action='store_false', dest='caching', help='Disable caching')
    parser.add_argument('--eras', nargs='+', default=[],
                        choices=['2022', '2022EE', '2023', '2023BPix', 'allYears'],
                        help='One or more eras to process')
    parser.add_argument('--era', dest='eras', action='append',
                        help='Deprecated: use --eras instead')
    parser.add_argument('--jobs', type=int, default=96, help='Number of parallel jobs')
    parser.add_argument('--prep_jobs', type=int, default=0,
                        help='step-1 preprocessing workers (text2workspace/combineCards). 0 = auto')
    parser.add_argument(
        '--mass_select',
        default='',
        help=(
            "Optional mass selector: 'min:max' for range, or 'm1,m2,m3' for explicit points "
            "(single value 'm' is also accepted). Only selected masses are queued."
        ),
    )
    
    args = parser.parse_args()
    run_start = time.perf_counter()
    step_durations = {}

    try:
        mass_selector = parse_mass_selector(args.mass_select)
    except ValueError as e:
        print(f"ERROR: {e}")
        return 2
    
    # Handle backward compatibility for single region/era
    if isinstance(args.regions, list) and len(args.regions) == 1 and args.regions[0] in ['region0', 'region1', 'region2']:
        regions = args.regions
    elif args.regions:
        regions = [r for r in args.regions if r in ['region0', 'region1', 'region2']]
    else:
        regions = ['region1']
    
    if isinstance(args.eras, list) and len(args.eras) == 1:
        eras = args.eras
    elif args.eras:
        eras = [e for e in args.eras if e in ['2022', '2022EE', '2023', '2023BPix', 'allYears']]
    else:
        eras = ['2023']
    
    # Build base configuration
    tag_label = f"_{args.tag}" if args.tag else ""
    fit_tag_label = f"_{args.fit_tag}" if args.fit_tag else ""
    folder_path = f"{args.folder_tag}/" if args.folder_tag else ""
    
    # Print global configuration
    print("="*80)
    print("GLOBAL CONFIGURATION")
    print("="*80)
    print(f"  Use data: {args.data}")
    print(f"  Use reweighting: {not args.no_reweight}")
    print(f"  Tag: {args.tag if args.tag else '(none)'}")
    print(f"  Eras: {', '.join(eras)}")
    print(f"  Regions: {', '.join(regions)}")
    print(f"  Category type: {args.category}")
    print(f"  Categories: {get_all_category_ids(args.category)}")
    print(f"  Plot only: {args.plot_only}")
    print(f"  Run combination: {args.combination}")
    print(f"  Caching grid points: {args.caching}")
    print(f"  Set parameters: {args.setParameters if args.setParameters else '(none)'}")
    print(f"  Freeze parameters: {args.freezeParameters if args.freezeParameters else '(none)'}")
    print(f"  CL: {args.cl if args.cl is not None else '(combine default)'}")
    print(f"  Parallel jobs: {args.jobs}")
    print(f"  Preprocessing jobs: {args.prep_jobs if args.prep_jobs > 0 else 'auto'}")
    if mass_selector:
        if mass_selector['mode'] == 'range':
            print(f"  Mass selection: range [{mass_selector['min']}, {mass_selector['max']}]")
        else:
            print(f"  Mass selection: explicit points {mass_selector['points']}")
    else:
        print("  Mass selection: full region range")
    print(f"  Total (era,region) combinations: {len(eras) * len(regions)}")
    print()
    
    # Build configs for all (era, region) combinations
    configs = []
    for era in eras:
        for region in regions:
            # Input folder
            input_folder = f"cards/{folder_path}cards_{region}"
            if args.data:
                input_folder += "_data"
            if args.tag:
                input_folder += f"_{args.tag}"
            
            # Output folder
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
            
            # Era suffix
            run_year_combination = (era == "allYears")
            era_suffix = "allYears" if run_year_combination else era
            
            config = {
                'category_type': args.category,
                'region': region,
                'era': era,
                'era_suffix': era_suffix,
                'input_folder': input_folder,
                'outfolder': outfolder,
                'tag_label': tag_label,
                'fit_tag_label': fit_tag_label,
                'caching': args.caching,
                'cl': args.cl,
                'set_parameters': args.setParameters.strip(),
                'freeze_parameters': args.freezeParameters.strip(),
                'run_combination': args.combination,
                'run_year_combination': run_year_combination,
                'use_data': args.data,
                'use_reweight': not args.no_reweight,
                'plot_only': args.plot_only,
                'mass_selector': mass_selector,
            }
            configs.append(config)
            
            print(f"Config {len(configs)}: era={era}, region={region}")
            print(f"  Input:  {input_folder}")
            print(f"  Output: {outfolder}")
    
    # Create output folders and copy input files for all configs
    for config in configs:
        outfolder = config['outfolder']
        era_suffix = config['era_suffix']
        
        if args.combination:
            combo_dir = Path(outfolder) / f"{args.category}Combination_{era_suffix}"
            combo_dir.mkdir(parents=True, exist_ok=True)
            (combo_dir / "s").mkdir(exist_ok=True)
            (combo_dir / "b").mkdir(exist_ok=True)
        else:
            for cat_id in get_all_category_ids(args.category):
                cat_name = get_category_name(cat_id)
                cat_dir = Path(outfolder) / f"{cat_name}_{era_suffix}"
                cat_dir.mkdir(parents=True, exist_ok=True)
                (cat_dir / "s").mkdir(exist_ok=True)
                (cat_dir / "b").mkdir(exist_ok=True)
        
        # Copy input file
        if not config['run_year_combination']:
            input_root_path = Path(config['input_folder']) / "ee" / "common" / f"Xee_ee_{config['era']}.input.root"
            if input_root_path.exists():
                dest = Path(outfolder) / f"Xee_ee_{config['era']}.input.{config['region']}.root"
                subprocess.run(["cp", str(input_root_path), str(dest)])
    
    if args.plot_only:
        print("Plot-only mode: skipping combine runs")
        return 0
    
    # ========================================================================
    # STEP 1: Process all directories and collect grid jobs for ALL configs
    # ========================================================================
    print("\n" + "="*80)
    print("STEP 1: Collecting grid point jobs for all (era, region) combinations")
    print("="*80)
    step1_start = time.perf_counter()
    
    all_grid_jobs = []
    all_harvest_params = []
    
    for config_idx, config in enumerate(configs, 1):
        print(f"\n--- Processing config {config_idx}/{len(configs)}: {config['era']}, {config['region']} ---")
        
        # Find mass directories for this config
        ee_dir = Path(config['input_folder']) / "ee"
        if not ee_dir.exists():
            print(f"  WARNING: Input directory does not exist: {ee_dir}")
            continue
        
        mass_dirs = [d for d in ee_dir.iterdir() if d.is_dir() and d.name.replace('.', '').replace('-', '').isdigit()]
        mass_dirs = sorted(mass_dirs, key=lambda d: float(d.name))
        
        if not mass_dirs:
            print(f"  WARNING: No mass directories found in {ee_dir}")
            continue
        
        print(f"  Found {len(mass_dirs)} mass directories")
        
        # Process each mass directory for this config (parallelized).
        if args.prep_jobs > 0:
            prep_workers = min(args.prep_jobs, len(mass_dirs))
        else:
            # Keep this lower than grid jobs to avoid excessive I/O contention.
            prep_workers = min(max(4, args.jobs // 4), 32, len(mass_dirs))

        print(f"  step-1 preprocessing workers for this config: {prep_workers}")

        config_jobs_before = len(all_grid_jobs)
        with ThreadPoolExecutor(max_workers=prep_workers) as prep_executor:
            futures = {
                prep_executor.submit(process_mass_directory, (str(mass_dir), config)): mass_dir
                for mass_dir in mass_dirs
            }

            for future in as_completed(futures):
                mass_dir = futures[future]
                try:
                    result = future.result()
                    if result:
                        all_grid_jobs.extend(result['grid_jobs'])
                        all_harvest_params.extend(result['harvest_params'])
                except Exception as e:
                    print(f"  EXCEPTION while preprocessing mass dir {mass_dir}: {e}")
        
        jobs_added = len(all_grid_jobs) - config_jobs_before
        print(f"  Added {jobs_added} grid jobs from this config")

    step_durations['step1_collect'] = time.perf_counter() - step1_start
    print(f"STEP 1 elapsed: {format_duration(step_durations['step1_collect'])}")
    
    print(f"\n" + "="*80)
    print(f"Total grid points to compute across all configs: {len(all_grid_jobs)}")
    print(f"Total harvest targets: {len(all_harvest_params)}")
    print("="*80)
    
    if not all_grid_jobs:
        print("No grid jobs to run!")
        return 0
    
    # ========================================================================
    # STEP 2: Run all grid points in parallel (HIGHLY PARALLEL)
    # ========================================================================
    print("\n" + "="*80)
    print(f"STEP 2: Running {len(all_grid_jobs)} grid points on {args.jobs} cores")
    print("="*80 + "\n")
    step2_start = time.perf_counter()
    
    completed = 0
    failed = 0
    cached = 0
    
    with ThreadPoolExecutor(max_workers=args.jobs) as executor:
        # Submit all jobs
        futures = {executor.submit(run_single_grid_point, job): job for job in all_grid_jobs}
        
        # Process completed jobs
        for future in as_completed(futures):
            job = futures[future]
            try:
                success, point, label, mass, log_path = future.result()
                if success:
                    if log_path is None:
                        cached += 1
                        if cached % 100 == 0:
                            print(f"Progress: {completed} computed, {cached} cached, {failed} failed (of {len(all_grid_jobs)})")
                    else:
                        completed += 1
                        if completed % 10 == 0:
                            print(f"Progress: {completed} computed, {cached} cached, {failed} failed (of {len(all_grid_jobs)})")
                else:
                    failed += 1
                    print(f"FAILED: {label} M{mass} point {point}")
            except Exception as e:
                failed += 1
                print(f"EXCEPTION: {job['label']} M{job['mass']} point {job['point']}: {e}")
    
    print(f"\nGrid computation complete: {completed} computed, {cached} cached, {failed} failed")
    step_durations['step2_grid'] = time.perf_counter() - step2_start
    print(f"STEP 2 elapsed: {format_duration(step_durations['step2_grid'])}")
    
    if failed > 0:
        print(f"WARNING: {failed} grid points failed. Harvesting will likely fail for affected targets.")
    
    # ========================================================================
    # STEP 3: Harvest all results (less parallel, but still parallel per target)
    # ========================================================================
    print("\n" + "="*80)
    print(f"STEP 3: Harvesting {len(all_harvest_params)} targets")
    print("="*80 + "\n")
    step3_start = time.perf_counter()
    
    harvest_failed = 0
    
    # Harvesting is I/O bound and less CPU intensive, use fewer workers
    with ProcessPoolExecutor(max_workers=min(16, args.jobs)) as executor:
        futures = {executor.submit(harvest_limits, **params): params for params in all_harvest_params}
        
        for future in as_completed(futures):
            params = futures[future]
            try:
                success = future.result()
                if not success:
                    harvest_failed += 1
                    print(f"Harvest FAILED: {params['label']} M{params['mass']}")
            except Exception as e:
                harvest_failed += 1
                print(f"Harvest EXCEPTION: {params['label']} M{params['mass']}: {e}")
    
    print(f"\nHarvesting complete: {len(all_harvest_params) - harvest_failed} successful, {harvest_failed} failed")
    step_durations['step3_harvest'] = time.perf_counter() - step3_start
    print(f"STEP 3 elapsed: {format_duration(step_durations['step3_harvest'])}")
    
    # ========================================================================
    # STEP 4: Generate summary plots for all configs
    # ========================================================================
    print("\n" + "="*80)
    print("STEP 4: Generating summary plots for all configs")
    print("="*80 + "\n")
    step4_start = time.perf_counter()
    
    basedir = os.getcwd()
    
    for config_idx, config in enumerate(configs, 1):
        outfolder = config['outfolder']
        input_folder = config['input_folder']
        era_suffix = config['era_suffix']
        region = config['region']
        
        print(f"\nGenerating plots for config {config_idx}/{len(configs)}: {config['era']}, {region}")
        
        if args.combination:
            plot_cmd = [
                "python3", f"{basedir}/scripts/plot_limits_result.py",
                "-o", f"{outfolder}/{args.category}Combination_{era_suffix}",
                "-i", input_folder,
                "-c", f"{args.category}Combination",
                "-r", region,
                "--era", era_suffix
            ]
            if args.fit_tag:
                plot_cmd.extend(["--tag", args.fit_tag])
            
            log_path = f"{outfolder}/{args.category}Combination_{era_suffix}/limits_summary_{region}{fit_tag_label}.log"
            with open(log_path, 'w') as f:
                subprocess.run(plot_cmd, stdout=f, stderr=subprocess.STDOUT)
        else:
            for cat_id in get_all_category_ids(args.category):
                cat_name = get_category_name(cat_id)
                plot_cmd = [
                    "python3", f"{basedir}/scripts/plot_limits_result.py",
                    "-o", f"{outfolder}/{cat_name}_{era_suffix}",
                    "-i", input_folder,
                    "-c", cat_name,
                    "-r", region,
                    "--era", era_suffix
                ]
                if args.fit_tag:
                    plot_cmd.extend(["--tag", args.fit_tag])
                
                log_path = f"{outfolder}/{cat_name}_{era_suffix}/limits_summary_{region}{fit_tag_label}.log"
                print(f"  Creating summary plots for {cat_name}")
                with open(log_path, 'w') as f:
                    subprocess.run(plot_cmd, stdout=f, stderr=subprocess.STDOUT)
                trim_file_to_head_tail(log_path)
        
        # Copy this script to output folder
        script_path = Path(__file__)
        if script_path.exists():
            subprocess.run(["cp", str(script_path), f"{outfolder}/limits_script.py"])

    step_durations['step4_plots'] = time.perf_counter() - step4_start
    total_elapsed = time.perf_counter() - run_start
    step_durations['total'] = total_elapsed
    
    print("\n" + "="*80)
    print("✓ ALL STEPS COMPLETE - SUCCESS")
    print(f"  Processed {len(configs)} (era, region) combinations")
    print(f"  Total grid points: {len(all_grid_jobs)}")
    print(f"  Grid failures: {failed}")
    print(f"  Harvest failures: {harvest_failed}")
    print("="*80)
    print("TIMING SUMMARY")
    print(f"  Step 1 (collect/preprocess): {format_duration(step_durations['step1_collect'])}")
    print(f"  Step 2 (grid points):        {format_duration(step_durations['step2_grid'])}")
    print(f"  Step 3 (harvesting):         {format_duration(step_durations['step3_harvest'])}")
    print(f"  Step 4 (plots):              {format_duration(step_durations['step4_plots'])}")
    print(f"  Total runtime:                {format_duration(step_durations['total'])}")
    print("="*80)
    
    # Return error code if there were failures
    if failed > 0 or harvest_failed > 0:
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())

