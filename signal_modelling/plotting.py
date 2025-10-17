import ROOT
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import uproot
import mplhep as hep

import os

# ------- PLOTTING SETTINGS ------ #

# enable batch mode
ROOT.gROOT.SetBatch(True)
ROOT.gStyle.SetLineScalePS(1.75)

# Load CMS style including color-scheme
hep.style.use("CMS")
plt.style.use(hep.style.CMS)

# Styling options
mpl.rcParams['patch.linewidth'] = 2 #for step hist plots

plots_outfolder = "plots_cats/"

# ------------ UTILS ------------- #

kBlue = ROOT.TColor.GetColor("#5790fc")
kYellow = ROOT.TColor.GetColor("#f89c20")
kRed = ROOT.TColor.GetColor("#e42536")

def make_plots_outfolder(outfolder, categories = ["inclusive"]):
    # make dir if it does not exist
    if not os.path.exists(outfolder):
        for subfolder in ["response", "model_test", "GEN_test", "shape_comparison"]:
            for category in categories:
                os.makedirs(os.path.join(outfolder, subfolder, category))
    else:
        print(f"Output folder {outfolder} already exists. Not creating it again.")

def copy_plots_to_eos(eos_folder, categories = ["inclusive"]):
    make_plots_outfolder(eos_folder, categories)
    os.system(f"cp -r {plots_outfolder}/* {eos_folder}")

# ------ PLOTTING FUNCTIONS ------ #

def plot_response_fit(samples, categories, wsfile, plot_fit = True, use_reco_mass = False):
    # open workspace
    f = ROOT.TFile.Open(wsfile)
    w = f.Get("w")

    # plotting settings
    ROOT.gROOT.SetBatch(True)

    # create output folder
    make_plots_outfolder(plots_outfolder, categories.keys())
    
    for name, sample in samples.items():
        for category_label, category in categories.items():
            cat_name = f"_{category['name']}" if category["name"] != "" else category["name"]

            # retrieve ingredients
            data = w.data(f"response_data_{name}{cat_name}")

            # draw the model
            c = ROOT.TCanvas(f"c{name}{cat_name}", f"c{name}{cat_name}", 900, 900)

            obs_name = "mass" if use_reco_mass else "reduced_mass"
            obs_title = "Mass" if use_reco_mass else "Reduced mass"
            frame = w.var(f"{obs_name}_{name}").frame(
                ROOT.RooFit.Title(f"{obs_title} distribution of {name} sample, category {category_label}")
            )
            data.plotOn(frame, ROOT.RooFit.Name("data"), ROOT.RooFit.DataError(ROOT.RooAbsData.SumW2))

            paramOn_draw_args = [
                ROOT.RooFit.Format("NEU", ROOT.RooFit.AutoPrecision(2)), 
                ROOT.RooFit.ShowConstants(True),
            ]

            if plot_fit:
                model = w.pdf(f"response_function_{name}{cat_name}")
                model.plotOn(frame)
                # model.paramOn(frame, 
                #               ROOT.RooFit.Layout(0.6, 0.9, 0.9),
                #               *paramOn_draw_args)
                # frame.getAttText().SetTextSize(0.03)
                # frame.getAttText().SetTextColor(kBlue)
            
            obs_latex = r"m(ee) [GeV]" if use_reco_mass else r"(m(ee) - mX)/mX"
            frame.GetXaxis().SetTitle(obs_latex)
            # frame.GetYaxis().SetTitle("Events")
            frame.Draw()

            # add legend with chi2
            chi2 = frame.chiSquare(f"{model.GetName()}_Norm[{w.var(f'{obs_name}_{name}').GetName()}]", "data")
            # model.createChi2(data)
            # chi2 = model_param.getValV()

            leg = ROOT.TLegend(0.15, 0.7, 0.16, 0.89)
            leg.SetBorderSize(0)
            leg.SetTextSize(0.03)
            leg.AddEntry("data", "Data", "P")
            leg.AddEntry("response_function", f"Fit, #chi^2 = {chi2:.2f}", "L")
            leg.Draw()

            for ext in ["png", "pdf"]:
                c.SaveAs(os.path.join(plots_outfolder, "response", f"response_{name}{cat_name}.{ext}"))

            # set y log scale
            c.SetLogy()
            frame.SetMinimum(1e-1)
            for ext in ["png", "pdf"]:
                c.SaveAs(os.path.join(plots_outfolder, "response", f"response_{name}{cat_name}_log.{ext}"))

    # close the file
    f.Close()

