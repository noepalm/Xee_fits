import argparse
import glob
import json
import os
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

# Base templates (folder tag dynamically parameterized)
DEFAULT_FOLDER_TAG = "260828"
ALL_ERAS = ["2022", "2022EE", "2023", "2023BPix"]

OUTFOLDER_TEMPLATE = "/eos/home-n/npalmeri/www/DiElectron/sensitivity/{folder_tag}/fitDiagnostics_grid_data_envelope_allCorrections_binned/mu0/impacts"
FOLDER_TEMPLATE_RAW = "/eos/home-n/npalmeri/DiEleAnalyzer/Xee_fits/sensitivity_scan/cards/{folder_tag}/cards_{region}_data_envelope_allCorrections_binned/ee/{mass}"

POINTS = [
    ## OBSERVED RANGES (10%)
    ("region0", "1.2", (-50, 10)),
    # ("region0", "2.1", (-50, 10)),
    # ("region1", "3.3", (-10, 10)),
    # ("region1", "4.8", (-10, 10)),
    # ("region1", "5.8", (-10, 10)),
    # ("region2", "7.1", (-10, 10)),
    # ("region2", "9.1", (-10, 10)),
    # ("region2", "9.8", (-10, 10)),
    # ### ASIMOV RANGES
    # ("region0", "1.2", (-50,50)),
    # ("region0", "2.1", (-15,15)),
    # ("region1", "3.3", (-1,1)),
    # ("region1", "4.8", (-1,1)),
    # ("region2", "5.8", (-1,1)),
    # ("region2", "7.5", (-0.5,0.5)),
    # ### ASIMOV RANGES, r=1
    # ("region0", "1.2", (-30,30)),
    # ("region0", "2.1", (-10,15)),
    # ("region1", "3.3", (-1,3)),
    # ("region1", "4.8", (-1,4)),
    # ("region2", "5.8", (-0.2,4)),
    # ("region2", "7.5", (0,4)),
    # ### ASIMOV RANGES, r=0.1
    # ("region0", "1.2", (-30,30)),
    # ("region0", "2.1", (-10,15)),
    # ("region1", "3.3", (-1,3)),
    # ("region1", "4.8", (-1,4)),
    # ("region2", "5.8", (0.03,0.4)),
    # ("region2", "7.5", (-0.05,4)),
    # ### ASIMOV RANGES, r=10
    # ("region0", "1.2", (-30,60)),
    # ("region0", "2.1", (0,50)),
    # ("region1", "3.3", (-10, 50)),
    # ("region1", "4.8", (-10, 50)),
    # ("region2", "5.8", (-10, 50)),
    # ("region2", "7.5", (-10, 50)),
]

def get_nuisances_and_extra_args(eras_to_use: list[str]) -> tuple[str, list[str]]:
    """Build nuisance string and frozen envelope parameters for specified eras."""
    nuisances = "CMS_eff_e_id,CMS_eff_trigger_e,CMS_eff_e_reco,CMS_scale_e," + ",".join(
        [f"CMS_EXO25020_signalModelSigmaNuisance_{era}" for era in eras_to_use]
    )
    common_extra_args = [
        # "--setParameters", ",".join([f"CMS_EXO25020_bkgEnvelopeIdx_{era}=1" for era in eras_to_use]),
        # "--freezeParameters", ",".join([f"CMS_EXO25020_bkgEnvelopeIdx_{era}" for era in eras_to_use]),
    ]
    return nuisances, common_extra_args


def cmd_to_string(cmd: list[str]) -> str:
    return " ".join(subprocess.list2cmdline([arg]) for arg in cmd)


def run_command(cmd: list[str], cwd: str) -> None:
    print(f"\n>>> [{cwd}] {cmd_to_string(cmd)}")
    subprocess.run(cmd, check=True, cwd=cwd)


