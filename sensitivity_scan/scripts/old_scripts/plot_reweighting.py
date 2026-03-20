import uproot
import numpy as np
import matplotlib.pyplot as plt
import mplhep as hep
from mplhep import error_estimation
import awkward as ak
import ROOT
import argparse

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

parser = argparse.ArgumentParser(description="Plot reweighting comparison for Jpsi pT and DiElectron mass distributions.")
parser.add_argument("--prompt", action="store_true", help="Use prompt Jpsi MC")
parser.add_argument("--ecal_mass", action="store_true", help="Use Ecal mass instead of track pT for Jpsi mass")
parser.add_argument("--per_path", action="store_true", help="Make plots per L1/HLT")
cli_args = parser.parse_args()

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

    if "mass" in var:
        # make a different plot for each bin
        plot_range = (2.6, 4.2)
        plot_nbins = 50

        # make additional plots using snap (need to apply selections)
        if cli_args.prompt:
            # PROMPT JPSI
            snap_pre_path = "/eos/home-n/npalmeri/www/DiElectron/PS_reweighting/fw_output_Jpsi_reweight/zsnap/era2023/base_7_ID/"
            snap_post_path = "/eos/home-n/npalmeri/www/DiElectron/PS_reweighting/fw_output_Jpsi_reweight/zsnap/era2023/base_8_TriggerPSReweight/"
            snap_pre = uproot.open(snap_pre_path + "JPsiToEE.root")
            snap_post = uproot.open(snap_post_path + "JPsiToEE.root")
        else:
            # MIN BIAS
            snap_pre_path = "/eos/home-n/npalmeri/www/DiElectron/PS_reweighting/fw_output_actualReweight/zsnap/era2023/base_7_ID/"
            snap_post_path = "/eos/home-n/npalmeri/www/DiElectron/PS_reweighting/fw_output_actualReweight/zsnap/era2023/base_8_TriggerPSReweight/"
            snap_pre = uproot.open(snap_pre_path + "InclusiveMinBias.root")
            snap_post = uproot.open(snap_post_path + "InclusiveMinBias.root")

        snap_data_path = "/eos/home-n/npalmeri/www/DiElectron/PS_reweighting/fw_output_actualReweight/zsnap/era2023/base_8_TriggerPSReweight/DoubleElectronNANO_Run3_2023_data_allNano_2025Apr11_*.root_Run2023Dv1.root"
        snap_data = uproot.open(snap_data_path)

        t_pre = snap_pre["Events"].arrays()
        t_post = snap_post["Events"].arrays()
        t_data = snap_data["Events"].arrays()
        trees = {"pre": t_pre, "post": t_post, "data": t_data}
        
        # Extract weights (assuming they're in a branch called 'weight' or similar)
        # You may need to adjust the weight branch name
        mass_var = "DiElectron_ecal_mass" if cli_args.ecal_mass else "DiElectron_fitted_mass"
        masses = {"pre": t_pre[mass_var],
                  "post": t_post[mass_var],
                  "data": t_data[mass_var]}
        weights = {"pre": ak.broadcast_arrays(t_pre["weight"], masses["pre"])[0], 
                   "post": ak.broadcast_arrays(t_post["trigger_PS_weight"], masses["post"])[0],
                   "data": ak.broadcast_arrays(t_data["weight"], masses["data"])[0]}

        # # TEST FIGURE: are the base histos from the snap the same?
        # fig, ax = plt.subplots(1, 1, figsize=(10, 8))
        # weight_pre_reshaped = ak.broadcast_arrays(weights["pre"], t_pre["DiElectron_fitted_mass"])[0]
        # ax.hist(ak.flatten(t_pre["DiElectron_fitted_mass"]).to_numpy(), 
        #         weights=ak.flatten(weight_pre_reshaped).to_numpy(),
        #         bins=50, range=(2.6, 4.2), 
        #         histtype='step', label="Pre-reweighting", color=palette[0], density=True)
        # weight_post_reshaped = ak.broadcast_arrays(weights["post"], t_post["DiElectron_fitted_mass"])[0]
        # ax.hist(ak.flatten(t_post["DiElectron_fitted_mass"]).to_numpy(), 
        #         weights=ak.flatten(weight_post_reshaped).to_numpy(),
        #         bins=50, range=(2.6, 4.2),
        #         histtype='step', label="Post-reweighting", color=palette[1], density=True)

        # plt.xlabel("DiElectron mass [GeV]")
        # plt.ylabel("Density")
        # plt.yscale("log")
        # plt.legend()
        # plt.grid(True, alpha=0.6)
        # hep.cms.label("Preliminary", data=True, year=2023, lumi=7.98, com=13.6)
        # plt.savefig(f"{outfolder}/elena_plots/DiElectron_mass_reweighting_comparison.png")
        # plt.savefig(f"{outfolder}/elena_plots/DiElectron_mass_reweighting_comparison.pdf")

        bins = [[4, 7.5], [7.5, 9], [9, 11], [11, 14], [14, 20], [20, 40], [0, 100]]
        # bins = [[4, 7.5]]
        # bins = [[0, 100]]
        masses = {"pre" : {}, "post": {}, "data": {}}
        weights_binned = {"pre": {}, "post": {}}
        
        for (key, tree), weight_array in zip(trees.items(), weights.values()):
            for i, bin in enumerate(bins):
                mask1 = (tree["DiElectron_e1_pt"] >= bin[0]) & (tree["DiElectron_e1_pt"] < bin[1])
                mask2 = (tree["DiElectron_e2_pt"] >= bin[0]) & (tree["DiElectron_e2_pt"] < bin[1])
                combined_mask = mask1 * mask2
                masses[key][i] = tree[mass_var][combined_mask]
                if key == "data":
                    continue # no weights for data
                weights_binned[key][i] = weight_array[combined_mask]

        # Create a RooRealVar for the mass
        m = ROOT.RooRealVar("m", "m", plot_range[0], plot_range[1])
        # define weight variable
        weight_var = ROOT.RooRealVar("weight", "weight", 0, 1000)

        # Create RooDataSet for each distribution
        datasets = {"pre": {}, "post": {}, "data": {}}
        for key in datasets.keys():
            for i in range(len(bins)):
                args = []
                if key != "data":
                    args = [ROOT.RooFit.WeightVar(weight_var)]
                datasets[key][i] = ROOT.RooDataSet(f"data_{key}_bin_{i}", f"data_{key}_bin_{i}", ROOT.RooArgList(m), *args)

        # Fill the datasets
        for key, mass_array in masses.items():
            weight = weights[key]
            dataset = datasets[key]
            
            for i, bin in enumerate(bins):
                mass_array = ak.flatten(masses[key][i]).to_numpy()

                if key == "post":
                    weight_array = ak.flatten(weights_binned[key][i]).to_numpy()

                    for mass, w in zip(mass_array, weight_array):
                        if mass < plot_range[0] or mass > plot_range[1]:
                            continue
                        m.setVal(mass)
                        weight_var.setVal(w)
                        dataset[i].add(m, w)
                else:
                    for mass in mass_array:
                        if mass < plot_range[0] or mass > plot_range[1]:
                            continue
                        m.setVal(mass)
                        dataset[i].add(m)


        print("SUCCESSFULLY CREATED DATASETS", flush = True)

        for i, bin in enumerate(bins):
            fig, ax = plt.subplots(1, 1, figsize=(10, 8))
            
            # Get the data and weights for this bin
            mass_pre = ak.flatten(masses["pre"][i]).to_numpy()
            mass_post = ak.flatten(masses["post"][i]).to_numpy()
            weight_pre = ak.flatten(weights_binned["pre"][i]).to_numpy()
            weight_post = ak.flatten(weights_binned["post"][i]).to_numpy()
            
            # Create weighted histograms
            hist_pre, bin_edges = np.histogram(mass_pre, bins=plot_nbins, range=plot_range, weights=weight_pre)
            hist_post, _ = np.histogram(mass_post, bins=plot_nbins, range=plot_range, weights=weight_post)
            
            # For Poisson errors with weights, we need sum(w) and sum(w^2)
            hist_pre_sumw2, _ = np.histogram(mass_pre, bins=plot_nbins, range=plot_range, weights=weight_pre**2)
            hist_post_sumw2, _ = np.histogram(mass_post, bins=plot_nbins, range=plot_range, weights=weight_post**2)
            
            # Compute Poisson errors using sum(w) and sum(w^2)
            yerr_pre = poisson_interval_ignore_empty(hist_pre, hist_pre_sumw2)
            yerr_post = poisson_interval_ignore_empty(hist_post, hist_post_sumw2)
            
            # # APPROACH 1: convert to (proper) density
            # # NOTE: doesn't normalize to same area for some reason. To investigate.
            # # (check )
            # # Convert to density
            # bin_width = (plot_range[1] - plot_range[0]) / plot_nbins
            # total_weight_pre = weight_pre.sum()
            # total_weight_post = weight_post.sum()
            
            # hist_pre_density = hist_pre / (total_weight_pre * bin_width)
            # hist_post_density = hist_post / (total_weight_post * bin_width)
            # yerr_pre_density = yerr_pre / (total_weight_pre * bin_width)
            # yerr_post_density = yerr_post / (total_weight_post * bin_width)

            # print("BIN: ", bin)
            # print("Total count pre: ", total_weight_pre)
            # print("Sum of histo entries, pre:", hist_pre_density.sum())
            # print("Total count post: ", total_weight_post)
            # print("Sum of histo entries, post:", hist_post_density.sum())


            # APPROACH 2: normalize to 1 
            # Normalize to same area
            hist_pre_integral = hist_pre.sum()
            hist_post_integral = hist_post.sum()

            hist_pre_density = hist_pre / hist_pre_integral
            hist_post_density = hist_post / hist_post_integral
            yerr_pre_density = yerr_pre / hist_pre_integral
            yerr_post_density = yerr_post / hist_post_integral

            print("BIN: ", bin)
            print("hist pre integral: ", hist_pre_integral)
            print("hist post integral: ", hist_post_integral)
            print("Sum of histo entries, pre:", hist_pre_density.sum())
            print("Sum of histo entries, post:", hist_post_density.sum())
            
            # Compute bin centers
            bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
            
            # Plot with error bars
            ax.errorbar(bin_centers, hist_pre_density, yerr=yerr_pre_density, fmt='none', 
                       color=palette[0], alpha=0.7, capsize=2)
            ax.step(bin_centers, hist_pre_density, where='mid', 
                   label=f"Pre-reweight", color=palette[0])
            
            ax.errorbar(bin_centers, hist_post_density, yerr=yerr_post_density, fmt='none', 
                       color=palette[1], alpha=0.7, capsize=2)
            ax.step(bin_centers, hist_post_density, where='mid', 
                   label=f"Post-reweight", color=palette[1])

            # Plot data
            # NOTE: no weights, trigger PS built-in
            # also normalize to same area
            mass_data = ak.flatten(masses["data"][i]).to_numpy()
            hist_data, bin_edges_data = np.histogram(mass_data, bins=plot_nbins, range=plot_range)
            hist_data_density = hist_data / hist_data.sum()  # Normalize to same area
            bin_centers_data = (bin_edges_data[:-1] + bin_edges_data[1:]) / 2
            yerr_data = poisson_interval_ignore_empty(hist_data, hist_data)
            yerr_data_density = yerr_data / hist_data.sum()  # Normalize errors to same area

            ax.errorbar(bin_centers_data, hist_data_density, yerr=yerr_data_density, fmt='o',
                          color="black", label="Data", markersize=5, capsize=2, linestyle='None')
            # ax.step(bin_centers_data, hist_data_density, where='mid',
            #        color="black", alpha=0.5, linestyle='--', label="Data: {bin[0]} < pT < {bin[1]} GeV")

            # Fit each distribution with a 4-th deg. Bernstein + 2 crystal balls
            bkg_functions = {
                "pre" : {},
                "post": {},
                "data": {}
            }

            bkg_components = {
                "pre" : {},
                "post": {},
                "data": {}
            }

            fit_results = {
                "pre": {},
                "post": {},
                "data": {},
            }

            var_bin = []
            funcs_bin = []

            for key in bkg_functions.keys():
                print(f"Creating background function for {key} in bin {i}", flush=True)
                vars_bernstein = []
                inits = [1.7, 1.9, -0.06610, 0.52400, 0.19075]  # Default values for inclusive category
                # inits = [2.33352, 3.59166, -0.06610, 0.52400, 0.19075] # different attempt, but still doesn't work
                for j in range(5):
                    vars_bernstein.append(ROOT.RooRealVar(f"c{j}_{key}_bin_{i}", f"c{j}_{key}_bin_{i}", 
                                                inits[j], inits[j]*0.9, inits[j]*1.1))
                    # # freeze parameters for test
                    # vars_bernstein[j].setConstant(True)
                bkg_nonres = ROOT.RooBernstein(f"bkg_nonres_{key}_bin_{i}", f"bkg_nonres_{key}_bin_{i}", m, 
                                               ROOT.RooArgList(vars_bernstein))
                for var in vars_bernstein:
                    var_bin.append(var)

                # vars_poly = []
                # inits_poly = [1e4, -4.6e4, 3.6e4, 1.2e5]
                # lower_bounds = [0, 0, -1e6, 0]
                # upper_bounds = [1e6, 1e6, 1e6, 1e6]
                # for j in range(4):
                #     vars_poly.append(ROOT.RooRealVar(f"c{j}_{key}_bin_{i}", f"c{j}_{key}_bin_{i}", 
                #                                 inits_poly[j], lower_bounds[j], upper_bounds[j]))
                # bkg_nonres = ROOT.RooPolynomial(f"bkg_nonres_{key}_bin_{i}", f"bkg_nonres_{key}_bin_{i}", m, 
                #                                ROOT.RooArgList(vars_poly)
                # )
                # for var in vars_poly:
                #     var_bin.append(var)

                # vars_exps = []
                # funcs_exps = []
                # inits_exps = [1, 1, 2, 1, 0.1, -2.9]
                # for j in range(6):
                #     vars_exps.append(ROOT.RooRealVar(f"c{j}_exp_{key}_bin_{i}", f"c{j}_exp_{key}_bin_{i}", 
                #                                 inits_exps[j], -10, 10))
                #     var_bin.append(vars_exps[j])
                # bkg_nonres = ROOT.RooGenericPdf(f"bkg_nonres_exp_{key}_bin_{i}",
                #     f"@0 * exp(@1 * m) + @2 * exp(@3 * m) + @4 * exp(@5 * m)",
                #     ROOT.RooArgList(*vars_exps, m)
                # )

                funcs_bin.append(bkg_nonres)
                bkg_components[key]["nonres"] = bkg_nonres
                print(f"BKG NONRES: {bkg_nonres}", flush=True)


                inits = [3.1, 0.04, 0.6, 3.1, 1.5, 2.9]  # Default values for Jpsi
                # lower_bounds = [2.9, 0.01, 0., 0., 0, 0.]
                # upper_bounds = [3.3, 0.2, 5., 10., 10, 10.]
                lower_bound_factor = [0.8, 0.8, 0.8, 0.8, 0.8, 0.8]
                upper_bound_factor = [1.2, 1.2, 1.2, 1.2, 1.2, 1.2]
                if cli_args.ecal_mass:
                    inits[1] = 0.1 #much larger
                    lower_bound_factor[0] = 0.92
                    upper_bound_factor[1] = 1.1
                    lower_bound_factor[1] = 0.5
                    upper_bound_factor[1] = 2.0
                var_names = ["mean", "sigma", "alphaL", "nL", "alphaR", "nR"]
                vars_jpsi = []
                for j, name in enumerate(var_names):
                    vars_jpsi.append(ROOT.RooRealVar(f"{name}_{key}_bin_{i}", f"{name}_{key}_bin_{i}", 
                                                inits[j], inits[j]*lower_bound_factor[j], inits[j]*upper_bound_factor[j]))
                                                # inits[j], lower_bounds[j], upper_bounds[j]))
                bkg_jpsi = ROOT.RooCrystalBall(f"bkg_jpsi_{key}_bin_{i}", f"bkg_jpsi_{key}_bin_{i}", m, *vars_jpsi)
                funcs_bin.append(bkg_jpsi)
                bkg_components[key]["jpsi"] = bkg_jpsi
                print(f"BKG JPSI: {bkg_jpsi}", flush=True)

                for var in vars_jpsi:
                    var_bin.append(var)

                inits = [3.7, 0.05, 0.5, 5.5, 1., 6.]  # Default values for Psi2S
                # lower_bounds = [3.5, 0.01, 0., 0., 0, 0.]
                # upper_bounds = [3.9, 0.2, 5., 10., 10, 10.]
                lower_bound_factor = [0.9, 0.8, 0.8, 0.8, 0.8, 0.8]
                upper_bound_factor = [1.1, 1.2, 1.2, 1.2, 1.2, 1.2]
                if cli_args.ecal_mass:
                    inits[1] = 0.1 #much larger
                    lower_bound_factor[0] = 0.92
                    upper_bound_factor[1] = 1.1
                    lower_bound_factor[1] = 0.5
                    upper_bound_factor[1] = 2.0
                vars_psi2s = []
                for j, name in enumerate(var_names):
                    vars_psi2s.append(ROOT.RooRealVar(f"{name}_psi2s_{key}_bin_{i}", f"{name}_psi2s_{key}_bin_{i}", 
                                                inits[j], inits[j]*lower_bound_factor[j], inits[j]*upper_bound_factor[j]))
                                                # inits[j], lower_bounds[j], upper_bounds[j]))

                bkg_psi2s = ROOT.RooCrystalBall(f"bkg_psi2s_{key}_bin_{i}", f"bkg_psi2s_{key}_bin_{i}", m, *vars_psi2s)
                funcs_bin.append(bkg_psi2s)
                bkg_components[key]["psi2s"] = bkg_psi2s
                print(f"BKG PSI2S: {bkg_psi2s}",  flush=True)

                for var in vars_psi2s:
                    var_bin.append(var)

                # take guess for n_jpsi from maximum of histogram
                if key == "pre":
                    h = hist_pre
                elif key == "post":
                    h = hist_post
                else:
                    h = hist_data

                n_jpsi_guess = h.max()
                n_jpsi = ROOT.RooRealVar(f"n_jpsi_{key}_bin_{i}", f"n_jpsi_{key}_bin_{i}", n_jpsi_guess, n_jpsi_guess / 1e4, n_jpsi_guess * 1e4)
                n_psi2s = ROOT.RooRealVar(f"n_psi2s_{key}_bin_{i}", f"n_psi2s_{key}_bin_{i}", n_jpsi_guess / 15, n_jpsi_guess / 1e4, n_jpsi_guess * 1e4)
                n_nonres = ROOT.RooRealVar(f"n_nonres_{key}_bin_{i}", f"n_nonres_{key}_bin_{i}", n_jpsi_guess / 10, n_jpsi_guess / 1e4, n_jpsi_guess * 1e4)

                # n_jpsi = ROOT.RooRealVar(f"n_jpsi_{key}_bin_{i}", f"n_jpsi_{key}_bin_{i}", 2e4, 2e2, 1e8)
                # n_psi2s = ROOT.RooRealVar(f"n_psi2s_{key}_bin_{i}", f"n_psi2s_{key}_bin_{i}", 2e3, 1e1, 1e7)
                # n_nonres = ROOT.RooRealVar(f"n_nonres_{key}_bin_{i}", f"n_nonres_{key}_bin_{i}", 1e6, 3e2, 1e8)

                bkg_functions[key] = ROOT.RooAddPdf(f"bkg_{key}_bin_{i}", f"bkg_{key}_bin_{i}",
                    ROOT.RooArgList(bkg_jpsi, bkg_psi2s, bkg_nonres),
                    ROOT.RooArgList(n_jpsi, n_psi2s, n_nonres)
                )

                var_bin.append(n_jpsi)
                var_bin.append(n_psi2s)
                var_bin.append(n_nonres)
                funcs_bin.append(bkg_functions[key])
                                    
                print(f"BKG FUNCTION: {bkg_functions[key]}", flush=True)

            # Set labels and legend
            plt.xlabel("DiElectron mass [GeV]")
            plt.ylabel("Density")
            plt.yscale("log")
            plt.legend()
            plt.grid(True, alpha=0.6)

            hep.cms.label("Preliminary", data=True, year=2023, lumi=7.98, com=13.6)

            subfolder = "elena_plots"
            if cli_args.prompt:
                subfolder += "/prompt_jpsi"
            if cli_args.ecal_mass:
                subfolder += "/ecal_mass"
            if cli_args.per_path:
                subfolder += "/per_L1"
            print("Saving plot to:", f"{outfolder}/{subfolder}/DiElectron_mass_reweighting_comparison_bin_{bin[0]:.1f}_{bin[1]:.1f}.png", flush=True)
            plt.savefig(f"{outfolder}/{subfolder}/DiElectron_mass_reweighting_comparison_bin_{bin[0]:.1f}_{bin[1]:.1f}.png")
            plt.savefig(f"{outfolder}/{subfolder}/DiElectron_mass_reweighting_comparison_bin_{bin[0]:.1f}_{bin[1]:.1f}.pdf")

            # Fit each dataset and make a separate plot
            for key in datasets.keys():
                # if key != "pre":
                #     continue # TODO: REMOVE
                print(f"Fitting dataset {datasets[key][i]} with bkg function {bkg_functions[key]}", flush=True)
                dataset = datasets[key][i]
                fit_result = bkg_functions[key].fitTo(dataset,
                    ROOT.RooFit.Save(),
                    ROOT.RooFit.Range(plot_range[0], plot_range[1]),
                )
                fit_result.Print()
                
                print("SUCCESSFULLY FITTED", flush=True)
                # plot the fit result
                c2 = ROOT.TCanvas(f"c2_{key}_bin_{i}", f"c2_{key}_bin_{i}", 800, 600)
                c2.SetLogy()
                f = m.frame()
                dataset.plotOn(f, ROOT.RooFit.Name(f"data_{key}_bin_{i}"))
                bkg_functions[key].plotOn(f, ROOT.RooFit.Name(f"fit_{key}_bin_{i}"),
                                          ROOT.RooFit.LineColor(ROOT.kGray),
                                          ROOT.RooFit.FillStyle(3001))
                # plot components
                bkg_functions[key].plotOn(f, ROOT.RooFit.Components(ROOT.RooArgSet(bkg_components[key]["nonres"])), 
                                          ROOT.RooFit.LineColor(ROOT.kGray+1),
                                          ROOT.RooFit.FillStyle(3001))
                bkg_functions[key].plotOn(f, ROOT.RooFit.Components(ROOT.RooArgSet(bkg_components[key]["jpsi"])),
                                          ROOT.RooFit.LineColor(ROOT.kRed),
                                          ROOT.RooFit.FillStyle(3001))
                bkg_functions[key].plotOn(f, ROOT.RooFit.Components(ROOT.RooArgSet(bkg_components[key]["psi2s"])),
                                          ROOT.RooFit.LineColor(ROOT.kBlue),
                                          ROOT.RooFit.FillStyle(3001))

                # compute chi2
                chi2 = f.chiSquare(f"fit_{key}_bin_{i}", f"data_{key}_bin_{i}")
                print(f"Chi2 for {key} in bin {i}: {chi2}", flush=True)

                # print all post-fit parameter values for background function
                print(f"Post-fit parameters for {key} in bin {i}:")
                for var in bkg_functions[key].getParameters(ROOT.RooArgSet(m)):
                    print(f"{var.GetName()}: {var.getValV()} ± {var.getError()}")

                # draw chi2 and sigma value for jpsi in text box
                chi2_text = ROOT.TLatex(0.65, 0.85,
                                         f"#chi^2 = {chi2:.2f}")
                chi2_text.SetNDC()
                chi2_text.SetTextSize(0.04)
                chi2_text.SetTextColor(ROOT.kBlack)
                f.addObject(chi2_text)

                # draw sigma value for jpsi
                sigma_jpsi = bkg_components[key]["jpsi"].getParameters(ROOT.RooArgSet(m)).find(f"sigma_{key}_bin_{i}")
                sigma_text = ROOT.TLatex(0.65, 0.80,
                                         f"#sigma_{{J/#psi}} = {sigma_jpsi.getValV():.4f} #pm {sigma_jpsi.getError():.4f} GeV")
                sigma_text.SetNDC()
                sigma_text.SetTextSize(0.04)
                sigma_text.SetTextColor(ROOT.kBlack)
                f.addObject(sigma_text)

                # draw frame, add legend, save figure
                f.Draw()
                # change minimum of y-axis to 1e-6
                f.SetMinimum(1)
                c2.SaveAs(f"{outfolder}/{subfolder}/fits/DiElectron_mass_reweighting_fit_bin_{bin[0]:.1f}_{bin[1]:.1f}_{key}.png")
                c2.SaveAs(f"{outfolder}/{subfolder}/fits/DiElectron_mass_reweighting_fit_bin_{bin[0]:.1f}_{bin[1]:.1f}_{key}.pdf")