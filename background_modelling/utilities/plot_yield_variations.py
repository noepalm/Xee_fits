import ROOT
import numpy as np
import matplotlib.pyplot as plt
import mplhep as hep
from pathlib import Path


def compute_variation_fractions(workspace, era, nominal_tmpl, up_tmpl, down_tmpl):
    fractions_up = {}
    fractions_down = {}

    for mass in np.arange(0.1, 11.0, 0.1):
        var_nominal = workspace.var(nominal_tmpl.format(mass=mass, era=era))
        var_up = workspace.var(up_tmpl.format(mass=mass, era=era))
        var_down = workspace.var(down_tmpl.format(mass=mass, era=era))

        if not (var_nominal and var_up and var_down):
            print(f"M{mass:.1f}: Variables not found: {var_nominal}, {var_up}, {var_down}")
            continue

        nominal_value = var_nominal.getVal()
        up_value = var_up.getVal()
        down_value = var_down.getVal()

        if nominal_value == 0.0:
            print(f"M{mass:.1f}: Nominal value is zero, skipping")
            continue

        print(
            f"M{mass:.1f}: {nominal_value:.4f} + {up_value - nominal_value:.4f} "
            f"({up_value / nominal_value:.4f}%) - {nominal_value / down_value:.4f} "
            f"({down_value / nominal_value:.4f}%)"
        )
        fractions_up[mass] = up_value / nominal_value
        fractions_down[mass] = down_value / nominal_value

    return fractions_up, fractions_down


def plot_variation(masses, up_values, down_values, up_label, down_label, ylabel, output_path):
    fig, ax = plt.subplots(figsize=(10, 10))
    ax.plot(masses, up_values, label=up_label, marker="o", markersize=3)
    ax.plot(masses, down_values, label=down_label, marker="o", markersize=3)
    ax.set_xlabel("$M(Z_D)$ [GeV]")
    ax.set_ylabel(ylabel)
    ax.legend()
    ax.grid()
    hep.cms.label(loc=0, data=False, label="Preliminary", com=13.6, ax=ax)

    for ext in ["png", "pdf"]:
        fig.savefig(output_path.with_suffix(f".{ext}"))

    plt.close(fig)


for era in ["2022", "2022EE", "2023", "2023BPix"]:
    # f = ROOT.TFile.Open("/eos/home-n/npalmeri/DiEleAnalyzer/Xee_fits/background_modelling/datasets/260130/dataset_data_region1_binned_data_altbkg_chebyshev_withScaleSyst_IDSF_full.root")
    # outfolder = "/eos/home-n/npalmeri/www/DiElectron/signal_model/use_reco_mass_nanov15_withScaleSyst_IDSF/"
    f = ROOT.TFile.Open(f"/eos/home-n/npalmeri/DiEleAnalyzer/Xee_fits/background_modelling/datasets/260404/{era}/dataset_data_region1_binned_data_envelope_withScaleSyst_IDSF_triggerSF_finerBinning_tighterCuts_PUreweight_signalEnvelope_{era}_envelope_full.root")
    outfolder = f"/eos/home-n/npalmeri/www/DiElectron/signal_model/260403/use_reco_mass_nanov15_withScaleSyst_IDSF_triggerSF_tighterCuts_newSignal_PUreweight_envelope/era{era}"
    w = f.Get("w")
    Path(outfolder).mkdir(parents=True, exist_ok=True)

    hep.style.use("CMS")

    variations = [
        {
            "name": "Electron ID",
            "up_label": "Electron ID Up",
            "down_label": "Electron ID Down",
            "up_tmpl": "Zd_M{mass:.1f}_expected_electronID_up_{era}",
            "down_tmpl": "Zd_M{mass:.1f}_expected_electronID_down_{era}",
            "output_base": "electron_id_yield_variation",
        },
        {
            "name": "Trigger SF",
            "up_label": "Trigger SF Up",
            "down_label": "Trigger SF Down",
            "up_tmpl": "Zd_M{mass:.1f}_expected_trigger_up_{era}",
            "down_tmpl": "Zd_M{mass:.1f}_expected_trigger_down_{era}",
            "output_base": "trigger_sf_yield_variation",
        },
    ]

    for variation in variations:
        print(f"\n--- Era {era}: {variation['name']} ---")
        fractions_up, fractions_down = compute_variation_fractions(
            w,
            era,
            nominal_tmpl="Zd_M{mass:.1f}_expected_{era}",
            up_tmpl=variation["up_tmpl"],
            down_tmpl=variation["down_tmpl"],
        )

        masses = sorted(fractions_up.keys())
        if not masses:
            print(f"No valid points found for {variation['name']} in era {era}, skipping plots")
            continue

        up_values = np.array([fractions_up[mass] for mass in masses])
        down_values = np.array([fractions_down[mass] for mass in masses])

        plot_variation(
            masses,
            up_values,
            down_values,
            variation["up_label"],
            variation["down_label"],
            "Nominal #signal/variation #signal",
            Path(outfolder) / variation["output_base"],
        )

        plot_variation(
            masses,
            np.abs(1 - up_values) * 100,
            np.abs(1 - down_values) * 100,
            variation["up_label"],
            variation["down_label"],
            "Abs(1 - Nominal #signal/variation #signal) [%]",
            Path(outfolder) / f"{variation['output_base']}_minus1",
        )

    f.Close()
