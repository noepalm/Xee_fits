import glob
import os
import shutil
import subprocess

OUTFOLDER = "/eos/home-n/npalmeri/www/DiElectron/sensitivity/260404/fitDiagnostics_grid_data_envelope_withScaleSyst_withMeanNuisance_IDSF_triggerSF_finerBinning_tighterCuts_PUreweight_signalEnvelope_bySubera_binned/mu0/impacts"

FOLDER_TEMPLATE = "/eos/home-n/npalmeri/DiEleAnalyzer/Xee_fits/sensitivity_scan/cards/260404/cards_{region}_data_envelope_withScaleSyst_withMeanNuisance_IDSF_triggerSF_finerBinning_tighterCuts_PUreweight_signalEnvelope_bySubera_binned/ee/{mass}"

POINTS = [
	# ("region0", "1.8"),
	# ("region1", "3.3"),
	# ("region1", "2.6"),
	# ("region1", "3.8"),
	# ("region2", "5.8"),
	("region2", "5.6"),
]

R_RANGES = {
    "region0" : (-30, 10),
    "region1" : (-10, 10),
    "region2" : (-10, 10),
}

# NUISANCES = "electronID_syst,lumi_1,lumi_2,triggerSF_syst,mean_nuisance_electronScaleVariation,sigma_nuisance_stat_2023BPix,sigma_nuisance_stat_2023,sigma_nuisance_stat_2022,sigma_nuisance_stat_2022EE"
NUISANCES = "electronID_syst,lumi_1,lumi_2,triggerSF_syst,mean_nuisance_electronScaleVariation"

# Add global extra options here (example values shown but commented out):
COMMON_EXTRA_ARGS = [
    "--setParameters", "signal_model_index_2023=0,signal_model_index_2022=0,signal_model_index_2022EE=0,signal_model_index_2023BPix=0,pdf_index_2022_envelope=0,pdf_index_2022EE_envelope=0,pdf_index_2023_envelope=0,pdf_index_2023BPix_envelope=0",
    "--freezeParameters", "signal_model_index_2023,signal_model_index_2022,signal_model_index_2022EE,signal_model_index_2023BPix,pdf_index_2022_envelope,pdf_index_2022EE_envelope,pdf_index_2023_envelope,pdf_index_2023BPix_envelope",
]

def cmd_to_string(cmd: list[str]) -> str:
	return " ".join(subprocess.list2cmdline([arg]) for arg in cmd)

def run_command(cmd: list[str], cwd: str) -> None:
	print(f"\n>>> [{cwd}] {cmd_to_string(cmd)}")
	subprocess.run(cmd, check=True, cwd=cwd)

def main() -> None:
	os.makedirs(OUTFOLDER, exist_ok=True)

	for region, mass in POINTS:
		folder = FOLDER_TEMPLATE.format(region=region, mass=mass)
		if not os.path.isdir(folder):
			raise FileNotFoundError(f"Folder does not exist: {folder}")

		base_args = [
			"combineTool.py",
			"-M", "Impacts", 
            "-d", "Xee_ee_4_allYears.root",
			"--cminDefaultMinimizerStrategy", "0",
			"--mass", mass,
			"--robustFit", "1",
			"--redefineSignalPOIs", "r",
			"--rMin", f"{R_RANGES[region][0]}",
            "--rMax", f"{R_RANGES[region][1]}",
			*COMMON_EXTRA_ARGS,
		]

		steps = [
			("initialFit", ["--doInitialFit"]),
			("doFits", ["--doFits", "--named", NUISANCES]),
			("saveJson", ["-o", "impacts.json", "--named", NUISANCES]),
		]

		for _name, extra_args in steps:
			run_command(base_args + extra_args, cwd=folder)

		run_command(["plotImpacts.py", "-i", "impacts.json", "-o", "impacts"], cwd=folder)

		src_pdf = os.path.join(folder, "impacts.pdf")
		dst_pdf = os.path.join(OUTFOLDER, f"impacts_M{mass}_{{region}}.pdf".format(region=region))
		shutil.move(src_pdf, dst_pdf)
		print(f"Saved: {dst_pdf}")


if __name__ == "__main__":
	main()