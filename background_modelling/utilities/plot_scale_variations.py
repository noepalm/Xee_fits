# python3 /eos/home-n/npalmeri/DiEleAnalyzer/Xee_fits/background_modelling/utilities/plot_scale_variations.py \
#     --folder-tag 260828 \
#     --mc-tag 261007 \
#     --signal-tag 260727 &> /eos/home-n/npalmeri/www/DiElectron/signal_model/260727/use_reco_mass_allCorrections/electron_scale_variation.log

import argparse
from pathlib import Path
import ROOT
import numpy as np
import matplotlib.pyplot as plt
import mplhep as hep

# ==============================================================================
# Resonance Configuration & PDG Masses
# ==============================================================================
# Standard PDG masses [GeV]
PDG_MASSES = {
    "omega": 0.7827,      # 782.66 MeV
    "phi": 1.0195,       # 1019.461 MeV
    "jpsi": 3.0969,      # 3096.900 MeV
    "psi2s": 3.6861,     # 3686.097 MeV
    "upsilon1s": 9.4603, # 9460.30 MeV
    "upsilon2s": 10.0233,# 10023.26 MeV
}

RESONANCE_REGIONS = {
    "omega": 0,
    "phi": 0,
    "jpsi": 1,
    "psi2s": 1,
    "upsilon1s": 2,
    "upsilon2s": 2,
}

RESONANCE_TITLES = {
    "omega": r"$\omega$",
    "phi": r"$\phi$",
    "jpsi": r"$J/\psi$",
    "psi2s": r"$\psi(2\mathrm{S})$",
    "upsilon1s": r"$\Upsilon(1\mathrm{S})$",
    "upsilon2s": r"$\Upsilon(2\mathrm{S})$",
}

ERA_COLORS = {
    "2022": "#5790fc",      # Blue
    "2022EE": "#f89c20",    # Orange
    "2023": "#e42536",      # Red
    "2023BPix": "#964a8b",  # Purple
}


def retrieve_scale_parameters(workspace, era):
    """
    Retrieve linear fit parameters for mean and electron scale variation avgdiff.

    Formula from signal_model_analyzer.py:
        mean_test = (p0 + p1 * M) + CMS_scale_e * (diff0 + diff1 * M)
    where:
        p0 = mean_fit_par0_{era}
        p1 = mean_fit_par1_{era}
        diff0 = mean_fit_par0_electronScaleVariation_avgdiff_{era}
        diff1 = mean_fit_par1_electronScaleVariation_avgdiff_{era}
    """
    p0_var = workspace.var(f"mean_fit_par0_{era}")
    p1_var = workspace.var(f"mean_fit_par1_{era}")
    diff0_var = workspace.var(f"mean_fit_par0_electronScaleVariation_avgdiff_{era}")
    diff1_var = workspace.var(f"mean_fit_par1_electronScaleVariation_avgdiff_{era}")

    missing = []
    if not p0_var:
        missing.append(f"mean_fit_par0_{era}")
    if not p1_var:
        missing.append(f"mean_fit_par1_{era}")
    if not diff0_var:
        missing.append(f"mean_fit_par0_electronScaleVariation_avgdiff_{era}")
    if not diff1_var:
        missing.append(f"mean_fit_par1_electronScaleVariation_avgdiff_{era}")

    if missing:
        raise ValueError(f"Era {era}: missing workspace variable(s): {', '.join(missing)}")

    return {
        "p0": p0_var.getVal(),
        "p1": p1_var.getVal(),
        "diff0": diff0_var.getVal(),
        "diff1": diff1_var.getVal(),
    }


def compute_relative_scale(masses, params):
    """
    Compute relative scale uncertainty: Delta M / M
    relative_scale = (diff0 + diff1 * masses) / (p0 + p1 * masses)
    """
    nominal_mean = params["p0"] + params["p1"] * masses
    scale_diff = params["diff0"] + params["diff1"] * masses
    return scale_diff / nominal_mean


def summarize_scale_variation(era, masses, relative_scale):
    """Print summary of min, max, and mean scale variations."""
    min_idx = int(np.argmin(relative_scale))
    max_idx = int(np.argmax(relative_scale))
    print(f"\n--- Era {era}: Scale Variation Summary ---")
    print(
        f"  Min variation: {relative_scale[min_idx]:.6f} "
        f"({relative_scale[min_idx] * 100:.3f}%) at M = {masses[min_idx]:.2f} GeV"
    )
    print(
        f"  Max variation: {relative_scale[max_idx]:.6f} "
        f"({relative_scale[max_idx] * 100:.3f}%) at M = {masses[max_idx]:.2f} GeV"
    )
    print(
        f"  Mean variation: {float(np.mean(relative_scale)):.6f} "
        f"({float(np.mean(relative_scale)) * 100:.3f}%)"
    )


