#!/usr/bin/env python3
import os
import subprocess
from typing import Iterable

FOLDER_TEMPLATE = "/eos/home-n/npalmeri/DiEleAnalyzer/Xee_fits/sensitivity_scan/cards/260430/cards_{region}_data_envelope_allCorrections_binned/ee/{mass}"
PLOT_DIR = "/eos/home-n/npalmeri/www/DiElectron/sensitivity/260430/fitDiagnostics_grid_data_envelope_allCorrections_binned/mu0/nll_scans/asimov_postfit_bonly"
# PLOT_DIR = "/eos/home-n/npalmeri/www/DiElectron/sensitivity/260430/fitDiagnostics_grid_data_envelope_allCorrections_binned/mu0/nll_scans/asimov_postfit_sb_breakdown"
# PLOT_DIR = "/eos/home-n/npalmeri/www/DiElectron/sensitivity/260430/fitDiagnostics_grid_data_envelope_allCorrections_binned/mu0/nll_scans/asimov_postfit_sb_r0p1_corrected"
# PLOT_DIR = "/eos/home-n/npalmeri/www/DiElectron/sensitivity/260430/fitDiagnostics_grid_data_envelope_allCorrections_binned/mu0/nll_scans/asimov_postfit_sb_r1_corrected"
# PLOT_DIR = "/eos/home-n/npalmeri/www/DiElectron/sensitivity/260430/fitDiagnostics_grid_data_envelope_allCorrections_binned/mu0/nll_scans/asimov_postfit_bonly_r1_corrected"
# PLOT_DIR = "/eos/home-n/npalmeri/www/DiElectron/sensitivity/260430/fitDiagnostics_grid_data_envelope_allCorrections_binned/mu0/nll_scans/asimov_postfit_bonly_r0p1_corrected"
# PLOT_DIR = "/eos/home-n/npalmeri/www/DiElectron/sensitivity/260430/fitDiagnostics_grid_data_envelope_allCorrections_binned/mu0/nll_scans/asimov_postfit_bonly_r10_corrected"

POINTS = [
	# ("region0", "1.2", (-50,10)),
	# ("region0", "2.1", (-2,20)),
	# ("region1", "3.3", (-6,5)),
	# ("region1", "4.8", (-1,1)),
	# ("region2", "5.8", (0,10)),
	# ("region2", "7.5", (-1,5)),
    ### ASIMOV
	("region0", "1.2", (-50,50)),
	("region0", "2.1", (-15,15)),
	("region1", "3.3", (-1,1)),
	("region1", "4.8", (-1,1)),
	("region2", "5.8", (-1,1)),
	("region2", "7.5", (-0.5,0.5)),
	# ### ASIMOV RANGES, r=1
	# ("region0", "1.2", (-30,30)),
	# ("region0", "2.1", (-10,15)),
	# ("region1", "3.3", (-1,3)),
	# ("region1", "4.8", (-1,4)),
	# ("region2", "5.8", (-0.2,4)),
	# ("region2", "7.5", (0,4)),
	# ## ASIMOV RANGES, r=0.1
	# ("region0", "1.2", (-30,30)),
	# ("region0", "2.1", (-10,15)),
	# ("region1", "3.3", (-1,3)),
	# ("region1", "4.8", (-1,4)),
	# ("region2", "5.8", (0.03,0.4)),
	# ("region2", "5.8", (-1,1)),
	# ("region2", "7.5", (-0.05,4)),
	# ### ASIMOV RANGES, r=10
	# ("region0", "1.2", (-30,60)),
	# ("region0", "2.1", (0,50)),
	# ("region1", "3.3", (-10, 50)),
	# ("region1", "4.8", (-10, 50)),
	# ("region2", "5.8", (-10, 50)),
	# ("region2", "7.5", (-10, 50)),
]

def cmd_to_string(cmd: list[str]) -> str:
    return " ".join(subprocess.list2cmdline([arg]) for arg in cmd)

def run_command(cmd: list[str], cwd: str) -> None:
    print(f"\n>>> [{cwd}] {cmd_to_string(cmd)}")
    subprocess.run(cmd, check=True, cwd=cwd)

def build_common_args(rmin, rmax) -> list[str]:
    return [
        "combine",
        "-M", "MultiDimFit",
        # "Xee_ee_4_allYears.root",
        "--algo", "grid",
        "--rMin", f"{rmin}",
        "--rMax", f"{rmax}",
        # "--setParameterRanges", f"r={range_str}",
        "--points", "50",
        "--cminDefaultMinimizerStrategy", "0",
        # # B-only Asimov (post-fit)
        # "--toysFrequentist",
        # "-t", "-1",
        # # ## no signal injection
        # "--expectSignal", "0",
        ## with signal injected
        ## no signal injection
        # S+B Asimov (post-fit)
        # "-d", "higgsCombine.sb_postfit.MultiDimFit.mH120.root",
        "-d", "higgsCombine.bonly_postfit.MultiDimFit.mH120.root",
        "--snapshotName", "MultiDimFit",
        "-t", "-1",
        # "--expectSignal", "10",
        "--saveNLL",
        # "--saveToys", #NOTE: good for tests, doesn't work for plot1DScan.py (expects no toys?)
        "-v", "0",
    ]


