"""
Plotting module for signal model analysis - Object-oriented approach

This module provides comprehensive plotting functionality for the signal modeling analysis,
organized using object-oriented principles.
"""

import ROOT
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import uproot
import mplhep as hep
import os
from typing import Dict, List, Optional, Tuple
from pathlib import Path

from signal_model_analyzer import SignalModelAnalyzer, SampleConfig, CategoryConfig


class PlotManager:
    """Manages plotting configuration and output"""
    
    def __init__(self, output_folder: str = "plots_cats/"):
        self.output_folder = Path(output_folder)
        self._setup_plotting_style()
        self._setup_colors()
        
    def _setup_plotting_style(self):
        """Setup ROOT and matplotlib plotting styles"""
        # ROOT settings
        ROOT.gROOT.SetBatch(True)
        ROOT.gStyle.SetLineScalePS(1.75)
        
        # Matplotlib settings
        hep.style.use("CMS")
        plt.style.use(hep.style.CMS)
        mpl.rcParams['patch.linewidth'] = 2
    
    def _setup_colors(self):
        """Define color scheme"""
        self.kBlue = ROOT.TColor.GetColor("#5790fc")
        self.kYellow = ROOT.TColor.GetColor("#f89c20")
        self.kRed = ROOT.TColor.GetColor("#e42536")
        self.cms6 = ["#5790fc", "#f89c20", "#e42536", "#964a8b", "#9c9ca1", "#7a21dd"]
        self.cms10 = ["#3f90da","#ffa90e","#bd1f01","#94a4a2","#832db6","#a96b59","#e76300","#b9ac70","#717581","#92dadd"]
    
    def _create_directory_structure(self, base_path: Path, categories: List[str]):
        """Create directory structure for given base path"""
        subdirs = ["response", "model_test", "GEN_test"]#, "shape_comparison"]
        
        for subdir in subdirs:
            for category in categories:
                dir_path = base_path / subdir / category
                print(f"Creating directory: {dir_path}")
                dir_path.mkdir(parents=True, exist_ok=True)
    
    def create_output_directories(self, categories: List[str]):
        """Create output directory structure"""
        self._create_directory_structure(self.output_folder, categories)
    
    def copy_to_eos(self, eos_folder: str, categories: List[str]):
        """Copy plots to EOS directory"""
        eos_path = Path(eos_folder)
        
        # Create local and EOS directory structures
        self.create_output_directories(categories)
        self._create_directory_structure(eos_path, categories)

        # Actually copy files      
        os.system(f"cp -r {self.output_folder}/* {eos_path}")