def extract_resonance_mean(workspace, resonance_name, era, jpsi_mode="average"):
    """
    Extract the fitted mean mass and uncertainty for a given resonance.

    For jpsi, the model is RooAddPdf::jpsi_<era>[ jpsi_core_frac_<era> * jpsi_cb_<era> + ... * jpsi_gauss_<era> ].
    jpsi_mode controls which mean is used:
      - 'gauss' / 'core': Gaussian core mean (jpsi_mean_core_<era>)
      - 'dcb' / 'cb': double Crystal Ball mean (jpsi_mean_<era>)
      - 'average' / 'weighted': weighted average between core and cb
    """
    if resonance_name == "jpsi":
        cb_var = workspace.var(f"jpsi_mean_{era}")
        core_var = workspace.var(f"jpsi_mean_core_{era}")
        frac_var = workspace.var(f"jpsi_core_frac_{era}")

        if not (cb_var and core_var and frac_var):
            raise ValueError(f"Era {era}: missing J/psi variables in workspace (need jpsi_mean, jpsi_mean_core, jpsi_core_frac)")

        mu_cb = cb_var.getVal()
        err_cb = cb_var.getError()
        mu_core = core_var.getVal()
        err_core = core_var.getError()
        frac = frac_var.getVal()
        err_frac = frac_var.getError()

        # Weighted average: frac * mu_cb + (1 - frac) * mu_core
        weighted_mean = frac * mu_cb + (1.0 - frac) * mu_core
        weighted_err = np.sqrt(
            (frac * err_cb) ** 2
            + ((1.0 - frac) * err_core) ** 2
            + ((mu_cb - mu_core) * err_frac) ** 2
        )

        if jpsi_mode in ["gauss", "core"]:
            mean_val = mu_core
            mean_err = err_core
        elif jpsi_mode in ["dcb", "cb"]:
            mean_val = mu_cb
            mean_err = err_cb
        else:
            mean_val = weighted_mean
            mean_err = weighted_err

        raw_info = {
            "type": "add_pdf",
            "jpsi_mode": jpsi_mode,
            "mu_cb": mu_cb,
            "err_cb": err_cb,
            "mu_core": mu_core,
            "err_core": err_core,
            "frac": frac,
            "err_frac": err_frac,
            "weighted_mean": weighted_mean,
            "weighted_err": weighted_err,
            "eff_mean": mean_val,
            "eff_err": mean_err,
        }
        return mean_val, mean_err, raw_info

    # Other resonances (double crystal balls):
    mean_var = workspace.var(f"{resonance_name}_mean_{era}")
    if not mean_var:
        raise ValueError(f"Era {era}: variable '{resonance_name}_mean_{era}' not found in workspace")

    raw_info = {
        "type": "single_mean",
        "var_name": f"{resonance_name}_mean_{era}",
        "mean": mean_var.getVal(),
        "err": mean_var.getError(),
    }
    return mean_var.getVal(), mean_var.getError(), raw_info


def retrieve_all_resonance_points(
    mc_folder,
    data_folder,
    era,
    bkg_func="bernstein",
    jpsi_mode="average",
    mc_bkg_func="bernstein",
):
    """
    Retrieve fitted resonance means for MC and Data across regions 0, 1, 2.
    MC is always retrieved from mc_bkg_func ('bernstein').
    Data is retrieved from bkg_func ('bernstein' or 'chebyshev').
    Computes differences wrt PDG masses and Data vs MC relative variation.
    """
    resonance_order = ["omega", "phi", "jpsi", "psi2s", "upsilon1s", "upsilon2s"]
    results = []

    # Cache opened workspaces per region to avoid reloading files
    workspaces_mc = {}
    workspaces_data = {}

    for res_name in resonance_order:
        reg = RESONANCE_REGIONS[res_name]
        pdg_mass = PDG_MASSES[res_name]

        if reg not in workspaces_mc:
            mc_path = (
                f"{mc_folder}/{era}/"
                f"dataset_data_region{reg}_binned_data_altbkg_{mc_bkg_func}_allCorrections_{era}_full.root"
            )
            f_mc = ROOT.TFile.Open(mc_path)
            if not f_mc or f_mc.IsZombie():
                print(f"Warning: Could not open MC file {mc_path}")
                workspaces_mc[reg] = (None, None)
            else:
                workspaces_mc[reg] = (f_mc, f_mc.Get("w"))

        if reg not in workspaces_data:
            data_path = (
                f"{data_folder}/{era}/"
                f"dataset_data_region{reg}_binned_data_altbkg_{bkg_func}_allCorrections_{era}_full.root"
            )
            f_data = ROOT.TFile.Open(data_path)
            if not f_data or f_data.IsZombie():
                print(f"Warning: Could not open Data file {data_path}")
                workspaces_data[reg] = (None, None)
            else:
                workspaces_data[reg] = (f_data, f_data.Get("w"))

        _, w_mc = workspaces_mc[reg]
        _, w_data = workspaces_data[reg]

        if not w_mc or not w_data:
            print(f"Warning: Missing workspace for region {reg}, skipping {res_name} in era {era}")
            continue

        try:
            val_mc, err_mc, raw_mc = extract_resonance_mean(w_mc, res_name, era, jpsi_mode=jpsi_mode)
            val_data, err_data, raw_data = extract_resonance_mean(w_data, res_name, era, jpsi_mode=jpsi_mode)
        except ValueError as err:
            print(f"Warning: {err}")
            continue

        if res_name == "jpsi":
            print(f"  [J/psi retrieved fit parameters for era {era} (mode: {jpsi_mode})]")
            print(
                f"    MC:   jpsi_mean = {raw_mc['mu_cb']:.6f} +- {raw_mc['err_cb']:.6f}, "
                f"jpsi_mean_core = {raw_mc['mu_core']:.6f} +- {raw_mc['err_core']:.6f}, "
                f"jpsi_core_frac = {raw_mc['frac']:.6f} +- {raw_mc['err_frac']:.6f} "
                f"--> selected ({jpsi_mode}) = {val_mc:.6f} +- {err_mc:.6f}"
            )
            print(
                f"    Data: jpsi_mean = {raw_data['mu_cb']:.6f} +- {raw_data['err_cb']:.6f}, "
                f"jpsi_mean_core = {raw_data['mu_core']:.6f} +- {raw_data['err_core']:.6f}, "
                f"jpsi_core_frac = {raw_data['frac']:.6f} +- {raw_data['err_frac']:.6f} "
                f"--> selected ({jpsi_mode}) = {val_data:.6f} +- {err_data:.6f}"
            )
        else:
            print(
                f"  [{res_name:<10}] MC ({res_name}_mean_{era}) = {val_mc:.6f} +- {err_mc:.6f}, "
                f"Data ({res_name}_mean_{era}) = {val_data:.6f} +- {err_data:.6f}"
            )

        # Relative variation: (M_data - M_mc) / M_mc
        rel_diff = (val_data - val_mc) / val_mc
        rel_diff_err = np.sqrt(
            (err_data / val_mc) ** 2 + (val_data * err_mc / (val_mc ** 2)) ** 2
        )

        # Difference wrt PDG [MeV] and [%]
        mc_pdg_diff_mev = (val_mc - pdg_mass) * 1e3
        mc_pdg_diff_err_mev = err_mc * 1e3
        mc_pdg_diff_percent = (val_mc - pdg_mass) / pdg_mass * 100.0
        mc_pdg_diff_err_percent = err_mc / pdg_mass * 100.0

        data_pdg_diff_mev = (val_data - pdg_mass) * 1e3
        data_pdg_diff_err_mev = err_data * 1e3
        data_pdg_diff_percent = (val_data - pdg_mass) / pdg_mass * 100.0
        data_pdg_diff_err_percent = err_data / pdg_mass * 100.0

        results.append({
            "name": res_name,
            "title": RESONANCE_TITLES[res_name],
            "region": reg,
            "era": era,
            "pdg_mass": pdg_mass,
            "val_mc": val_mc,
            "err_mc": err_mc,
            "val_data": val_data,
            "err_data": err_data,
            "rel_diff": rel_diff,
            "rel_diff_err": rel_diff_err,
            "mc_pdg_diff_mev": mc_pdg_diff_mev,
            "mc_pdg_diff_err_mev": mc_pdg_diff_err_mev,
            "mc_pdg_diff_percent": mc_pdg_diff_percent,
            "mc_pdg_diff_err_percent": mc_pdg_diff_err_percent,
            "data_pdg_diff_mev": data_pdg_diff_mev,
            "data_pdg_diff_err_mev": data_pdg_diff_err_mev,
            "data_pdg_diff_percent": data_pdg_diff_percent,
            "data_pdg_diff_err_percent": data_pdg_diff_err_percent,
            "raw_mc": raw_mc,
            "raw_data": raw_data,
        })

    # Close open files
    for f_mc, _ in workspaces_mc.values():
        if f_mc:
            f_mc.Close()
    for f_data, _ in workspaces_data.values():
        if f_data:
            f_data.Close()

    return results


