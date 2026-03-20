#!/usr/bin/env python3
"""
HTCondor DAGMan-based parallelization for AsymptoticLimits grid computation.
This version uses DAGMan to properly handle job dependencies.
"""

import os
import sys
import argparse
from pathlib import Path
import subprocess
from textwrap import dedent


class CategoryConfig:
    """Helper class for category name/label mappings."""
    
    @staticmethod
    def get_category_label(name):
        """Map category name to label (e.g., etaHigh -> etap0p6)."""
        mapping = {
            "etaHigh": "etap0p6",
            "etaLow": "etam0p6",
            "dRHigh": "dRp0p3",
            "dRLow": "dRm0p3",
            "inclusive": "inclusive",
        }
        return mapping.get(name, "unknown")
    
    @staticmethod
    def get_category_name(cat_id):
        """Map category ID to name."""
        mapping = {
            0: "etaHigh",
            1: "etaLow",
            2: "dRHigh",
            3: "dRLow",
            4: "inclusive",
        }
        return mapping.get(cat_id, "unknown")
    
    @staticmethod
    def get_all_category_ids(category_type):
        """Get all category IDs for a given type."""
        mapping = {
            "eta": [0, 1],
            "dR": [2, 3],
            "inclusive": [4],
        }
        return mapping.get(category_type, [0, 1])


def get_points_for_mass(mass, region):
    """
    Get grid points for a given mass value and region.
    Points are tuned per region for optimal scan resolution.
    """
    if region == "region0":
        if mass < 0.65:
            return [0.1, 0.2, 0.25, 0.3, 0.35, 0.37, 0.39, 0.4, 0.45, 0.5, 0.55, 
                    0.57, 0.6, 0.7, 0.9, 1, 1.2, 1.5, 1.7, 2, 5, 10]
        elif mass < 0.9:
            return [0.0005, 0.001, 0.002, 0.0025, 0.00275, 0.003, 0.0035, 0.004, 
                    0.005, 0.007, 0.008, 0.009, 0.01, 0.0125, 0.015, 0.0175, 0.018, 
                    0.02, 0.021, 0.023, 0.025, 0.027, 0.028, 0.03, 0.05, 0.06, 0.07]
        else:
            return [0.007, 0.01, 0.015, 0.017, 0.02, 0.0225, 0.025, 0.03, 0.035, 
                    0.04, 0.045, 0.05, 0.55, 0.06, 0.065, 0.07, 0.08, 0.09, 0.1, 
                    0.11, 0.12, 0.13, 0.15, 0.16, 0.17, 0.19, 0.2, 0.21, 0.23, 0.25, 
                    0.27, 0.29, 0.3, 0.32, 0.33, 0.34, 0.35, 0.37, 0.39, 0.4, 0.41, 
                    0.42, 0.43, 0.45, 0.5, 0.55, 0.57, 0.6, 0.62, 0.65, 0.7, 0.8, 
                    0.1, 2, 5, 10]
    
    # elif region == "region1":
    #     if 3.05 <= mass <= 3.15:
    #         return [1, 1.5, 2, 2.5, 3.5, 4, 4.2, 4.3, 4.6, 4.7, 5.1, 5.4, 6, 7]
    #     elif 3.67 <= mass <= 3.73:
    #         return [0.01, 0.025, 0.05, 0.075, 0.1, 0.15, 0.2, 0.25, 0.27, 0.3, 
    #                 0.35, 0.4, 0.5, 0.9, 1, 10]
    #     else:
    #         return [0.001, 0.005, 0.0100, 0.0207, 0.0336, 0.0546, 0.0886, 0.1000, 
    #                 0.2, 0.3, 0.8, 1, 5, 10, 20]

    elif region == "region1":
        if 3.05 <= mass <= 3.15:
            return [0.1, 1]
        elif 3.67 <= mass <= 3.73:
            return [0.01, 0.025, 0.05, 0.075, 0.1, 0.15, 0.2, 0.25, 0.27, 0.3, 
                    0.35, 0.4, 0.5, 0.9, 1, 10]
        else:
            return [0.001, 0.005, 0.0100]
    
    elif region == "region2":
        if 7 <= mass < 8:
            return [0.0100, 0.0113, 0.0127, 0.0144, 0.0162, 0.0183, 0.0207, 0.0234, 
                    0.0264, 0.0298, 0.0336, 0.0379, 0.0428, 0.0483, 0.0546, 0.0616, 
                    0.0695, 0.0785, 0.0886, 0.1000, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 
                    0.8, 0.9, 1, 2, 3, 5, 7, 10, 12, 15, 17, 20, 25, 30, 35, 40, 
                    50, 60]
        elif 8 <= mass < 9:
            return [0.1000, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1, 2, 3, 5, 7, 
                    10, 12, 15, 17, 20, 25, 30, 35, 40, 50, 60]
        elif 9 <= mass < 12:
            return [1, 2, 3, 4, 5, 6, 10, 12, 15, 17, 20, 25, 30, 35, 40, 50, 60, 
                    70, 80, 90, 100, 105, 110, 115, 120]
        else:
            return [0.001, 0.005, 0.006, 0.007, 0.008, 0.009, 0.0100, 0.0113, 
                    0.0127, 0.0144, 0.0162, 0.0183, 0.0207, 0.0234, 0.0264, 0.0298, 
                    0.0336, 0.0379, 0.0428, 0.0483, 0.0546, 0.0616, 0.0695, 0.0785, 
                    0.0886, 0.1000, 0.2, 0.3]
    
    else:
        raise ValueError(f"Unknown region: {region}")


