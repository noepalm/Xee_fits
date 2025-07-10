import uproot
import numpy as np
import matplotlib.pyplot as plt
import mplhep as hep
from mplhep import error_estimation

# compute errors
def poisson_interval_ignore_empty(sumw, sumw2):
    #Set to 0 yerr of empty bins
    interval = error_estimation.poisson_interval(sumw, sumw2)
    lo, hi = interval[0,...], interval[1,...]
    to_ignore = np.isnan(lo)
    lo[to_ignore] = 0.0
    hi[to_ignore] = 0.0
    res = np.array([lo,hi])
    return np.abs(res - sumw)

palette = [
    "#3f90da",
    "#ffa90e",
    "#bd1f01",
    "#94a4a2",
    "#832db6",
    "#a96b59",
    "#e76300",
    "#b9ac70",
    "#717581",
    "#92dadd",
]

# 1. retrieve Jpsi pT distribution pre/post reweighting

path_pre = "/eos/home-n/npalmeri/www/DiElectron/PS_reweighting/fw_output_actualReweight/era2023/base_7_ID/"
path_post = "/eos/home-n/npalmeri/www/DiElectron/PS_reweighting/fw_output_actualReweight/era2023/base_8_TriggerPSReweight/"
outfolder = "/eos/home-n/npalmeri/www/DiElectron/PS_reweighting/plots"

xlabels = {
    "Jpsi_pt": r"$p_T(ee)$ [GeV]",
    "Jpsi_pt_leading": r"$p_T(e_1)$ [GeV]",
    "Jpsi_pt_subleading": r"$p_T(e_2)$ [GeV]",
    "DiElectron_fitted_mass": r"$m(ee)$ [GeV]",
}

for var in ["Jpsi_pt", "DiElectron_fitted_mass", "Jpsi_pt_leading", "Jpsi_pt_subleading"]:
    print(f"Processing variable: {var}")

    f_pre = uproot.open(path_pre + f"{var}.root")
    f_post = uproot.open(path_post + f"{var}.root")

    h_pre = f_pre["InclusiveMinBias"]
    h_post = f_post["InclusiveMinBias"]
    h_data = f_post["data"]

    # normalize all to same area
    scale_pre = 1/h_pre.values().sum()
    scale_post = 1/h_post.values().sum()
    scale_data = 1/h_data.values().sum()

    yerr_pre = poisson_interval_ignore_empty(h_pre.values(), h_pre.variances())
    yerr_post = poisson_interval_ignore_empty(h_post.values(), h_post.variances())

    # 2. plot the distributions
    plt.style.use(hep.style.CMS)
    fig, ax = plt.subplots(1, 1, figsize=(10, 8))
    # compute bin centers
    bin_centers_pre = (h_pre.axis().edges()[:-1] + h_pre.axis().edges()[1:]) / 2

    hep.histplot(h_pre, ax = ax, histtype = 'step', yerr = yerr_pre, label="MinBias MC, pre-reweighting",
                color=palette[0], density=True, clip_on=True)
    hep.histplot(h_post, ax = ax, histtype = 'step', yerr = yerr_post, label="MinBias MC, post-reweighting",
                color=palette[1], density=True, clip_on=True)

    hep.histplot(h_data, ax = ax, histtype = 'errorbar', label="Data",
                color="black", density=True)

    plt.xlabel(f"{xlabels[var]} [GeV]")
    plt.ylabel("Density")
    plt.yscale("log")
    plt.legend()
    plt.grid(True, alpha=0.6)

    hep.cms.label("Preliminary", data=True, year=2023, lumi=7.98, com=13.6)

    plt.savefig(f"{outfolder}/{var}_reweighting_comparison.png")
    plt.savefig(f"{outfolder}/{var}_reweighting_comparison.pdf")