def format_relative_shifts_table_by_era(all_era_results, eras):
    """
    View 1: Results ordered by era, then resonance.
    Reports (MC-PDG)/PDG [%], (Data-PDG)/PDG [%], and (Data-MC)/MC [%] with uncertainties.
    Allows easy verification of compatibility across mass at fixed era.
    """
    header = (
        f"{'Era':<10} {'Resonance':<12} {'(MC - PDG)/PDG [%]':<25} "
        f"{'(Data - PDG)/PDG [%]':<25} {'(Data - MC)/MC [%]':<25}"
    )
    separator = "=" * len(header)
    sub_sep = "-" * len(header)

    lines = [
        "",
        separator,
        "VIEW 1: RELATIVE SHIFTS ORDERED BY ERA, THEN RESONANCE (FIXED ERA)",
        separator,
        header,
        sub_sep,
    ]

    for era in eras:
        res_list = all_era_results.get(era, [])
        for r in res_list:
            mc_pdg_str = f"{r['mc_pdg_diff_percent']:+.3f} +- {r['mc_pdg_diff_err_percent']:.3f}"
            data_pdg_str = f"{r['data_pdg_diff_percent']:+.3f} +- {r['data_pdg_diff_err_percent']:.3f}"
            data_mc_str = f"{r['rel_diff']*100:+.3f} +- {r['rel_diff_err']*100:.3f}"

            line = f"{era:<10} {r['name']:<12} {mc_pdg_str:<25} {data_pdg_str:<25} {data_mc_str:<25}"
            lines.append(line)
        lines.append(sub_sep)

    lines.append(separator)
    return "\n".join(lines)


def format_relative_shifts_table_by_resonance(all_era_results, eras):
    """
    View 2: Results ordered by resonance, then era.
    Reports (MC-PDG)/PDG [%], (Data-PDG)/PDG [%], and (Data-MC)/MC [%] with uncertainties.
    Allows easy verification of compatibility across eras at fixed mass.
    """
    header = (
        f"{'Resonance':<12} {'Era':<10} {'(MC - PDG)/PDG [%]':<25} "
        f"{'(Data - PDG)/PDG [%]':<25} {'(Data - MC)/MC [%]':<25}"
    )
    separator = "=" * len(header)
    sub_sep = "-" * len(header)

    lines = [
        "",
        separator,
        "VIEW 2: RELATIVE SHIFTS ORDERED BY RESONANCE, THEN ERA (FIXED MASS)",
        separator,
        header,
        sub_sep,
    ]

    res_by_era = {}
    for era in eras:
        res_by_era[era] = {r["name"]: r for r in all_era_results.get(era, [])}

    resonance_order = ["omega", "phi", "jpsi", "psi2s", "upsilon1s", "upsilon2s"]

    for res_name in resonance_order:
        has_any = False
        for era in eras:
            r = res_by_era.get(era, {}).get(res_name)
            if r:
                has_any = True
                mc_pdg_str = f"{r['mc_pdg_diff_percent']:+.3f} +- {r['mc_pdg_diff_err_percent']:.3f}"
                data_pdg_str = f"{r['data_pdg_diff_percent']:+.3f} +- {r['data_pdg_diff_err_percent']:.3f}"
                data_mc_str = f"{r['rel_diff']*100:+.3f} +- {r['rel_diff_err']*100:.3f}"

                line = f"{r['name']:<12} {era:<10} {mc_pdg_str:<25} {data_pdg_str:<25} {data_mc_str:<25}"
                lines.append(line)
        if has_any:
            lines.append(sub_sep)

    lines.append(separator)
    return "\n".join(lines)