def plot_parametrization(samples, categories, wsfile, vars, parametrized_vars, gen = False, plot_post_param = True):
    # DEBUGGING: do not consider JPsiToEE sample for parameter fit
    samples = {name : sample for name, sample in samples.items() if "JPsiToEE" not in name}

    # retrieve workspace
    f = ROOT.TFile.Open(wsfile)
    w = f.Get("w")

    # retrieve fitted mean, sigma values vs. nominal mass of MC samples
    const_vars = list(set(vars) - set(parametrized_vars))

    x_mean = [sample["nominal_mass"] for sample in samples.values()]        
    x = {var : x_mean for var in vars}

    varnames = [f"{var}_GEN_fit" if gen else f"response_{var}" for var in vars]

    for category_label, category in categories.items():
        cat_name = f"_{category['name']}" if category["name"] != "" else category["name"]

        y = {var : [w.var(f"{varname}_{name}{cat_name}").getVal() for name in samples.keys()] for var, varname in zip(vars, varnames)}
        y_err = {var : [w.var(f"{varname}_{name}{cat_name}").getError() for name in samples.keys()] for var, varname in zip(vars, varnames)}

        x_jpsi = [3.097]
        y_jpsi = {var : [w.var(f"{varname}_JPsiToEE{cat_name}").getVal()] for var, varname in zip(vars, varnames)}
        y_jpsi_err = {var : [w.var(f"{varname}_JPsiToEE{cat_name}").getError()] for var, varname in zip(vars, varnames)}

        # retrieve linear fit params of mean, sigma values
        tag = "_GEN" if gen else ""
        x_fit = {var : np.linspace(0, 12, 100) for var in parametrized_vars}
        y_fit = {var : x_fit[var] * w.obj(f"{var}{cat_name}_fit_par1").getVal() + w.obj(f"{var}{cat_name}_fit_par0").getVal() for var in parametrized_vars}

        y_fit_plus = {var : y_fit[var] + w.obj(f'{var}{cat_name}_fit_par0').getError() + w.obj(f'{var}{cat_name}_fit_par1').getError() * x_fit[var] for var in parametrized_vars}
        y_fit_minus = {var : y_fit[var] - w.obj(f'{var}{cat_name}_fit_par0').getError() - w.obj(f'{var}{cat_name}_fit_par1').getError() * x_fit[var] for var in parametrized_vars}

        x_const = {var : [0, 12] for var in const_vars}
        y_const = {var : w.obj(f"{var}{cat_name}{tag}_const").getVal() for var in const_vars}
        y_const_err = {var : w.obj(f"{var}{cat_name}{tag}_const").getError() for var in const_vars}

        # Create figure and axes
        width = 9
        ncols = 2
        nrows = int(np.ceil(len(vars) / ncols))
        fig, axs = plt.subplots(nrows, ncols, figsize=(ncols * 10, nrows * 9))

        plot_args = {
            "linestyle": "None",
            "marker": "o",
            "markersize": 12,
            "elinewidth": 2,
            "capsize": 8,
        }

        fit_plot_args = {
            "color" : "red",
            "linestyle" : "--",
            "linewidth" : 2,
        }

        ylabels = {
            "mean" : "$\mu$ [GeV]",
            "mean_BW" : "$\mu$ [GeV]",
            "sigma" : "$\sigma$ [GeV]",
            "width_BW" : "$\Gamma$ [GeV]",
            "alphaL" : "$\\alpha_L$",
            "nL" : "$n_L$",
            "alphaR" : "$\\alpha_R$",
            "nR" : "$n_R$",
        }

        for var, ax in zip(vars, axs.flatten()):
            ### labels
            hep.cms.label(ax = ax, label = "Preliminary", data = False, com = 13.6, year = 2023, fontsize = 20)
            ax.set_xlabel("Nominal mass [GeV]")
            ax.set_ylabel(ylabels[var])
            title = f"Relativistic Breit-Wigner {var}, cat. {category_label}" if gen else f"Double-sided Crystal Ball {var}, cat. {category_label}"
            ax.set_title(title, fontsize = 30, pad = 40)
            
            if var in parametrized_vars:
                ### fit plot
                fit_label = f"Fit:\nm = {w.obj(f'{var}{cat_name}_fit_par1').getVal():.3g} +- {w.obj(f'{var}{cat_name}_fit_par1').getError():.3g}"
                fit_label = fit_label + f"\nq = {w.obj(f'{var}{cat_name}_fit_par0').getVal():.3g} +- {w.obj(f'{var}{cat_name}_fit_par0').getError():.3g}"
                ax.plot(x_fit[var], y_fit[var], label=fit_label, **fit_plot_args)

                # uncertainty band
                ax.fill_between(x_fit[var], y_fit_plus[var], y_fit_minus[var], color = "red", alpha = 0.15)

            else:
                # plot horizontal line at y_const
                ax.hlines(y_const[var], x_const[var][0], x_const[var][1], color = "red", linestyle = "--", label = f"Const. value: {y_const[var]:.3g}")
                # plot uncertainty band from y_const_err
                ax.fill_between(x_const[var], y_const[var] - y_const_err[var], y_const[var] + y_const_err[var], color = "red", alpha = 0.15)

            # ### points
            # # post-param
            # if plot_post_param:
            #     # retrieve fit result from workspace
            #     fitResult = {name : w.obj(f"fitresult_model_nonParam_fit_{name}_data_{name}") for name in samples.keys()}
            #     # Retrieve post-fit, parametrization values
            #     post_fit_y = [w.obj(f"{var}_nonParam_fit_{name}").getVal() for name in samples.keys()]
            #     if var not in parametrized_vars:
            #         post_fit_y_err = [w.obj(f"{var}_nonParam_fit_{name}").getError() for name in samples.keys()]
            #     else:
            #         post_fit_y_err = [w.obj(f"{var}_nonParam_fit_{name}").getPropagatedError(fitResult[name]) for name in samples.keys()]
            #         # post_fit_y_err = [0] * len(samples)

            #     ax.errorbar(x[var], post_fit_y, post_fit_y_err, **plot_args, label = "Post-fit", color = "black")
            
            # pre-param
            ax.errorbar(x[var], y[var], y_err[var], **plot_args)

            # jpsi point
            ax.errorbar(x_jpsi, y_jpsi[var], y_jpsi_err[var], **plot_args, label = r"$J/\psi \to ee$", color = "C1")

            ### final stuff
            ax.legend()

        plt.tight_layout()
        
        # Save figure
        outname = f"parametrization{tag}{cat_name}"
        print(f"Saving figure as {outname} (png, pdf)")
        fig.savefig(f"{plots_outfolder}{outname}.png")
        fig.savefig(f"{plots_outfolder}{outname}.pdf")