class ResponsePlotter:
    """Handles plotting of response functions"""
    
    def __init__(self, analyzer: SignalModelAnalyzer, plot_manager: PlotManager):
        self.analyzer = analyzer
        self.plot_manager = plot_manager
        self.workspace = analyzer.workspace_manager.workspace
    
    def plot_response_fits(self, use_reco_mass: bool = False, plot_fit: bool = True, plot_residuals: bool = True):
        """Plot response function fits for all samples and categories"""
        print("Plotting response function fits...")
        
        # Create output directories
        self.plot_manager.create_output_directories([category.name for category in self.analyzer.categories.values()])
        
        for name, sample in self.analyzer.samples.items():
            for category_label, category in self.analyzer.categories.items():
                self._plot_single_response_fit(sample, category, category_label, 
                                             use_reco_mass, plot_fit, plot_residuals)
    
    def _plot_single_response_fit(self, sample: SampleConfig, category: CategoryConfig, 
                                category_label: str, use_reco_mass: bool, plot_fit: bool, plot_residuals: bool):
        """Plot response fit for a single sample and category"""

        # Get data and model
        data = self.workspace.data(f"response_data_{sample.label}{category.label}")
        if not data:
            print(f"Warning: No data found for {sample.label}{category.label}")
            return
        
        # Create canvas
        c = ROOT.TCanvas(f"c{sample.label}{category.label}", f"c{sample.label}{category.label}", 900, 900)
        
        # Setup pads for residuals if needed
        if plot_residuals and plot_fit:
            pad1 = ROOT.TPad("pad1", "pad1", 0, 0.3, 1, 1)
            pad1.SetBottomMargin(0.01)
            pad2 = ROOT.TPad("pad2", "pad2", 0, 0, 1, 0.3)
            pad2.SetTopMargin(0.01)
            pad2.SetBottomMargin(0.3)
            pad1.Draw()
            pad2.Draw()
            pad1.cd()
        
        # Create frame
        obs_name = "mass" if use_reco_mass else "reduced_mass"
        obs_title = "Mass" if use_reco_mass else "Reduced mass"
        obs_var = self.workspace.var(f"{obs_name}_{sample.label}")
        
        # frame = obs_var.frame(
        #     ROOT.RooFit.Title(f"{obs_title} distribution of {sample.label} sample, category {category_label}")
        # )
        frame = obs_var.frame(sample.mass_range[1], sample.mass_range[2])
        frame.SetTitle(f"{obs_title} distribution of {sample.label} sample, category {category_label}")
        
        # Plot invisible data first (for residuals) if needed
        if plot_residuals and plot_fit:
            data.plotOn(frame, ROOT.RooFit.Name("data"), ROOT.RooFit.Invisible(), 
                       ROOT.RooFit.DataError(ROOT.RooAbsData.Poisson))
        
        # Plot fit if requested
        model = None
        if plot_fit:
            model = self.workspace.pdf(f"response_function_{sample.label}{category.label}")
            if model:
                model.plotOn(frame, ROOT.RooFit.Name("model"), ROOT.RooFit.LineWidth(3))
            else:
                print(f"WARNING: No model found for response_function_{sample.label}{category.label}")
        
        # Plot residuals if requested
        if plot_residuals and plot_fit and model:
            pad2.cd()
            pad2.SetGrid()
            
            residuals = frame.residHist("data", "model", True, True)
            residuals.SetMarkerColor(ROOT.kBlue)
            residuals.SetLineColor(ROOT.kBlue)
            residuals.SetMarkerStyle(20)
            residuals.SetMarkerSize(0.8)
            
            residuals.GetYaxis().SetTitle("Pulls")
            residuals.GetYaxis().SetTitleSize(0.1)
            residuals.GetYaxis().SetTitleOffset(0.3)
            residuals.GetYaxis().SetLabelSize(0.1)
            residuals.GetXaxis().SetTitleSize(0.1)
            residuals.GetXaxis().SetTitleOffset(0.9)
            residuals.GetXaxis().SetLabelSize(0.1)
            
            obs_latex = r"m(ee) [GeV]" if use_reco_mass else r"(m(ee) - mX)/mX"
            residuals.GetXaxis().SetTitle(obs_latex)
            residuals.SetTitle("")
            residuals.GetXaxis().SetRangeUser(frame.GetXaxis().GetXmin(), frame.GetXaxis().GetXmax())
            residuals.SetMinimum(-5)
            residuals.SetMaximum(5)
            residuals.GetYaxis().SetNdivisions(505)
            residuals.Draw("AP")
            
            pad1.cd()
        
        # Plot actual data
        if not (plot_residuals and plot_fit):
            data.plotOn(frame, ROOT.RooFit.Name("data"), ROOT.RooFit.DataError(ROOT.RooAbsData.Poisson))
        else:
            data.plotOn(frame, ROOT.RooFit.Name("data"), ROOT.RooFit.MarkerSize(0.8),
                       ROOT.RooFit.DataError(ROOT.RooAbsData.Poisson))
                        
        # Set axis labels
        obs_latex = r"m(ee) [GeV]" if use_reco_mass else r"(m(ee) - mX)/mX"
        frame.GetXaxis().SetTitle(obs_latex)
        frame.Draw()

        # Plot legend
        leg = ROOT.TLegend(0.15, 0.7, 0.16, 0.89)
        leg.SetBorderSize(0)
        leg.SetTextSize(0.03)
        leg.AddEntry("data", "Data", "P")
        if plot_fit and model:
            ndof = len(self.analyzer.param_manager.response_vars)
            chi2 = frame.chiSquare("model", "data", ndof)
            leg.AddEntry("model", f"Fit, #chi^2/ndf = {chi2:.2f} (ndf = {ndof})", "L")
        leg.Draw()
        
        # Save plots
        output_dir = self.plot_manager.output_folder / "response"
        for ext in ["png", "pdf"]:
            c.SaveAs(str(output_dir / category.name / f"response_{sample.label}{category.label}.{ext}"))
        
        # Log scale version
        if plot_residuals and plot_fit:
            pad1.SetLogy()
        else:
            c.SetLogy()
        frame.SetMinimum(1e-1)
        for ext in ["png", "pdf"]:
            c.SaveAs(str(output_dir / category.name / f"response_{sample.label}{category.label}_log.{ext}"))