def create_worker_script(output_path):
    """Create the HTCondor worker script for running individual grid points."""
    content = dedent("""\
        #!/bin/bash
        set -e
        MASS=$1; LABEL=$2; INPUT_ROOT=$3; POINT=$4
        FREEZE_PARAMS=$5; REGION=$6; USE_SB_SNAPSHOT=$7; FIT_TAG_LABEL=$8; WORK_DIR=$9

        cd "$WORK_DIR"
        source /cvmfs/cms.cern.ch/cmsset_default.sh
        eval `scramv1 runtime -sh`

        RMIN=0; RMAX=10
        (( $(echo "$MASS > 9" | bc -l) )) && RMIN=1
        (( $(echo "$MASS > 8.5" | bc -l) )) && RMAX=120

        if [ "$USE_SB_SNAPSHOT" = "true" ]; then
            combine -M AsymptoticLimits "$INPUT_ROOT" --rMin $RMIN --rMax $RMAX \\
                    --snapshotName MultiDimFit --singlePoint "$POINT" \\
                    -n "_${LABEL}${FIT_TAG_LABEL}_point_${POINT}" -v 3
        else
            combine -M AsymptoticLimits "$INPUT_ROOT" --rMin $RMIN --rMax $RMAX \\
                    --singlePoint "$POINT" -n "_${LABEL}${FIT_TAG_LABEL}_point_${POINT}" -v 3
        fi
        """)
    with open(output_path, 'w') as f:
        f.write(content)
    os.chmod(output_path, 0o755)


def create_merge_script(output_path):
    """Create the HTCondor merge script for combining grid results."""
    content = dedent("""\
        #!/bin/bash
        set -e
        MASS=$1; LABEL=$2; INPUT_ROOT=$3; REGION=$4; FIT_TAG_LABEL=$5; WORK_DIR=$6; POINTS="$7"; PLOT_DIR=$8

        cd "$WORK_DIR"
        source /cvmfs/cms.cern.ch/cmsset_default.sh
        eval `scramv1 runtime -sh`

        GRID_FILES=()
        for point in $POINTS; do
            GRID_FILES+=("higgsCombine_${LABEL}${FIT_TAG_LABEL}_point_${point}.AsymptoticLimits.mH120.root")
        done

        hadd -f limits_from_grid_${LABEL}.root "${GRID_FILES[@]}"

        RMIN=0; RMAX=10
        (( $(echo "$MASS > 9" | bc -l) )) && RMIN=1
        (( $(echo "$MASS > 8.5" | bc -l) )) && RMAX=120

        combine -M AsymptoticLimits "$INPUT_ROOT" --rMin $RMIN --rMax $RMAX \\
                --getLimitFromGrid limits_from_grid_${LABEL}.root \\
                -n "_${LABEL}${FIT_TAG_LABEL}" -v 3

        # Copy final limit results to plot directory
        mkdir -p "$PLOT_DIR/$LABEL/M$MASS"
        cp "fitAsymptotic_${LABEL}${FIT_TAG_LABEL}.log" \
           "higgsCombine_${LABEL}${FIT_TAG_LABEL}.AsymptoticLimits.mH120.root" \
           "$PLOT_DIR/$LABEL/M$MASS/"
        [ -f combine_logger.out ] && cp combine_logger.out "$PLOT_DIR/$LABEL/M$MASS/combine_logger_${LABEL}${FIT_TAG_LABEL}.out"
        
        echo "Results copied to $PLOT_DIR/$LABEL/M$MASS/"
        """)
    with open(output_path, 'w') as f:
        f.write(content)
    os.chmod(output_path, 0o755)


