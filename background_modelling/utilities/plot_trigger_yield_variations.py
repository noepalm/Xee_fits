import ROOT
import numpy as np
import matplotlib.pyplot as plt
import mplhep as hep
from pathlib import Path

f = ROOT.TFile.Open("/eos/home-n/npalmeri/DiEleAnalyzer/Xee_fits/background_modelling/datasets/260226/dataset_data_region1_binned_data_altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_full.root")
outfolder = "/eos/home-n/npalmeri/www/DiElectron/signal_model/use_reco_mass_nanov15_withScaleSyst_IDSF_triggerSF/"
w = f.Get("w")

fractions_up = {}
fractions_down = {}

for mass in np.arange(0.1, 11.0, 0.1):
    var_nominal = w.var(f"Zd_M{mass:.1f}_expected")
    var_up = w.var(f"Zd_M{mass:.1f}_expected_trigger_up")
    var_down = w.var(f"Zd_M{mass:.1f}_expected_trigger_down")
    if var_nominal and var_up and var_down:
        var_nominal, var_up, var_down = var_nominal.getVal(), var_up.getVal(), var_down.getVal()
        print(f"M{mass:.1f}: {var_nominal:.4f} + {var_up - var_nominal:.4f} ({var_up/var_nominal:.4f}%) - {var_nominal/var_down:.4f} ({var_down/var_nominal:.4f}%)")
        fractions_up[mass] = (var_up / var_nominal)
        fractions_down[mass] = (var_down / var_nominal)
    else:
        print(f"M{mass:.1f}: Variables not found: {var_nominal}, {var_up}, {var_down}")

masses = sorted(fractions_up.keys())
up_values = [fractions_up[mass] for mass in masses]
down_values = [fractions_down[mass] for mass in masses]

hep.style.use("CMS")
fig, ax = plt.subplots(figsize=(10, 10))
ax.plot(masses, up_values, label="Trigger SF Up", marker='o', markersize=3)
ax.plot(masses, down_values, label="Trigger SF Down", marker='o', markersize=3)
ax.set_xlabel("$M(Z_D)$ [GeV]")
ax.set_ylabel("Nominal #signal/variation #signal")
ax.legend()
ax.grid()
hep.cms.label(loc=0, data=False, label="Preliminary", com=13.6, ax=ax)

for ext in ["png", "pdf"]:
    plt.savefig(Path(outfolder) / f"trigger_sf_yield_variation.{ext}")

fig, ax = plt.subplots(figsize=(10, 10))
up_values_fraction = abs(1-np.array(up_values))
down_values_fraction = abs(1-np.array(down_values))
ax.plot(masses, up_values_fraction * 100, label="Trigger SF Up", marker='o', markersize=3)
ax.plot(masses, down_values_fraction * 100, label="Trigger SF Down", marker='o', markersize=3)
ax.set_xlabel("$M(Z_D)$ [GeV]")
ax.set_ylabel("Abs(1 - Nominal #signal/variation #signal) [%]")
ax.legend()
ax.grid()
hep.cms.label(loc=0, data=False, label="Preliminary", com=13.6, ax=ax)

for ext in ["png", "pdf"]:
    plt.savefig(Path(outfolder) / f"trigger_sf_yield_variation_minus1.{ext}")