class ParametrizationPlotter:
    """Handles plotting of parameter fits vs mass"""
    
    def __init__(self, analyzer: SignalModelAnalyzer, plot_manager: PlotManager):
        self.analyzer = analyzer
        self.plot_manager = plot_manager
        self.workspace = analyzer.workspace_manager.workspace
    
    def plot_parametrization(self, vars_to_plot: List[str], gen: bool = False):
        """Plot parameter values vs nominal mass"""
        print(f"Plotting parametrization {'(GEN)' if gen else ''}...")
        
        # Filter out JPsi samples for parameter fit visualization
        plot_samples = {name: sample for name, sample in self.analyzer.samples.items() 
                       if "JPsiToEE" not in name}
        
        for category_label, category in self.analyzer.categories.items():
            self._plot_parametrization_for_category(plot_samples, category, category_label, 
                                                   vars_to_plot, gen)
        
        # make a plot overlapping parametrization results for all categories
        self._plot_parametrization_comparison(plot_samples, self.analyzer.categories, 
                                              vars_to_plot, gen)
    
    def _plot_parametrization_for_category(self, samples: Dict[str, SampleConfig], 
                                         category: CategoryConfig, category_label: str,
                                         vars_to_plot: List[str], gen: bool):
        """Plot parametrization for a single category"""
        
        # Collect data points
        data_points = self._collect_parametrization_data(samples, category, vars_to_plot, gen)
        jpsi_points = self._collect_jpsi_data(category, vars_to_plot, gen)
        
        # Create figure
        ncols = 2
        nrows = int(np.ceil(len(vars_to_plot) / ncols))
        fig, axs = plt.subplots(nrows, ncols, figsize=(ncols * 10, nrows * 9))
        if nrows == 1 and ncols == 1:
            axs = [axs]
        elif nrows == 1:
            axs = axs.reshape(1, -1)
        
        # Plot each variable
        for i, var in enumerate(vars_to_plot):
            ax = axs.flatten()[i] if len(vars_to_plot) > 1 else axs[0]
            self._plot_single_parameter(ax, var, data_points[var], jpsi_points[var], 
                                      category, category_label, gen)
        
        # Remove unused subplots
        for i in range(len(vars_to_plot), len(axs.flatten())):
            axs.flatten()[i].remove()
        
        plt.tight_layout()
        
        # Save figure
        tag = "_GEN" if gen else ""
        outname = f"parametrization{tag}{category.label}"
        fig.savefig(str(self.plot_manager.output_folder / f"{outname}.png"))
        fig.savefig(str(self.plot_manager.output_folder / f"{outname}.pdf"))
        plt.close(fig)

    def _plot_parametrization_comparison(self, samples: Dict[str, SampleConfig], 
                                         categories: Dict[str, CategoryConfig],
                                         vars_to_plot: List[str], gen: bool):
        """Plot parametrization comparison across all categories"""

        # Create figure
        ncols = 2
        nrows = int(np.ceil(len(vars_to_plot) / ncols))
        fig, axs = plt.subplots(nrows, ncols, figsize=(ncols * 10, nrows * 9))
        if nrows == 1 and ncols == 1:
            axs = [axs]
        elif nrows == 1:
            axs = axs.reshape(1, -1)
        
        # Plot each variable
        for i, var in enumerate(vars_to_plot):
            ax = axs.flatten()[i] if len(vars_to_plot) > 1 else axs[0]
            
            # Setup basic plot styling
            self._setup_parameter_plot_style(ax, var, gen, comparison_mode=True)
            
            # Plot fits for each category
            for j, (cat_name, category) in enumerate(categories.items()):
                color = self.plot_manager.cms10[j % 10]
                self._plot_parameter_fit_only(ax, var, category, color, cat_name, gen)
            
            ax.legend()
        
        # Remove unused subplots
        for i in range(len(vars_to_plot), len(axs.flatten())):
            axs.flatten()[i].remove()
        
        plt.tight_layout()
        
        # Save figure
        tag = "_GEN" if gen else ""
        outname = f"parametrization_comparison{tag}"
        fig.savefig(str(self.plot_manager.output_folder / f"{outname}.png"))
        fig.savefig(str(self.plot_manager.output_folder / f"{outname}.pdf"))
        plt.close(fig)
    
    def _collect_parametrization_data(self, samples: Dict[str, SampleConfig], 
                                    category: CategoryConfig, vars_to_plot: List[str], 
                                    gen: bool, min_entries: int = 10) -> Dict[str, Dict]:
        """Collect parametrization data points"""

        data_points = {var: {'x': [], 'y': [], 'y_err': []} for var in vars_to_plot}    
        varnames = [f"{var}_GEN_fit" if gen else f"response_{var}" for var in vars_to_plot]
            
        for name, sample in samples.items():
            # FIXME: not very elegant, could invoke get_entry_counts_for_category somewhere higher up 
            entry_counts = self.analyzer.dataset_loader.get_dataset_entry_count(f"response_data_{sample.label}{category.label}")
            if entry_counts < min_entries:
                print(f"Skipping {name} in category {category.label} due to insufficient entries: {entry_counts}")
                continue
            for var, varname in zip(vars_to_plot, varnames):
                workspace_var = self.workspace.var(f"{varname}_{name}{category.label}")
                    
                if workspace_var:
                    data_points[var]['x'].append(sample.nominal_mass)
                    data_points[var]['y'].append(workspace_var.getVal())
                    data_points[var]['y_err'].append(workspace_var.getError())
        
        return data_points
    
    def _collect_jpsi_data(self, category: CategoryConfig, vars_to_plot: List[str], 
                          gen: bool) -> Dict[str, Dict]:
        """Collect JPsi data points"""
        
        jpsi_points = {var: {'x': [3.097], 'y': [], 'y_err': []} for var in vars_to_plot}
        
        varnames = [f"{var}_GEN_fit" if gen else f"response_{var}" for var in vars_to_plot]
        
        for var, varname in zip(vars_to_plot, varnames):
            workspace_var = self.workspace.var(f"{varname}_JPsiToEE{category.label}")
            if workspace_var:
                jpsi_points[var]['y'].append(workspace_var.getVal())
                jpsi_points[var]['y_err'].append(workspace_var.getError())
            else:
                jpsi_points[var]['y'].append(0)
                jpsi_points[var]['y_err'].append(0)
        
        return jpsi_points
    
    def _plot_single_parameter(self, ax, var: str, data_points: Dict, jpsi_points: Dict,
                             category: CategoryConfig, category_label: str, gen: bool):
        """Plot a single parameter vs mass with data points and fits"""
        # Styling for data points
        plot_args = {
            "linestyle": "None",
            "marker": "o", 
            "markersize": 12,
            "elinewidth": 2,
            "capsize": 8,
        }
        
        # Setup basic plot styling
        self._setup_parameter_plot_style(ax, var, gen, comparison_mode=False)
        
        # Update title to include category
        model_type = "Relativistic Breit-Wigner" if gen else "Double-sided Crystal Ball"
        title = f"{model_type} {var}, cat. {category_label}"
        ax.set_title(title, fontsize=30, pad=40)
        
        # Plot fit curve and uncertainty band
        self._plot_parameter_fit_only(ax, var, category, "red", "Fit", gen, show_fit_params=True)
        
        # Plot data points
        ax.errorbar(data_points['x'], data_points['y'], data_points['y_err'], **plot_args)
        
        # Plot JPsi point
        if jpsi_points['y'][0] != 0:
            ax.errorbar(jpsi_points['x'], jpsi_points['y'], jpsi_points['y_err'], 
                       **plot_args, label=r"$J/\psi \to ee$", color="C1")
        
        ax.legend()
    
    def _setup_parameter_plot_style(self, ax, var: str, gen: bool, comparison_mode: bool = False):
        """Setup basic styling for parameter plots"""
        # Labels
        ylabels = {
            "mean": r"$\mu$ [GeV]", "mean_BW": r"$\mu$ [GeV]",
            "sigma": r"$\sigma$ [GeV]", "width_BW": r"$\Gamma$ [GeV]",
            "alphaL": r"$\alpha_L$", "nL": r"$n_L$",
            "alphaR": r"$\alpha_R$", "nR": r"$n_R$",
        }
        
        hep.cms.label(ax=ax, label="Preliminary", data=False, com=13.6, year=2023, fontsize=20)
        ax.set_xlabel("Nominal mass [GeV]")
        ax.set_ylabel(ylabels.get(var, var))
        
        if comparison_mode:
            model_type = "Relativistic Breit-Wigner" if gen else "Double-sided Crystal Ball"
            title = f"{model_type} {var} comparison vs cat."
        else:
            title = f"Relativistic Breit-Wigner {var}" if gen else f"Double-sided Crystal Ball {var}"
        
        ax.set_title(title, fontsize=30, pad=40)
    
    def _plot_parameter_fit_only(self, ax, var: str, category: CategoryConfig, color: str, 
                                category_label: str, gen: bool, show_fit_params: bool = False):
        """Plot only the fit curve and uncertainty band for a parameter"""
        # Plot fit curves or constant lines
        if var in self.analyzer.parametrized_vars:
            # Get fit parameters
            par0_obj = self.workspace.obj(f"{var}{category.label}_fit_par0")
            par1_obj = self.workspace.obj(f"{var}{category.label}_fit_par1")
            
            if par0_obj and par1_obj:
                x_fit = np.linspace(0, 12, 100)
                y_fit = x_fit * par1_obj.getVal() + par0_obj.getVal()
                
                # Create label
                if show_fit_params:
                    fit_label = f"Fit:\nm = {par1_obj.getVal():.3g} ± {par1_obj.getError():.3g}"
                    fit_label += f"\nq = {par0_obj.getVal():.3g} ± {par0_obj.getError():.3g}"
                else:
                    fit_label = category_label
                
                # Plot the fit line
                ax.plot(x_fit, y_fit, color=color, linestyle="--", linewidth=2, 
                       label=fit_label)
                
                # Uncertainty band
                y_plus = y_fit + par0_obj.getError() + par1_obj.getError() * x_fit
                y_minus = y_fit - par0_obj.getError() - par1_obj.getError() * x_fit
                ax.fill_between(x_fit, y_plus, y_minus, color=color, alpha=0.15)
        else:
            # Constant parameter
            tag = "_GEN" if gen else ""
            const_obj = self.workspace.obj(f"{var}{category.label}{tag}_const")
            if const_obj:
                const_val = const_obj.getVal()
                const_err = const_obj.getError()
                
                # Create label
                if show_fit_params:
                    label = f"Const. value: {const_val:.3g}"
                else:
                    label = category_label
                
                ax.hlines(const_val, 0, 12, color=color, linestyle="--", linewidth=2,
                         label=label)
                ax.fill_between([0, 12], const_val - const_err, const_val + const_err, 
                               color=color, alpha=0.15)


