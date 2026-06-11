import glob
import os
import shutil
import subprocess

# OUTFOLDER = "/eos/home-n/npalmeri/www/DiElectron/sensitivity/260404/fitDiagnostics_grid_data_envelope_withScaleSyst_withMeanNuisance_IDSF_triggerSF_finerBinning_tighterCuts_PUreweight_signalEnvelope_bySubera_binned/mu0/impacts"
# FOLDER_TEMPLATE = "/eos/home-n/npalmeri/DiEleAnalyzer/Xee_fits/sensitivity_scan/cards/260404/cards_{region}_data_envelope_withScaleSyst_withMeanNuisance_IDSF_triggerSF_finerBinning_tighterCuts_PUreweight_signalEnvelope_bySubera_binned/ee/{mass}"
# OUTFOLDER = "/eos/home-n/npalmeri/www/DiElectron/sensitivity/260430/fitDiagnostics_grid_data_envelope_allCorrections_binned/mu0/impacts/asimov_postfit_sb"
OUTFOLDER = "/eos/home-n/npalmeri/www/DiElectron/sensitivity/260430/fitDiagnostics_grid_data_envelope_allCorrections_binned/mu0/impacts/asimov_postfit_bonly"
# OUTFOLDER = "/eos/home-n/npalmeri/www/DiElectron/sensitivity/260430/fitDiagnostics_grid_data_envelope_allCorrections_binned/mu0/impacts/asimov_postfit_bonly_r1_corrected"
# OUTFOLDER = "/eos/home-n/npalmeri/www/DiElectron/sensitivity/260430/fitDiagnostics_grid_data_envelope_allCorrections_binned/mu0/impacts/asimov_postfit_bonly_r10_corrected"
# OUTFOLDER = "/eos/home-n/npalmeri/www/DiElectron/sensitivity/260430/fitDiagnostics_grid_data_envelope_allCorrections_binned/mu0/impacts/asimov_postfit_bonly_r0p1_corrected"
FOLDER_TEMPLATE = "/eos/home-n/npalmeri/DiEleAnalyzer/Xee_fits/sensitivity_scan/cards/260430/cards_{region}_data_envelope_allCorrections_binned/ee/{mass}"

POINTS = [
	# ## OBSERVED RANGES (10%)
	# ("region0", "1.2", (-50, 10)),
	# ("region0", "2.1", (-50, 10)),
	# ("region1", "3.3", (-10, 10)),
	# ("region1", "4.8", (-10, 10)),
	# ("region2", "5.8", (0, 10)),
	# ("region2", "7.5", (-10, 10)),
	### ASIMOV RANGES
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

# NUISANCES = "electronID_syst,lumi_1,lumi_2,triggerSF_syst,mean_nuisance_electronScaleVariation,sigma_nuisance_stat_2023BPix,sigma_nuisance_stat_2023,sigma_nuisance_stat_2022,sigma_nuisance_stat_2022EE"
NUISANCES = "electronID_syst,triggerSF_syst,recoSF_syst,mean_nuisance_electronScaleVariation,sigma_nuisance_stat_2023BPix,sigma_nuisance_stat_2023,sigma_nuisance_stat_2022,sigma_nuisance_stat_2022EE,lumi_1,lumi_2"
# NUISANCES = "electronID_syst,triggerSF_syst,recoSF_syst,mean_nuisance_electronScaleVariation,"
# NUISANCES = "triggerSF_syst"

# Add global extra options here (example values shown but commented out):
COMMON_EXTRA_ARGS = [
    # "--setParameters", "signal_model_index_2023=0,signal_model_index_2022=0,signal_model_index_2022EE=0,signal_model_index_2023BPix=0,pdf_index_2022_envelope=0,pdf_index_2022EE_envelope=0,pdf_index_2023_envelope=0,pdf_index_2023BPix_envelope=0",
    # "--freezeParameters", "signal_model_index_2023,signal_model_index_2022,signal_model_index_2022EE,signal_model_index_2023BPix,pdf_index_2022_envelope,pdf_index_2022EE_envelope,pdf_index_2023_envelope,pdf_index_2023BPix_envelope",
    "--setParameters", "pdf_index_2022_envelope=0,pdf_index_2022EE_envelope=0,pdf_index_2023_envelope=0,pdf_index_2023BPix_envelope=0",
    "--freezeParameters", "pdf_index_2022_envelope,pdf_index_2022EE_envelope,pdf_index_2023_envelope,pdf_index_2023BPix_envelope",
]

def cmd_to_string(cmd: list[str]) -> str:
	return " ".join(subprocess.list2cmdline([arg]) for arg in cmd)

def run_command(cmd: list[str], cwd: str) -> None:
	print(f"\n>>> [{cwd}] {cmd_to_string(cmd)}")
	subprocess.run(cmd, check=True, cwd=cwd)

def main() -> None:
	os.makedirs(OUTFOLDER, exist_ok=True)

	for region, mass, r_range in POINTS:
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
			"--rMin", f"{r_range[0]}",
            "--rMax", f"{r_range[1]}",
			# "--verbose", "2",
			"--parallel", "20",
			"--cminDefaultMinimizerTolerance", "0.0001", # needed for Asimov; variations are too small
			# # running on Asimov (post-fit, B-only)
	        # "--toysFrequentist",
			# "-t", "-1",
			# # running on Asimov (post-fit, S+B)
			# "-d", "higgsCombine.sb_postfit.MultiDimFit.mH120.root",
			# "--snapshotName", "MultiDimFit",
			# "-t", "-1",
			# running on Asimov (post-fit, b-only)
			"-d", "higgsCombine.bonly_postfit.MultiDimFit.mH120.root",
			"--snapshotName", "MultiDimFit",
			"-t", "-1",
			# # no injected signal
			# "--expectSignal", "0",
			# # inject signal in dataset
			# "--expectSignal", "10",
			# freezing discrete profiling
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

		# also COPY the datacard to the destination folder
		src_datacard = os.path.join(folder, "Xee_ee_4_allYears.txt")
		dst_datacard = os.path.join(OUTFOLDER, f"Xee_ee_4_allYears_M{mass}_{{region}}.txt".format(region=region))
		shutil.copy(src_datacard, dst_datacard)
		print(f"Copied datacard to: {dst_datacard}")


if __name__ == "__main__":
	main()