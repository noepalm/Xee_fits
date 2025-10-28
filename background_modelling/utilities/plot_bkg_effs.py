import ROOT
import numpy as np
import matplotlib.pyplot as plt
import os
import mplhep as hep
import argparse
import uproot

plt.style.use(hep.style.CMS)
palette = [
    "#5790fc",
    "#ffa90e",
    "#ff4c4c",
    "#00bfae",
    "#a8a8a8",
]

outfolder = "/eos/home-n/npalmeri/www/DiElectron/background_model/fit/"

numerator_file = "/eos/home-n/npalmeri/www/DiElectron/PS_reweighting/fw_output_actualReweight/era2023/base_8_TriggerPSReweight/DiElectron_fitted_mass_absolute.root"
denominator_file = "/eos/home-n/npalmeri/www/DiElectron/PS_reweighting/fw_output_actualReweight/era2023/base_7_ID/DiElectron_fitted_mass_absolute.root"

f1 = ROOT.TFile.Open(numerator_file)
f2 = ROOT.TFile.Open(denominator_file)

h_num = f1.Get("InclusiveMinBias")
h_den = f2.Get("InclusiveMinBias")

# set batch mode
ROOT.gROOT.SetBatch(True)

# plot the two histograms on the same plot as check
c1 = ROOT.TCanvas("c1", "c1", 800, 600)
h_den.SetLineColor(ROOT.kBlue)
h_den.SetMarkerColor(ROOT.kBlue)
h_den.SetMarkerStyle(21)
h_den.SetTitle("Denominator (ID);m_{ee} [GeV];Events")
h_den.Draw("E")
h_num.SetLineColor(ROOT.kRed)
h_num.SetMarkerColor(ROOT.kRed)
h_num.SetMarkerStyle(20)
h_num.SetTitle("Numerator (w/ trigger reweight);m_{ee} [GeV];Events")
h_num.Draw("E SAME")
c1.BuildLegend()
c1.SaveAs(os.path.join(outfolder, "den_num_check.png"))

# compute efficiency (use TEfficiency)
eff = ROOT.TEfficiency(h_num, h_den)
eff.SetTitle("Trigger PS reweight efficiency on MinBias ;m_{ee} [GeV];Efficiency")
c2 = ROOT.TCanvas("c2", "c2", 800, 600)
eff.SetLineColor(ROOT.kBlack)
eff.SetMarkerColor(ROOT.kBlack)
eff.SetMarkerStyle(20)
eff.Draw("AP")
c2.SaveAs(os.path.join(outfolder, "efficiency_bkg_triggerPSreweight.png"))

# --------------------------
# ALSO PLOT SIGNAL EFFICIENCIES

from get_signal_effs_xsecs import retrieve_efficiencies, clean_string

input_folder = "/eos/home-n/npalmeri/www/DiElectron/signal_model/fw_output/signal_model_reweighted/ztables/era2023/base_9_GenMatching/csv"

# -- Interpolate xsec, selection efficiency
samples = [
    "HAHM_13p6TeV_M1",
    "HAHM_13p6TeV_M3p1",
    "HAHM_13p6TeV_M5",
    "HAHM_13p6TeV_M5p5",
    "HAHM_13p6TeV_M6",
    "HAHM_13p6TeV_M6p5"
]

both_efficiencies = retrieve_efficiencies("/eos/home-n/npalmeri/www/DiElectron/signal_model/fw_output/signal_model_reweighted/ztables/era2023/base_9_GenMatching/csv")
relative_efficiencies = both_efficiencies["reweight_relative_efficiencies"]
print(relative_efficiencies)

masses = np.array([1, 3.1, 5, 5.5, 6, 6.5])

effs = np.array([relative_efficiencies[sample][0] for sample in samples]) / 100
effs_err = np.array([(relative_efficiencies[sample][1]+relative_efficiencies[sample][2])/2 / 100 for sample in samples]) #take average of lower and upper error for simplicity

# plot as graph
fig, ax = plt.subplots(figsize=(10, 10))
plt.errorbar(masses, effs * 100, yerr=effs_err * 100, fmt='o', markersize=8, capsize=7, elinewidth=2, color = palette[0])
plt.ylim(0, 100)
plt.xlabel('M(X) [GeV]')
plt.ylabel('Efficiency [%]')
hep.cms.label("Preliminary", loc=0, ax=ax, com = 13.6)

ax.set_title("Trigger PS reweight efficiency on signal", pad = 45, fontsize = 20)
plt.grid()

print("Saving figure to ", os.path.join(outfolder, "efficiency_signal_triggerPSreweight.png"))
plt.savefig(os.path.join(outfolder, "efficiency_signal_triggerPSreweight.png"))