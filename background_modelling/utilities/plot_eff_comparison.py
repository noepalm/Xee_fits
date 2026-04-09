import pickle
import matplotlib.pyplot as plt
import numpy as np
import mplhep as hep

hep.style.use("CMS")

cms_palette = [
    "#5790fc",
    "#f89c20",
    "#e42536",
]

eff_trigger6p5 = pickle.load(open("trigger_6p5_only_effs.pkl", "rb"))
eff_allTriggers = pickle.load(open("allTriggers_effs.pkl", "rb"))
masses = np.linspace(0, 12, 100)

fig, (ax, ax_ratio) = plt.subplots(2, 1, figsize=(10, 10), sharex=True, gridspec_kw={"height_ratios": [3, 1], "hspace": 0.05},)

ax.plot(masses, eff_allTriggers * 100, label="All triggers", color=cms_palette[1], linewidth=2)
ax.plot(masses, eff_trigger6p5 * 100, label="6.5 GeV trigger only", color=cms_palette[0], linewidth=2)
# highlight splined points at: 1, 3.1, 5, 5.5, 6, 6.5, 8, 10
# same efficiency as eff_trigger6p5
splined_points = [1, 3.1, 5, 5.5, 6, 6.5, 8, 10]
mass_indices = [np.argmin(np.abs(masses - p)) for p in splined_points]
ax.scatter(masses[mass_indices], np.array(eff_allTriggers)[mass_indices] * 100, color=cms_palette[1], zorder=5, s=50)
ax.scatter(masses[mass_indices], np.array(eff_trigger6p5)[mass_indices] * 100, color=cms_palette[0], zorder=5, s=50)
ax.set_ylabel("Signal efficiency [%]")

# add ratio value for splined points to legend
ax.scatter([], [], color=cms_palette[1], label=f"Ratio values:", s=0)
for i, p in enumerate(splined_points):
    ratio_value = eff_allTriggers[mass_indices[i]] / eff_trigger6p5[mass_indices[i]] if eff_trigger6p5[mass_indices[i]] != 0 else np.nan
    ax.scatter([], [], color=cms_palette[1], label=f"{p} GeV: {ratio_value:.2f}x", s=0)
ax.legend(fontsize=15)
ax.grid(alpha=0.6)
ax.tick_params(axis="x", labelbottom=False)

ratio = np.divide(
    eff_allTriggers,
    eff_trigger6p5,
    out=np.full_like(eff_allTriggers, np.nan, dtype=float),
    where=np.asarray(eff_trigger6p5) != 0,
)
ax_ratio.plot(masses, ratio, color=cms_palette[2], label="All triggers / 6.5 only")
ax_ratio.axhline(1.0, color="black", linestyle="--", linewidth=1.0)
ax_ratio.set_xlabel("m(ee) [GeV]")
ax_ratio.set_ylabel("Ratio")
ax_ratio.grid(alpha=0.3)
ax_ratio.legend()

fig.tight_layout()

plt.savefig("trigger_efficiency_comparison.png")