"""
Main background analysis - Object-oriented approach

This module provides the main interface for running background modeling analysis,
replicating the functionality of both create_dataset.py and bkg_test.py.
"""
import argparse
import os
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any

from dataset_creator import DatasetCreator
from background_config import BackgroundModelConfig
from background_fitter import BackgroundFitter, FitResult
from background_plotter import BackgroundPlotter


class BackgroundAnalysis:
    """Main class for running complete background analysis"""
    
    def __init__(self):
        self.config: Optional[BackgroundModelConfig] = None
        self.fitter: Optional[BackgroundFitter] = None
        self.plotter: Optional[BackgroundPlotter] = None
        
        # Results storage
        self.background_results: Dict[str, FitResult] = {}
        self.combined_result: Optional[FitResult] = None
        
        print("Background analysis initialized")
        
    def setup_from_args(self, args):
        """Setup analysis from command line arguments"""
        print("Setting up analysis from command line arguments...")
        
        # Parse categories if provided
        categories = None
        if args.categories:
            from shared_config import parse_category_args
            categories = parse_category_args(args.categories)
        
        # Create configuration
        self.config = BackgroundModelConfig(categories=categories)
        
        # Set selected category for fitting
        if args.category:
            print(f"DEBUG: Setting selected category to '{args.category}'", flush=True)
            self.config.set_category(args.category)
        
        # Apply command line settings
        self.config.use_jpsi = args.use_jpsi
        self.config.use_reduced_mass = args.use_reduced_mass
        self.config.use_binned = args.binned
        self.config.freeze_bkg_sidebands = args.freeze_bkg_sidebands
        self.config.floating_resonant = args.floating_resonant
        self.config.fit_jpsi_first = args.fit_jpsi_first
        self.config.fit_jpsi_prompt = args.fit_jpsi_prompt
        self.config.set_background_function(args.bkg_function)
        
        # Apply tag if provided
        if args.tag:
            self.config.apply_tag(args.tag)
            
        print(f"Configuration setup complete")
        self.config.print_summary()
        
    def create_datasets(self) -> bool:
        """Create datasets for analysis"""
        print("="*60)
        print("CREATING DATASETS")
        print("="*60)
        
        try:
            # Create main dataset (MinBias/data)
            print("\n1. Creating main dataset...")
            main_creator = DatasetCreator(
                use_jpsi=False,  # Always false for main dataset
                use_reduced_mass=self.config.use_reduced_mass,
                categories=self.config.categories
            )
            main_dataset_path = main_creator.create_full_dataset()
            
            # Create J/psi dataset if needed
            if self.config.fit_jpsi_prompt:
                print("\n2. Creating J/psi dataset...")
                jpsi_creator = DatasetCreator(
                    use_jpsi=True,
                    use_reduced_mass=self.config.use_reduced_mass,
                    categories=self.config.categories
                )
                jpsi_dataset_path = jpsi_creator.create_full_dataset()
                print(f"J/psi dataset created: {jpsi_dataset_path}")
            else:
                print("\n2. Skipping J/psi dataset creation")
                
            print(f"\nMain dataset created: {main_dataset_path}")
            return True
            
        except Exception as e:
            print(f"Error creating datasets: {e}")
            import traceback
            traceback.print_exc()
            return False
            
    def setup_fitter(self, category: "CategoryConfig" = None) -> bool:
        """Setup the background fitter for a specific category"""
        from shared_config import CategoryConfig
        
        if category is None and self.config.selected_category:
            # Get CategoryConfig object from selected category name
            categories = self.config.get_available_categories()
            category = categories.get(self.config.selected_category)
            
        print(f"Setting up background fitter...")
        if category:
            print(f"Category: {category.name} (label: '{category.label}')")
        
        self.fitter = BackgroundFitter(self.config, category=category)
        
        # Load workspace for the specified category
        if not self.fitter.load_workspace():
            return False
            
        # Create background functions
        self.fitter.create_background_functions()
        
        # Setup resonant background models for the category
        self.fitter.setup_resonant_backgrounds()
        
        # Setup normalizations
        self.fitter.setup_normalizations()
        
        print("Background fitter setup complete")
        return True
        
    def setup_plotter(self, category: "CategoryConfig" = None):
        """Setup the background plotter"""
        from shared_config import CategoryConfig
        
        print("Setting up background plotter...")
        if category is None and self.config.selected_category:
            # Get CategoryConfig object from selected category name
            categories = self.config.get_available_categories()
            category = categories.get(self.config.selected_category)
            
        self.plotter = BackgroundPlotter(self.config, self.fitter, category)
        print("Background plotter setup complete")
        
    def fit_sidebands(self, fit_region_name: str, tag: str = "") -> bool:
        """Fit background functions to sideband regions"""
        print(f"\nFitting background to sidebands in {fit_region_name}...")
        
        fit_region = self.config.get_fit_region(fit_region_name)
        if not fit_region:
            print(f"Error: Unknown fit region '{fit_region_name}'")
            return False
            
        # Open log file
        print(f"DEBUG: opening log file for {fit_region_name}, tag = {tag}, category =  {self.fitter.category.name}", flush=True)
        self.fitter.open_log_file(fit_region_name, tag, self.fitter.category.name)
        self.fitter.log_print(f"Starting background fit analysis for {fit_region.display_name}")
        
        try:
            # Fit background functions to sidebands
            if fit_region_name != "region1":
                print("DEBUG: fitting sidebands", flush=True)
                self.background_results = self.fitter.fit_background_to_sidebands(fit_region)
                
                # Log results
                self._log_background_results(fit_region)
                
            return True
            
        except Exception as e:
            self.fitter.log_print(f"Error in sideband fitting: {e}")
            return False
            
    def fit_combined_background(self, fit_region_name: str) -> bool:
        """Fit combined resonant + non-resonant background model"""
        print(f"\nFitting combined background model in {fit_region_name}...")
        
        fit_region = self.config.get_fit_region(fit_region_name)
        if not fit_region:
            print(f"Error: Unknown fit region '{fit_region_name}'")
            return False
            
        try:
            # For main region, fit combined background model
            if fit_region_name == "region1":
                # First fit non-resonant background to sidebands within this region
                sideband_results = self.fitter.fit_background_to_sidebands(fit_region)
                
                # Freeze background parameters if requested
                self.fitter.freeze_background_parameters()
                
                print("DEBUG: creating combined model", flush=True)
                # Create combined model
                self.fitter.create_combined_model(fit_region)

                # Fit combined model                
                # Fit J/psi first if requested
                if self.config.fit_jpsi_first:
                    self._fit_jpsi_first()
                                
                print("DEBUG: fitting combined model", flush=True)
                # Fit combined model
                self.combined_result = self.fitter.fit_combined_model(fit_region)
                
                # Calculate integrals
                integrals = self.fitter.calculate_integrals(fit_region)
                self.combined_result.integrals = integrals
                
                # Log results
                self._log_combined_results(fit_region)
                
            return True
            
        except Exception as e:
            self.fitter.log_print(f"Error in background fitting: {e}")
            return False
            
    def _fit_jpsi_first(self):
        """Fit J/psi component first in its own region"""
        if not self.config.fit_jpsi_first:
            return
            
        self.fitter.log_print("Fitting J/psi model first")
        
        # This would implement the J/psi-first fitting logic
        # For now, just log that it would happen
        self.fitter.log_print("J/psi-first fitting not yet fully implemented")
        
    def _log_background_results(self, fit_region):
        """Log background fitting results"""
        self.fitter.log_print(f"\nBackground fit results for {fit_region.display_name}:")
        self.fitter.log_print("-" * 50)
        
        for func_name, result in self.background_results.items():
            func_config = None
            for f in self.config.background_functions:
                if f.name == func_name:
                    func_config = f
                    break
                    
            if func_config:
                self.fitter.log_print(f"\n{func_config.display_name} ({func_name}):")
                self.fitter.log_print(f"  Fit status: {result.fit_status}")
                self.fitter.log_print(f"  Chi2/ndf: {result.chi2_ndf:.3f}")
                self.fitter.log_print(f"  Free parameters: {result.n_free_params}")
                
                # Log parameters
                for param_name, value in result.parameters.items():
                    error = result.parameter_errors.get(param_name, 0)
                    print(f"DEBUG: printing limits to {self.fitter.log_file}")
                    self.fitter.log_print(f"    {param_name}: {value:.5f} +/- {error:.5f} (limits: {result.parameter_limits.get(param_name, 'N/A')})")
                    
    def _log_combined_results(self, fit_region):
        """Log combined background fitting results"""
        if not self.combined_result:
            return
            
        self.fitter.log_print(f"\nCombined background fit results for {fit_region.display_name}:")
        self.fitter.log_print("-" * 50)
        
        result = self.combined_result
        self.fitter.log_print(f"Fit status: {result.fit_status}")
        self.fitter.log_print(f"Chi2/ndf: {result.chi2_ndf:.3f}")
        self.fitter.log_print(f"Free parameters: {result.n_free_params}")
        
        # Log parameters with prefit comparison
        resonant_params = ["mean", "sigma", "alphaL", "nL", "alphaR", "nR"]
        for param_name, value in result.parameters.items():
            error = result.parameter_errors.get(param_name, 0)
            self.fitter.log_print(f"  {param_name}: {value:.5f} +/- {error:.5f} (limits: {result.parameter_limits.get(param_name, 'N/A')})")
            
            # Show prefit comparison for resonant background parameters
            if any(sp in param_name for sp in resonant_params):
                prefit_val = result.prefit_parameters.get(param_name)
                if prefit_val is not None:
                    rel_change = (value - prefit_val) / value * 100 if value != 0 else 0
                    self.fitter.log_print(f"    Prefit: {prefit_val:.5f} (rel. change: {rel_change:.2f}%)")
                    
        # Log integrals
        if result.integrals:
            self.fitter.log_print(f"\nComponent integrals in {fit_region.display_name}:")
            for comp_name, integral_val in result.integrals.items():
                self.fitter.log_print(f"  {comp_name}: {integral_val:.5f}")
                
    def create_plots(self, fit_region_name: str, tag: str = "") -> List[str]:
        """Create plots for the analysis"""
        print(f"\nCreating plots for {fit_region_name}...")
        
        if not self.plotter:
            print("Error: Plotter not setup")
            return []
            
        fit_region = self.config.get_fit_region(fit_region_name)
        if not fit_region:
            print(f"Error: Unknown fit region '{fit_region_name}'")
            return []
            
        try:
            plots = self.plotter.create_all_plots(
                fit_region, 
                self.background_results, 
                self.combined_result, 
                tag
            )
            return plots
            
        except Exception as e:
            print(f"Error creating plots: {e}")
            return []
            
    def save_workspace(self):
        """Save the fitted workspace"""
        if self.fitter:
            self.fitter.save_workspace()
            
    def cleanup(self):
        """Cleanup resources"""
        if self.fitter:
            self.fitter.close_log_file()
            
    def run_complete_analysis(self, fit_region_name: str, tag: str = "", category: "CategoryConfig" = None) -> bool:
        """Run the complete background analysis workflow for a specific category"""
        from shared_config import CategoryConfig
        
        print("="*60)
        print("RUNNING COMPLETE BACKGROUND ANALYSIS")
        if category:
            print(f"Category: {category.display_name} (label: '{category.name}')")
        print("="*60)
        
        success = True
        
        try:
            # Step 1: Setup config, fitter and plotter  with category
            self.config.select_category(category)

            print("DEBUG: SETTING UP FITTER", flush=True)
            if not self.setup_fitter(category):
                print("Failed to setup fitter")
                return False

            print("DEBUG: SETTING UP PLOTTER", flush=True)
            self.setup_plotter(category)
            
            # Step 2: Fit floating resonant backgrounds to prompt data (if configured)
            if self.config.fit_jpsi_prompt and self.config.floating_resonant:
                print("DEBUG: fitting floating resonant backgrounds to prompt data", flush=True)
                try:
                    prompt_result = self.fitter.fit_floating_resonant_to_prompt()
                    if prompt_result.fit_status != 0:
                        print(f"Warning: Prompt fit status = {prompt_result.fit_status}")
                    print("Fitted floating resonant backgrounds to prompt data")
                except Exception as e:
                    print(f"Error fitting to prompt data: {e}")
                    success = False
            
            # Step 3: Fit backgrounds to sidebands (or entire region for sideband regions)
            print("DEBUG: fitting sidebands", flush=True)
            if not self.fit_sidebands(fit_region_name, tag):
                print("Failed to fit sidebands")
                success = False
                
            # Step 4: Fit combined background model (for main region)
            if success and fit_region_name == "region1":
                if not self.fit_combined_background(fit_region_name):
                    print("Failed to fit combined background model")
                    success = False
                    
            # Step 5: Create plots
            if success:
                plots = self.create_plots(fit_region_name, tag)
                print(f"Created {len(plots)} plots")
                
            # Step 6: Save workspace
            if success:
                self.save_workspace()
                
            return success
            
        except Exception as e:
            print(f"Error in complete analysis: {e}")
            import traceback
            traceback.print_exc()
            return False
            
        finally:
            self.cleanup()

    def run_analysis_for_all_categories(self, fit_region_name: str, tag: str = "") -> Dict[str, bool]:
        """Run analysis for all available categories"""
        print("="*60)
        print("RUNNING ANALYSIS FOR ALL CATEGORIES")
        print("="*60)
        
        categories = self.config.get_available_categories()
        results = {}
        
        for category_name, category_config in categories.items():
            print(f"\n{'='*40}")
            print(f"PROCESSING CATEGORY: {category_name}")
            print(f"{'='*40}")
            
            try:
                # Create fresh analysis instance for each category
                success = self.run_complete_analysis(fit_region_name, tag, category_config)
                results[category_name] = success
                
                if success:
                    print(f"✅ Category '{category_name}' completed successfully")
                else:
                    print(f"❌ Category '{category_name}' failed")
                    
            except Exception as e:
                print(f"❌ Error processing category '{category_name}': {e}")
                results[category_name] = False
        
        # Summary
        print(f"\n{'='*60}")
        print("CATEGORY ANALYSIS SUMMARY")
        print(f"{'='*60}")
        successful = [name for name, success in results.items() if success]
        failed = [name for name, success in results.items() if not success]
        
        print(f"Successful categories ({len(successful)}): {successful}")
        if failed:
            print(f"Failed categories ({len(failed)}): {failed}")
        
        return results

    def create_plots_for_all_categories(self, fit_region_name: str, tag: str = "") -> Dict[str, List[str]]:
        """Create plots for all available categories by running individual analysis for each."""
        print(f"\n{'='*60}")
        print("CREATING PLOTS FOR ALL CATEGORIES")
        print(f"{'='*60}")
        
        available_categories = self.config.get_available_categories()
        plot_results = {}
        
        for category_config in available_categories:
            category_name = category_config.display_name
            print(f"\n{'='*40}")
            print(f"CREATING PLOTS FOR: {category_name}")
            print(f"{'='*40}")
            
            try:
                # Run the plotting part of complete analysis for this category
                # This will load workspace, setup plotter, and create plots
                plots = self._create_plots_for_category(fit_region_name, tag, category_config)
                plot_results[category_name] = plots
                
                if plots:
                    print(f"✅ Created {len(plots)} plots for category '{category_name}'")
                else:
                    print(f"❌ Failed to create plots for category '{category_name}'")
                    
            except Exception as e:
                print(f"❌ Error creating plots for category '{category_name}': {e}")
                plot_results[category_name] = []
        
        # Summary
        print(f"\n{'='*60}")
        print("PLOTTING SUMMARY")
        print(f"{'='*60}")
        total_plots = sum(len(plots) for plots in plot_results.values())
        print(f"Total plots created: {total_plots}")
        for category_name, plots in plot_results.items():
            if plots:
                print(f"  - {category_name}: {len(plots)} plots")
        
        return plot_results
    
    def _create_plots_for_category(self, fit_region_name: str, tag: str, 
                                  category_config: "CategoryConfig") -> List[str]:
        """Create plots for a specific category."""
        try:
            # Update config to this category
            print(f"DEBUG: Setting up config for '{category_config.name}'", flush=True)
            self.config.select_category(category_config)
            
            # Setup fitter for this category
            success = self.setup_fitter(category_config)
            if not success:
                print(f"Failed to setup fitter for category")
                return []
            
            # Load workspace with existing fits
            if not self.fitter.load_workspace(fit_region_name, tag):
                print(f"Failed to load workspace for category (fits may not exist)")
                return []
            
            # Setup plotter
            self.setup_plotter(category_config)
            if self.plotter is None:
                print(f"Failed to setup plotter for category")
                return []
            
            # Create plots using the existing create_plots method
            plots = self.create_plots(fit_region_name, tag)
            return plots
            
        except Exception as e:
            print(f"Error in _create_plots_for_category: {e}")
            return []


