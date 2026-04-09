import ROOT
import os
import matplotlib.pyplot as plt
import mplhep as hep

hep.style.use("CMS")

masses = ["0p5", "1", "2", "3p1", "4", "6", "8", "10", "12"]
eras = ["2022", "2022EE", "2023", "2023BPix"]
infolder_template = "/eos/home-n/npalmeri/www/DiElectron/PS_reweighting/nanov15/per_subera/260329/signal_model_withScaleSyst_IDSF_triggerSF_tighterCuts_updatedSignal_PUreweight/zsnap/era{era}/base_14_full/"
fname_template = "HAHM_13p6TeV_M{mass}.root"
outfolder = "/eos/home-n/npalmeri/www/DiElectron/PS_reweighting/nanov15/per_subera/260329/signal_model_withScaleSyst_IDSF_triggerSF_tighterCuts_updatedSignal_PUreweight/SF_variations/yield_variation"

branch_nominal = "weight"
branch_up = "weight__pileupReweight_up"
branch_down = "weight__pileupReweight_down"


def mass_to_float(mass_label):
	return float(mass_label.replace("p", "."))


def get_tree_name(root_file):
	if root_file.Get("Events"):
		return "Events"

	for key in root_file.GetListOfKeys():
		obj = key.ReadObj()
		if obj.InheritsFrom("TTree"):
			return obj.GetName()

	return None


def sum_branch(file_path, branch_name):
	root_file = ROOT.TFile.Open(file_path)
	if not root_file or root_file.IsZombie():
		raise RuntimeError(f"Could not open ROOT file: {file_path}")

	tree_name = get_tree_name(root_file)
	root_file.Close()

	if tree_name is None:
		raise RuntimeError(f"No TTree found in file: {file_path}")

	dataframe = ROOT.RDataFrame(tree_name, file_path)
	if not dataframe.HasColumn(branch_name):
		raise RuntimeError(f"Branch '{branch_name}' not found in {file_path} (tree: {tree_name})")

	return float(dataframe.Sum(branch_name).GetValue())


def compute_yields():
	yields = {}

	for era in eras:
		yields[era] = {}
		infolder = infolder_template.format(era=era)

		for mass in masses:
			file_name = fname_template.format(mass=mass)
			file_path = os.path.join(infolder, file_name)

			if not os.path.exists(file_path):
				print(f"[WARNING] Missing file for era={era}, mass={mass}: {file_path}")
				continue

			nominal_sum = sum_branch(file_path, branch_nominal)
			up_sum = sum_branch(file_path, branch_up)
			down_sum = sum_branch(file_path, branch_down)

			up_pct = 100.0 * (up_sum - nominal_sum) / nominal_sum if nominal_sum != 0.0 else 0.0
			down_pct = 100.0 * (down_sum - nominal_sum) / nominal_sum if nominal_sum != 0.0 else 0.0
			avg_abs_pct = 0.5 * (abs(up_pct) + abs(down_pct))

			yields[era][mass] = {
				"nominal": nominal_sum,
				"up": up_sum,
				"down": down_sum,
				"up_pct": up_pct,
				"down_pct": down_pct,
				"avg_abs_pct": avg_abs_pct,
			}

	return yields


def make_plot(yields):
	os.makedirs(outfolder, exist_ok=True)

	fig, ax = plt.subplots(figsize=(10, 8))

	for era in eras:
		masses_for_era = [m for m in masses if m in yields.get(era, {})]
		if not masses_for_era:
			continue

		ordered_masses = sorted(masses_for_era, key=mass_to_float)
		x = [mass_to_float(m) for m in ordered_masses]
		y_up = [yields[era][m]["up_pct"] for m in ordered_masses]
		y_down = [yields[era][m]["down_pct"] for m in ordered_masses]

		line_up, = ax.plot(x, y_up, marker="^", linewidth=1.8, label=f"{era} up")
		ax.plot(x, y_down, marker="v", linewidth=1.8, linestyle="--", color=line_up.get_color(), label=f"{era} down")
		ax.fill_between(x, y_down, y_up, color=line_up.get_color(), alpha=0.16)

	ax.set_xlabel("Mass [GeV]")
	ax.set_ylabel("Variation wrt nominal [%]")
	ax.set_title("Pileup reweight yield variation: up/down band")
	ax.grid(True, alpha=0.3)
	ax.legend(fontsize=14)

	output_path = os.path.join(outfolder, "pileup_yield_variation.png")
	fig.tight_layout()
	fig.savefig(output_path, dpi=200)
	plt.close(fig)

	print(f"[INFO] Plot saved to: {output_path}")


def main():
	yields = compute_yields()

	print("\n[INFO] Yields dictionary:")
	for era in eras:
		if era not in yields:
			continue
		print(f"  Era: {era}")
		for mass in masses:
			if mass not in yields[era]:
				continue
			vals = yields[era][mass]
			print(
				"    "
				f"M{mass}: nominal={vals['nominal']:.6g}, "
				f"up={vals['up']:.6g}, down={vals['down']:.6g}, "
				f"up_pct={vals['up_pct']:.4f}%, down_pct={vals['down_pct']:.4f}%"
			)

	make_plot(yields)


if __name__ == "__main__":
	main()