def format_raw_parameters_dump(all_era_results, eras, jpsi_mode="average"):
    """
    Format a complete dump of all retrieved fit parameters for MC and Data,
    specifically showing the J/psi decomposition (jpsi_mean, jpsi_mean_core, jpsi_core_frac)
    alongside effective/selected mean values.
    """
    lines = []

    # 1. Dedicated J/psi decomposition dump
    header_jpsi = (
        f"{'Era':<10} {'Sample':<8} {'jpsi_mean (CB) [GeV]':<26} "
        f"{'jpsi_mean_core (Gauss) [GeV]':<30} {'jpsi_core_frac':<24} "
        f"{f'Selected ({jpsi_mode}) [GeV]':<26}"
    )
    sep_jpsi = "=" * len(header_jpsi)
    sub_sep_jpsi = "-" * len(header_jpsi)

    lines.extend([
        sep_jpsi,
        f"RAW J/PSI FIT PARAMETERS DUMP (RooAddPdf: CB + Gauss, Selected mode: {jpsi_mode})",
        sep_jpsi,
        header_jpsi,
        sub_sep_jpsi,
    ])

    for era in eras:
        res_list = all_era_results.get(era, [])
        jpsi_item = next((r for r in res_list if r["name"] == "jpsi"), None)
        if not jpsi_item:
            continue

        raw_mc = jpsi_item.get("raw_mc", {})
        raw_data = jpsi_item.get("raw_data", {})

        mc_cb_str = f"{raw_mc.get('mu_cb', 0.0):.6f} +- {raw_mc.get('err_cb', 0.0):.6f}"
        mc_core_str = f"{raw_mc.get('mu_core', 0.0):.6f} +- {raw_mc.get('err_core', 0.0):.6f}"
        mc_frac_str = f"{raw_mc.get('frac', 0.0):.6f} +- {raw_mc.get('err_frac', 0.0):.6f}"
        mc_eff_str = f"{jpsi_item['val_mc']:.6f} +- {jpsi_item['err_mc']:.6f}"

        data_cb_str = f"{raw_data.get('mu_cb', 0.0):.6f} +- {raw_data.get('err_cb', 0.0):.6f}"
        data_core_str = f"{raw_data.get('mu_core', 0.0):.6f} +- {raw_data.get('err_core', 0.0):.6f}"
        data_frac_str = f"{raw_data.get('frac', 0.0):.6f} +- {raw_data.get('err_frac', 0.0):.6f}"
        data_eff_str = f"{jpsi_item['val_data']:.6f} +- {jpsi_item['err_data']:.6f}"

        lines.append(f"{era:<10} {'MC':<8} {mc_cb_str:<26} {mc_core_str:<30} {mc_frac_str:<24} {mc_eff_str:<26}")
        lines.append(f"{era:<10} {'Data':<8} {data_cb_str:<26} {data_core_str:<30} {data_frac_str:<24} {data_eff_str:<26}")
        lines.append(sub_sep_jpsi)

    lines.append(sep_jpsi)

    # 2. Complete dump of all parameters for all resonances
    header_all = (
        f"{'Era':<10} {'Resonance':<11} {'Reg':<4} {'Parameter Name':<34} "
        f"{'MC Value +- Error':<26} {'Data Value +- Error':<26}"
    )
    sep_all = "=" * len(header_all)
    sub_sep_all = "-" * len(header_all)

    lines.extend([
        "",
        sep_all,
        "ALL RETRIEVED RESONANCE FIT PARAMETERS DUMP",
        sep_all,
        header_all,
        sub_sep_all,
    ])

    for era in eras:
        res_list = all_era_results.get(era, [])
        for r in res_list:
            res_name = r["name"]
            reg = r["region"]
            raw_mc = r.get("raw_mc", {})
            raw_data = r.get("raw_data", {})

            if res_name == "jpsi":
                p1_mc = f"{raw_mc.get('mu_cb', 0.0):.6f} +- {raw_mc.get('err_cb', 0.0):.6f}"
                p1_data = f"{raw_data.get('mu_cb', 0.0):.6f} +- {raw_data.get('err_cb', 0.0):.6f}"
                lines.append(f"{era:<10} {res_name:<11} {reg:<4} {'jpsi_mean_' + era + ' (CB)':<34} {p1_mc:<26} {p1_data:<26}")

                p2_mc = f"{raw_mc.get('mu_core', 0.0):.6f} +- {raw_mc.get('err_core', 0.0):.6f}"
                p2_data = f"{raw_data.get('mu_core', 0.0):.6f} +- {raw_data.get('err_core', 0.0):.6f}"
                lines.append(f"{'':<10} {'':<11} {'':<4} {'jpsi_mean_core_' + era + ' (Gauss)':<34} {p2_mc:<26} {p2_data:<26}")

                p3_mc = f"{raw_mc.get('frac', 0.0):.6f} +- {raw_mc.get('err_frac', 0.0):.6f}"
                p3_data = f"{raw_data.get('frac', 0.0):.6f} +- {raw_data.get('err_frac', 0.0):.6f}"
                lines.append(f"{'':<10} {'':<11} {'':<4} {'jpsi_core_frac_' + era + ' (fraction)':<34} {p3_mc:<26} {p3_data:<26}")

                eff_mc = f"{r['val_mc']:.6f} +- {r['err_mc']:.6f}"
                eff_data = f"{r['val_data']:.6f} +- {r['err_data']:.6f}"
                lines.append(f"{'':<10} {'':<11} {'':<4} {f'[Selected ({jpsi_mode}) Mean]':<34} {eff_mc:<26} {eff_data:<26}")
            else:
                var_name = f"{res_name}_mean_{era}"
                mc_val = f"{r['val_mc']:.6f} +- {r['err_mc']:.6f}"
                data_val = f"{r['val_data']:.6f} +- {r['err_data']:.6f}"
                lines.append(f"{era:<10} {res_name:<11} {reg:<4} {var_name:<34} {mc_val:<26} {data_val:<26}")
        lines.append(sub_sep_all)

    lines.append(sep_all)
    return "\n".join(lines)