class ModelPlotter:
    """Handles plotting of fitted models"""
    
    def __init__(self, analyzer: SignalModelAnalyzer, plot_manager: PlotManager):
        self.analyzer = analyzer
        self.plot_manager = plot_manager
        self.workspace = analyzer.workspace_manager.workspace
    
    def plot_sample_fits(self, plot_residuals: bool = True, gen: bool = False):
        """Plot model fits to sample data"""
        print(f"Plotting sample fits {'(GEN)' if gen else ''}...")
        
        tag = "_GEN" if gen else ""
        
        for name, sample in self.analyzer.samples.items():
            for category_label, category in self.analyzer.categories.items():
                self._plot_single_sample_fit(sample, category, category_label, 
                                           plot_residuals, gen, tag)
    
    def _plot_single_sample_fit(self, sample: SampleConfig, category: CategoryConfig,
                              category_label: str, plot_residuals: bool, gen: bool, tag: str):
        """Plot fit for a single sample and category"""

        # Get data
        data = self.workspace.obj(f"data{tag}_{sample.label}{category.label}")
        if not data:
            print(f"Warning: No data found for data{tag}_{sample.label}{category.label}")
            return
        
        # Create canvas
        c = ROOT.TCanvas(f"c_{sample.label}{category.label}", f"c_{sample.label}{category.label}", 900, 900)
        
        # Setup pads for residuals if needed
        if plot_residuals:
            pad1 = ROOT.TPad("pad1", "pad1", 0, 0.3, 1, 1)
            pad1.SetBottomMargin(0.01)
            pad2 = ROOT.TPad("pad2", "pad2", 0, 0, 1, 0.3)
            pad2.SetTopMargin(0.01)
            pad2.SetBottomMargin(0.3)
            pad1.Draw()
            pad2.Draw()
            pad1.cd()
        
        # Create frame
        mass_var = self.workspace.var(f"mass{tag}_{sample.label}")
        # frame = mass_var.frame(ROOT.RooFit.Title(f"{sample.label} sample, cat. {category_label}"))
        frame = mass_var.frame(sample.mass_range[1], sample.mass_range[2])
        frame.SetTitle(f"{sample.label} sample, cat. {category_label}")
        
        # Plot invisible data first (for residuals)
        data.plotOn(frame, ROOT.RooFit.Name(f"data{tag}"), ROOT.RooFit.Invisible(), 
                   ROOT.RooFit.DataError(ROOT.RooAbsData.Poisson))
        
        # Plot models
        model_tag = "_GEN" if gen else "_param"
        model = self.workspace.obj(f"model{model_tag}_{sample.label}{category.label}")
        if model:
            color = self.plot_manager.kBlue if gen else self.plot_manager.kYellow
            model.plotOn(frame, ROOT.RooFit.LineColor(color), 
                        ROOT.RooFit.Name(f"model{model_tag}"), ROOT.RooFit.LineWidth(3))
        
        # Plot residuals if requested
        if plot_residuals and model:
            pad2.cd()
            pad2.SetGrid()
            
            residuals = frame.residHist(f"data{tag}", f"model{model_tag}", True, True)
            residuals.SetMarkerColor(color)
            residuals.SetLineColor(color)
            residuals.SetMarkerStyle(20)
            residuals.SetMarkerSize(0.8)
            
            residuals.GetYaxis().SetTitle("Pulls")
            residuals.GetYaxis().SetTitleSize(0.1)
            residuals.GetYaxis().SetTitleOffset(0.3)
            residuals.GetYaxis().SetLabelSize(0.1)
            residuals.GetXaxis().SetTitleSize(0.1)
            residuals.GetXaxis().SetTitleOffset(0.9)
            residuals.GetXaxis().SetLabelSize(0.1)
            residuals.GetXaxis().SetTitle(f"M(ee){tag} [GeV]")
            residuals.SetTitle("")
            residuals.GetXaxis().SetRangeUser(frame.GetXaxis().GetXmin(), frame.GetXaxis().GetXmax())
            residuals.SetMinimum(-5)
            residuals.SetMaximum(5)
            residuals.GetYaxis().SetNdivisions(505)
            residuals.Draw("AP")
            
            pad1.cd()
        
        # Plot actual data
        data.plotOn(frame, ROOT.RooFit.Name("data"), ROOT.RooFit.MarkerSize(0.8),
                   ROOT.RooFit.DataError(ROOT.RooAbsData.Poisson))
        frame.Draw()

        # Add legend with chi2
        if model:
            chi2 = frame.chiSquare(f"model{model_tag}", f"data")
            print(f"Chi2 for sample {sample.label}, cat. {category_label}: {chi2}")
            leg = ROOT.TLegend(0.15, 0.7, 0.3, 0.89)
            leg.SetBorderSize(0)
            leg.SetTextSize(0.03)
            leg.AddEntry(f"data{tag}", "Data", "P")
            leg.AddEntry(f"model{model_tag}", f"Fit, #chi^2/ndf = {chi2:.2f}", "L")
            leg.Draw()
        
        # Save plots
        outname = "GEN_test_BW_" if gen else "signal_model_"
        output_dir = self.plot_manager.output_folder / "model_test"
        
        for ext in ["png", "pdf"]:
            c.SaveAs(str(output_dir / category.name / f"{outname}{sample.label}{category.label}.{ext}"))
        
        # Log scale version
        if plot_residuals:
            pad1.SetLogy()
        else:
            c.SetLogy()
        frame.SetMinimum(1e-1)
        for ext in ["png", "pdf"]:
            c.SaveAs(str(output_dir / category.name / f"{outname}{sample.label}{category.label}_log.{ext}"))
    
    def plot_models_only(self):
        """Plot parametric models for different mass points"""
        print("Plotting parametric models...")
        
        for category_label, category in self.analyzer.categories.items():
            self._plot_models_for_category(category, category_label)
    
    def _plot_models_for_category(self, category: CategoryConfig, category_label: str):
        """Plot models for a single category"""

        # Find all test models in workspace
        all_objects = [key.GetName() for idx, key in enumerate(self.workspace.allGenericObjects()) 
                      if f"model_test_M" in key.GetName() and category.label in key.GetName() and idx % 3 == 0]
        
        # For the inclusive category:
        if category.label == "":
            # exclude all models that have a category label
            all_objects = [model for model in all_objects if "_cat_" not in model]
        
        models = {model.split("_M")[1].split("_")[0]: model for model in all_objects}
        
        if not models:
            print(f"No test models found for category {category_label}")
            return
        
        # Create canvas and frame
        c = ROOT.TCanvas("c", "c", 1200, 900)
        mass_var = self.workspace.var("mass_test")
        frame = mass_var.frame(
            ROOT.RooFit.Title(f"Parametric model for several mass points, cat. {category_label}")
        )
        
        # Plot all models
        for idx, (sample, model_name) in enumerate(models.items()):
            model = self.workspace.obj(model_name)
            if model:
                model.plotOn(frame, ROOT.RooFit.Name(sample), ROOT.RooFit.LineWidth(3),
                           ROOT.RooFit.LineColor(59 + idx))
            else:
                print("WARNING: No model found for", model_name)
        
        # Set labels and draw
        frame.GetXaxis().SetTitle("M(ee) [GeV]")
        frame.GetYaxis().SetTitle("Density")
        frame.Draw()
        
        # Save plots
        outname = f"signal_model_testing{category.label}"
        for ext in ["png", "pdf"]:
            c.SaveAs(str(self.plot_manager.output_folder / "model_test" / category.name / f"{outname}.{ext}"))
        
        # Log scale version
        c.SetLogy()
        for ext in ["png", "pdf"]:
            c.SaveAs(str(self.plot_manager.output_folder / "model_test" / category.name / f"{outname}_log.{ext}"))