def create_argument_parser():
    """Create command line argument parser"""
    parser = argparse.ArgumentParser(description="Background Model Analysis - Object-oriented version")
    
    # Dataset creation options
    parser.add_argument("--create_datasets", action="store_true", default=False,
                       help="Create datasets from root files")
    parser.add_argument("--use_jpsi", action="store_true", default=False,
                       help="Use J/psi sample instead of MinBias sample")
    parser.add_argument("--use_reduced_mass", action="store_true", default=False,
                       help="Use reduced mass instead of fitted mass")
    parser.add_argument('--categories', nargs='+', default=None,
                       help='Custom categories to create (specify as key=value pairs, e.g. central="pt_1>20&&pt_2>20")')
    parser.add_argument('--category', default=None,
                       help='Specific category to fit (if not specified, uses all categories)')
    parser.add_argument('--all_categories', action='store_true', default=False,
                       help='Run analysis for all available categories')
    
    # Fitting options
    parser.add_argument("--fit_region", default="region1", 
                       choices=["region1", "region0", "region2", "full"],
                       help="Pick fit region")
    parser.add_argument("--bkg_function", default=-1, type=int, choices=[-1, 0, 1, 2, 3],
                       help="Choose background function (0: Bernstein, 1: Poly×Exp, 2: Sum Exp, 3: Simple Exp; -1 for all)")
    parser.add_argument("--freeze_bkg_sidebands", action="store_true", default=False,
                       help="Freeze background parameters from sideband fit")
    parser.add_argument("--floating_resonant", action="store_true", default=False,
                       help="Use floating resonant background parameters")
    parser.add_argument("--fit_jpsi_first", action="store_true", default=False,
                       help="Fit J/psi component first")
    parser.add_argument("--fit_jpsi_prompt", action="store_true", default=False,
                       help="Fit resonant models from prompt J/psi sample")
    parser.add_argument("--binned", action="store_true", default=False,
                       help="Use binned data instead of unbinned")
    
    # Output options
    parser.add_argument("--tag", default="", help="Tag for output files")
    parser.add_argument("--no_plots", action="store_true", default=False,
                       help="Skip plot creation")
    parser.add_argument("--plot_all_categories", action="store_true", default=False,
                       help="Create plots for all categories (requires existing fits)")
    
    # Workflow options
    parser.add_argument("--full_analysis", action="store_true", default=False,
                       help="Run complete analysis (create datasets + fit + plot)")
    parser.add_argument("--fit_only", action="store_true", default=False,
                       help="Run fitting only (assumes datasets exist)")
    
    return parser


