"""
Background plotting - Object-oriented approach

This module handles plotting of background fits and results.
"""
import ROOT
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from background_config import BackgroundModelConfig, FitRegion
from background_fitter import BackgroundFitter, FitResult
from shared_config import CategoryConfig


class BackgroundPlotter:
    """Main class for creating background fit plots"""
    
    def __init__(self, config: BackgroundModelConfig, fitter: BackgroundFitter, 
                 category: CategoryConfig = None):
        self.config = config
        self.fitter = fitter
        self.category = category
        
        # ROOT plotting setup
        ROOT.gROOT.SetBatch(True)
        ROOT.gStyle.SetOptStat(0)
        ROOT.gStyle.SetOptFit(1111)
        
        category_info = f" for category '{self.category.name}'" if self.category else ""
        print(f"Background plotter initialized{category_info}")
        
    def plot_fits(self, fit_region: FitRegion, results: Dict[str, FitResult], 
                 tag: str = "") -> List[str]:
        """Create plots for background fits"""
        print(f"Creating plots for {fit_region.display_name}...")
        
        created_plots = []
        
        # Create canvas
        canvas = ROOT.TCanvas("canvas", "canvas", 800, 600)
        canvas.SetGrid()
        
        # Create frame
        xmin, xmax = fit_region.range
        frame = self.fitter.mass_var.frame(xmin, xmax) #xmin-1, xmax+1 for debug margin
        frame.SetTitle("")
        
        # Setup drawing arguments
        draw_args = [
            ROOT.RooFit.Name("data_obs"),
            ROOT.RooFit.MarkerSize(1),
            ROOT.RooFit.MarkerColor(ROOT.kBlack),
            ROOT.RooFit.LineColor(ROOT.kBlack),
            ROOT.RooFit.DrawOption("HIST"),
        ]
        
        if not self.config.use_binned:
            draw_args.append(ROOT.RooFit.Binning(100))
            
        # Plot data
        self.fitter.data.plotOn(frame, *draw_args)

        # print(f"DEBUG: bin content:", flush=True)
        # for i in range(500):
        #     self.fitter.data.get(i)
        #     print(f"  bin {i}: {self.fitter.data.weight()}", flush=True)
        print(f"DEBUG: mass var range = ({xmin}, {xmax})", flush=True)
        
        # Plot combined background model
        plotted_functions = self._plot_combined_model(frame, fit_region)
        
        # if fit_region.name == "region1" or True:  # Main region with combined background #FIXME
        #     plotted_functions = self._plot_combined_model(frame, fit_region)
        #     # pass
        # else:  # Sideband regions with background only
        #     plotted_functions = self._plot_background_models(frame, fit_region)
            
        # Calculate chi2 values
        chi2_values = self._calculate_chi2_values(frame, results)
       
        # Add legend
        # legend = self._create_legend(fit_region, results, chi2_values)
        legend = ROOT.TLegend(0.2, 0.15, 0.9, 0.45)
        legend.SetBorderSize(0)
        legend.SetFillColor(0)
        legend.SetFillStyle(0)
        legend.SetTextSize(0.04)
        legend.AddEntry(frame.findObject("data_obs"), "Data", "p")
        for func in plotted_functions:
            label = func if func != "full_bkg_model" else f"#splitline{{Full Background Model}}{{(#chi^2 = {chi2_values['full_bkg_model']:.2f})}}"
            legend.AddEntry(frame.findObject(func), label, "l")
        legend.Draw()

        # Draw everything
        frame.Draw()
        # change minimum to 1
        frame.SetMinimum(20)
        frame.GetXaxis().SetTitle("m(ee) [GeV]")
        legend.Draw()
        
        # Add special markers if needed
        if self.config.fit_jpsi_first and fit_region.name == "region1":
            self._add_jpsi_region_markers(frame)
            
        # Save plots
        plot_files = self._save_plots(canvas, fit_region, tag)
        created_plots.extend(plot_files)
        
        canvas.Close()
        
        print(f"  Created {len(created_plots)} plots")
        return created_plots
        
    def _plot_combined_model(self, frame: ROOT.RooPlot, fit_region: FitRegion):
        """Plot combined background model and components"""
        if not self.fitter.combined_model:
            return
            
        # Plot total model
        self.fitter.combined_model.plotOn(frame, 
                                        ROOT.RooFit.LineColor(ROOT.kBlack), 
                                        ROOT.RooFit.Name("full_bkg_model"), 
                                        ROOT.RooFit.NormRange(fit_region.name))
        
        # Plot components with category-specific names
        category_label = self.category.label if self.category else ""
        
        colors = [ROOT.kRed, ROOT.kBlue, ROOT.kGreen, ROOT.kOrange]
        for idx, res_bkg in enumerate(self.fitter.resonant_backgrounds.keys()):
            component_name = f"{res_bkg}_resonant_bkg{category_label}"
            self.fitter.combined_model.plotOn(frame, 
                                            ROOT.RooFit.Components(component_name),
                                            ROOT.RooFit.LineColor(colors[idx % len(colors)]), 
                                            ROOT.RooFit.Name(f"{res_bkg}_bkg"),
                                            ROOT.RooFit.Range(fit_region.range[0], fit_region.range[1]),
                                            ROOT.RooFit.NormRange(fit_region.name))

        # if "jpsi" in self.fitter.resonant_backgrounds:
        #     jpsi_component_name = f"jpsi_resonant_bkg{category_label}"
        #     self.fitter.combined_model.plotOn(frame, 
        #                                     ROOT.RooFit.Components(jpsi_component_name),
        #                                     ROOT.RooFit.LineColor(ROOT.kRed), 
        #                                     ROOT.RooFit.Name("jpsi_bkg"), 
        #                                     ROOT.RooFit.NormRange(fit_region.name))
                                            
        # if "psi2s" in self.fitter.resonant_backgrounds:
        #     psi2s_component_name = f"psi2s_resonant_bkg{category_label}"
        #     self.fitter.combined_model.plotOn(frame, 
        #                                     ROOT.RooFit.Components(psi2s_component_name),
        #                                     ROOT.RooFit.LineColor(ROOT.kBlue), 
        #                                     ROOT.RooFit.Name("psi2s_bkg"), 
        #                                     ROOT.RooFit.NormRange(fit_region.name))

        chosen_bkg = self.fitter.get_chosen_background_function()
        if chosen_bkg:
            nonres_bkg_name = self.fitter.get_chosen_background_function().GetTitle()
            print(f"DEBUG: nonres_bkg_name = {nonres_bkg_name}", flush=True)
            print(f"DEBUG: chosen bkg = {self.fitter.get_chosen_background_function()}", flush=True)
            self.fitter.combined_model.plotOn(frame, 
                                            ROOT.RooFit.Components(nonres_bkg_name),
                                            ROOT.RooFit.LineColor(ROOT.kGreen), 
                                            ROOT.RooFit.Name("nonresonant_bkg"), 
                                            ROOT.RooFit.Range(fit_region.range[0], fit_region.range[1]),
                                            ROOT.RooFit.NormRange(fit_region.name))
        
        # Replot data on top
        frame.drawAfter("nonresonant_bkg", "data_obs")

        plot_name_list = ["full_bkg_model", "nonresonant_bkg"]
        for res_bkg in self.fitter.resonant_backgrounds.keys():
            plot_name_list.append(f"{res_bkg}_bkg")

        # plot_name_list = ["full_bkg_model", "jpsi_bkg", "psi2s_bkg", "nonresonant_bkg"]
        return plot_name_list
        
    def _plot_background_models(self, frame: ROOT.RooPlot, fit_region: FitRegion):
        """Plot background-only models"""
        colors = [ROOT.kRed, ROOT.kBlue, ROOT.kGreen, ROOT.kOrange]
        
        for i, func_config in enumerate(self.config.background_functions):
            func_name = func_config.name
            if func_name in self.fitter.background_functions:
                func = self.fitter.background_functions[func_name]
                color = colors[i % len(colors)]
                
                func.plotOn(frame, 
                          ROOT.RooFit.LineColor(color), 
                          ROOT.RooFit.Name(func_name), 
                          ROOT.RooFit.NormRange(fit_region.name))
                          
    def _calculate_chi2_values(self, frame: ROOT.RooPlot, 
                              results: Dict[str, FitResult]) -> Dict[str, float]:
        """Calculate chi2 values for plotting"""
        chi2_values = {}
        
        for name, result in results.items():
            if result.n_free_params > 0:
                print(f"DEBUG: computing chi2 between data_obs and {name} with {result.n_free_params} free params", flush=True)
                # Get chi2 from frame
                chi2_val = frame.chiSquare(name, "data_obs", result.n_free_params)
                chi2_values[name] = chi2_val
                print(f"  Chi2 for {name}: {chi2_val} (n. free params = {result.n_free_params})", flush=True)

                # DEBUG: compute using createChi2 
                # first: create binned clone of data
                binned_data = self.fitter.data.binnedClone()
                model_to_compute = self.fitter.combined_model if name == "full_bkg_model" else self.fitter.background_functions.get(name)
                chi2_obj = model_to_compute.createChi2(binned_data,
                                           ROOT.RooFit.DataError(ROOT.RooAbsData.SumW2))
                # chi2_obj = ROOT.RooChi2Var(f"chi2_{name}", f"chi2_{name}", 
                #                            model_to_compute,
                #                            binned_data,
                #                            ROOT.RooFit.Range(self.config.chosen_fit_region.name),
                #                            ROOT.RooFit.DataError(ROOT.RooAbsData.SumW2))
                chi2_over_ndf = chi2_obj.getVal() / result.n_free_params
                print(f"  (DEBUG) Chi2 for {name} using RooChi2Var: {chi2_obj.getVal()} (chi2/ndf = {chi2_over_ndf})", flush=True)
                
                # Update result object
                result.calculate_chi2_ndf(chi2_val * result.n_free_params, result.n_free_params)
                
        return chi2_values
        
    def _create_legend(self, fit_region: FitRegion, results: Dict[str, FitResult], 
                      chi2_values: Dict[str, float]) -> ROOT.TLegend:
        """Create legend for the plot"""
        # Position legend based on region
        if fit_region.name == "region0":
            legend = ROOT.TLegend(0.2, 0.15, 0.9, 0.45)
        elif fit_region.name == "region2":
            legend = ROOT.TLegend(0.2, 0.6, 0.9, 0.9)
        else:
            legend = ROOT.TLegend(0.15, 0.2, 0.3, 0.4)
            
        legend.SetBorderSize(0)
        legend.SetFillColor(0)
        legend.SetFillStyle(0)
        legend.SetTextSize(0.04)
        
        # Add data entry
        legend.AddEntry("data_obs", "data_obs", "p")
        
        # Function display info
        fs_to_plot = {
            "bkg_f0": {"label": "Bernstein, {}th deg.", "degree": 5},
            "bkg_f1": {"label": "Polynomial, {}th deg.", "degree": 4},
            "bkg_f2": {"label": "Sum of {} exponentials", "degree": 4},
            "bkg_f3": {"label": "1 exponential", "degree": 1},
            "full_bkg_model": {"label": "Full Background Model", "degree": 0},
        }
        
        # Determine which entries to show
        if fit_region.name == "region1" or True: #FIXME
            keys_to_plot = ["full_bkg_model"]
        else:
            keys_to_plot = [func.name for func in self.config.background_functions]
            
        # Add function entries
        for key in keys_to_plot:
            if key in fs_to_plot and key in results:
                info = fs_to_plot[key]
                result = results[key]
                chi2_val = chi2_values.get(key, -1)
                
                label = info["label"].format(info["degree"])
                label += f" (chi2 = {chi2_val:.2f}, npar = {result.n_free_params})"
                
                legend.AddEntry(key, label, "l")
                
        return legend
        
    def _add_jpsi_region_markers(self, frame: ROOT.RooPlot):
        """Add vertical lines marking J/psi region"""
        jpsi_region = self.config.get_fit_region("jpsi")
        if not jpsi_region:
            return
            
        xmin, xmax = jpsi_region.range
        
        line0 = ROOT.TLine(xmin, 0, xmin, frame.GetMaximum())
        line0.SetLineColor(ROOT.kRed)
        line0.SetLineStyle(2)
        line0.Draw("same")
        
        line1 = ROOT.TLine(xmax, 0, xmax, frame.GetMaximum())
        line1.SetLineColor(ROOT.kRed)
        line1.SetLineStyle(2)
        line1.Draw("same")
        
    def _save_plots(self, canvas: ROOT.TCanvas, fit_region: FitRegion, 
                   tag: str = "") -> List[str]:
        """Save plots in different formats"""
        created_files = []
        
        # Get category name for file path
        category_name = self.category.name if self.category else None
        
        # Linear scale
        for fmt in ["png", "pdf"]:
            plot_path = self.config.get_plot_file_path(fit_region.name, tag, 
                                                     log_scale=False, file_format=fmt,
                                                     category=category_name)
            canvas.SaveAs(str(plot_path))
            created_files.append(str(plot_path))
            
        # Log scale
        canvas.SetLogy()
        for fmt in ["png", "pdf"]:
            plot_path = self.config.get_plot_file_path(fit_region.name, tag, 
                                                     log_scale=True, file_format=fmt,
                                                     category=category_name)
            canvas.SaveAs(str(plot_path))
            created_files.append(str(plot_path))
            
        return created_files
        
    def plot_prompt_jpsi_fit(self, tag: str = "", fit_region: str = "") -> List[str]:
        """Plot J/psi fit from prompt sample (if configured)"""
        if not self.config.fit_jpsi_prompt:
            return []
            
        print("Creating prompt J/psi resonant background fit plots...")
        
        # Check if prompt data and models are available
        if not hasattr(self.fitter, 'resonant_data') or not self.fitter.resonant_data:
            print("  Warning: No prompt data available for plotting")
            return []
            
        if not hasattr(self.fitter, 'resonant_combined_model') or not self.fitter.resonant_combined_model:
            print("  Warning: No prompt combined model available for plotting")
            return []
            
        created_plots = []
        
        # Create canvas
        canvas_prompt = ROOT.TCanvas("canvas_prompt", "canvas_prompt", 800, 600)
        canvas_prompt.SetGrid()
        
        # Get mass variable range for unblinded region
        xmin, xmax = self.config.chosen_fit_region.range
        # xmin, xmax = self.fitter.mass_var.getRange("unblinded")
        # xmin = 2
        # xmax = 4.2
        frame_resonant = self.fitter.mass_var.frame(xmin, xmax)
        print(f"DEBUG: Plotting resonant data in range [{xmin}, {xmax}]", flush=True)
        frame_resonant.SetTitle("")
        
        # Plot prompt data
        print("DEBUG: resonant data = ", self.fitter.resonant_data, "; entries = ", self.fitter.resonant_data.sumEntries(), flush=True)
        for i in range(100):
            self.fitter.resonant_data.get(i)
            print(f"  bin {i}: {self.fitter.resonant_data.weight()}", flush=True)
        self.fitter.resonant_data.plotOn(frame_resonant,
                    ROOT.RooFit.Name("resonant_data"),
                    ROOT.RooFit.Binning(100),
                    ROOT.RooFit.DataError(ROOT.RooAbsData.SumW2))
                            
        # Plot combined model
        print("DEBUG: resonant combined model = ", self.fitter.resonant_combined_model, flush=True)
        self.fitter.resonant_combined_model.plotOn(frame_resonant,
                    ROOT.RooFit.LineColor(ROOT.kBlack), 
                    ROOT.RooFit.Name("resonant_combined_model"))
                    # ROOT.RooFit.NormRange(self.config.chosen_fit_region.name))
        
        # Plot components
        # print("DEBUG: plotting J/psi and psi2S models", flush=True)
        print("DEBUG: self.fitter.resonant_backgrounds = ", self.fitter.resonant_backgrounds, flush=True)
        # jpsi_model = self.fitter.resonant_backgrounds.get("jpsi")
        # psi2s_model = self.fitter.resonant_backgrounds.get("psi2s")

        # if jpsi_model:
        #     self.fitter.resonant_combined_model.plotOn(frame_resonant,
        #                 ROOT.RooFit.Components(jpsi_model.GetName()),
        #                 ROOT.RooFit.LineColor(ROOT.kRed),
        #                 ROOT.RooFit.Name("jpsi_model"),
        #                 ROOT.RooFit.NormRange("unblinded"))
        
        # if psi2s_model:
        #     self.fitter.resonant_combined_model.plotOn(frame_resonant,
        #                 ROOT.RooFit.Components(psi2s_model.GetName()),
        #                 ROOT.RooFit.LineColor(ROOT.kBlue),
        #                 ROOT.RooFit.Name("psi2s_model"),
        #                 ROOT.RooFit.NormRange("unblinded"))

        print(f"DEBUG: plotting components: {self.config.chosen_fit_region.backgrounds}", flush=True)
        
        colors = [ROOT.kRed, ROOT.kBlue, ROOT.kGreen, ROOT.kOrange]

        for idx, (model_name, model) in enumerate(self.fitter.resonant_backgrounds.items()):
            print(f"DEBUG: resonant model = {model.GetName()}", flush=True)
            self.fitter.resonant_combined_model.plotOn(frame_resonant,
                        ROOT.RooFit.Components(model.GetName().split("_cat_")[0]),
                        ROOT.RooFit.LineColor(colors[idx]),
                        ROOT.RooFit.Name(model_name))
                        # ROOT.RooFit.NormRange(self.config.chosen_fit_region.name))
        
        # Draw frame
        frame_resonant.Draw()
        frame_resonant.GetXaxis().SetTitle("m(ee) [GeV]")
        
        # Compute chi2
        npar = self.fitter.resonant_combined_model.getParameters(self.fitter.resonant_data).selectByAttrib("Constant", False).getSize()
        chi2_val = frame_resonant.chiSquare("resonant_combined_model", "resonant_data", int(npar))
        
        self.fitter.log_print(f"chi2 = {chi2_val} (n. free params = {npar})")
        
        # Create legend
        legend_prompt = ROOT.TLegend(0.2, 0.15, 0.9, 0.45)
        legend_prompt.SetBorderSize(0)
        legend_prompt.SetFillColor(0)
        legend_prompt.SetFillStyle(0)
        legend_prompt.SetTextSize(0.04)
        legend_prompt.AddEntry(frame_resonant.findObject("resonant_data"), "Data for resonant bkg", "p")
        legend_prompt.AddEntry(frame_resonant.findObject("resonant_combined_model"), 
                             f"#splitline{{Combined resonant model}}{{chi2 = {chi2_val:.2f}}}", "l")

        for model_name, model in self.fitter.resonant_backgrounds.items():
            legend_prompt.AddEntry(frame_resonant.findObject(model_name), f"{model.GetTitle()} model", "l")
        # if jpsi_model:
        #     legend_prompt.AddEntry(frame_resonant.findObject("jpsi_model"), "J/psi model", "l")
        # if psi2s_model:
        #     legend_prompt.AddEntry(frame_resonant.findObject("psi2s_model"), "psi(2S) model", "l")
        legend_prompt.Draw()
        
        # Save plots
        output_dir = self.config.output_dir
        tag_suffix = f"_{tag}" if tag else ""
        
        # Linear scale
        plot_path = output_dir / self.category.name / f"dataset_prompt{tag_suffix}_{fit_region}{self.fitter.category.label}.png"
        canvas_prompt.SaveAs(str(plot_path))
        created_plots.append(str(plot_path))
        
        plot_path = output_dir / self.category.name / f"dataset_prompt{tag_suffix}_{fit_region}{self.fitter.category.label}.pdf"
        canvas_prompt.SaveAs(str(plot_path))
        created_plots.append(str(plot_path))
        
        # Log scale
        frame_resonant.SetMinimum(1)
        canvas_prompt.SetLogy()
        
        plot_path = output_dir / self.category.name / f"dataset_prompt{tag_suffix}_{fit_region}{self.fitter.category.label}_log.png"
        canvas_prompt.SaveAs(str(plot_path))
        created_plots.append(str(plot_path))
        
        plot_path = output_dir / self.category.name / f"dataset_prompt{tag_suffix}_{fit_region}{self.fitter.category.label}_log.pdf"
        canvas_prompt.SaveAs(str(plot_path))
        created_plots.append(str(plot_path))
        
        print(f"  Created {len(created_plots)} resonant fit plots")
        return created_plots
        
    def create_all_plots(self, fit_region: FitRegion, 
                        background_results: Dict[str, FitResult],
                        combined_result: Optional[FitResult] = None,
                        tag: str = "") -> List[str]:
        """Create all plots for a fitting session"""
        print(f"Creating all plots for {fit_region.display_name}...")
        
        created_plots = []
        
        # Combine all results
        all_results = background_results.copy()
        if combined_result:
            all_results[combined_result.name] = combined_result
            
        # Create main plots
        plots = self.plot_fits(fit_region, all_results, tag)
        created_plots.extend(plots)
        
        # Create prompt J/psi plots if configured
        if self.config.fit_jpsi_prompt:
            prompt_plots = self.plot_prompt_jpsi_fit(tag, fit_region.name)
            created_plots.extend(prompt_plots)
            
        print(f"Total plots created: {len(created_plots)}")
        return created_plots
    
    def create_plots_for_all_categories(self, fit_region: FitRegion,
                                      background_results_by_category: Dict[str, Dict[str, FitResult]],
                                      combined_results_by_category: Dict[str, FitResult] = None,
                                      tag: str = "") -> Dict[str, List[str]]:
        """Create plots for all categories separately
        
        Args:
            fit_region: The fit region to plot
            background_results_by_category: Dictionary mapping category names to their background results
            combined_results_by_category: Dictionary mapping category names to their combined results
            tag: Tag for output files
            
        Returns:
            Dictionary mapping category names to lists of created plot file paths
        """
        print(f"Creating plots for all categories in {fit_region.display_name}...")
        
        all_category_plots = {}
        categories = self.config.get_available_categories()
        
        for category_name, category_config in categories.items():
            print(f"\n--- Creating plots for category: {category_name} ---")
            
            # Check if we have results for this category
            if category_name not in background_results_by_category:
                print(f"  Warning: No background results found for category {category_name}")
                continue
            
            # Create a temporary plotter for this specific category
            category_plotter = BackgroundPlotter(self.config, self.fitter, category_config)
            
            # Get results for this category
            background_results = background_results_by_category[category_name]
            combined_result = combined_results_by_category.get(category_name) if combined_results_by_category else None
                    
            try:
                # Create plots for this category
                category_plots = category_plotter.create_all_plots(
                    fit_region, background_results, combined_result, tag
                )
                all_category_plots[category_name] = category_plots
                print(f"  Created {len(category_plots)} plots for category {category_name}")
                
            except Exception as e:
                print(f"  Error creating plots for category {category_name}: {e}")
                all_category_plots[category_name] = []
        
        # Summary
        total_plots = sum(len(plots) for plots in all_category_plots.values())
        print(f"\nTotal plots created across all categories: {total_plots}")
        
        return all_category_plots
    
    def create_comparison_plots_across_categories(self, fit_region: FitRegion,
                                                combined_results_by_category: Dict[str, FitResult],
                                                tag: str = "") -> List[str]:
        """Create comparison plots showing results from all categories on the same canvas
        
        Args:
            fit_region: The fit region to plot
            combined_results_by_category: Dictionary mapping category names to their combined results
            tag: Tag for output files
            
        Returns:
            List of created comparison plot file paths
        """
        print(f"Creating comparison plots across all categories for {fit_region.display_name}...")
        
        created_plots = []
        categories = self.config.get_available_categories()
        
        # Create canvas for comparison
        canvas = ROOT.TCanvas("canvas_comparison", "canvas_comparison", 1200, 800)
        canvas.SetGrid()
        
        # Create frame
        xmin, xmax = fit_region.range
        frame = self.fitter.mass_var.frame(xmin, xmax)
        frame.SetTitle(f"Background Models Comparison - {fit_region.display_name}")
        
        # Colors for different categories
        colors = [ROOT.kBlack, ROOT.kRed, ROOT.kBlue, ROOT.kGreen, ROOT.kOrange, ROOT.kMagenta, ROOT.kCyan]
        
        # Plot data and models for each category
        legend = ROOT.TLegend(0.7, 0.6, 0.95, 0.9)
        legend.SetBorderSize(0)
        legend.SetFillColor(0)
        legend.SetFillStyle(0)
        legend.SetTextSize(0.03)
        
        color_idx = 0
        for category_name, category_config in categories.items():
            if category_name not in combined_results_by_category:
                continue
                
            color = colors[color_idx % len(colors)]
            
            # Try to get category-specific data from workspace
            try:
                dataset_name = f"data_obs{category_config.label}"
                category_data = self.fitter.workspace.obj(dataset_name)
                
                if category_data:
                    # Plot data for this category
                    category_data.plotOn(frame,
                        ROOT.RooFit.Name(f"data_{category_name}"),
                        ROOT.RooFit.MarkerColor(color),
                        ROOT.RooFit.LineColor(color),
                        ROOT.RooFit.MarkerStyle(20 + color_idx),
                        ROOT.RooFit.Binning(50))
                    
                    legend.AddEntry(f"data_{category_name}", f"Data ({category_name})", "p")
                
                # Plot combined model for this category if available
                if self.fitter.combined_model:
                    # This would need category-specific models - simplified for now
                    model_name = f"model_{category_name}"
                    legend.AddEntry(model_name, f"Model ({category_name})", "l")
                
            except Exception as e:
                print(f"  Warning: Could not plot category {category_name}: {e}")
                
            color_idx += 1
        
        # Draw everything
        frame.Draw()
        frame.GetXaxis().SetTitle("m(ee) [GeV]")
        frame.GetYaxis().SetTitle("Events")
        legend.Draw()
        
        # Save comparison plots
        comparison_tag = f"comparison_{tag}" if tag else "comparison"
        
        # Linear scale
        for fmt in ["png", "pdf"]:
            plot_path = self.config.get_plot_file_path(fit_region.name, comparison_tag,
                                                     log_scale=False, file_format=fmt,
                                                     category="all_categories")
            canvas.SaveAs(str(plot_path))
            created_plots.append(str(plot_path))
            
        # Log scale
        canvas.SetLogy()
        for fmt in ["png", "pdf"]:
            plot_path = self.config.get_plot_file_path(fit_region.name, comparison_tag,
                                                     log_scale=True, file_format=fmt,
                                                     category="all_categories")
            canvas.SaveAs(str(plot_path))
            created_plots.append(str(plot_path))
            
        canvas.Close()
        
        print(f"  Created {len(created_plots)} comparison plots")
        return created_plots
