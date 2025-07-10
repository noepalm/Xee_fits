import ROOT
import mplhep as hep
import os
import uproot
import matplotlib.pyplot as plt
import numpy as np

infolder = "/eos/home-n/npalmeri/www/DiElectron/background_model/fw_output/MinBias_tests/MinBias_noskim/era2022"

hists_cutflow = {}
hists_cutflow_errors = {}

# iterate over subfolders, each representing a different cut step
for subfolder in os.listdir(infolder):
    subfolder_path = os.path.join(infolder, subfolder)
    if not os.path.isdir(subfolder_path):
        continue
    
    # retrieve file subfolder/DiElectron_fitted_mass.root
    if not os.path.exists(os.path.join(subfolder_path, 'DiElectron_fitted_mass.root')):
        print(f"File 'DiElectron_fitted_mass.root' not found in {subfolder_path}. Skipping...")
        continue

    h = uproot.open(os.path.join(subfolder_path, 'DiElectron_fitted_mass.root'))['InclusiveMinBias']

    if not h:
        print(f"Histogram 'InclusiveMinBias' not found in {subfolder_path}. Skipping...")
        continue

    if subfolder.split("_")[-1] == "TriggerMatch":
        # basically same cut as DiEleTriggerMatch, just skip it
        continue

    # retrieve cut name from subfolder
    cut_name = subfolder.split('_')[-1]

    hists_cutflow[cut_name] = h.to_numpy()
    # save also error list 
    hists_cutflow_errors[cut_name] = np.sqrt(h.variances())


# plot the cutflow
fig, ax = plt.subplots(figsize=(12, 8))
hep.style.use(hep.style.CMS)
# change label size 
ax.tick_params(axis='both', which='major', labelsize=20, length = 10)

label_dict = {
    "Baseline" : "Baseline",
    "Preselection" : "Preselection",
    "VertexPrefitSelection" : "Vertex pre-fit sel.",
    "VertexPostsfitSelection" : "Vertex post-fit sel.",
    "HLT" : "OR of HLT_DoubleEle*",
    "DiEleTriggerMatch" : "Trigger-matching",
    "ID" : "PF MVA ID wp90",
}

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

for idx, (cut_name, hist) in enumerate(hists_cutflow.items()):
    hep.histplot(hist, ax=ax, label=label_dict[cut_name], yerr = hists_cutflow_errors[cut_name], color = palette[idx])

ax.set_xlabel("m(ee) [GeV]", fontsize = 24)
ax.set_ylabel("Events", fontsize = 24)
hep.cms.label(ax=ax, data=False, com = 13.6, year = 2022, label="Preliminary")

ax.set_yscale('log')
ax.legend()
ax.grid()

plt.savefig(f'cut_flow.png')
plt.close(fig)