def plot_sample_fit(samples, categories, wsfile, plot_pre_param = False, plot_post_param = True, plot_residuals = True, gen = False):
    # open workspace
    f = ROOT.TFile.Open(wsfile)
    w = f.Get("w")

    # plotting settings
    ROOT.gROOT.SetBatch(True)

    tag = "_GEN" if gen else ""
    
    for name, sample in samples.items():
        for category_label, category in categories.items():
            cat_name = f"_{category['name']}" if category["name"] != "" else category["name"]

            # retrieve ingredients
            data = w.obj(f"data{tag}_{name}{cat_name}")

            # draw the model
            c = ROOT.TCanvas(f"c_{name}{cat_name}", f"c_{name}{cat_name}", 900, 900)

            if plot_residuals:
                pad1 = ROOT.TPad("pad1", "pad1", 0, 0.3, 1, 1)
                pad1.SetBottomMargin(0.01)
                pad2 = ROOT.TPad("pad2", "pad2", 0, 0, 1, 0.3)
                pad2.SetTopMargin(0.01)
                pad2.SetBottomMargin(0.3)

                pad1.Draw()
                pad2.Draw()

                pad1.cd()

            frame = w.var(f"mass{tag}_{name}").frame(ROOT.RooFit.Title(f"{name} sample, cat. {category_label}"))

            # draw invisible data (sets up frame, needed for residuals)
            data.plotOn(frame, ROOT.RooFit.Name(f"data{tag}"), ROOT.RooFit.Invisible(), ROOT.RooFit.DataError(ROOT.RooAbsData.SumW2))

            paramOn_draw_args = [
                ROOT.RooFit.Format("NEU", ROOT.RooFit.AutoPrecision(2)), 
                ROOT.RooFit.ShowConstants(True),
            ]

            plotOn_draw_args = [
                ROOT.RooFit.LineWidth(3),
            ]

            if plot_pre_param or gen:
                model_tag = "_GEN" if gen else "_nonParam_fit"
                model = w.obj(f"model{model_tag}_{name}{cat_name}")
                model.plotOn(frame, 
                            ROOT.RooFit.LineColor(kBlue),
                            ROOT.RooFit.Name(f"model{model_tag}{cat_name}"),
                            *plotOn_draw_args)
                label = "Nominal values" if gen else "Non parametrized"
                # model.paramOn(frame,
                #               ROOT.RooFit.Layout(0.6, 0.9, 0.9),
                #               ROOT.RooFit.Label(label),
                #               *paramOn_draw_args)
                # frame.getAttText().SetTextSize(0.03)
                # frame.getAttText().SetTextColor(kBlue)
                
            if plot_post_param:
                model_tag = "_GEN_fit" if gen else "_param"
                model_param = w.obj(f"model{model_tag}_{name}{cat_name}")
                model_param.plotOn(frame,
                                ROOT.RooFit.LineColor(kYellow),
                                ROOT.RooFit.Name(f"model{model_tag}"),
                                *plotOn_draw_args)
                label = "Fitted values" if gen else "Parametrized"
                # model_param.paramOn(frame,
                #                     ROOT.RooFit.Layout(0.1, 0.4, 0.9),
                #                     ROOT.RooFit.Label(label),
                #                     *paramOn_draw_args)
                # frame.getAttText().SetTextSize(0.03)
                # frame.getAttText().SetTextColor(kYellow)
            
            frame.Draw()

            chi2 = frame.chiSquare(f"model{model_tag}", f"data{tag}")
            # also compute chi2 manually
            data_binned = data.binnedClone(f"data{tag}_binned")
            chi2_manual = 0
            for i in range(data_binned.numEntries()):
                print(data_binned.get(i))
                # value = data_binned.get(i).getRealValue(f"mass{tag}_{name}")
                # error = data_binned.get(i).getError(f"mass{tag}_{name}")
                # model_value = model_param.evaluate(value)
                # chi2_manual += ((value - model_value) / error) ** 2
            
            print(f"Chi2 for {name} sample, cat. {category_label}: {chi2:.2f} (manual: {chi2_manual:.2f} / {data_binned.numEntries()})")

            # model_param.createChi2(data)
            # chi2 = model_param.getValV()

            if plot_residuals:
                pad2.cd()
                pad2.SetGrid()

                model_tag = "_GEN" if gen else "_param"
                residuals_param = frame.residHist(f"data{tag}", f"model{model_tag}", True, True)

                color = kBlue if gen else kYellow
                residuals_param.SetMarkerColor(color)
                residuals_param.SetLineColor(color)
                residuals_param.SetMarkerStyle(20)
                residuals_param.SetMarkerSize(0.8)

                residuals_param.GetYaxis().SetTitle("Pulls")
                residuals_param.GetYaxis().SetTitleSize(0.1)
                residuals_param.GetYaxis().SetTitleOffset(0.3)
                residuals_param.GetYaxis().SetLabelSize(0.1) 
                residuals_param.GetXaxis().SetTitleSize(0.1)
                residuals_param.GetXaxis().SetTitleOffset(0.9)
                residuals_param.GetXaxis().SetLabelSize(0.1)
                residuals_param.GetXaxis().SetTitle(f"M(ee){tag} [GeV]")

                # remove title
                residuals_param.SetTitle("")

                # make x axis match exactly top frame
                residuals_param.GetXaxis().SetRangeUser(frame.GetXaxis().GetXmin(), frame.GetXaxis().GetXmax())
                # set y range to -5,5
                residuals_param.SetMinimum(-5)
                residuals_param.SetMaximum(5)
                # change number of axis divisions
                residuals_param.GetYaxis().SetNdivisions(505)

                residuals_param.Draw("AP")
                if gen and plot_post_param:
                    residuals_fit = frame.residHist(f"data_GEN", f"model_GEN_fit", True, True)
                    residuals_fit.SetMarkerColor(kYellow)
                    residuals_fit.SetLineColor(kYellow)
                    residuals_fit.SetMarkerStyle(20)
                    residuals_fit.SetMarkerSize(0.8)
                    residuals_fit.Draw("P SAME")        

            # actually draw data
            pad1.cd()
            data.plotOn(frame, 
                        ROOT.RooFit.Name("data"),
                        ROOT.RooFit.MarkerSize(0.8),
                        ROOT.RooFit.DataError(ROOT.RooAbsData.SumW2))
            frame.Draw()

            leg = ROOT.TLegend(0.15, 0.7, 0.3, 0.89)
            leg.SetBorderSize(0)
            leg.SetTextSize(0.03)
            leg.AddEntry(f"data{tag}", "Data", "P")
            leg.AddEntry(f"model{model_tag}", f"Fit, #chi^2 = {chi2:.2f}", "L")
            leg.Draw()

            outname = "GEN_test_BW_" if gen else "signal_model_"
            for ext in ["png", "pdf"]:
                c.SaveAs(os.path.join(plots_outfolder, "model_test", f"{outname}{name}{cat_name}.{ext}"))

            # set y log scale
            pad1.SetLogy()
            frame.SetMinimum(1e-1)
            for ext in ["png", "pdf"]:
                c.SaveAs(os.path.join(plots_outfolder, "model_test", f"{outname}{name}{cat_name}_log.{ext}"))

    # close the file
    f.Close()    

