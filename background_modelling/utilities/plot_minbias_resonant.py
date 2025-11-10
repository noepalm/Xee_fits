import uproot
import numpy as np
import matplotlib.pyplot as plt
import mplhep as hep
import os

# Set CMS style
plt.style.use(hep.style.CMS)

# CMS color palette (fixed order)
CMS_COLORS = ["#5790fc", "#f89c20", "#e42536", "#964a8b", "#9c9ca1", "#7a21dd"]

# Define resonance configurations
resonances = {
    "total": {
        "file": "/eos/home-n/npalmeri/www/DiElectron/PS_reweighting/fw_output_minBias_resonant_nanov15/zsnap/era2023/all_10_AllResonances/InclusiveMinBias.root",
        "label": "Total",
        "mass_branch": "DiElectron_fitted_mass"
    },
    "eta": {
        "file": "/eos/home-n/npalmeri/www/DiElectron/PS_reweighting/fw_output_minBias_resonant_nanov15/zsnap/era2023/eta_10_EtaResonance/InclusiveMinBias.root",
        "label": r"$\eta$",
        "mass_branch": "DiElectron_eta_fitted_mass"
    },
    # "rho": {
    #     "file": "/eos/home-n/npalmeri/www/DiElectron/PS_reweighting/fw_output_minBias_resonant_nanov15/zsnap/era2023/rho_10_RhoResonance/InclusiveMinBias.root",
    #     "label": r"$\rho$",
    #     "mass_branch": "DiElectron_rho_fitted_mass"
    # },
    "omega": {
        "file": "/eos/home-n/npalmeri/www/DiElectron/PS_reweighting/fw_output_minBias_resonant_nanov15/zsnap/era2023/omega_10_OmegaResonance/InclusiveMinBias.root",
        "label": r"$\omega$",
        "mass_branch": "DiElectron_omega_fitted_mass"
    },
    "phi": {
        "file": "/eos/home-n/npalmeri/www/DiElectron/PS_reweighting/fw_output_minBias_resonant_nanov15/zsnap/era2023/phi_10_PhiResonance/InclusiveMinBias.root",
        "label": r"$\phi$",
        "mass_branch": "DiElectron_phi_fitted_mass"
    },
}

# Define the plot order (change this to reorder resonances in the stack)
PLOT_ORDER = ["phi", "omega", "eta"]

def load_mass_data(file_path, mass_branch):
    """
    Load mass data from ROOT file using uproot
    
    Args:
        file_path: Path to ROOT file
        mass_branch: Name of the mass branch to read
    
    Returns:
        numpy array of mass values
    """
    print(f"Loading {os.path.basename(file_path)} using branch '{mass_branch}'...")
    
    try:
        with uproot.open(file_path) as f:
            tree = f["Events"]
            
            # Read the mass branch
            mass_data = tree[mass_branch].array(library="np")
            
            # Flatten the array (in case it's jagged)
            mass_values = np.concatenate(mass_data)
            
            print(f"  -> Loaded {len(mass_values)} entries")
            return mass_values
            
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return np.array([])

def load_deltaR_data(file_path, deltaR_branch):
    """
    Load deltaR data from ROOT file using uproot
    
    Args:
        file_path: Path to ROOT file
        deltaR_branch: Name of the deltaR branch to read
    
    Returns:
        numpy array of deltaR values
    """
    print(f"Loading deltaR from {os.path.basename(file_path)} using branch '{deltaR_branch}'...")
    
    try:
        with uproot.open(file_path) as f:
            tree = f["Events"]
            
            # Read the deltaR branch
            deltaR_data = tree[deltaR_branch].array(library="np")
            
            # Flatten the array (in case it's jagged)
            deltaR_values = np.concatenate(deltaR_data)
            
            # Filter out invalid values (e.g., -1.0)
            deltaR_values = deltaR_values[deltaR_values >= 0]
            
            print(f"  -> Loaded {len(deltaR_values)} valid deltaR entries")
            return deltaR_values
            
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return np.array([])

# Load data for all resonances
data = {}
for name, config in resonances.items():
    data[name] = load_mass_data(config["file"], config["mass_branch"])

# Filter to mass range
mass_range = (0, 2)
for name in data:
    mask = (data[name] >= mass_range[0]) & (data[name] <= mass_range[1])
    data[name] = data[name][mask]
    print(f"{name}: {len(data[name])} events in range [{mass_range[0]}, {mass_range[1]}] GeV")

# Create figure
fig, ax = plt.subplots(figsize=(10, 8))

# Define bins
bins = np.linspace(mass_range[0], mass_range[1], 31)

# Prepare data for stacked histogram using PLOT_ORDER
stack_data = [data[name] for name in PLOT_ORDER if len(data[name]) > 0]
stack_labels = [resonances[name]["label"] for name in PLOT_ORDER if len(data[name]) > 0]
# Assign colors from CMS_COLORS in order, regardless of resonance order
stack_colors = [CMS_COLORS[i] for i in range(len(stack_data))]

# Plot stacked histogram
ax.hist(stack_data, bins=bins, histtype='stepfilled',
        stacked=True,
        color=stack_colors,
        label=stack_labels,
        linewidth=1.5)

# Overlay total as a black line
if len(data["total"]) > 0:
    ax.hist(data["total"], bins=bins, histtype='step', 
            color='black', 
            linewidth=2.5,
            label=resonances["total"]["label"])

# Set log scale
ax.set_yscale('log')
ax.set_ylim(bottom=1e1)

# Labels
ax.set_xlabel(r'$m_{ee}$ [GeV]', fontsize=20)
ax.set_ylabel('Events / bin', fontsize=20)

# Legend
ax.legend(loc='upper right', fontsize=16, frameon=False)

# CMS label
hep.cms.label(ax=ax, data=False, label="Preliminary", lumi=59, year=2022, loc=0)

# Grid
ax.grid(True, alpha=0.3, linestyle='--')

# Output
# outfolder = "plots"
outfolder = "/eos/home-n/npalmeri/www/DiElectron/PS_reweighting/fw_output_minBias_resonant_nanov15"
os.makedirs(outfolder, exist_ok=True)

plt.tight_layout()
plt.savefig(os.path.join(outfolder, "data_minbias_resonant.png"), dpi=300)
plt.savefig(os.path.join(outfolder, "data_minbias_resonant.pdf"))
print(f"\nSaved mass plots to {outfolder}/")