def print_and_save_resonance_table(all_era_results, eras, output_file=None, jpsi_mode="average"):
    """
    Format and print summary table of MC & Data resonance fits wrt PDG masses
    and Data vs MC relative variation, including raw parameters dump and the two additional views.
    """
    raw_dump_text = format_raw_parameters_dump(all_era_results, eras, jpsi_mode=jpsi_mode)

    header = (
        f"{'Era':<9} {'Resonance':<10} {'Reg':<4} {'M_PDG [GeV]':<11} "
        f"{'M_MC [GeV]':<22} {'MC-PDG [MeV]':<16} {'(MC-PDG)/PDG [%]':<18} "
        f"{'M_Data [GeV]':<22} {'Data-PDG [MeV]':<16} {'(Data-PDG)/PDG [%]':<19} "
        f"{'(Data-MC)/MC [%]':<20}"
    )
    separator = "=" * len(header)
    sub_sep = "-" * len(header)

    lines = [
        separator,
        "RESONANCE FIT COMPARISON TABLE (MC vs DATA vs PDG)",
        separator,
        header,
        sub_sep,
    ]

    for era, res_list in all_era_results.items():
        for r in res_list:
            mc_str = f"{r['val_mc']:.6f} +- {r['err_mc']:.6f}"
            data_str = f"{r['val_data']:.6f} +- {r['err_data']:.6f}"
            mc_pdg_mev_str = f"{r['mc_pdg_diff_mev']:+.2f} +- {r['err_mc']*1e3:.2f}"
            mc_pdg_pct_str = f"{r['mc_pdg_diff_percent']:+.3f} +- {r['mc_pdg_diff_err_percent']:.3f}"
            data_pdg_mev_str = f"{r['data_pdg_diff_mev']:+.2f} +- {r['err_data']*1e3:.2f}"
            data_pdg_pct_str = f"{r['data_pdg_diff_percent']:+.3f} +- {r['data_pdg_diff_err_percent']:.3f}"
            rel_str = f"{r['rel_diff']*100:+.3f} +- {r['rel_diff_err']*100:.3f}"

            line = (
                f"{era:<9} {r['name']:<10} {r['region']:<4} {r['pdg_mass']:<11.4f} "
                f"{mc_str:<22} {mc_pdg_mev_str:<16} {mc_pdg_pct_str:<18} "
                f"{data_str:<22} {data_pdg_mev_str:<16} {data_pdg_pct_str:<19} "
                f"{rel_str:<20}"
            )
            lines.append(line)
        lines.append(sub_sep)

    lines.append(separator)
    table_text = "\n".join(lines)

    view1_text = format_relative_shifts_table_by_era(all_era_results, eras)
    view2_text = format_relative_shifts_table_by_resonance(all_era_results, eras)

    full_output = (
        raw_dump_text
        + "\n\n"
        + table_text
        + "\n"
        + view1_text
        + "\n"
        + view2_text
    )

    print("\n" + raw_dump_text)
    print("\n" + table_text)
    print("\n" + view1_text)
    print("\n" + view2_text)

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w") as f:
            f.write(full_output + "\n")
        print(f"Complete table with all views saved to {output_file}")


def generate_latex_table(all_era_results, eras, diff_mode="pdg"):
    """
    Generate LaTeX table code for resonant background mean values across eras.

    diff_mode:
        "pdg": Row 2 shows (M_data - M_pdg)/M_pdg, Row 4 shows (M_mc - M_pdg)/M_pdg
        "mc":  Row 2 shows (M_data - M_pdg)/M_pdg, Row 4 shows (M_data - M_mc)/M_mc
    """
    res_by_era = {}
    for era in eras:
        res_by_era[era] = {r["name"]: r for r in all_era_results.get(era, [])}

    resonance_order = ["omega", "phi", "jpsi", "psi2s", "upsilon1s", "upsilon2s"]

    def fmt_pct(x):
        sign = "+" if x > 0 else "-" if x < 0 else ""
        return f"${sign}{abs(x):.2f}\\%$"

    n_eras = len(eras)
    col_spec = "l c " + "c" * n_eras
    mc_sublabel = r"    \quad (MC)"
    blank = ""

    caption = (
        "Fitted double Crystal Ball (dCB) mean values and relative shifts "
        r"$\Delta m / m_{\text{nominal}}$ across Run~3 data-taking eras for resonant backgrounds, "
        "compared to reference nominal PDG masses."
        if diff_mode == "pdg"
        else
        "Fitted double Crystal Ball (dCB) mean values across Run~3 data-taking eras for resonant backgrounds "
        r"in data ($\Delta m / m_{\text{nominal}}$) and relative shifts wrt MC ($\Delta m / m_{\text{MC}}$)."
    )
    label = (
        "tab:resonant_bkg_era_means_stacked_with_pdg"
        if diff_mode == "pdg"
        else "tab:resonant_bkg_era_means_stacked_with_mc"
    )

    lines = [
        r"\begin{table}[htbp]",
        r"  \centering",
        r"  \small",
        f"  \\caption{{{caption}}}",
        f"  \\label{{{label}}}",
        r"  \vspace{0.8em}",
        f"  \\begin{{tabular}}{{{col_spec}}}",
        r"    \toprule",
        f"    & \\multicolumn{{{n_eras + 1}}}{{c}}{{Mass $[\\text{{GeV}}]$}} \\\\",
        f"    \\cmidrule(lr){{2-{n_eras + 2}}}",
        "    Resonance & Nominal & " + " & ".join(eras) + r" \\",
        r"    \midrule",
    ]

    for res_name in resonance_order:
        if not any(res_name in res_by_era[era] for era in eras):
            continue

        tex_title = RESONANCE_TITLES.get(res_name, res_name)
        pdg_mass = PDG_MASSES[res_name]

        data_vals = []
        data_shifts = []
        mc_vals = []
        mc_shifts = []

        for era in eras:
            info = res_by_era[era].get(res_name)
            if info:
                data_vals.append(f"{info['val_data']:.4f}")
                data_shifts.append(fmt_pct(info['data_pdg_diff_percent']))
                mc_vals.append(f"{info['val_mc']:.4f}")
                if diff_mode == "pdg":
                    mc_shifts.append(fmt_pct(info['mc_pdg_diff_percent']))
                else:
                    mc_shifts.append(fmt_pct(info['rel_diff'] * 100.0))
            else:
                data_vals.append("-")
                data_shifts.append("-")
                mc_vals.append("-")
                mc_shifts.append("-")

        # Row 1: Data mean
        lines.append(f"    {tex_title:<24} & {pdg_mass:<7.4f} & " + " & ".join(f"{v:<9}" for v in data_vals) + r" \\")
        # Row 2: Data shift
        lines.append(f"    {blank:<24} & {blank:<7} & " + " & ".join(f"{v:<9}" for v in data_shifts) + r" \\")
        # Row 3: MC mean
        lines.append(f"{mc_sublabel:<28} & {blank:<7} & " + " & ".join(f"{v:<9}" for v in mc_vals) + r" \\")
        # Row 4: MC shift or Data-vs-MC shift
        lines.append(f"    {blank:<24} & {blank:<7} & " + " & ".join(f"{v:<9}" for v in mc_shifts) + r" \\")
        lines.append(r"    \addlinespace")

    # Remove trailing \addlinespace
    if lines[-1] == r"    \addlinespace":
        lines.pop()

    lines.extend([
        r"    \bottomrule",
        r"  \end{tabular}",
        r"\end{table}",
    ])

    return "\n".join(lines)


