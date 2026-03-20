#!/usr/bin/env python3

"""
Parallel workspace creation script for multiple eras and regions.
Queues up all workspace conversion jobs and runs them in parallel using ThreadPoolExecutor,
rather than invoking make_combine_workspace.py separately for each era/region.
"""

import argparse
import subprocess
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(
        description='Parallel workspace creation for multiple eras and regions'
    )
    
    # Era/Region selection
    parser.add_argument('--eras', type=str, default='2022,2022EE,2023,2023BPix',
                        help='Comma-separated list of eras to process')
    parser.add_argument('--regions', type=str, default='region0,region1,region2',
                        help='Comma-separated list of regions to process')
    
    # Dataset configuration
    parser.add_argument('--cat', type=str, default='inclusive', choices=["inclusive", "eta", "dR"],
                        help='Which category to process')
    parser.add_argument('--data', action='store_true',
                        help='Run on data instead of MinBias MC')
    parser.add_argument('--withSyst', action='store_true', default=False,
                        help='Include systematics in the datacard')
    parser.add_argument('--no_reweight', action='store_true',
                        help='Use non-reweighted datasets')
    parser.add_argument('--input_tag', type=str, default='',
                        help='Tag used for dataset creation')
    parser.add_argument('--envelope', action='store_true',
                        help='Use dataset with envelope of background functions')
    parser.add_argument('--binned', action='store_true',
                        help='Use binned data')
    parser.add_argument('--no_res', action='store_true',
                        help='Exclude resonant backgrounds from the fit')
    
    # Output configuration
    parser.add_argument('--tag', type=str, default='',
                        help='Tag to append to output folder name')
    parser.add_argument('--folder_tag', type=str, default='',
                        help='Base folder output name; card folder is created inside')
    
    # Testing options
    parser.add_argument('--signal_multiplier', '-s', type=float, default=1.0,
                        help='Multiplier to apply to signal rates')
    parser.add_argument('--bkg_x2', action='store_true',
                        help='Multiply background rates by 2')
    parser.add_argument('--bkg_div100', action='store_true',
                        help='Divide background rates by 100')
    
    # Parallelization
    parser.add_argument('--n_workers', type=int, default=None,
                        help='Number of parallel workers (default: min(8, n_jobs))')
    parser.add_argument('--dry_run', action='store_true',
                        help='Print jobs without running them')
    
    return parser.parse_args()


def convert_datacard_to_workspace(job):
    """Run workspace creation for a single era/region combination."""
    era = job['era']
    region = job['region']
    
    cmd = ['python3', 'make_combine_workspace.py']
    
    # Add all configuration arguments
    for key, value in job['args'].items():
        if value is True:
            cmd.append(f'--{key}')
        elif value is not False and value is not None and value != '':
            if isinstance(value, float):
                cmd.extend([f'--{key}', str(value)])
            else:
                cmd.extend([f'--{key}', str(value)])
    
    cmd.extend(['--era', era, '--region', region])
    
    # Build log file path
    log_dir = f"logs/{job['log_tag']}" if job['log_tag'] else "logs"
    os.makedirs(log_dir, exist_ok=True)
    log_file = f"{log_dir}/workspace_{job['cat']}_{region}_{job['data_tag']}_{era}.log"
    
    try:
        with open(log_file, 'w') as f:
            proc = subprocess.run(cmd, check=True, stdout=f, stderr=subprocess.STDOUT, text=True)
        return (True, f"{era:8s} {region:8s} - OK", log_file)
    except subprocess.CalledProcessError as e:
        with open(log_file, 'a') as f:
            f.write(f"\n>> Process exited with code {e.returncode}\n")
        return (False, f"{era:8s} {region:8s} - FAILED", log_file)
    except Exception as e:
        return (False, f"{era:8s} {region:8s} - ERROR: {str(e)}", log_file)


def main():
    args = parse_args()
    
    # Parse comma-separated lists
    eras = [e.strip() for e in args.eras.split(',')]
    regions = [r.strip() for r in args.regions.split(',')]
    
    print(f">> Workspace creation for {len(eras)} eras × {len(regions)} regions = {len(eras)*len(regions)} jobs")
    print(f"   Eras:   {', '.join(eras)}")
    print(f"   Regions: {', '.join(regions)}")
    
    # Build job queue
    jobs = []
    arg_dict = {
        'cat': args.cat,
        'data': args.data,
        'withSyst': args.withSyst,
        'no_reweight': args.no_reweight,
        'input_tag': args.input_tag,
        'envelope': args.envelope,
        'binned': args.binned,
        'no_res': args.no_res,
        'tag': args.tag,
        'signal_multiplier': args.signal_multiplier,
        'bkg_x2': args.bkg_x2,
        'bkg_div100': args.bkg_div100,
    }
    
    data_tag = "data" if args.data else "mc"
    
    for era in eras:
        for region in regions:
            jobs.append({
                'era': era,
                'region': region,
                'args': arg_dict,
                'cat': args.cat,
                'data_tag': data_tag,
                'log_tag': args.folder_tag,
            })
    
    if args.dry_run:
        print("\n>> DRY RUN - Jobs that would be created:\n")
        for i, job in enumerate(jobs, 1):
            era = job['era']
            region = job['region']
            print(f"  {i:2d}. Era={era:8s} Region={region:8s}")
        return
    
    if not jobs:
        print(">> No jobs to process!")
        return
    
    # Determine number of workers
    n_workers = args.n_workers or min(8, len(jobs))
    print(f"\n>> Using {n_workers} parallel workers")
    
    completed = 0
    failed = 0
    failed_jobs = []
    start_time = time.perf_counter()
    
    with ThreadPoolExecutor(max_workers=n_workers) as executor:
        futures = {executor.submit(convert_datacard_to_workspace, job): job for job in jobs}
        
        for future in as_completed(futures):
            try:
                success, msg, log_file = future.result()
                if success:
                    completed += 1
                    if completed % max(1, len(jobs)//10) == 0 or completed == len(jobs):
                        print(f'  >> {msg}')
                else:
                    failed += 1
                    failed_jobs.append((msg, log_file))
                    print(f'  >> {msg}')
            except Exception as e:
                failed += 1
                print(f'  >> EXCEPTION: {str(e)}')
    
    elapsed = time.perf_counter() - start_time
    print(f"\n>> Workspace creation complete: {completed} succeeded, {failed} failed in {elapsed:.1f}s", flush=True)
    
    if failed_jobs:
        print("\n>> Failed jobs:")
        for msg, log_file in failed_jobs:
            print(f"   {msg} -> {log_file}")


if __name__ == '__main__':
    main()
