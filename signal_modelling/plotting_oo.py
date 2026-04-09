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
from concurrent.futures import ThreadPoolExecutor, as_completed

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
        
        # Ensure base_path is a Path object
        if not isinstance(base_path, Path):
            base_path = Path(base_path)

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


class ParametrizationPlotter:
    """Handles plotting of parameter fits vs mass"""
    
    def __init__(self, analyzer: SignalModelAnalyzer, plot_manager: PlotManager):
        self.analyzer = analyzer
        self.plot_manager = plot_manager
        self.workspace = analyzer.workspace_manager.workspace
    
    def plot_parametrization(self, vars_to_plot: List[str], gen: bool = False):
        """Plot parameter values vs nominal mass"""
        print(f"Plotting parametrization {'(GEN)' if gen else ''}...")
        
        # # Filter out JPsi samples for parameter fit visualization
        # plot_samples = {name: sample for name, sample in self.analyzer.samples.items() 
        #                if "JPsiToEE" not in name and "Upsilon" not in name}
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
        
        # Collect data points (now returns nominal, var_up, var_down)
        data_points, var_up_points, var_down_points = self._collect_parametrization_data(samples, category, vars_to_plot, gen)
        jpsi_points = self._collect_jpsi_data(category, vars_to_plot, gen)
        upsilon_points = self._collect_upsilon_data(category, vars_to_plot, gen)
        
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
            self._plot_single_parameter(ax, var, data_points[var], jpsi_points[var], upsilon_points[var],
                                      category, category_label, gen, var_up_points[var], var_down_points[var])
        
        # Remove unused subplots
        for i in range(len(vars_to_plot), len(axs.flatten())):
            axs.flatten()[i].remove()
        
        plt.tight_layout()
        
        # Save figure
        tag = "_GEN" if gen else ""
        outname = f"parametrization{tag}{category.label}"
        fig.savefig(str(self.plot_manager.output_folder / f"{outname}.png"))
        fig.savefig(str(self.plot_manager.output_folder / f"{outname}.pdf"))
        print(f"Saved parametrization plot: {self.plot_manager.output_folder / f'{outname}.png'}")
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
        print(f"Saved parametrization comparison plot: {self.plot_manager.output_folder / f'{outname}.png'}")
        plt.close(fig)
    
    def _collect_parametrization_data(self, samples: Dict[str, SampleConfig], 
                                    category: CategoryConfig, vars_to_plot: List[str], 
                                    gen: bool, min_entries: int = 10) -> Tuple[Dict[str, Dict], Dict[str, Dict], Dict[str, Dict]]:
        """Collect parametrization data points including systematic variations
        
        Returns:
            Tuple of (nominal_data, variation_up_data, variation_down_data)
            where variation data is organized by variation name: {var: {variation_name: {'x': [], 'y': [], 'y_err': []}}}
        """

        data_points = {var: {'x': [], 'y': [], 'y_err': []} for var in vars_to_plot}
        varnames = [f"{var}_GEN_fit" if gen else f"response_{var}" for var in vars_to_plot]
        
        # Only initialize variation dictionaries if systematics are enabled
        # Now organized by variation name
        if self.analyzer.use_syst:
            var_up_points = {var: {variation: {'x': [], 'y': [], 'y_err': []} 
                                  for variation in self.analyzer.dataset_loader.variations} 
                            for var in vars_to_plot}
            var_down_points = {var: {variation: {'x': [], 'y': [], 'y_err': []} 
                                    for variation in self.analyzer.dataset_loader.variations} 
                              for var in vars_to_plot}
        else:
            var_up_points = {}
            var_down_points = {}
            
        for name, sample in samples.items():
            # FIXME: not very elegant, could invoke get_entry_counts_for_category somewhere higher up 
            entry_counts = self.analyzer.dataset_loader.get_dataset_entry_count(f"response_data_{sample.label}{category.label}_{self.analyzer.era}")
            if entry_counts < min_entries:
                print(f"Skipping {name} in category {category.label} due to insufficient entries: {entry_counts}")
                continue
            
            for var, varname in zip(vars_to_plot, varnames):
                # Nominal values (all variables have era suffix)
                workspace_var = self.workspace.var(f"{varname}_{name}{category.label}_{self.analyzer.era}")
                if workspace_var:
                    data_points[var]['x'].append(sample.nominal_mass)
                    data_points[var]['y'].append(workspace_var.getVal())
                    data_points[var]['y_err'].append(workspace_var.getError())
                
                # Systematic variations (only if enabled)
                if self.analyzer.use_syst:
                    for variation in self.analyzer.dataset_loader.variations:
                        # All variation variables have era suffix
                        # Up variation
                        var_up = self.workspace.var(f"{varname}_{name}{category.label}_{variation}_up_{self.analyzer.era}")
                        if var_up:
                            var_up_points[var][variation]['x'].append(sample.nominal_mass)
                            var_up_points[var][variation]['y'].append(var_up.getVal())
                            var_up_points[var][variation]['y_err'].append(var_up.getError())
                        
                        # Down variation
                        var_down = self.workspace.var(f"{varname}_{name}{category.label}_{variation}_down_{self.analyzer.era}")
                        if var_down:
                            var_down_points[var][variation]['x'].append(sample.nominal_mass)
                            var_down_points[var][variation]['y'].append(var_down.getVal())
                            var_down_points[var][variation]['y_err'].append(var_down.getError())
        
        return data_points, var_up_points, var_down_points
    
    def _collect_jpsi_data(self, category: CategoryConfig, vars_to_plot: List[str], 
                          gen: bool) -> Dict[str, Dict]:
        """Collect JPsi data points"""
        
        jpsi_points = {var: {'x': [3.097], 'y': [], 'y_err': []} for var in vars_to_plot}
        
        varnames = [f"{var}_GEN_fit" if gen else f"response_{var}" for var in vars_to_plot]
        
        for var, varname in zip(vars_to_plot, varnames):
            workspace_var = self.workspace.var(f"{varname}_JPsiToEE{category.label}_{self.analyzer.era}")
            if workspace_var:
                jpsi_points[var]['y'].append(workspace_var.getVal())
                jpsi_points[var]['y_err'].append(workspace_var.getError())
            else:
                jpsi_points[var]['y'].append(0)
                jpsi_points[var]['y_err'].append(0)
        
        return jpsi_points

    def _collect_upsilon_data(self, category: CategoryConfig, vars_to_plot: List[str], 
                          gen: bool) -> Dict[str, Dict]:
        """Collect Upsilon data points"""
        
        upsilon_points = {var: {'x': [9.460], 'y': [], 'y_err': []} for var in vars_to_plot}
        
        varnames = [f"{var}_GEN_fit" if gen else f"response_{var}" for var in vars_to_plot]
        
        for var, varname in zip(vars_to_plot, varnames):
            workspace_var = self.workspace.var(f"{varname}_UpsilonToEE{category.label}_{self.analyzer.era}")
            if workspace_var:
                upsilon_points[var]['y'].append(workspace_var.getVal())
                upsilon_points[var]['y_err'].append(workspace_var.getError())
            else:
                upsilon_points[var]['y'].append(0)
                upsilon_points[var]['y_err'].append(0)
        
        return upsilon_points
    
    def _plot_single_parameter(self, ax, var: str, data_points: Dict, jpsi_points: Dict,
                               upsilon_points: Dict, category: CategoryConfig, category_label: str, gen: bool,
                               var_up_points: Optional[Dict] = None, var_down_points: Optional[Dict] = None):
        """Plot a single parameter vs mass with data points and fits
        
        Args:
            var_up_points: Systematic variation up points (dict by variation name)
            var_down_points: Systematic variation down points (dict by variation name)
        """
        # Styling for nominal data points
        plot_args = {
            "linestyle": "None",
            "marker": "o", 
            "markersize": 12,
            "elinewidth": 2,
            "capsize": 8,
        }
        
        # Base styling for variation points
        var_plot_args_base = {
            "linestyle": "None",
            "markerfacecolor": "none",
            "markersize": 10,
            "elinewidth": 1.5,
            "capsize": 6,
            "alpha": 0.7,
        }
        
        # Setup basic plot styling
        self._setup_parameter_plot_style(ax, var, gen, comparison_mode=False)
        
        # Update title to include category
        model_type = "Relativistic Breit-Wigner" if gen else "Double-sided Crystal Ball"
        title = f"{model_type} {var}, cat. {category_label}"
        ax.set_title(title, fontsize=30, pad=40)
        
        # Plot fit curve and uncertainty band (only uses nominal points)
        self._plot_parameter_fit_only(ax, var, category, "red", "Fit", gen, show_fit_params=True)
        
        # Plot variation fits as filled bands (only if systematics are enabled)
        if self.analyzer.use_syst and var_up_points:
            for variation_name in self.analyzer.dataset_loader.variations:
                if variation_name in var_up_points:
                    # Plot filled band between up and down variations
                    self._plot_parameter_variation_band(ax, var, category, variation_name, gen)
        
        # Plot nominal data points
        has_variations = var_up_points and any(len(v.get('x', [])) > 0 for v in var_up_points.values())
        label = "Nominal" if has_variations else None  # Only label if variations exist
        ax.errorbar(data_points['x'], data_points['y'], data_points['y_err'], **plot_args, label=label)
        
        # Plot systematic variations (only if systematics are enabled)
        # Each variation gets its own color and marker style
        if var in self.analyzer.param_manager.nuisanced_vars:
            if var_up_points:
                color_idx = 3  # Start from C3
                for variation_name, points in var_up_points.items():
                    if len(points.get('x', [])) > 0:
                        # FIXME: temporarily hiding alphaR variation at M10 
                        #        (fit visibly bad + uncertainty not considered anyway)
                        if var == "alphaR" and variation_name == "electronScaleVariation":
                            points['x'] = points['x'][:-1]
                            points['y'] = points['y'][:-1]
                            points['y_err'] = points['y_err'][:-1]
                        var_plot_args = var_plot_args_base.copy()
                        var_plot_args["marker"] = "^"  # Triangle up
                        color = f"C{color_idx}"
                        ax.errorbar(points['x'], points['y'], points['y_err'],
                                **var_plot_args, color=color, markeredgecolor=color, 
                                label=f"{variation_name} ↑")
                        color_idx += 1
            
            if var_down_points:
                color_idx = 3  # Reset color index to match up variations
                for variation_name, points in var_down_points.items():
                    if len(points.get('x', [])) > 0:
                        if var == "alphaR" and variation_name == "electronScaleVariation":
                            points['x'] = points['x'][:-1]
                            points['y'] = points['y'][:-1]
                            points['y_err'] = points['y_err'][:-1]
                        var_plot_args = var_plot_args_base.copy()
                        var_plot_args["marker"] = "v"  # Triangle down
                        color = f"C{color_idx}"
                        ax.errorbar(points['x'], points['y'], points['y_err'],
                                **var_plot_args, color=color, markeredgecolor=color, 
                                label=f"{variation_name} ↓")
                        color_idx += 1
            
        # Plot JPsi point
        if jpsi_points['y'][0] != 0:
            ax.errorbar(jpsi_points['x'], jpsi_points['y'], jpsi_points['y_err'], 
                       **plot_args, label=r"$J/\psi \to ee$", color="C1")

        # Plot Upsilon point
        if upsilon_points['y'][0] != 0:
            ax.errorbar(upsilon_points['x'], upsilon_points['y'], upsilon_points['y_err'], 
                       **plot_args, label=r"$\Upsilon (1S) \to ee$", color="C2")

        ax.legend(fontsize=15)
    
    def _setup_parameter_plot_style(self, ax, var: str, gen: bool, comparison_mode: bool = False):
        """Setup basic styling for parameter plots"""
        # Labels
        ylabels = {
            "mean": r"$\mu$ [GeV]", "mean_BW": r"$\mu$ [GeV]",
            "sigma": r"$\sigma$ [GeV]", "width_BW": r"$\Gamma$ [GeV]",
            "alphaL": r"$\alpha_L$", "nL": r"$n_L$",
            "alphaR": r"$\alpha_R$", "nR": r"$n_R$",
        }
        
        hep.cms.label(ax=ax, label="Preliminary", data=False, com=13.6, year=self.analyzer.era, fontsize=20)
        ax.set_xlabel("Nominal mass [GeV]")
        ax.set_ylabel(ylabels.get(var, var))
        
        if comparison_mode:
            model_type = "Relativistic Breit-Wigner" if gen else "Double-sided Crystal Ball"
            title = f"{model_type} {var} comparison vs cat."
        else:
            title = f"Relativistic Breit-Wigner {var}" if gen else f"Double-sided Crystal Ball {var}"
        
        ax.set_title(title, fontsize=30, pad=40)
    
    def _plot_parameter_fit_only(self, ax, var: str, category: CategoryConfig, color: str, 
                                category_label: str, gen: bool, show_fit_params: bool = False,
                                variation_tag: str = "", linestyle: str = "--", linewidth: float = 2.0):
        """Plot only the fit curve and uncertainty band for a parameter
        
        Args:
            variation_tag: Variation tag like "_electronSmearing_up" or empty for nominal
            linestyle: Line style for the fit curve
            linewidth: Line width for the fit curve
        """
        # Plot fit curves or constant lines
        if var in self.analyzer.parametrized_vars:
            # Get fit parameters (with variation tag if specified)
            par0_obj = self.workspace.obj(f"{var}{category.label}_fit_par0{variation_tag}_{self.analyzer.era}")
            par1_obj = self.workspace.obj(f"{var}{category.label}_fit_par1{variation_tag}_{self.analyzer.era}")

            # also retrieve errors and covariance
            par0_err_obj = self.workspace.obj(f"{var}{category.label}_fit_par0_err{variation_tag}_{self.analyzer.era}")
            par1_err_obj = self.workspace.obj(f"{var}{category.label}_fit_par1_err{variation_tag}_{self.analyzer.era}")
            par01_cov_obj = self.workspace.obj(f"{var}{category.label}_fit_par01_cov{variation_tag}_{self.analyzer.era}")
            
            if par0_obj and par1_obj:
                x_fit = np.linspace(0, 10.5, 100)
                y_fit = x_fit * par1_obj.getVal() + par0_obj.getVal()
                
                # Create label
                if show_fit_params:
                    fit_label = f"Fit:\nm = {par1_obj.getVal():.3g} ± {par0_err_obj.getVal():.3g}"
                    fit_label += f"\nq = {par0_obj.getVal():.3g} ± {par1_err_obj.getVal():.3g}"
                    fit_label += f"\ncorr(m,q) = {par01_cov_obj.getVal()/par0_err_obj.getVal()/par1_err_obj.getVal():.3g}"
                else:
                    fit_label = category_label
                
                # Plot the fit line
                ax.plot(x_fit, y_fit, color=color, linestyle=linestyle, linewidth=linewidth, 
                       label=fit_label)
                
                ### Uncertainty band
                # y_plus = y_fit + par0_obj.getError() + par1_obj.getError() * x_fit
                # y_minus = y_fit - par0_obj.getError() - par1_obj.getError() * x_fit
                # Uncertainty bands (alternative)
                error = np.sqrt(par0_err_obj.getVal()**2 + (x_fit * par1_err_obj.getVal())**2 + 2 * x_fit * par01_cov_obj.getVal())
                y_plus = y_fit + error
                y_minus = y_fit - error
                ax.fill_between(x_fit, y_plus, y_minus, color=color, alpha=0.15)
        else:
            # Constant parameter
            tag = "_GEN" if gen else ""
            const_obj = self.workspace.obj(f"{var}{category.label}{tag}_const_{self.analyzer.era}")
            if const_obj:
                const_val = const_obj.getVal()
                const_err = const_obj.getError()
                
                # Create label
                if show_fit_params:
                    label = f"Const. value: {const_val:.3g}"
                else:
                    label = category_label
                
                ax.hlines(const_val, 0, 10.5, color=color, linestyle="--", linewidth=2,
                         label=label)
                ax.fill_between([0, 10.5], const_val - const_err, const_val + const_err, 
                               color=color, alpha=0.15)
    
    def _plot_parameter_variation_band(self, ax, var: str, category: CategoryConfig, 
                                      variation_name: str, gen: bool):
        """Plot filled band between up and down systematic variations
        
        Args:
            variation_name: Name of the systematic variation (e.g., 'electronSmearing')
        """
        if var in self.analyzer.parametrized_vars:
            # Get fit parameters for up variation
            par0_up = self.workspace.obj(f"{var}{category.label}_fit_par0_{variation_name}_up_{self.analyzer.era}")
            par1_up = self.workspace.obj(f"{var}{category.label}_fit_par1_{variation_name}_up_{self.analyzer.era}")
            
            # Get fit parameters for down variation
            par0_down = self.workspace.obj(f"{var}{category.label}_fit_par0_{variation_name}_down_{self.analyzer.era}")
            par1_down = self.workspace.obj(f"{var}{category.label}_fit_par1_{variation_name}_down_{self.analyzer.era}")
            
            if par0_up and par1_up and par0_down and par1_down:
                x_fit = np.linspace(0, 10.5, 100)
                y_up = x_fit * par1_up.getVal() + par0_up.getVal()
                y_down = x_fit * par1_down.getVal() + par0_down.getVal()
                
                # Plot filled band between up and down
                ax.fill_between(x_fit, y_up, y_down, color='blue', alpha=0.15, 
                               label=f"{variation_name} syst.")
        else:
            # Constant parameter
            tag = "_GEN" if gen else ""
            const_up = self.workspace.obj(f"{var}{category.label}{tag}_const_{variation_name}_up_{self.analyzer.era}")
            const_down = self.workspace.obj(f"{var}{category.label}{tag}_const_{variation_name}_down_{self.analyzer.era}")
            
            if const_up and const_down:
                val_up = const_up.getVal()
                val_down = const_down.getVal()
                
                # Plot filled band for constant
                ax.fill_between([0, 12], val_down, val_up, color='blue', alpha=0.15,
                               label=f"{variation_name} syst.")