def run_point(region, mass, r_range) -> None:

    folder = FOLDER_TEMPLATE.format(region=region, mass=mass)

    if not os.path.isdir(folder):
        raise FileNotFoundError(f"Folder does not exist: {folder}")

    base_args = build_common_args(r_range[0], r_range[1])

    # # OPTIONAL: run S+B fit to generate S+B Asimov 
    # run_command([
    #         "combine", "-M", "MultiDimFit", "Xee_ee_4_allYears.root", 
    #         "--saveWorkspace", "-n", ".sb_postfit", 
    #         "--cminDefaultMinimizerStrategy", "0", "--robustFit", "1", 
    #         "--rMin", "-40", "--rMax", "40",
    #         "--keepFailures",
    #     ],
    #     cwd=folder,
    # )

    # #OPTIONAL: run B-only fit to generate B+injected signal Asimov (but from B-only best fit params)
    # run_command([
    #         "combine", "-M", "MultiDimFit", "Xee_ee_4_allYears.root", 
    #         "--saveWorkspace", "-n", ".bonly_postfit", 
    #         "--cminDefaultMinimizerStrategy", "0", "--robustFit", "1",
    #         "--setParameters", "r=0",
    #         "--freezeParameters", "r",
    #         "--keepFailures",
    #     ],
    #     cwd=folder,
    # )    

    # run_command(
    #     base_args
    #     + [
    #         "--setParameters",
    #         "pdf_index_2022_envelope=0,pdf_index_2022EE_envelope=0,pdf_index_2023_envelope=0,pdf_index_2023BPix_envelope=0",
    #         "--freezeParameters",
    #         "pdf_index_2022_envelope,pdf_index_2022EE_envelope,pdf_index_2023_envelope,pdf_index_2023BPix_envelope",
    #         # "-n", ".nll_scan_sb",
    #         "-n", ".nll_scan_asimovBonly",
    #     ],
    #     cwd=folder,
    # )

    # # do the same, but freeze systematics
    # run_command(
    #     base_args
    #     + [
    #         "--setParameters",
    #         "pdf_index_2022_envelope=0,pdf_index_2022EE_envelope=0,pdf_index_2023_envelope=0,pdf_index_2023BPix_envelope=0",
    #         "--freezeParameters",
    #         "pdf_index_2022_envelope,pdf_index_2022EE_envelope,pdf_index_2023_envelope,pdf_index_2023BPix_envelope,allConstrainedNuisances",
    #         # "-n", ".nll_scan_sb_asimovBonly_freezeSysts",
    #         "-n", ".nll_scan_asimovBonly_freezeSysts",
    #     ],
    #     cwd=folder,
    # )

    # run_command(
    #     [
    #         "python3",
    #         "/eos/home-n/npalmeri/DiEleAnalyzer/Xee_fits/sensitivity_scan/scripts/utilities/plot_nll_scan.py",
    #         "-i", "higgsCombine.nll_scan.MultiDimFit.mH120.root",
    #         "-o", f"{PLOT_DIR}/nll_scan_bkg_region{args['region']}_M{args['mass']}.png",
    #         "--deltaNLL",
    #         "--title", f"S+B NLL scan at {args['mass']} GeV, {args['region']}",
    #     ],
    #     cwd=folder,
    # )
    ### ALTERNATIVE: use Combine's plotting tool
    run_command(
        [
            # "plot1DScan.py", "higgsCombine.nll_scan_sb.MultiDimFit.mH120.root",
            # "--others", "higgsCombine.nll_scan_sb_freezeSysts.MultiDimFit.mH120.root:Stat:2",
            "plot1DScan.py", "higgsCombine.nll_scan_asimovBonly.MultiDimFit.mH120.root",
            # "--others", "higgsCombine.nll_scan_asimovBonly_freezeSysts.MultiDimFit.mH120.root:Stat:2",
            # "plot1DScan.py", "higgsCombine.nll_scan_r0p1_injected.MultiDimFit.mH120.123456.root", #when saving toys -- DOESN'T WORK with centra l
            # "plot1DScan.py", "higgsCombine.nll_scan_r10_injected.MultiDimFit.mH120.root",
            "-o", f"nll_scan_SB_{region}_M{mass}",
        ],
        cwd=folder,
    )
    # and move output to PLOT_DIR
    os.rename(
        os.path.join(folder, f"nll_scan_SB_{region}_M{mass}.png"),
        os.path.join(PLOT_DIR, f"nll_scan_SB_{region}_M{mass}.png"),
    )


def main():
    os.makedirs(PLOT_DIR, exist_ok=True)
    for point in POINTS:
        run_point(*point)

if __name__ == "__main__":
    main()