def plot_model_only(samples, categories, wsfile, parametrized_vars):
    # open workspace
    f = ROOT.TFile.Open(wsfile)
    w = f.Get("w")

    # plotting settings
    ROOT.gROOT.SetBatch(True)

    tag = "test"

    # retrieve mass_test variable
    mass = w.var(f"mass_{tag}")

    for category_label, category in categories.items():
        cat_name = f"_{category['name']}" if category["name"] != "" else category["name"]

        # retrieve all models in workspace of the type model_{tag}_Mxxx
        models = [key.GetName() for idx, key in enumerate(w.allGenericObjects()) if f"model_test_M" in key.GetName() and cat_name in key.GetName() and idx % 3 == 0]
        samples = {model.split("_")[-1] : model for model in models}

        # create frame
        c = ROOT.TCanvas("c", "c", 1200, 900)
        frame = mass.frame(ROOT.RooFit.Title(f"Parametric model for several mass points, cat. {category_label}"))

        for idx, (sample, model) in enumerate(samples.items()):
            w.obj(model).plotOn(frame,
                                ROOT.RooFit.Name(model), 
                                ROOT.RooFit.LineWidth(3), 
                                ROOT.RooFit.Name(sample),
                                ROOT.RooFit.LineColor(59 + idx))
        
        # change x axis label
        frame.GetXaxis().SetTitle("M(ee) [GeV]")
        frame.GetYaxis().SetTitle("Density")
        frame.Draw()

        # leg = ROOT.TLegend(0.6, 0.2, 0.9, 0.89)
        # leg.SetBorderSize(0)
        # # change font size
        # leg.SetTextSize(0.03)
        # for sample, model in samples.items():
        #     leg.AddEntry(model, sample, "L")
        # leg.Draw()
            
        outname = f"signal_model_testing{cat_name}"
        for ext in ["png", "pdf"]:
            c.SaveAs(f"{plots_outfolder}{outname}.{ext}")

        # set y log scale
        c.SetLogy()
        for ext in ["png", "pdf"]:
            c.SaveAs(f"{plots_outfolder}{outname}_log.{ext}")

    # close the file
    f.Close()