def get_best_fit_r_from_impacts(impacts_json_path: str) -> tuple[float, float, float]:
    with open(impacts_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    pois = data.get("POIs")
    if not isinstance(pois, list) or len(pois) == 0:
        raise ValueError(f"Invalid or empty POIs in {impacts_json_path}")

    first_poi = pois[0]
    if not isinstance(first_poi, dict) or "fit" not in first_poi:
        raise ValueError(f"Missing POIs[0].fit in {impacts_json_path}")

    fit = first_poi["fit"]
    if not isinstance(fit, list) or len(fit) < 3:
        raise ValueError(f"Invalid POIs[0].fit format in {impacts_json_path}")

    return float(fit[0]), float(fit[1]), float(fit[2])


SUPERSCRIPT_TRANS = str.maketrans({
    "0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴",
    "5": "⁵", "6": "⁶", "7": "⁷", "8": "⁸", "9": "⁹",
    "+": "⁺", "-": "⁻", "e": "ᵉ", "E": "ᴱ",
})

SUBSCRIPT_TRANS = str.maketrans({
    "0": "₀", "1": "₁", "2": "₂", "3": "₃", "4": "₄",
    "5": "₅", "6": "₆", "7": "₇", "8": "₈", "9": "₉",
    "+": "₊", "-": "₋", "e": "ₑ", "E": "ₑ",
})


def to_superscript(text: str) -> str:
    return text.translate(SUPERSCRIPT_TRANS)


def to_subscript(text: str) -> str:
    return text.translate(SUBSCRIPT_TRANS)


def convert_output_pdfs_to_pngs(outfolder: str) -> None:
    pdf_files = sorted(glob.glob(os.path.join(outfolder, "*.pdf")))
    if not pdf_files:
        print(f"No PDF files found in {outfolder}; skipping PNG conversion")
        return

    converter = shutil.which("magick") or shutil.which("convert")
    if converter:
        for pdf_file in pdf_files:
            png_file = os.path.splitext(pdf_file)[0] + ".png"
            if os.path.basename(converter) == "magick":
                cmd = [converter, pdf_file, png_file]
            else:
                cmd = [converter, pdf_file, png_file]
            run_command(cmd, cwd=outfolder)
        return

    print("No PDF-to-PNG converter found (magick/convert); skipping PNG conversion")


def run_impact_point(
    region: str,
    mass: str,
    r_range: tuple[int, int],
    folder_template: str,
    outfolder: str,
    era: Optional[str] = None,
) -> tuple[bool, str, Optional[tuple[float, float, float]]]:
    folder = folder_template.format(region=region, mass=mass)
    if not os.path.isdir(folder):
        return False, f"Folder does not exist: {folder}", None

    # Handle dataset and naming based on era mode
    if era is None:
        datacard_base = "Xee_ee_4_allYears"
        eras_to_use = ALL_ERAS
        tag_suffix = ""
        impacts_json_name = "impacts.json"
        plot_prefix = "impacts"
    else:
        datacard_base = f"Xee_ee_4_{era}"
        eras_to_use = [era]
        tag_suffix = f"_{era}"
        impacts_json_name = f"impacts_{era}.json"
        plot_prefix = f"impacts_{era}"

    nuisances, common_extra_args = get_nuisances_and_extra_args(eras_to_use)

    base_args = [
        "combineTool.py",
        "-M", "Impacts",
        "-d", f"{datacard_base}.root",
        "--cminDefaultMinimizerStrategy", "0",
        "--mass", mass,
        # "--robustFit", "1",
        "--redefineSignalPOIs", "r",
        "--rMin", f"{r_range[0]}",
        "--rMax", f"{r_range[1]}",
        # "--verbose", "2",
        "--parallel", "20",
        "--cminDefaultMinimizerTolerance", "0.0001",  # needed for Asimov; variations are too small
        "--X-rtd", "MINIMIZER_freezeDisassociatedParams=1",
        # # running on Asimov (post-fit, B-only)
        # "--toysFrequentist",
        # "-t", "-1",
        # # running on Asimov (post-fit, S+B)
        # "-d", "higgsCombine.sb_postfit.MultiDimFit.mH120.root",
        # "--snapshotName", "MultiDimFit",
        # "-t", "-1",
        # # running on Asimov (post-fit, b-only)
        # "-d", "higgsCombine.bonly_postfit.MultiDimFit.mH120.root",
        # "--snapshotName", "MultiDimFit",
        # "-t", "-1",
        # # no injected signal
        # "--expectSignal", "0",
        # # inject signal in dataset
        # "--expectSignal", "10",
        # freezing discrete profiling
        *common_extra_args,
    ]

    # Add -n tag for individual eras to prevent collisions with allYears combine outputs
    if tag_suffix:
        base_args.extend(["-n", tag_suffix])

    steps = [
        ("initialFit", ["--doInitialFit"]),
        ("doFits", ["--doFits", "--named", nuisances]),
        ("saveJson", ["-o", impacts_json_name, "--named", nuisances]),
    ]

    for _name, extra_args in steps:
        run_command(base_args + extra_args, cwd=folder)

    run_command(["plotImpacts.py", "-i", impacts_json_name, "-o", plot_prefix], cwd=folder)

    src_pdf = os.path.join(folder, f"{plot_prefix}.pdf")
    if era is None:
        dst_pdf = os.path.join(outfolder, f"impacts_M{mass}_{region}.pdf")
        dst_datacard = os.path.join(outfolder, f"{datacard_base}_M{mass}_{region}.txt")
    else:
        dst_pdf = os.path.join(outfolder, f"impacts_M{mass}_{region}_{era}.pdf")
        dst_datacard = os.path.join(outfolder, f"{datacard_base}_M{mass}_{region}.txt")

    shutil.move(src_pdf, dst_pdf)
    print(f"Saved: {dst_pdf}")

    # also COPY the datacard to the destination folder
    src_datacard = os.path.join(folder, f"{datacard_base}.txt")
    shutil.copy(src_datacard, dst_datacard)
    print(f"Copied datacard to: {dst_datacard}")

    r_fit = get_best_fit_r_from_impacts(os.path.join(folder, impacts_json_name))

    era_label = f" ({era})" if era else ""
    return True, f"OK: {region} {mass}{era_label}", r_fit


def main() -> None:
    parser = argparse.ArgumentParser(description="Run impact plots on multiple mass points in parallel.")
    parser.add_argument(
        "--folder-tag",
        default=DEFAULT_FOLDER_TAG,
        help=f"Tag for input cards and output directories (default: {DEFAULT_FOLDER_TAG})",
    )
    parser.add_argument(
        "--eras",
        nargs="+",
        default=[],
        choices=["2022", "2022EE", "2023", "2023BPix", "allYears"],
        help="One or more eras to process individually, or 'allYears' (default: allYears)",
    )
    parser.add_argument(
        "--jobs",
        type=int,
        default=None,
        help="Number of mass points to process in parallel",
    )
    args = parser.parse_args()

    base_outfolder = OUTFOLDER_TEMPLATE.format(folder_tag=args.folder_tag)
    folder_template = FOLDER_TEMPLATE_RAW.format(folder_tag=args.folder_tag, region="{region}", mass="{mass}")

    # If no eras passed or 'allYears' specified, run on combined years
    eras_to_run = args.eras if args.eras else ["allYears"]

    for era_item in eras_to_run:
        is_all_years = era_item == "allYears"
        era = None if is_all_years else era_item

        if is_all_years:
            outfolder = base_outfolder
        else:
            outfolder = os.path.join(base_outfolder, "by_era", era)

        os.makedirs(outfolder, exist_ok=True)

        print("=" * 80)
        print(f"RUNNING IMPACTS: Era={era_item} | Folder Tag={args.folder_tag}")
        print(f"Output folder: {outfolder}")
        print("=" * 80)

        max_workers = args.jobs or min(len(POINTS), os.cpu_count() or 1)
        print(f"Running impacts for {len(POINTS)} mass points on {max_workers} workers")

        failed = 0
        r_recap: list[tuple[str, str, tuple[float, float, float]]] = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(run_impact_point, region, mass, r_range, folder_template, outfolder, era): (region, mass)
                for region, mass, r_range in POINTS
            }
            for future in as_completed(futures):
                region, mass = futures[future]
                try:
                    success, msg, r_fit = future.result()
                    if success:
                        print(msg)
                        if r_fit is not None:
                            r_recap.append((region, mass, r_fit))
                    else:
                        failed += 1
                        print(f"FAILED: {msg}")
                except Exception as e:
                    failed += 1
                    era_str = f" [{era}]" if era else ""
                    print(f"EXCEPTION: {region} {mass}{era_str}: {e}")

        if r_recap:
            print(f"\n===== Best-fit r recap from impacts.json ({era_item}) =====")
            # print("Format: POIs[0].fit = [low, central, high]  ->  r = central⁺sigma_up₋sigma_down")
            for region, mass, (low, central, high) in sorted(r_recap, key=lambda x: (x[0], float(x[1]))):
                sigma_down = central - low
                sigma_up = high - central
                # sigma_up_str = to_superscript(f"+{sigma_up:.2g}")
                # sigma_down_str = to_subscript(f"-{sigma_down:.2g}")
                sigma_up_str = f"+{sigma_up:.2g}"
                sigma_down_str = f"-{sigma_down:.2g}"
                print(
                    f"{region} m={mass}: "
                    f"r = {central:.2g}{sigma_up_str}{sigma_down_str}"
                )

        # convert_output_pdfs_to_pngs(outfolder)

        if failed > 0:
            raise SystemExit(1)


if __name__ == "__main__":
    main()