def create_plot_script(output_path, basedir, outfolder, input_folder, categories, region, fit_tag):
    """Create the POST script for generating summary plots after all jobs complete."""
    # Start with the header
    content = dedent(f"""\
        #!/bin/bash
        # DAGMan POST script to generate summary plots after all limit calculations complete

        set -e

        BASEDIR="{basedir}"
        OUTFOLDER="{outfolder}"
        INPUT_FOLDER="{input_folder}"
        REGION="{region}"
        FIT_TAG="{fit_tag}"
        FIT_TAG_LABEL=""
        if [[ -n "$FIT_TAG" ]]; then
            FIT_TAG_LABEL="_$FIT_TAG"
        fi

        echo "=========================================="
        echo "Generating summary plots..."
        echo "=========================================="

        """)
    
    # Add plotting commands for each category
    for cat_name in categories:
        content += f'echo "Creating summary plots for category {cat_name}"\n'
        plot_cmd = f'python3 "$BASEDIR/scripts/plot_limits_result.py"'
        plot_cmd += f' -o "$OUTFOLDER/{cat_name}"'
        plot_cmd += f' -i "$INPUT_FOLDER"'
        plot_cmd += f' -c {cat_name}'
        plot_cmd += f' -r "$REGION"'
        if fit_tag:
            plot_cmd += ' --tag "$FIT_TAG"'
        
        content += f'{plot_cmd} &> "$OUTFOLDER/{cat_name}/limits_summary_${{REGION}}${{FIT_TAG_LABEL}}.log"\n'
    
    # Add footer
    content += dedent("""
        echo "=========================================="
        echo "Summary plots complete!"
        echo "=========================================="
        """)
    
    with open(output_path, 'w') as f:
        f.write(content)
    os.chmod(output_path, 0o755)


def prepare_workspace_for_combination(work_dir, config, dry_run=False):
    """
    Prepare combination datacards and workspaces before job submission.
    This handles combineCards.py and text2workspace.py calls.
    
    Returns the path to the workspace ROOT file, or None if preparation failed.
    """
    import subprocess
    
    category_type = config['category_type']
    cat_ids = CategoryConfig.get_all_category_ids(category_type)
    
    # Check that all category datacards exist
    card_files = []
    for cat_id in cat_ids:
        card_name = work_dir / f"Xee_ee_{cat_id}_2023.txt"
        if not card_name.exists():
            if dry_run:
                print(f"    Warning: missing datacard {card_name}")
            return None
        card_files.append(card_name)
    
    txt_file = work_dir / f"Xee_ee_{category_type}Combination_2023.txt"
    root_file = work_dir / f"Xee_ee_{category_type}Combination_2023.root"
    
    if dry_run:
        print(f"    Would combine cards: {[f.name for f in card_files]} -> {txt_file.name}")
        print(f"    Would create workspace: {root_file.name}")
        return root_file
    
    # Skip if already exists
    if root_file.exists():
        return root_file
    
    # Combine cards
    print(f"    Combining cards into {txt_file.name}")
    with open(txt_file, 'w') as outf:
        subprocess.run(['combineCards.py'] + [str(f) for f in card_files], 
                      stdout=outf, cwd=work_dir, check=True)
    
    # Create workspace
    print(f"    Building workspace {root_file.name}")
    subprocess.run(['text2workspace.py', str(txt_file)], cwd=work_dir, check=True)
    
    return root_file