class ModelPlotter:
    """Unified plotter for both response functions and signal models"""
    
    def __init__(self, analyzer: SignalModelAnalyzer, plot_manager: PlotManager, plotter_parent=None):
        self.analyzer = analyzer
        self.plot_manager = plot_manager
        self.workspace = analyzer.workspace_manager.workspace
        self.plotter_parent = plotter_parent  # Reference to SignalModelPlotter for logging
    
    def plot_response_fits(self, use_reco_mass: bool = False, plot_fit: bool = True, 
                          plot_residuals: bool = True, max_workers: int = 1):
        """Plot response function fits for all samples and categories
        
        Args:
            use_reco_mass: Whether to use reconstructed mass
            plot_fit: Whether to plot the fit
            plot_residuals: Whether to plot residuals
            max_workers: Maximum number of parallel workers
        """
        print("Plotting response function fits...")
        
        # Create output directories
        self.plot_manager.create_output_directories([category.name for category in self.analyzer.categories.values()])
        
        # Create list of all plot tasks
        plot_tasks = []
        for name, sample in self.analyzer.samples.items():
            for category_label, category in self.analyzer.categories.items():
                variation_label = ""
                plot_tasks.append((sample, category, category_label, variation_label))
                for variation in set(sum(self.analyzer.nuisanced_vars.values(), [])):
                    for direction in ["up", "down"]:
                        variation_label = f"_{variation}_{direction}"
                        plot_tasks.append((sample, category, category_label, variation_label))
        
        # Execute plots in parallel
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self._plot_single_fit, sample, category, category_label,
                              variation_label = variation_label,
                              plot_type="response", use_reco_mass=use_reco_mass,
                              plot_fit=plot_fit, plot_residuals=plot_residuals): 
                f"{sample.label}_{category.name}"
                for sample, category, category_label, variation_label in plot_tasks
            }
            
            for future in as_completed(futures):
                task_name = futures[future]
                try:
                    future.result()
                except Exception as e:
                    print(f"Error plotting {task_name}: {e}")
    
    def plot_sample_fits(self, plot_residuals: bool = True, gen: bool = False, max_workers: int = 4):
        """Plot model fits to sample data
        
        Args:
            plot_residuals: Whether to plot residuals
            gen: Whether to use GEN level
            max_workers: Maximum number of parallel workers
        """
        print(f"Plotting sample fits {'(GEN)' if gen else ''}...")
        
        # Create list of all plot tasks
        plot_tasks = []
        for name, sample in self.analyzer.samples.items():
            for category_label, category in self.analyzer.categories.items():
                plot_tasks.append((sample, category, category_label))
        
        # Execute plots in parallel
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self._plot_single_fit, sample, category, category_label,
                              plot_type="signal", gen=gen, plot_residuals=plot_residuals,
                              plot_uncertainty_bands=True):
                f"{sample.label}_{category.name}"
                for sample, category, category_label in plot_tasks
            }
            
            for future in as_completed(futures):
                task_name = futures[future]
                try:
                    future.result()
                except Exception as e:
                    print(f"Error plotting {task_name}: {e}")
    
    def _plot_single_fit(self, sample: SampleConfig, category: CategoryConfig, 
                        category_label: str, plot_type: str = "signal", gen: bool = False,
                        variation_label: str = "",
                        use_reco_mass: bool = False,
                        plot_fit: bool = True,
                        plot_residuals: bool = True,
                        plot_uncertainty_bands: bool = False):
        """Unified plotting method for both response and signal fits"""
        
        # Configure based on plot type
        if plot_type == "response":
            data_name = f"response_data_{sample.label}{category.label}{variation_label}_{self.analyzer.era}"
            model_name = f"response_function_{sample.label}{category.label}{variation_label}_{self.analyzer.era}"
            obs_name = "mass" if use_reco_mass else "reduced_mass"
            obs_title = "Mass" if use_reco_mass else "Reduced mass"
            obs_var = self.workspace.var(f"{obs_name}_{sample.label}_{self.analyzer.era}")
            output_subdir = "response"
            file_prefix = "response_"
            canvas_name = f"c{sample.label}{category.label}"
            frame_title = f"{obs_title} distribution of {sample.label} sample, category {category_label}, {variation_label}"
            x_axis_label = r"m(ee) [GeV]" if use_reco_mass else r"(m(ee) - mX)/mX"
            data_legend_name = f"data"
            model_legend_name = f"model"
            color = ROOT.kBlue
            log_type = "response_fit"
        else:  # signal model
            tag = "_GEN" if gen else ""
            model_tag = "_GEN" if gen else "_param"
            data_name = f"data{tag}_{sample.label}{category.label}_{self.analyzer.era}"
            model_name = f"model{model_tag}_{sample.label}{category.label}_{self.analyzer.era}"
            # Observable variable (mass) does NOT include era suffix - it's shared
            obs_var = self.workspace.var(f"mass{tag}_{sample.label}")
            output_subdir = "model_test"
            file_prefix = "GEN_test_BW_" if gen else "signal_model_"
            canvas_name = f"c_{sample.label}{category.label}"
            frame_title = f"{sample.label} sample, cat. {category_label}"
            x_axis_label = f"M(ee){tag} [GeV]"
            data_legend_name = f"data{tag}"
            model_legend_name = f"model{model_tag}"
            color = self.plot_manager.kBlue if gen else self.plot_manager.kYellow
            log_type = "signal_model"
        
        # Get data
        data = self.workspace.data(data_name) if plot_type == "response" else self.workspace.obj(data_name)
        if not data:
            print(f"Warning: No data found for {data_name}")
            return
        
        # Create canvas
        c = ROOT.TCanvas(canvas_name, canvas_name, 900, 900)
        
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
        frame = obs_var.frame(sample.mass_range[1], sample.mass_range[2])
        frame.SetTitle(frame_title)
        
        # Plot invisible data first (for residuals) if needed
        if plot_residuals and plot_fit:
            data.plotOn(frame, ROOT.RooFit.Name(data_legend_name), ROOT.RooFit.Invisible(), 
                       ROOT.RooFit.DataError(ROOT.RooAbsData.SumW2))
        
        # Plot fit if requested
        model = None
        nuisances = {}

        if plot_fit:
            model = self.workspace.pdf(model_name) if plot_type == "response" else self.workspace.obj(model_name)
            if model:
                # Plot variations by varying nuisance parameters
                if plot_uncertainty_bands and plot_type == "signal" and self.analyzer.use_syst:
                    darker_color = ROOT.TColor.GetColor("#CC5500")  # Dark orange
                    
                    # Get all nuisance parameters from model parameters
                    model_params = model.getParameters(ROOT.RooArgSet())
                    
                    # Find nuisance parameters (those ending with "_nuisance")
                    for param in model_params:
                        param_name = param.GetName()
                        if "nuisance" in param_name:
                            variation = param_name.split("_")[-1]
                            # if it's an era, skip that, it's a nuisance to be ignored
                            if "2022" in variation or "2023" in variation:
                                continue
                            nuisances[variation] = param

                    print(f"Found nuisances for {model_name}: {list(nuisances.keys())}")
                    
                    # Plot variations for each nuisance found
                    for var_base, nuisance in nuisances.items():
                        # Plot up variation (dashed line, thicker)
                        nuisance.setVal(1.0)
                        model.plotOn(frame, ROOT.RooFit.Name(f"{model_legend_name}_{var_base}_up"),
                                ROOT.RooFit.LineColor(darker_color), ROOT.RooFit.LineWidth(2))
                        
                        # Plot down variation (dotted line, thicker)
                        nuisance.setVal(-1.0)
                        model.plotOn(frame, ROOT.RooFit.Name(f"{model_legend_name}_{var_base}_down"),
                                    ROOT.RooFit.LineColor(darker_color), ROOT.RooFit.LineWidth(3),
                                    ROOT.RooFit.LineStyle(ROOT.kDashed))
                        
                        # Reset nuisance to nominal
                        nuisance.setVal(0.0)
                
                # plot nominal model on top (solid line, standard width)
                model.plotOn(frame, ROOT.RooFit.Name(model_legend_name), 
                            ROOT.RooFit.LineWidth(2), ROOT.RooFit.LineColor(color))

                # # when using envelope: plot alternative model
                # if self.analyzer.envelope and plot_type == "signal":
                #     # pdf_index = self.workspace.obj(f"signal_model_index_{self.analyzer.era}")
                #     # pdf_index.setIndex(1)  # Switch to alternative model
                #     # model.Print("v")
                #     params = model.getParameters(data)
                #     # print(f"DBEUG: parameters for {model_name}:", params.Print("v"))
                #     index = params[f"signal_model_index_{self.analyzer.era}"]
                #     index.setIndex(1)
                #     #retrieve index parm
                #     model.plotOn(frame, ROOT.RooFit.Name(f"{model_legend_name}_alt"),
                #                 ROOT.RooFit.LineWidth(2), ROOT.RooFit.LineColor(ROOT.kRed), ROOT.RooFit.Normalization(data.sumEntries() * 0.7, ROOT.RooAbsReal.NumEvent))
                #     # reset index
                #     index.setIndex(0)
                
                # # TEMPORARY: also print fit parameters on canvas
                # model.paramOn(frame, ROOT.RooFit.Layout(0.1, 0.5, 0.5), ROOT.RooFit.Format("NEU", ROOT.RooFit.AutoPrecision(2)),
                #               ROOT.RooFit.ShowConstants(True), ROOT.RooFit.Name("model_params"))

            else:
                print(f"WARNING: No model found for {model_name}")
        

        # Plot residuals if requested
        if plot_residuals and plot_fit and model:
            pad2.cd()
            pad2.SetGrid()
            
            residuals = frame.residHist(data_legend_name, model_legend_name, True, True)
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
            residuals.GetXaxis().SetTitle(x_axis_label)
            residuals.SetTitle("")
            residuals.GetXaxis().SetRangeUser(frame.GetXaxis().GetXmin(), frame.GetXaxis().GetXmax())
            residuals.SetMinimum(-5)
            residuals.SetMaximum(5)
            residuals.GetYaxis().SetNdivisions(505)
            residuals.Draw("AP")
            
            pad1.cd()
        
        # Plot actual data
        if not (plot_residuals and plot_fit):
            data.plotOn(frame, ROOT.RooFit.Name(data_legend_name),
                        ROOT.RooFit.DataError(ROOT.RooAbsData.SumW2))
        else:
            data.plotOn(frame, ROOT.RooFit.Name(data_legend_name), ROOT.RooFit.MarkerSize(0.8),
                       ROOT.RooFit.DataError(ROOT.RooAbsData.SumW2))
        
        # Set axis labels and draw
        frame.GetXaxis().SetTitle(x_axis_label)
        frame.Draw()

        # Plot legend
        leg = ROOT.TLegend(0.15, 0.7, 0.16 if plot_type == "response" else 0.3, 0.89)
        leg.SetBorderSize(0)
        leg.SetTextSize(0.03)
        leg.AddEntry(data_legend_name, "Data", "P")
        
        if plot_fit and model:
            # Compute chi2 using the analyzer's fit manager  
            chi2_result = self.analyzer.fit_manager.compute_chi2(model, data, 1 if plot_type == "signal" else None)
            if chi2_result is not None:
                chi2_ndf, ndof = chi2_result
                leg.AddEntry(model_legend_name, f"Fit, #chi^2/ndf = {chi2_ndf:.2f} (ndf = {ndof})", "L")
                # Log Chi2 value
                if self.plotter_parent:
                    self.plotter_parent.log_plotting_chi2(sample.label, category.name, chi2_ndf, plot_type=log_type)
            else:
                # Fallback to original method if compute_chi2 fails
                chi2_ndf = frame.chiSquare(model_legend_name, data_legend_name)
                leg.AddEntry(model_legend_name, f"Fit, #chi^2/ndf = {chi2_ndf:.2f}", "L")
                # Log Chi2 value
                if self.plotter_parent:
                    self.plotter_parent.log_plotting_chi2(sample.label, category.name, chi2_ndf, plot_type=log_type)
            
            # Add variation models to legend if they were plotted
            if plot_uncertainty_bands and plot_type == "signal" and self.analyzer.use_syst:
                # Get nuisances from model to know what was plotted
                model_params = model.getParameters(ROOT.RooArgSet())
                for variation in nuisances.keys():
                    curve_up = frame.getCurve(f"{model_legend_name}_{variation}_up")
                    curve_down = frame.getCurve(f"{model_legend_name}_{variation}_down")
                    if curve_up:
                        leg.AddEntry(curve_up, f"{variation} #uparrow", "L")
                    if curve_down:
                        leg.AddEntry(curve_down, f"{variation} #downarrow", "L")
            
            # # add alternative model to legend if envelope is used
            # if self.analyzer.envelope:
            #     alt_curve = frame.getCurve(f"{model_legend_name}_alt")
            #     if alt_curve:
            #         leg.AddEntry(alt_curve, f"{model_legend_name} (gaussian alt.)", "L")
        
        leg.Draw()
        
        # Save plots
        output_dir = self.plot_manager.output_folder / output_subdir
        for ext in ["png", "pdf"]:
            c.SaveAs(str(output_dir / category.name / f"{file_prefix}{sample.label}{category.label}{variation_label}.{ext}"))
            print(f"Saved plot: {output_dir / category.name / f'{file_prefix}{sample.label}{category.label}{variation_label}.{ext}'}")
        
        # Log scale version
        if plot_residuals and plot_fit:
            pad1.SetLogy()
        else:
            c.SetLogy()
        frame.SetMinimum(1e-1)
        for ext in ["png", "pdf"]:
            c.SaveAs(str(output_dir / category.name / f"{file_prefix}{sample.label}{category.label}{variation_label}_log.{ext}"))
            print(f"Saved log plot: {output_dir / category.name / f'{file_prefix}{sample.label}{category.label}{variation_label}_log.{ext}'}")
        
        # Clean up ROOT objects
        c.Close()
    
    def plot_models_only(self):
        """Plot parametric models for different mass points"""
        print("Plotting parametric models...")
        
        for category_label, category in self.analyzer.categories.items():
            self._plot_models_for_category(category, category_label)
    
    def _plot_models_for_category(self, category: CategoryConfig, category_label: str):
        """Plot models for a single category"""

        # Find all test models in workspace (including era suffix)
        all_objects = [key.GetName() for key in self.workspace.allPdfs() 
                      if f"model_test_M" in key.GetName() and category.label in key.GetName()
                      and f"_{self.analyzer.era}" in key.GetName()
                      and ("up" not in key.GetName()) and ("down" not in key.GetName())]
        all_objects = all_objects[::3] #take every third mass point
        
        # For the inclusive category:
        if category.label == "":
            # exclude all models that have a category label
            all_objects = [model for model in all_objects if "_cat_" not in model]
        
        models = {model.split("_M")[1].split("_")[0]: model for model in all_objects}
        
        if not models:
            print(f"No test models found for category {category_label}")
            return

        def draw_models_and_save(index_label: str = "", envelope_index: Optional[int] = None):
            if envelope_index is not None:
                index_obj = self.workspace.cat(f"signal_model_index_{self.analyzer.era}")
                if index_obj:
                    index_obj.setIndex(envelope_index)

            # Create canvas and frame
            c = ROOT.TCanvas(f"c{index_label}", f"c{index_label}", 1200, 900)
            mass_var = self.workspace.var("mass")
            title_suffix = f" (gaussian alt signal)" if index_label else ""
            frame = mass_var.frame(
                ROOT.RooFit.Title(f"Parametric model for several mass points, cat. {category_label}{title_suffix}")
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
            plot_suffix = f"_gaussian_alt" if index_label else ""
            outname = f"signal_model_testing{category.label}{plot_suffix}"
            for ext in ["png", "pdf"]:
                c.SaveAs(str(self.plot_manager.output_folder / "model_test" / category.name / f"{outname}.{ext}"))
                print(f"Saved model comparison plot: {self.plot_manager.output_folder / 'model_test' / category.name / f'{outname}.{ext}'}")
            
            # Log scale version
            c.SetLogy()
            for ext in ["png", "pdf"]:
                c.SaveAs(str(self.plot_manager.output_folder / "model_test" / category.name / f"{outname}_log.{ext}"))
                print(f"Saved log model comparison plot: {self.plot_manager.output_folder / 'model_test' / category.name / f'{outname}_log.{ext}'}")
            
            # Clean up ROOT objects
            c.Close()

        draw_models_and_save()

        if self.analyzer.envelope:
            draw_models_and_save("_envelope_gaussian", envelope_index=1)

class SignalModelPlotter:
    """Main plotting interface for signal model analysis"""
    
    def __init__(self, analyzer: SignalModelAnalyzer, output_folder: str = "plots_cats/"):
        self.analyzer = analyzer
        self.plot_manager = PlotManager(output_folder)
        
        # Initialize specialized plotters
        self.model_plotter = ModelPlotter(analyzer, self.plot_manager, self)
        self.param_plotter = ParametrizationPlotter(analyzer, self.plot_manager)
    
    def log_plotting_chi2(self, sample_name: str, category_name: str, chi2: float, plot_type: str = "model"):
        """Log Chi2 value computed during plotting"""
        logger = self.analyzer.get_logger()
        logger.log_info(f"PLOTTING CHI2 - {plot_type.upper()} - Sample: {sample_name}, Category: {category_name}: {chi2:.4f}")
    
    def plot_all_response_fits(self, use_reco_mass: bool = False, plot_residuals: bool = True, max_workers: int = 1):
        """Plot all response function fits
        
        Args:
            use_reco_mass: Whether to use reconstructed mass
            plot_residuals: Whether to plot residuals
            max_workers: Maximum number of parallel workers
        """
        self.model_plotter.plot_response_fits(use_reco_mass, plot_fit=True, 
                                             plot_residuals=plot_residuals, max_workers=max_workers)
    
    def plot_all_parametrizations(self, vars_to_plot: Optional[List[str]] = None, gen: bool = False):
        """Plot parameter parametrizations"""
        if vars_to_plot is None:
            vars_to_plot = self.analyzer.param_manager.dcb_vars if not gen else self.analyzer.param_manager.bw_vars
        self.param_plotter.plot_parametrization(vars_to_plot, gen)
    
    def plot_all_sample_fits(self, plot_residuals: bool = True, gen: bool = False, max_workers: int = 4):
        """Plot all sample fits
        
        Args:
            plot_residuals: Whether to plot residuals
            gen: Whether to use GEN level
            max_workers: Maximum number of parallel workers
        """
        self.model_plotter.plot_sample_fits(plot_residuals, gen, max_workers)
    
    def plot_parametric_models(self):
        """Plot parametric models for different masses"""
        self.model_plotter.plot_models_only()
    
    def copy_plots_to_eos(self, eos_folder: str):
        """Copy all plots to EOS directory"""
        categories = [category.name for category in self.analyzer.categories.values()]
        self.plot_manager.copy_to_eos(eos_folder, categories)
    
    def plot_full_analysis(self, use_reco_mass: bool = False, gen_analysis: bool = True, max_workers: int = 4):
        """Generate all plots for the analysis
        
        Args:
            use_reco_mass: Whether to use reconstructed mass
            gen_analysis: Whether to include GEN analysis
            max_workers: Maximum number of parallel workers for plotting
        """
        print("Generating all analysis plots...")
        
        # Response function plots
        self.plot_all_response_fits(use_reco_mass, max_workers=max_workers)
        
        # Parameter parametrization plots
        self.plot_all_parametrizations(gen=False)
        # if gen_analysis:
        #     self.plot_all_parametrizations(vars_to_plot=["mean_BW", "width_BW"], gen=True)
        
        # Sample fit plots
        self.plot_all_sample_fits(gen=False, max_workers=max_workers)
        # if gen_analysis:
        #     self.plot_all_sample_fits(gen=True)
        
        # Parametric model plots
        self.plot_parametric_models()
        
        print("All plots generated successfully!")
    
    def plot_parametrization_comparison(self, vars_to_plot: Optional[List[str]] = None, gen: bool = False):
        """Plot parametrization comparison across all categories (fits only)"""
        if vars_to_plot is None:
            vars_to_plot = self.analyzer.param_manager.dcb_vars if not gen else self.analyzer.param_manager.bw_vars
        
        # # Filter out JPsi samples for parameter fit visualization
        # plot_samples = {name: sample for name, sample in self.analyzer.samples.items() 
        #                if "JPsiToEE" not in name and "Upsilon" not in name}

        # Filter out JPsi samples for parameter fit visualization
        plot_samples = {name: sample for name, sample in self.analyzer.samples.items() 
                       if "JPsiToEE" not in name}

        self.param_plotter._plot_parametrization_comparison(plot_samples, self.analyzer.categories, 
                                                           vars_to_plot, gen)