def compare_zd_jpsi_shape(samples, categories, wsfile, plot_fit = True, use_reco_mass = False):
    # open workspace
    f = ROOT.TFile.Open(wsfile)
    w = f.Get("w")

    # plotting settings
    ROOT.gROOT.SetBatch(True)

    samples = {name : sample for name, sample in samples.items() if "JPsiToEE" in name or "Zd_M3p1" in name}

    for category_label, category in categories.items():
        cat_name = f"_{category['name']}" if category["name"] != "" else category["name"]
    
        # rebuild dataset from sample files
        red_mass = w.obj("reduced_mass_JPsiToEE")
        mass = w.obj("mass_JPsiToEE")
        # gen_mass = w.obj("mass_GEN_JPsiToEE")
        
        masses = {
            "reduced_mass" : red_mass,
            "mass" : mass,
            # "gen_mass" : gen_mass,
        }
        
        datasets = {
            "reduced_mass" : {},
            "mass" : {},
            # "gen_mass" : {},
        }

        if use_reco_mass:
            keys = ["mass"]
        else:
            keys = ["reduced_mass", "mass"]

        print(keys)

        for var in keys:
            for name, sample in samples.items():
                f = ROOT.TFile.Open(sample['file'])
                t = f.Get("Events")

                datasets[var][name] = ROOT.RooDataSet(f"{var}_{name}{cat_name}", f"{var}_{name}{cat_name}", ROOT.RooArgSet(masses[var]))
                
                for i in range(t.GetEntries()):
                    t.GetEntry(i)
                    cat_vars = {var : t.__getattr__(var) for var in category["cuts"].keys()}
                    cat_ranges = {var : category["cuts"][var] for var in category["cuts"].keys()}

                    vals = []
                    if "gen" in var:
                        vals = [t.GenZd_invMass] if not isinstance(t.GenZd_invMass, ROOT.RVec('float')) else t.GenZd_invMass
                    elif "reduced" in var:
                        vals = [(val/t.GenZd_mass[0]) - 1 for val in t.SelectedDiEle_fitted_mass]
                    else:
                        vals = t.SelectedDiEle_fitted_mass

                    for j, val in enumerate(vals):
                        # CATEGORY CHECK
                        is_in_cat = True
                        for var, ranges in cat_ranges.items():
                            cat_var_value = cat_vars[var][j]
                            # consider OR of specified ranges
                            range_check = False
                            for r in ranges: 
                                if cat_var_value > r[0] and cat_var_value <= r[1]:
                                    range_check = True
                            if not range_check:
                                is_in_cat = False
                                break
                        
                        if not is_in_cat:
                            continue

                        masses[var].setVal(val)
                        datasets[var][name].add(ROOT.RooArgSet(masses[var]))

                f.Close()

        titles = {
            "reduced_mass" : "Reduced mass",
            "mass" : "Mass",
            # "gen_mass" : "GEN mass"
        }

        xlabels = {
            "reduced_mass" : "(m(ee) - mX)/mX",
            "mass" : "M(ee)",
            # "gen_mass" : "GEN M(ee)"
        }

        for key in keys:
            var = key
            dataset = datasets[key]

            c = ROOT.TCanvas(var, var, 900, 900)

            frame = masses[var].frame(
                ROOT.RooFit.Title(f"{titles[var]} distributions of JPsiToEE and Zd @ M=3.1 GeV samples, cat. {category_label}") 
            )

            colors = ["kBlack", "kRed"]

            for idx, (name, data) in enumerate(dataset.items()):
                data.plotOn(frame, 
                            ROOT.RooFit.Name(name),
                            ROOT.RooFit.MarkerColor(colors[idx]),
                            ROOT.RooFit.Rescale(1/data.sumEntries()))
            

            frame.GetXaxis().SetTitle(xlabels[var])
            frame.GetYaxis().SetTitle("Events")

            frame.Draw()

            # add legend
            x1 = 0.6 if var == "reduced_mass" else 0.11
            x2 = 0.9 if var == "reduced_mass" else 0.41
            leg = ROOT.TLegend(x1, 0.6, x2, 0.89)

            leg.SetBorderSize(0)
            leg.SetFillStyle(0)
            for name in dataset.keys():
                leg.AddEntry(name, name, "P")
            leg.Draw()
            
            for ext in ["png", "pdf"]:
                c.SaveAs(os.path.join(plots_outfolder, "shape_comparison", f"{var}_M3p1_comparison{cat_name}.{ext}"))

            # set y log scale
            c.SetLogy()
            for ext in ["png", "pdf"]:
                c.SaveAs(os.path.join(plots_outfolder, "shape_comparison", f"{var}_M3p1_comparison{cat_name}_log.{ext}"))

if __name__ == "__main__":
    from main import samples, wsfile
    
    plot_parametrization(samples, wsfile)
    plot_response_fit(samples, wsfile)
    plot_sample_fit(samples, wsfile)