def plot_scale_variation(
    masses,
    relative_scale,
    ylabel,
    output_path,
    era=None,
    resonance_points=None,
    color="black",
    is_percent=False,
    bkg_func=None,
    xlim=(0.6, 11.0),
):
    """
    Plot scale variation following the styling of plot_yield_variations.py.
    Overlays resonance data points if provided (excluding Y(2S)).
    Saves both .png and .pdf.
    """
    fig, ax = plt.subplots(figsize=(10, 10))

    scale_vals = relative_scale * 100.0 if is_percent else relative_scale

    # Signed representation: show +- 1 sigma systematic band
    ax.plot(
        masses,
        scale_vals,
        color=color,
        linewidth=2,
    )
    ax.plot(
        masses,
        -scale_vals,
        color=color,
        linestyle="--",
        linewidth=2,
    )
    ax.fill_between(
        masses,
        -scale_vals,
        scale_vals,
        color=color,
        alpha=0.12,
    )
    ax.axhline(0, color="gray", linestyle=":", linewidth=1)

    # Exclude Y(2S) from plotting
    plot_points = [pt for pt in (resonance_points or []) if pt.get("name") != "upsilon2s"]

    # Overlay resonance comparison points (round marker 'o')
    for pt in plot_points:
        pt_val = pt["rel_diff"] * 100.0 if is_percent else pt["rel_diff"]
        pt_err = pt["rel_diff_err"] * (100.0 if is_percent else 1.0)

        ax.errorbar(
            pt["pdg_mass"],
            pt_val,
            yerr=pt_err,
            fmt="o",
            markersize=6,
            capsize=3,
            color=color,
            ecolor=color,
        )

    # Clean legend
    from matplotlib.lines import Line2D
    handles = [
        Line2D([0], [0], color=color, linestyle="-", linewidth=2, label=f"Scale ({era})" if era else "Scale systematic"),
    ]
    if plot_points:
        res_label = f"Resonances ({era})" if era else "Resonances"
        if bkg_func:
            res_label += f" ({bkg_func.capitalize()})"
        handles.append(
            Line2D([0], [0], color=color, marker="o", markersize=6, linestyle="None", label=res_label)
        )

    ax.set_xlabel(r"$M(Z_D)$ [GeV]")
    ax.set_ylabel(ylabel)
    ax.set_xlim(xlim)
    ax.legend(handles=handles, loc="best", fontsize=14)
    ax.grid(True)
    hep.cms.label(loc=0, data=True, label="Preliminary", com=13.6, ax=ax)

    for ext in ["png", "pdf"]:
        fig.savefig(output_path.with_suffix(f".{ext}"))

    plt.close(fig)


def plot_all_eras_comparison(
    masses,
    era_scales,
    all_resonance_points,
    ylabel,
    output_path,
    is_percent=False,
    bkg_func=None,
    xlim=(0.6, 11.0),
):
    """Plot scale variation across all eras for direct comparison."""
    fig, ax = plt.subplots(figsize=(10, 10))

    ax.axhline(0, color="gray", linestyle=":", linewidth=1)

    for era, rel_scale in era_scales.items():
        color = ERA_COLORS.get(era, "black")
        scale_vals = rel_scale * 100.0 if is_percent else rel_scale

        ax.plot(
            masses,
            scale_vals,
            color=color,
            linewidth=2,
        )
        ax.plot(
            masses,
            -scale_vals,
            color=color,
            linestyle="--",
            linewidth=1.5,
        )
        ax.fill_between(
            masses,
            -scale_vals,
            scale_vals,
            color=color,
            alpha=0.08,
        )

        # Plot resonance points for this era, excluding upsilon2s
        res_list = [pt for pt in all_resonance_points.get(era, []) if pt.get("name") != "upsilon2s"]
        for pt in res_list:
            pt_val = pt["rel_diff"] * 100.0 if is_percent else pt["rel_diff"]
            pt_err = pt["rel_diff_err"] * (100.0 if is_percent else 1.0)

            ax.errorbar(
                pt["pdg_mass"],
                pt_val,
                yerr=pt_err,
                fmt="o",
                markersize=6,
                capsize=3,
                color=color,
                ecolor=color,
            )

    # Custom legend:
    # Single entry for each era with both line and marker in era's color
    # Then separate black entries: line for "scale", marker for "resonance"
    from matplotlib.lines import Line2D
    handles = []
    for era in era_scales.keys():
        c = ERA_COLORS.get(era, "black")
        handles.append(
            Line2D([0], [0], color=c, marker="o", markersize=6, linestyle="-", linewidth=2, label=era)
        )
    handles.append(
        Line2D([0], [0], color="black", linestyle="-", linewidth=2, label="Energy scale")
    )
    res_label = f"Resonances ({bkg_func.capitalize()})" if bkg_func else "Resonances"
    handles.append(
        Line2D([0], [0], color="black", marker="o", markersize=6, linestyle="None", label=res_label)
    )

    ax.set_xlabel(r"$M(Z_D)$ [GeV]")
    ax.set_ylabel(ylabel)
    ax.set_xlim(xlim)
    ax.legend(handles=handles, loc="best", fontsize=14)
    ax.grid(True)
    hep.cms.label(loc=0, data=True, label="Preliminary", com=13.6, ax=ax)

    for ext in ["png", "pdf"]:
        fig.savefig(output_path.with_suffix(f".{ext}"))

    plt.close(fig)