def create_dag_for_mass(mass, work_dir, config, scripts, paths, dry_run=False):
    """
    Create a DAG file for a single mass point.
    
    Args:
        mass: Mass value
        work_dir: Working directory path
        config: Configuration dict
        scripts: Dict with 'worker' and 'merge' script paths
        paths: Dict with 'dag_dir', 'log_dir' paths
        dry_run: If True, print information without creating files
    """
    if not work_dir.exists():
        return
    
    # Check mass limits - only compute limits in the tighter range
    if mass < config['min_mass_limit'] or mass > config['max_mass_limit']:
        return
    
    dag_file = paths['dag_dir'] / f"limits_M{mass}.dag"
    
    if dry_run:
        print(f"\n{'='*60}")
        print(f"Mass Point: {mass} GeV")
        print(f"{'='*60}")
    else:
        print(f"Creating DAG for mass {mass}: {dag_file}")
    
    points = get_points_for_mass(mass, config['region'])
    
    # Determine categories and prepare workspaces
    if config['run_combination']:
        # For combination, prepare the combined datacard/workspace first
        if not dry_run:
            root_file = prepare_workspace_for_combination(work_dir, config, dry_run)
            if not root_file:
                print(f"  Skipping mass {mass}: combination workspace preparation failed")
                return None
        
        categories = [(f"{config['category_type']}Combination", f"{config['category_type']}Combination")]
    else:
        cat_ids = CategoryConfig.get_all_category_ids(config['category_type'])
        categories = [(cid, CategoryConfig.get_category_name(cid)) for cid in cat_ids]
        
        # For individual categories, prepare workspaces by running text2workspace
        if not dry_run:
            for cat_id, _ in categories:
                txt_file = work_dir / f"Xee_ee_{cat_id}_2023.txt"
                root_file = work_dir / f"Xee_ee_{cat_id}_2023.root"
                if txt_file.exists() and not root_file.exists():
                    print(f"    Creating workspace for category {cat_id}")
                    subprocess.run(['text2workspace.py', str(txt_file)], cwd=work_dir, check=True)
    
    if dry_run:
        print(f"Working directory: {work_dir}")
        print(f"Categories: {', '.join([label for _, label in categories])}")
        print(f"Grid points ({len(points)}): {', '.join(map(str, points[:10]))}{' ...' if len(points) > 10 else ''}")
        print()
    
    for cat_id, label in categories:
        root_file = work_dir / f"Xee_ee_{cat_id}_2023.root"
        if not root_file.exists():
            if dry_run:
                print(f"  ⚠ Category {label}: ROOT file not found - {root_file}")
            continue
        
        if dry_run:
            print(f"  Category: {label}")
            print(f"    Input: {root_file}")
            print(f"    Grid jobs: {len(points)}")
            
            # Show example combine commands
            example_point = points[0]
            rmin = 1 if mass > 9 else 0
            rmax = 120 if mass > 8.5 else 10
            
            print(f"    Example grid point command (point={example_point}):")
            if config['use_sb_snapshot'] == 'true':
                print(f"      combine -M AsymptoticLimits {root_file} --rMin {rmin} --rMax {rmax} \\")
                print(f"              --snapshotName MultiDimFit --singlePoint {example_point} \\")
                print(f"              -n \"_{label}{config['fit_tag_label']}_point_{example_point}\" -v 3")
            else:
                print(f"      combine -M AsymptoticLimits {root_file} --rMin {rmin} --rMax {rmax} \\")
                print(f"              --singlePoint {example_point} \\")
                print(f"              -n \"_{label}{config['fit_tag_label']}_point_{example_point}\" -v 3")
            
            print(f"    Merge command:")
            print(f"      hadd -f limits_from_grid_{label}.root <{len(points)} grid files>")
            print(f"      combine -M AsymptoticLimits {root_file} --rMin {rmin} --rMax {rmax} \\")
            print(f"              --getLimitFromGrid limits_from_grid_{label}.root \\")
            print(f"              -n \"_{label}{config['fit_tag_label']}\" -v 3")
            print()
            continue
        
        # Normal execution: create JDL files
        jdl_base = paths['dag_dir'] / f"{label}_M{mass}"
        
        # Create JDL for grid point jobs
        grid_jdl = f"{jdl_base}_grid.jdl"
        with open(grid_jdl, 'w') as jdl:
            jdl.write(f"executable = {scripts['worker']}\n")
            jdl.write(f"arguments = {mass} {label} {root_file} $(Point) ")
            jdl.write(f'"{config["freeze_params"]}" {config["region"]} ')
            jdl.write(f'{config["use_sb_snapshot"]} {config["fit_tag_label"]} {work_dir}\n')
            jdl.write(f'output = {paths["log_dir"]}/grid_{label}_M{mass}_$(Point).out\n')
            jdl.write(f'error = {paths["log_dir"]}/grid_{label}_M{mass}_$(Point).err\n')
            jdl.write(f'log = {paths["log_dir"]}/grid_{label}_M{mass}.log\n')
            jdl.write('+JobFlavour = "longlunch"\n')
            jdl.write('queue Point from (\n')
            for point in points:
                jdl.write(f'{point}\n')
            jdl.write(')\n')
        
        # Create JDL for merge job
        merge_jdl = f"{jdl_base}_merge.jdl"
        points_str = ' '.join(str(p) for p in points)
        with open(merge_jdl, 'w') as jdl:
            jdl.write(f"executable = {scripts['merge']}\n")
            jdl.write(f'arguments = {mass} {label} {root_file} {config["region"]} ')
            jdl.write(f'{config["fit_tag_label"]} {work_dir} "{points_str}" {config["plot_dir"]}\n')
            jdl.write(f'output = {paths["log_dir"]}/merge_{label}_M{mass}.out\n')
            jdl.write(f'error = {paths["log_dir"]}/merge_{label}_M{mass}.err\n')
            jdl.write(f'log = {paths["log_dir"]}/merge_{label}_M{mass}_merge.log\n')
            jdl.write('+JobFlavour = "espresso"\n')
            jdl.write('queue 1\n')
    
    if dry_run:
        return None
    
    # Create DAG file
    with open(dag_file, 'w') as dag:
        dag.write(f"# DAG for mass {mass}\n")
        
        for cat_id, label in categories:
            root_file = work_dir / f"Xee_ee_{cat_id}_2023.root"
            if not root_file.exists():
                continue
            
            jdl_base = paths['dag_dir'] / f"{label}_M{mass}"
            grid_jdl = f"{jdl_base}_grid.jdl"
            merge_jdl = f"{jdl_base}_merge.jdl"
            
            # Add to DAG with dependencies
            dag.write(f'\n# Category: {label}\n')
            
            # Define grid jobs
            for point in points:
                job_name = f"grid_{label}_{point}"
                dag.write(f'JOB {job_name} {grid_jdl}\n')
                dag.write(f'VARS {job_name} Point="{point}"\n')
            
            # Define merge job
            merge_job = f"merge_{label}"
            dag.write(f'JOB {merge_job} {merge_jdl}\n')
            
            # Set up dependencies: merge depends on all grid jobs
            dag.write('PARENT ')
            for point in points:
                dag.write(f'grid_{label}_{point} ')
            dag.write(f'CHILD {merge_job}\n')
    
    return dag_file