class SignalModelPlotter:
    """Main plotting interface for signal model analysis"""
    
    def __init__(self, analyzer: SignalModelAnalyzer, output_folder: str = "plots_cats/"):
        self.analyzer = analyzer
        self.plot_manager = PlotManager(output_folder)
        
        # Initialize specialized plotters
        self.response_plotter = ResponsePlotter(analyzer, self.plot_manager)
        self.param_plotter = ParametrizationPlotter(analyzer, self.plot_manager)
        self.model_plotter = ModelPlotter(analyzer, self.plot_manager)
    
    def plot_all_response_fits(self, use_reco_mass: bool = False, plot_residuals: bool = True):
        """Plot all response function fits"""
        self.response_plotter.plot_response_fits(use_reco_mass, plot_fit=True, plot_residuals=plot_residuals)
    
    def plot_all_parametrizations(self, vars_to_plot: Optional[List[str]] = None, gen: bool = False):
        """Plot parameter parametrizations"""
        if vars_to_plot is None:
            vars_to_plot = self.analyzer.param_manager.dcb_vars if not gen else self.analyzer.param_manager.bw_vars
        self.param_plotter.plot_parametrization(vars_to_plot, gen)
    
    def plot_all_sample_fits(self, plot_residuals: bool = True, gen: bool = False):
        """Plot all sample fits"""
        self.model_plotter.plot_sample_fits(plot_residuals, gen)
    
    def plot_parametric_models(self):
        """Plot parametric models for different masses"""
        self.model_plotter.plot_models_only()
    
    def copy_plots_to_eos(self, eos_folder: str):
        """Copy all plots to EOS directory"""
        categories = [category.name for category in self.analyzer.categories.values()]
        self.plot_manager.copy_to_eos(eos_folder, categories)
    
    def plot_full_analysis(self, use_reco_mass: bool = False, gen_analysis: bool = True):
        """Generate all plots for the analysis"""
        print("Generating all analysis plots...")
        
        # Response function plots
        self.plot_all_response_fits(use_reco_mass)
        
        # Parameter parametrization plots
        self.plot_all_parametrizations(gen=False)
        # if gen_analysis:
        #     self.plot_all_parametrizations(vars_to_plot=["mean_BW", "width_BW"], gen=True)
        
        # Sample fit plots
        self.plot_all_sample_fits(gen=False)
        # if gen_analysis:
        #     self.plot_all_sample_fits(gen=True)
        
        # Parametric model plots
        self.plot_parametric_models()
        
        print("All plots generated successfully!")
    
    def plot_parametrization_comparison(self, vars_to_plot: Optional[List[str]] = None, gen: bool = False):
        """Plot parametrization comparison across all categories (fits only)"""
        if vars_to_plot is None:
            vars_to_plot = self.analyzer.param_manager.dcb_vars if not gen else self.analyzer.param_manager.bw_vars
        
        # Filter out JPsi samples for parameter fit visualization
        plot_samples = {name: sample for name, sample in self.analyzer.samples.items() 
                       if "JPsiToEE" not in name}
        
        self.param_plotter._plot_parametrization_comparison(plot_samples, self.analyzer.categories, 
                                                           vars_to_plot, gen)
