import ROOT
import matplotlib.pyplot as plt
import numpy as np

fpath = "/eos/home-n/npalmeri/DiEleAnalyzer/Xee_fits/signal_modelling/workspaces/260329/era2022/signal_model_nanov15_withScaleSyst_IDSF_triggerSF_tighterCuts_newSignal_PUreweight.root"
f = ROOT.TFile(fpath)
w = f.Get("w")

masses = [0.5, 1, 2, 3.1, 4, 6, 8, 9.4]
residuals = {}
for var in ["sigma", "alphaL", "alphaR", "nL", "nR"]:
    residuals[var] = []
    for i in range(8):
        res = w.obj(f"{var}_residual_point{i}_2022")
        residuals[var].append(res.getValV())

# make single plot with a panel for each variable plotting residual vs mass
fig, ax = plt.subplots(1, 5, figsize=(20, 4))
for i, var in enumerate(["sigma", "alphaL", "alphaR", "nL", "nR"]):
    ax[i].plot(masses, residuals[var], marker="o", linestyle="-")
    ax[i].set_xlabel("Mass (GeV)")
    ax[i].set_ylabel("Residual")
    ax[i].set_title(var)
plt.tight_layout()
plt.savefig("residuals_vs_mass.png")