def submit_dag(dag_file, dry_run=False):
    """Submit a DAG file to HTCondor."""
    if dry_run:
        print(f"  [DRY RUN] Would submit: {dag_file}")
        return
    
    try:
        subprocess.run(['condor_submit_dag', str(dag_file)], check=True)
        print(f"  ✓ Submitted: {dag_file}")
    except subprocess.CalledProcessError as e:
        print(f"  ✗ Failed to submit {dag_file}: {e}")


def main():
    parser = argparse.ArgumentParser(
        description='HTCondor DAGMan-based parallelization for AsymptoticLimits'
    )
    parser.add_argument('--tag', default='', help='Tag appended to input/output folder names')
    parser.add_argument('--fit_tag', default='', help='Tag appended to output filenames only')
    parser.add_argument('--category', '--cat', default='eta', 
                        choices=['eta', 'dR', 'inclusive'],
                        help='Category type')
    parser.add_argument('--region', default='region1',
                        choices=['region0', 'region1', 'region2'],
                        help='Mass region')
    parser.add_argument('--no_reweight', action='store_true',
                        help='Use cards without reweighting')
    parser.add_argument('--data', action='store_true',
                        help='Run on data instead of MC')
    parser.add_argument('--use_sb_snapshot', action='store_true',
                        help='Use S+B MultiDimFit snapshot as input for limits')
    parser.add_argument('--combination', action='store_true',
                        help='Run combination of categories instead of individual fits')
    parser.add_argument('--dry_run', action='store_true',
                        help='Generate scripts and print commands without submitting jobs')
    
    args = parser.parse_args()
    
    # Setup paths
    basedir = Path.cwd()
    
    # Configure input folder
    input_folder = "cards/cards_noReweight" if args.no_reweight else "cardscards"
    input_folder = f"{input_folder}_{args.region}"
    
    # Configure output folder (for plots only)
    outfolder = Path("/eos/home-n/npalmeri/www/DiElectron/sensitivity/fitDiagnostics_grid_condortest")
    
    # Configure HTCondor working directory
    condor_base = basedir / "condor"
    
    if args.data:
        outfolder = Path(str(outfolder) + "_data")
        input_folder = f"{input_folder}_data"
    elif not args.no_reweight:
        outfolder = Path(str(outfolder) + "_reweight_categories")
    else:
        outfolder = Path(str(outfolder) + "_noReweight")
    
    if args.tag:
        input_folder = f"{input_folder}_{args.tag}"
        outfolder = Path(str(outfolder) + f"_{args.tag}")
    
    outfolder = outfolder / "mu0"
    input_folder = basedir / input_folder
    
    # Create HTCondor directory structure
    # Each submission gets its own timestamped folder
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    condor_run_dir = condor_base / f"{args.region}_{args.category}_{timestamp}"
    condor_logs = condor_run_dir / "logs"
    condor_dags = condor_run_dir / "dags"
    condor_scripts = condor_run_dir / "scripts"
    
    condor_logs.mkdir(parents=True, exist_ok=True)
    condor_dags.mkdir(parents=True, exist_ok=True)
    condor_scripts.mkdir(parents=True, exist_ok=True)
    
    # Create plots output directory
    outfolder.mkdir(parents=True, exist_ok=True)
    
    # Mass ranges by region
    # NOTE: region definition vs limit range
    # - MIN_MASS/MAX_MASS: full mass range for cards/fits
    # - MIN_MASS_LIMIT/MAX_MASS_LIMIT: tighter range where limits are computed (boundaries unreliable)
    mass_ranges = {
        'region0': {
            'mass' : [0.3, 2.4],
            'mass_limit' : [0.5, 2.2],
        },
        'region1': {
            'mass' : [1.6, 4.6],
            'mass_limit' : [1.8, 4.4],
        },
        'region2': {
            'mass' : [3.8, 11.0],
            'mass_limit' : [4.0, 10.8],
        },
    }
    region_ranges = mass_ranges[args.region]
    min_mass, max_mass = region_ranges['mass']
    min_mass_limit, max_mass_limit = region_ranges['mass_limit']
    
    # Create worker and merge scripts in condor scripts directory
    worker_script = condor_scripts / "condor_worker.sh"
    merge_script = condor_scripts / "condor_merge.sh"
    create_worker_script(worker_script)
    create_merge_script(merge_script)
    
    # Determine which categories we're processing
    if args.combination:
        plot_categories = [f"{args.category}Combination"]
    else:
        cat_ids = CategoryConfig.get_all_category_ids(args.category)
        plot_categories = [CategoryConfig.get_category_name(cid) for cid in cat_ids]
    
    # Create plotting POST script in condor scripts directory
    plot_script = condor_scripts / "condor_plot.sh"
    create_plot_script(plot_script, basedir, outfolder, input_folder, 
                      plot_categories, args.region, args.fit_tag if args.fit_tag else "")
    
    # Configuration
    config = {
        'region': args.region,
        'category_type': args.category,
        'run_combination': args.combination,
        'use_sb_snapshot': 'true' if args.use_sb_snapshot else 'false',
        'freeze_params': '',
        'fit_tag_label': f"_{args.fit_tag}" if args.fit_tag else '',
        'min_mass': min_mass,
        'min_mass_limit': min_mass_limit,
        'max_mass': max_mass,
        'max_mass_limit': max_mass_limit,
        'plot_dir': outfolder,
    }
    
    scripts = {
        'worker': worker_script,
        'merge': merge_script,
        'plot': plot_script,
    }
    
    paths = {
        'dag_dir': condor_dags,
        'log_dir': condor_logs,
    }
    
    # Print configuration
    print("=" * 60)
    print("HTCondor DAGMan Submission Configuration")
    if args.dry_run:
        print(" [DRY RUN MODE - No jobs will be submitted]")
    print("=" * 60)
    print(f"  Region:         {args.region}")
    print(f"  Category:       {args.category}")
    print(f"  Input folder:   {input_folder}")
    print(f"  Plot folder:    {outfolder}")
    print(f"  HTCondor base:  {condor_run_dir}")
    print(f"    - DAG files:  {condor_dags}")
    print(f"    - Log files:  {condor_logs}")
    print(f"    - Scripts:    {condor_scripts}")
    print(f"  Data mode:      {args.data}")
    print(f"  Combination:    {args.combination}")
    print(f"  Mass range:     {min_mass} - {max_mass} (limits: {min_mass_limit} - {max_mass_limit})")
    print("=" * 60)
    print()
    
    # Create output folder structure for plots only
    if args.combination:
        combination_name = f"{args.category}Combination"
        print(f"Creating plot output folders for {combination_name}")
        (outfolder / combination_name).mkdir(parents=True, exist_ok=True)
    else:
        cat_ids = CategoryConfig.get_all_category_ids(args.category)
        for cat_id in cat_ids:
            cat_name = CategoryConfig.get_category_name(cat_id)
            print(f"Creating plot output folders for {cat_name}")
            (outfolder / cat_name).mkdir(parents=True, exist_ok=True)
    
    # Copy input .root file to plot output folder
    input_root_file = input_folder / "ee" / "common" / "Xee_ee.input.root"
    if input_root_file.exists():
        import shutil
        output_root_file = outfolder / f"Xee_ee.input.{args.region}.root"
        shutil.copy2(input_root_file, output_root_file)
        print(f"Copied input file: {input_root_file} -> {output_root_file}")
    else:
        print(f"Warning: Input root file not found: {input_root_file}")
    print()
    
    # Process all mass directories
    ee_dir = input_folder / "ee"
    if not ee_dir.exists():
        print(f"Error: Input directory not found: {ee_dir}")
        sys.exit(1)
    
    dag_files = []
    for mass_dir in sorted(ee_dir.iterdir()):
        if mass_dir.is_dir():
            try:
                mass = float(mass_dir.name)
                # TEMPORARY TEST: only run on 2 mass points
                if mass > 1.9:
                    continue
                dag_file = create_dag_for_mass(mass, mass_dir, config, scripts, paths, args.dry_run)
                if dag_file:
                    dag_files.append(dag_file)
            except ValueError:
                print(f"Skipping non-numeric directory: {mass_dir.name}")
    
    if args.dry_run:
        print("\n" + "=" * 60)
        print("DRY RUN COMPLETE")
        print("=" * 60)
        print(f"  Would create {len(dag_files)} DAG files")
        print(f"  Scripts generated:")
        print(f"    - {worker_script}")
        print(f"    - {merge_script}")
        print(f"    - {plot_script}")
        print("\n  To actually submit jobs, run without --dry_run flag")
        print("=" * 60)
        return
    
    # Create master DAG that coordinates all mass-point DAGs and plotting
    master_dag = condor_dags / "master_limits.dag"
    print(f"\nCreating master DAG: {master_dag}")
    
    with open(master_dag, 'w') as dag:
        dag.write("# Master DAG coordinating all mass point calculations and plotting\n\n")
        
        # Add SUBDAG nodes for each mass
        subdag_jobs = []
        for i, dag_file in enumerate(dag_files):
            job_name = f"mass_{dag_file.stem}"
            subdag_jobs.append(job_name)
            dag.write(f"SUBDAG EXTERNAL {job_name} {dag_file}\n")
        
        dag.write("\n# Plotting job - runs after all mass calculations complete\n")
        
        # Create a simple JDL for the plotting job
        plot_jdl = condor_dags / "plot_results.jdl"
        with open(plot_jdl, 'w') as jdl:
            jdl.write(f"executable = {plot_script}\n")
            jdl.write(f"output = {condor_logs}/plot_results.out\n")
            jdl.write(f"error = {condor_logs}/plot_results.err\n")
            jdl.write(f"log = {condor_logs}/plot_results.log\n")
            jdl.write('+JobFlavour = "espresso"\n')
            jdl.write('queue 1\n')
        
        dag.write(f"JOB plot_all {plot_jdl}\n")
        
        # Set up dependency: plotting depends on all mass calculations
        dag.write("\n# Dependencies: plotting runs after all mass point DAGs complete\n")
        dag.write("PARENT ")
        dag.write(" ".join(subdag_jobs))
        dag.write(" CHILD plot_all\n")
    
    # Submit master DAG
    print(f"\nSubmitting master DAG...")
    submit_dag(master_dag, args.dry_run)
    
    print("\n" + "=" * 60)
    print("DAG submission complete!")
    print("=" * 60)
    print(f"  Monitor with:  condor_q")
    print(f"  Master DAG:    {master_dag}")
    print(f"  Sub-DAGs in:   {condor_dags}")
    print(f"  Logs in:       {condor_logs}")
    print()
    print("The plotting script will run automatically after all jobs complete.")
    print(f"Plot script: {plot_script}")
    print("=" * 60)


if __name__ == '__main__':
    main()