def plot_scale_only_comparison(
    masses,
    era_scales,
    ylabel,
    output_path,
    xlim=(0.6, 11.0),
):
    """
    Plot scale-only relative uncertainty (% Delta M / M) across all eras:
    no bands/symmetrization (no fill_between, no negative mirror line),
    no resonances, just the initial scale uncertainty curves for each era.
    """
    fig, ax = plt.subplots(figsize=(10, 10))

    ax.axhline(0, color="gray", linestyle=":", linewidth=1)

    for era, rel_scale in era_scales.items():
        color = ERA_COLORS.get(era, "black")
        scale_vals = rel_scale * 100.0

        ax.plot(
            masses,
            scale_vals,
            color=color,
            linewidth=2.5,
            label=era,
        )

    ax.set_xlabel(r"$M(Z_D)$ [GeV]")
    ax.set_ylabel(ylabel)
    ax.set_xlim(xlim)
    ax.legend(loc="best", fontsize=16)
    ax.grid(True)
    hep.cms.label(loc=0, data=True, label="Preliminary", com=13.6, ax=ax)

    for ext in ["png", "pdf"]:
        fig.savefig(output_path.with_suffix(f".{ext}"))

    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(
        description="Plot signal mass uncertainty over mass due to energy scale systematic with SM resonance data vs MC overlay."
    )
    parser.add_argument(
        "--folder-tag",
        "--data-tag",
        "--tag",
        type=str,
        default="260828",
        dest="folder_tag",
        help="Input folder tag for data background dataset (default: 260828)",
    )
    parser.add_argument(
        "--mc-tag",
        type=str,
        default="261007",
        help="Input folder tag for MC resonant fit dataset (default: 261007)",
    )
    parser.add_argument(
        "--signal-tag",
        type=str,
        default="260727",
        help="Signal model output tag (default: 260727)",
    )
    parser.add_argument(
        "--bkg-funcs",
        "--bkg-func",
        "--altbkg",
        nargs="+",
        default=["bernstein", "chebyshev"],
        choices=["bernstein", "chebyshev"],
        help="Background function models used for data resonant fits (default: ['bernstein', 'chebyshev'])",
    )
    parser.add_argument(
        "--eras",
        nargs="+",
        default=["2022", "2022EE", "2023", "2023BPix"],
        help="List of eras to process",
    )
    parser.add_argument(
        "--min-mass",
        type=float,
        default=0.6,
        help="Minimum mass in GeV (default: 0.6)",
    )
    parser.add_argument(
        "--max-mass",
        type=float,
        default=11.0,
        help="Maximum mass in GeV (default: 11.0)",
    )
    parser.add_argument(
        "--mass-step",
        type=float,
        default=0.1,
        help="Mass step in GeV (default: 0.1)",
    )
    parser.add_argument(
        "--no-resonances",
        action="store_true",
        help="Disable automatic retrieval and overlay of resonance comparison points",
    )
    parser.add_argument(
        "--jpsi-mode",
        type=str,
        default="average",
        choices=["gauss", "core", "average", "weighted", "dcb", "cb"],
        help="Mean parameter to use for J/psi: 'gauss' (core Gaussian mean, default), 'dcb' (double Crystal Ball mean), or 'average' (weighted average).",
    )
    args = parser.parse_args()

    if args.jpsi_mode in ["gauss", "core"]:
        args.jpsi_mode = "gauss"
    elif args.jpsi_mode in ["dcb", "cb"]:
        args.jpsi_mode = "dcb"
    else:
        args.jpsi_mode = "average"

    ROOT.gROOT.SetBatch(True)
    hep.style.use("CMS")

    masses = np.round(
        np.arange(args.min_mass, args.max_mass + 0.5 * args.mass_step, args.mass_step),
        4,
    )

    mc_folder = (
        f"/eos/home-n/npalmeri/DiEleAnalyzer/Xee_fits/background_modelling/datasets/{args.mc_tag}"
    )
    data_folder = (
        f"/eos/home-n/npalmeri/DiEleAnalyzer/Xee_fits/background_modelling/datasets/{args.folder_tag}"
    )

    all_eras_scale = {}

    for era in args.eras:
        input_file = (
            f"/eos/home-n/npalmeri/DiEleAnalyzer/Xee_fits/background_modelling/"
            f"datasets/{args.folder_tag}/{era}/"
            f"dataset_data_region0_binned_data_envelope_allCorrections_{era}_envelope_full.root"
        )
        print(f"\n==================================================")
        print(f"Retrieving scale systematic for Era: {era}")
        print(f"Input: {input_file}")
        print(f"==================================================")

        root_file = ROOT.TFile.Open(input_file)
        if not root_file or root_file.IsZombie():
            print(f"Error: Could not open file {input_file}, skipping era {era}.")
            continue

        workspace = root_file.Get("w")
        if not workspace:
            print(f"Error: Workspace 'w' not found in {input_file}, skipping era {era}.")
            root_file.Close()
            continue

        try:
            params = retrieve_scale_parameters(workspace, era)
        except ValueError as err:
            print(f"Error: {err}")
            root_file.Close()
            continue

        print(f"Scale systematic parameters retrieved:")
        print(f"  mean_fit_par0_{era}: {params['p0']:.6e}")
        print(f"  mean_fit_par1_{era}: {params['p1']:.6e}")
        print(f"  mean_fit_par0_electronScaleVariation_avgdiff_{era}: {params['diff0']:.6e}")
        print(f"  mean_fit_par1_electronScaleVariation_avgdiff_{era}: {params['diff1']:.6e}")

        # Compute relative scale uncertainty Delta M / M
        relative_scale = compute_relative_scale(masses, params)
        all_eras_scale[era] = relative_scale

        summarize_scale_variation(era, masses, relative_scale)
        root_file.Close()

    parent_outfolder = Path(
        f"/eos/home-n/npalmeri/www/DiElectron/signal_model/{args.signal_tag}/"
        f"use_reco_mass_allCorrections"
    )
    parent_outfolder.mkdir(parents=True, exist_ok=True)

    # Scale-only cumulative plot across all eras (no bands/symmetrization, no resonances)
    if len(all_eras_scale) > 1:
        plot_scale_only_comparison(
            masses=masses,
            era_scales=all_eras_scale,
            ylabel=r"$\Delta M / M$ [%]",
            output_path=parent_outfolder / "electron_scale_variation_all_eras_percent_scale_only",
            xlim=(args.min_mass, args.max_mass),
        )
        print(f"\nScale-only cumulative comparison plot saved to {parent_outfolder}")

    # Iterate over data background functions (MC is always bernstein)
    for bkg_func in args.bkg_funcs:
        print(f"\n" + "#" * 80)
        print(f"# Processing Resonant Fits: Data [{bkg_func.upper()}], MC [BERNSTEIN], jpsi_mode: {args.jpsi_mode}")
        print(f"#" * 80)

        all_resonance_points = {}

        for era in args.eras:
            outfolder = parent_outfolder / f"era{era}"
            outfolder.mkdir(parents=True, exist_ok=True)

            resonance_points = []
            if not args.no_resonances:
                print(f"\nRetrieving SM resonance fits for era {era} (MC: {args.mc_tag} [bernstein], Data: {args.folder_tag} [{bkg_func}], jpsi_mode: {args.jpsi_mode})...")
                resonance_points = retrieve_all_resonance_points(
                    mc_folder=mc_folder,
                    data_folder=data_folder,
                    era=era,
                    bkg_func=bkg_func,
                    jpsi_mode=args.jpsi_mode,
                    mc_bkg_func="bernstein",
                )
                all_resonance_points[era] = resonance_points

            era_color = ERA_COLORS.get(era, "black")
            relative_scale = all_eras_scale.get(era)
            if relative_scale is None:
                continue

            # Plot signed relative scale variation (percentage) for this background function
            plot_scale_variation(
                masses=masses,
                relative_scale=relative_scale,
                ylabel=r"$\Delta M / M$ [%]",
                output_path=outfolder / f"electron_scale_variation_percent_{bkg_func}",
                era=era,
                resonance_points=resonance_points,
                color=era_color,
                is_percent=True,
                bkg_func=bkg_func,
                xlim=(args.min_mass, args.max_mass),
            )
            # For bernstein, also save as default un-suffixed filename for backward compatibility
            if bkg_func == "bernstein":
                plot_scale_variation(
                    masses=masses,
                    relative_scale=relative_scale,
                    ylabel=r"$\Delta M / M$ [%]",
                    output_path=outfolder / "electron_scale_variation_percent",
                    era=era,
                    resonance_points=resonance_points,
                    color=era_color,
                    is_percent=True,
                    bkg_func=bkg_func,
                    xlim=(args.min_mass, args.max_mass),
                )

        if all_resonance_points:
            table_path = parent_outfolder / f"resonance_fits_comparison_{bkg_func}.txt"
            print_and_save_resonance_table(
                all_resonance_points, args.eras, output_file=table_path, jpsi_mode=args.jpsi_mode
            )

            # Generate and print LaTeX tables
            latex_table_pdg = generate_latex_table(all_resonance_points, args.eras, diff_mode="pdg")
            latex_table_mc = generate_latex_table(all_resonance_points, args.eras, diff_mode="mc")

            print("\n" + "=" * 80)
            print(f"LATEX TABLE CODE ({bkg_func.upper()} - Shifts wrt Nominal PDG Mass):")
            print("=" * 80)
            print(latex_table_pdg)

            print("\n" + "=" * 80)
            print(f"LATEX TABLE CODE ({bkg_func.upper()} - Data vs MC Shifts):")
            print("=" * 80)
            print(latex_table_mc)

            tex_path_pdg = parent_outfolder / f"resonance_era_means_pdg_{bkg_func}.tex"
            with open(tex_path_pdg, "w") as f:
                f.write(latex_table_pdg + "\n")
            print(f"\nLaTeX table (PDG shifts, {bkg_func}) saved to: {tex_path_pdg}")

            tex_path_mc = parent_outfolder / f"resonance_era_means_mc_{bkg_func}.tex"
            with open(tex_path_mc, "w") as f:
                f.write(latex_table_mc + "\n")
            print(f"LaTeX table (Data vs MC shifts, {bkg_func}) saved to: {tex_path_mc}")

        # If multiple eras were processed, also save all-eras comparison plot in parent directory
        if len(all_eras_scale) > 1:
            plot_all_eras_comparison(
                masses=masses,
                era_scales=all_eras_scale,
                all_resonance_points=all_resonance_points,
                ylabel=r"$\Delta M / M$ [%]",
                output_path=parent_outfolder / f"electron_scale_variation_all_eras_percent_{bkg_func}",
                is_percent=True,
                bkg_func=bkg_func,
                xlim=(args.min_mass, args.max_mass),
            )
            if bkg_func == "bernstein":
                plot_all_eras_comparison(
                    masses=masses,
                    era_scales=all_eras_scale,
                    all_resonance_points=all_resonance_points,
                    ylabel=r"$\Delta M / M$ [%]",
                    output_path=parent_outfolder / "electron_scale_variation_all_eras_percent",
                    is_percent=True,
                    bkg_func=bkg_func,
                    xlim=(args.min_mass, args.max_mass),
                )

            print(f"\nAll-eras comparison plot ({bkg_func}) saved to {parent_outfolder}")

    print("\nDone!")


if __name__ == "__main__":
    main()