def main():
    """Main function with category support"""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    print("="*60)
    print("BACKGROUND MODEL ANALYSIS - OBJECT-ORIENTED VERSION")
    print("="*60)
    
    # Print arguments
    print("Arguments:")
    for arg in vars(args):
        print(f"  {arg}: {getattr(args, arg)}")
    print()
    
    try:
        # Create analysis object
        analysis = BackgroundAnalysis()
        print("DEBUG: SETTING ANALYZER", flush=True)
        analysis.setup_from_args(args)
        
        success = True
        
        print("DEBUG: SETTING ANALYZER COMPLETED", flush=True)
        # Step 1: Create datasets if requested
        if args.create_datasets or args.full_analysis:
            if not analysis.create_datasets():
                print("Dataset creation failed!")
                return 1
                
        print("DEBUG: dataset created successfully. Moving onto fit.", flush=True)
        # Step 2: Run fitting analysis
        if args.fit_only or args.full_analysis or (not args.create_datasets):
            # Determine analysis strategy based on category selection
            if args.all_categories or (not args.category and not args.all_categories):
                # Multi-category analysis (default if no specific category chosen)
                print("Running analysis for all categories...")
                results = analysis.run_analysis_for_all_categories(args.fit_region, args.tag)
                success = any(results.values())  # Success if at least one category succeeds
            elif args.category:
                # Single category analysis
                print(f"Running analysis for category '{args.category}'...")
                categories = analysis.config.get_available_categories()
                if args.category in categories:
                    category_config = categories[args.category]
                    success = analysis.run_complete_analysis(args.fit_region, args.tag, category_config)
                else:
                    print(f"❌ Category '{args.category}' not found. Available: {list(categories.keys())}")
                    return 1
            else:
                # Fallback to old behavior (no category specified)
                success = analysis.run_complete_analysis(args.fit_region, args.tag)
        
        # Step 3: Optional multi-category plotting
        if args.plot_all_categories:
            print("\nCreating plots for all categories...")
            plot_results = analysis.create_plots_for_all_categories(args.fit_region, args.tag)
            total_plots = sum(len(plots) for plots in plot_results.values())
            print(f"📊 Created {total_plots} plots across all categories")
                
        if success:
            print("\n🎉 Background analysis completed successfully!")
        else:
            print("\n❌ Background analysis failed!")
            
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n⚠️  Analysis interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
