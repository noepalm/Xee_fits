import matplotlib.pyplot as plt
import mplhep as hep
import numpy as np
from fetch_efficiencies_csv import retrieve_efficiencies

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
efficiencies = both_efficiencies["reweight_efficiencies"]
old_efficiencies = both_efficiencies["ID_efficiencies"]

masses = np.array([1, 3.1, 5, 5.5, 6, 6.5])

effs = np.array([efficiencies[sample][0] for sample in samples])
effs_err = np.array([(efficiencies[sample][1]+efficiencies[sample][2])/2 for sample in samples]) #take average of lower and upper error for simplicity

effs_old = np.array([old_efficiencies[sample][0] for sample in samples])
effs_err_old = np.array([(old_efficiencies[sample][1]+old_efficiencies[sample][2])/2 for sample in samples]) #take average of lower and upper error for simplicity

print(effs)
print(effs_old)
print(effs/effs_old)

# effs = np.array([1.562, 14.010, 19.821, 20.552, 18.541, 11.550]) # %
# effs_err = np.array([0.055, 0.155, 0.179, 0.181, 0.2, 0.143])
# xsecs = np.array([3.396, 2.679, 1.952, 1.910, 1.865, 1.834]) # pb
# xsecs_err = np.array([0.01646, 0.0095, 0.003978, 0.003451, 0.001997, 0.001002])
xsecs = np.array([39.62, 16.00, 11.31, 11.06, 10.81, 10.07]) # pb
xsecs_err = xsecs * 0.0015 # oom for available points

fig, ax = plt.subplots(figsize=(9, 8))
hep.style.use(hep.style.CMS)

palette = [
    "#3f90da",
    "#ffa90e",
    "#ff4c4c",
    "#00bfae",
    "#a8a8a8",
]
ax.set_prop_cycle(color=palette)

ax.errorbar(
    masses, effs_old, yerr=effs_err_old, fmt='o', label='No reweight',
    markersize=8, capsize=7, elinewidth=2
)
ax.errorbar(
    masses, effs, yerr=effs_err, fmt='o', label='After trigger reweight',
    markersize=8, capsize=7, elinewidth=2
)

ax.set_xlabel("M($Z_D$) [GeV]", fontsize=24)
ax.set_ylabel("Efficiency [%]", fontsize=24)
ax.tick_params(axis='both', which='major', labelsize=20, length=10)
ax.grid()
ax.legend()

plt.savefig("efficiency_vs_mass.png")
plt.savefig("efficiency_vs_mass.pdf")