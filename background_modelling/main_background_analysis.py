"""
Main background analysis - Object-oriented approach

This module provides the main interface for running background modeling analysis,
replicating the functionality of both create_dataset.py and bkg_test.py.
"""
import ROOT
import argparse
import os
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any

from dataset_creator import DatasetCreator
from background_config import BackgroundModelConfig
from background_fitter import BackgroundFitter, FitResult
from background_plotter import BackgroundPlotter

# Suppress RooFit INFO messages (only show WARNING and ERROR)
ROOT.RooMsgService.instance().setGlobalKillBelow(ROOT.RooFit.WARNING)


class BackgroundAnalysis:
    """Main class for running complete background analysis"""
    
    def __init__(self):
        self.config: Optional[BackgroundModelConfig] = None
        self.fitter: Optional[BackgroundFitter] = None
        self.plotter: Optional[BackgroundPlotter] = None
        
        # Results storage
        self.background_results: Dict[str, FitResult] = {}
        self.combined_result: Optional[FitResult] = None
        
        # Centralized workspace management
        self.output_workspace: Optional["ROOT.RooWorkspace"] = None
        self.output_workspace_file: Optional[str] = None
        
        # Reweighting setting (will be set from command line args)
        self.use_reweighting: bool = True
        
        print("Background analysis initialized")
        
    def create_output_workspace(self, tag: str = "", fit_region_name: str = "") -> bool:
        """Create a centralized output workspace for all categories"""
        if not self.config:
            print("❌ Config not setup")
            return False
            
        # Create workspace file path
        self.output_workspace_file = str(self.config.get_output_workspace_path())
        # TODO: tag is redundant here? UNIFORM USAGE ACROSS FOLDER/OUTPUT ROOT. We want a tag feature.
        # if tag:
        #     # Insert tag before file extension
        #     base_path = Path(self.output_workspace_file)
        #     self.output_workspace_file = str(base_path.with_stem(f"{base_path.stem}_{tag}"))
        
        print(f"Creating centralized output workspace: {self.output_workspace_file}")
        
        # Create workspace
        self.output_workspace = ROOT.RooWorkspace("w", "w")
        
        # Import mass variable from signal workspace (following create_dataset.py pattern)
        suffix = "" if not self.config.use_reduced_mass else "_reducedMass"
        # signal_ws_file = f'../signal_modelling/workspaces/signal_model_withReweight_Categories{suffix}_nanov15.root'
        #FIXME: not available for reduced mass (anymore)
        # signal_ws_file = f'../signal_modelling/workspaces/signal_model_nanov15_withSyst_scaleOnly_elenaSyst.root'
        # signal_ws_file = f'../signal_modelling/workspaces/signal_model_nanov15_withScaleSyst_IDSF.root'
        era = getattr(self, 'era', '2023')  # Default to 2023 if not set
        signal_ws_file = f'../signal_modelling/workspaces/{era}/signal_model_nanov15_withScaleSyst_IDSF_triggerSF.root'
        
        if not os.path.exists(signal_ws_file):
            print(f"❌ Signal workspace not found: {signal_ws_file}")
            return False
            
        signal_file = ROOT.TFile.Open(signal_ws_file)
        signal_ws = signal_file.Get('w')
        
        if not signal_ws:
            print(f"❌ Workspace 'w' not found in {signal_ws_file}")
            signal_file.Close()
            return False
        
        # Get mass variable from signal workspace and set up for background analysis
        m = signal_ws.var('mass')
        if not m:
            print("❌ Variable 'mass' not found in signal workspace")
            signal_file.Close()
            return False
            
        m.SetName("mass")
        if fit_region_name != "":
            fit_region = self.config.get_fit_region(fit_region_name)
            if fit_region:
                # If no_res is set, use only sideband range
                if self.config.no_res and fit_region.sidebands:
                    all_sideband_mins = [sb[0] for sb in fit_region.sidebands]
                    all_sideband_maxs = [sb[1] for sb in fit_region.sidebands]
                    m.setMin(min(all_sideband_mins))
                    m.setMax(max(all_sideband_maxs))
                    
                    # Set individual sideband ranges on the mass variable
                    for i, (sb_min, sb_max) in enumerate(fit_region.sidebands):
                        m.setRange(f"sideband_{i}", sb_min, sb_max)
                        print(f"  Set sideband_{i} range: [{sb_min}, {sb_max}] GeV")
                    
                    print(f"✅ Mass variable imported from signal workspace: range [{min(all_sideband_mins)}, {max(all_sideband_maxs)}] GeV (sidebands only for --no_res)")
                else:
                    m.setMin(fit_region.range[0])
                    m.setMax(fit_region.range[1])
                    print(f"✅ Mass variable imported from signal workspace: range [{fit_region.range[0]}, {fit_region.range[1]}] GeV")
            else:
                print(f"⚠️  Warning: Fit region '{fit_region_name}' not found, using full mass range from signal workspace")
        else:
            print(f"⚠️  Warning: No fit region specified, using full mass range from signal workspace")
        m.setBins(100)
        self.output_workspace.Import(m, ROOT.RooCmdArg())
        
        signal_file.Close()
        
        print("✅ Centralized output workspace created")
        return True
    
    def create_envelope_workspace(self, input_workspaces: List[str]) -> bool:
        """Create a centralized output workspace for envelope from input workspaces"""
        if not self.config:
            print("❌ Config not setup")
            return False
            
        if not input_workspaces:
            print("❌ No input workspaces provided for envelope creation")
            return False
            
        print(f"Creating workspace with envelope of background functions")

        bkg_funcs = []

        # retrieve workspace from first input file
        with ROOT.TFile.Open(input_workspaces[0]) as f:
            base_ws = f.Get("w")
            if not base_ws:
                print(f"❌ Workspace 'w' not found in {input_workspaces[0]}")
                return False
            self.output_workspace = base_ws

        # retrieve background functions from other input files
        for idx, file in enumerate(input_workspaces):
            with ROOT.TFile.Open(file) as f:
                ws = f.Get("w")
                if not ws:
                    print(f"❌ Workspace 'w' not found in {file}")
                    return False
                dy = ws.pdf("dy")
                if not dy:
                    print(f"❌ Non-resonant background function 'dy' not found in {file}")
                    return False
                else:
                    # rename function to avoid name clashes
                    dy.SetName(f"dy_component_{idx}")
                    bkg_funcs.append(dy)

        # Create envelope function
        pdf_index = ROOT.RooCategory("pdf_index", "pdf_index")
        envelope_f = ROOT.RooMultiPdf("dy", "dy", pdf_index, ROOT.RooArgList(*bkg_funcs))

        # Remove all dy functions from base workspace
        self.output_workspace.RecursiveRemove(self.output_workspace.pdf("dy"))
        # Import envelope function
        self.output_workspace.Import(envelope_f, ROOT.RooCmdArg())

        # Set output workspace file path
        self.output_workspace_file = str(self.config.get_output_workspace_path())

        return True        

    def save_output_workspace(self) -> bool:
        """Save the centralized output workspace to file"""
        if not self.output_workspace or not self.output_workspace_file:
            print("❌ No output workspace to save")
            return False

        print(f"Saving centralized workspace to: {self.output_workspace_file}", flush=True)
        self.output_workspace.writeToFile(str(self.output_workspace_file), True)
        print("✅ Centralized output workspace saved", flush=True)
        return True

    def get_output_workspace(self):
        """Get the centralized output workspace"""
        return self.output_workspace
    
    def set_reweighting(self, use_reweighting: bool):
        """Update the reweighting flag"""
        self.use_reweighting = use_reweighting
        print(f"Updated background analysis reweighting setting: {use_reweighting}")
    
    def setup_from_args(self, args):
        """Setup analysis from command line arguments"""
        print("Setting up analysis from command line arguments...")
        
        # Parse categories if provided
        categories = None
        if args.categories:
            from shared_config import parse_category_args
            categories = parse_category_args(args.categories)
        
        # Create configuration with era
        self.config = BackgroundModelConfig(categories=categories, era=args.era)
        
        # Store era for later use
        self.era = args.era
        
        # # Set selected category for fitting
        # if args.category:
        #     self.config.set_category(args.category)
        
        # Apply command line settings
        self.config.use_data = args.data
        self.config.fit_data = args.fit_data  # Control whether to fit data or MinBias
        self.config.use_jpsi = args.use_jpsi
        self.config.use_reduced_mass = args.use_reduced_mass
        self.config.use_binned = args.binned
        self.config.with_systematics = args.withSyst
        self.config.corrected = args.corrected
        self.config.freeze_bkg_sidebands = args.freeze_bkg_sidebands
        self.config.floating_resonant = args.floating_resonant
        self.config.fit_jpsi_first = args.fit_jpsi_first
        self.config.fit_jpsi_prompt = args.fit_jpsi_prompt
        self.config.set_background_function(args.bkg_function)
        self.config.use_reweighting = not args.no_reweighting
        self.config.no_res = args.no_res
        self.config.chosen_fit_region = self.config.get_fit_region(args.fit_region) if args.fit_region else None
        # TODO FIXME: currently it's Background Config blabla that returns dataset path -- that makes no sense, it's DatasetCreator's duty
        
        # Store reweighting setting for dataset creation
        self.use_reweighting = not args.no_reweighting

        # Store fit region
        self.fit_region = args.fit_region

        # Weight multiplier for dataset creation
        self.weight_multiplier = args.weight_multiplier

        # Apply folder tag first (creates subfolder structure)
        # Include era in folder tag for organization
        folder_tag = args.folder_tag
        if folder_tag:
            self.config.apply_folder_tag(folder_tag)

        # sets output tag and creates output folders accordingly
        # Include era in output tag
        tag = args.tag
        if tag:
            self.config.apply_tag(tag)
            
        print(f"Configuration setup complete")
        print(f"Use reweighting: {self.use_reweighting}")
        self.config.print_summary()
    
    def load_cached_datasets(self) -> Dict[str, Any]:
        """Load ONLY datasets from existing file and return them as a dictionary.
        Everything else (templates, normalizations, etc.) will be recreated."""
        print("="*60)
        print("LOADING CACHED DATASETS")
        print("="*60)
        
        try:
            # Use the existing method to get the dataset file path
            dataset_file = self.config.get_dataset_path()
            
            if not dataset_file.exists():
                print(f"❌ Cached dataset file not found: {dataset_file}")
                return None
            
            print(f"📂 Loading datasets from: {dataset_file}")
            
            # Open the cached file
            cached_file = ROOT.TFile.Open(str(dataset_file))
            if not cached_file or cached_file.IsZombie():
                print(f"❌ Cannot open cached dataset file: {dataset_file}")
                return None
            
            cached_workspace = cached_file.Get("w")
            if not cached_workspace:
                print(f"❌ Workspace 'w' not found in cached file")
                cached_file.Close()
                return None
            
            # Extract ONLY the datasets and store them
            categories = self.config.get_available_categories()
            cached_datasets = {}
            
            for category_name, category_config in categories.items():
                # Load main dataset (data if use_data=True, else MinBias)
                dataset_name = f'data_obs{category_config.label}'
                cached_dataset = cached_workspace.data(dataset_name)
                
                if cached_dataset:
                    # Clone the dataset so we can close the file
                    cached_datasets[dataset_name] = cached_dataset.Clone()
                    print(f"  ✅ Cached {dataset_name}: {cached_datasets[dataset_name].numEntries()} entries")
                else:
                    print(f"  ⚠️  Warning: Dataset {dataset_name} not found in cached file")
                
                # If use_data is set, also load the MinBias dataset for background modeling
                if self.config.use_data:
                    minbias_dataset_name = f'data_obs{category_config.label}_minbias'
                    cached_minbias_dataset = cached_workspace.data(minbias_dataset_name)
                    
                    if cached_minbias_dataset:
                        cached_datasets[minbias_dataset_name] = cached_minbias_dataset.Clone()
                        print(f"  ✅ Cached {minbias_dataset_name}: {cached_datasets[minbias_dataset_name].numEntries()} entries")
                    else:
                        print(f"  ⚠️  Warning: MinBias dataset {minbias_dataset_name} not found in cached file")
                
                # Load resonant dataset if it exists
                if self.config.fit_jpsi_prompt:
                    resonant_dataset_name = f'data_obs{category_config.label}_resonant'
                    cached_resonant_dataset = cached_workspace.data(resonant_dataset_name)
                    
                    if cached_resonant_dataset:
                        cached_datasets[resonant_dataset_name] = cached_resonant_dataset.Clone()
                        print(f"  ✅ Cached {resonant_dataset_name}: {cached_datasets[resonant_dataset_name].numEntries()} entries")
                    else:
                        print(f"  ⚠️  Warning: Resonant dataset {resonant_dataset_name} not found in cached file")
            
            # Close the file now that we have cloned the datasets
            cached_file.Close()
            
            print(f"\n✅ Successfully loaded {len(cached_datasets)} datasets from cache")
            return cached_datasets
            
        except Exception as e:
            print(f"❌ Error loading cached datasets: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _save_dataset_file(self):
        """Save the dataset workspace to file using the existing method"""
        dataset_file = self.config.get_dataset_path()
        
        print(f"💾 Saving dataset workspace to: {dataset_file}")
        self.output_workspace.writeToFile(str(dataset_file), True)  # True = recreate file
        print(f"✅ Dataset file saved successfully")
        
    def create_datasets(self, cached_datasets: Dict[str, Any] = None) -> bool:
        """Create datasets for analysis
        
        Args:
            cached_datasets: Optional pre-loaded datasets to use instead of creating from files
        """
        print("="*60)
        print("CREATING DATASETS")
        print("="*60)
        
        try:
            # Get tag from config (now stored directly)
            tag = self.config.tag
            
            # Create main dataset (MinBias/data)
            if cached_datasets is not None:
                print("\n1. Using cached main datasets...")
            else:
                print("\n1. Creating main dataset...")
                
            main_creator = DatasetCreator(
                use_data=self.config.use_data,
                use_jpsi=False,  # Always false for main dataset
                use_reduced_mass=self.config.use_reduced_mass,
                with_systematics=self.config.with_systematics,
                corrected=self.config.corrected,
                categories=self.config.categories,
                output_workspace=self.output_workspace,
                use_reweighting=self.use_reweighting,                
                weight_multiplier=self.weight_multiplier,
                use_binned=self.config.use_binned,
                fit_region=self.config.chosen_fit_region,
                tag=tag,
                cached_datasets=cached_datasets,  # Pass cached datasets if provided
                no_res=self.config.no_res  # Pass no_res flag
            )
            main_dataset_path = main_creator.create_full_dataset()
            
            # Create J/psi dataset if needed
            if self.config.fit_jpsi_prompt:
                if cached_datasets is not None:
                    print("\n2. Using cached J/psi datasets...")
                else:
                    print("\n2. Creating J/psi dataset...")
                    
                jpsi_creator = DatasetCreator(
                    use_data=False,
                    use_jpsi=True,
                    use_reduced_mass=self.config.use_reduced_mass,
                    # with_systematics=False,
                    with_systematics=self.config.with_systematics,
                    corrected=self.config.corrected,
                    categories=self.config.categories,
                    output_workspace=self.output_workspace,
                    use_reweighting=self.use_reweighting,
                    use_binned=self.config.use_binned,
                    fit_region=self.config.chosen_fit_region,
                    tag=tag,
                    cached_datasets=cached_datasets  # Pass cached datasets (includes resonant)
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
        
        # Pass the centralized output workspace to the fitter
        self.fitter = BackgroundFitter(self.config, category=category, 
                                     output_workspace=self.output_workspace)
        
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
            if fit_region_name != "region1" and False:
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
            if fit_region_name == "region1" or True: #FIXME
                # First fit non-resonant background to sidebands within this region
                sideband_results = self.fitter.fit_background_to_sidebands(fit_region)
                
                if self.config.freeze_bkg_sidebands:
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
                
    def create_plots(self, fit_region_name: str, tag: str = "", category: "CategoryConfig" = None) -> List[str]:
        """Create plots for the analysis"""
        print(f"\nCreating plots for {fit_region_name}...")
        
        if not self.plotter:
            # run plotter setup
            self.setup_plotter(category)

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
                
            # Step 4: Create combined model and optionally fit it
            # When --no_res is set, combined model is just the background function (no fitting needed)
            # When normal mode, fit the combined model with resonant components
            if success:
                if self.config.no_res:
                    print("Creating combined model from sideband fit (--no_res set)")
                    # Fit background to sidebands
                    self.background_results = self.fitter.fit_background_to_sidebands(self.config.chosen_fit_region)
                    
                    # Create combined model (just wraps the background function)
                    self.fitter.create_combined_model(self.config.chosen_fit_region)
                    
                    # Create a combined_result from the sideband fit for the chosen background
                    chosen_func = self.config.get_chosen_background_function()
                    if chosen_func.name in self.background_results:
                        import copy
                        # Deep copy the sideband result and just change the name
                        self.combined_result = copy.deepcopy(self.background_results[chosen_func.name])
                        self.combined_result.name = "full_bkg_model"
                    
                    print("Combined model set to background function (no additional fit)")
                else:
                    if not self.fit_combined_background(fit_region_name):
                        print("Failed to fit combined background model")
                        success = False
                    
            # Step 5: Create plots
            if success:
                plots = self.create_plots(fit_region_name, tag, category)
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
        
        # Create centralized output workspace if not already created
        if not self.output_workspace:
            if not self.create_output_workspace(tag, fit_region_name):
                print("❌ Failed to create output workspace")
                return {}
        
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
        
        # Save the centralized workspace containing all category results
        if not self.save_output_workspace():
            print("⚠️  Warning: Failed to save output workspace")
        
        return results

def create_argument_parser():
    """Create command line argument parser"""
    parser = argparse.ArgumentParser(description="Background Model Analysis - Object-oriented version")
    
    # Dataset creation options
    parser.add_argument("--era", default="2023", type=str, help="Data-taking era (default: 2023). Supported values: 2022, 2022EE, 2023, 2023BPix")
    parser.add_argument("--create_datasets", action="store_true", default=False,
                       help="Create datasets from root files")
    parser.add_argument("--cached", action="store_true", default=False,
                       help="Use cached datasets from existing output file if available (still recreates the file with all objects)")
    parser.add_argument("--withSyst", action="store_true", default=False,
                       help="Include systematic variations in dataset creation")
    parser.add_argument("--corrected", action="store_true", default=False,
                       help="Use corrected mass value (electron scale and smearing).")
    parser.add_argument("--use_jpsi", action="store_true", default=False,
                       help="Use J/psi sample instead of MinBias sample")
    parser.add_argument("--use_reduced_mass", action="store_true", default=False,
                       help="Use reduced mass instead of fitted mass")
    parser.add_argument("--no_reweighting", action="store_true", default=False,
                       help="Disable reweighting (set weights to luminosity rescale only)")
    parser.add_argument("--weight_multiplier", type=float, default=1.0,
                       help="Weight multiplier to scale dataset weights (default: 1.0)")
    parser.add_argument('--categories', default = None,
                       help='Specify categories to fit (comma-separated); processes all otherwise.')
    # parser.add_argument('--category', default=None,
    #                    help='Specific category to fit (if not specified, uses all categories)')
    parser.add_argument('--all_categories', action='store_true', default=False,
                       help='Run analysis for all available categories')
    parser.add_argument('--data', action='store_true', default=False,
                       help='Load real data files (in addition to MinBias for dataset creation)')
    parser.add_argument('--fit_data', action='store_true', default=False,
                       help='Use real data for fitting/plotting instead of MinBias (requires --data)')
    
    # Fitting options
    parser.add_argument("--fit_region", default="region1", 
                       choices=["region1", "region0", "region2", "full"],
                       help="Pick fit region")
    parser.add_argument("--bkg_function", default=-1, type=int, choices=[-1, 0, 1, 2, 3, 4, 5, 6, 7, 8],
                       help="Choose background function (0: Bernstein, 1: Poly×Exp, 2: Sum Exp, 3: Simple Exp; 4: Chebyshev, 5: Bernstein + exp, 6: modified BW. -1 for all)")
    parser.add_argument("--input_workspaces", nargs='+', default=[],
                       help="Input workspace files for envelope (only works with bkg_function=-1)")
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
    parser.add_argument("--no_res", action="store_true", default=False,
                       help="Exclude resonant regions from fit (use only sidebands)")
    
    # Output options
    parser.add_argument("--tag", default="", help="Tag for output files")
    parser.add_argument("--folder_tag", default="", help="Subfolder tag for organizing outputs")
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
        
        # Validate arguments
        if args.fit_data and not args.data:
            print("❌ Error: --fit_data requires --data to be set")
            print("   (You need to load data files before you can fit them)")
            return 1
        
        print("DEBUG: SETTING ANALYZER", flush=True)
        analysis.setup_from_args(args)
        
        success = True
        
        print("DEBUG: SETTING ANALYZER COMPLETED", flush=True)

        if args.bkg_function < 0:
            # TEMPORARY: only works for inclusive category for now
            if args.categories != "inclusive":
                print("❌ Background function envelope (-1) currently only supported for 'inclusive' category")
                return 1

            # check that input workspaces are provided
            if not args.input_workspaces:
                print("❌ When using bkg_function=-1 (all), you must provide input workspaces for the envelope using --input_workspaces")
                return 1
            else:
                print(f"✅ Using {len(args.input_workspaces)} input workspaces for background function envelope")

                if not analysis.create_envelope_workspace(args.input_workspaces):
                    print("❌ Failed to create envelope workspace")
                    return 1

                if not analysis.save_output_workspace():
                    print("⚠️  Warning: Failed to save output workspace")
                    return
                
                print(f"✅ SUCCESS: created and saved envelope workspace.")
                return True
        
        # Create output workspace if we need to do dataset creation or full analysis
        if args.create_datasets or args.full_analysis or args.cached:
            if not analysis.create_output_workspace(args.tag, args.fit_region):
                print("❌ Failed to create output workspace")
                return 1
        
        # Step 1: Create or load cached datasets
        if args.create_datasets or args.full_analysis:
            if args.cached:
                # Try to load cached datasets first
                print("🔄 Attempting to use cached datasets...")
                cached_datasets = analysis.load_cached_datasets()
                
                if cached_datasets is None:
                    print("⚠️  Cached datasets not available, creating from scratch...")
                    if not analysis.create_datasets():
                        print("Dataset creation failed!")
                        return 1
                else:
                    print("✅ Using cached datasets")
                    # Pass cached datasets to create_datasets - it will handle everything
                    if not analysis.create_datasets(cached_datasets=cached_datasets):
                        print("Dataset recreation with cached data failed!")
                        return 1
            else:
                # Create datasets from scratch
                if not analysis.create_datasets():
                    print("Dataset creation failed!")
                    return 1
        
        print("DEBUG: dataset created successfully. Moving onto fit.", flush=True)
        # Step 2: Run fitting analysis
        if args.fit_only or args.full_analysis:# or (not args.create_datasets): # why was create_dataset here in the first place?
            # Determine analysis strategy based on category selection
            if args.all_categories or (not args.categories and not args.all_categories):
                # Multi-category analysis (default if no specific category chosen)
                print("Running analysis for all categories...")
                results = analysis.run_analysis_for_all_categories(args.fit_region, args.tag)
                success = any(results.values())  # Success if at least one category succeeds
            elif args.categories:
                # Single category analysis
                print(f"Running analysis for categories '{args.categories}'...")
                categories = analysis.config.get_available_categories()
                arg_categories = args.categories.split(',')
                for cat in arg_categories:
                    if cat in categories:
                        # Create output workspace for single category if not already created
                        if not analysis.output_workspace:
                            if not analysis.create_output_workspace(args.tag):
                                print("❌ Failed to create output workspace")
                                return 1
                        
                        category_config = categories[cat]
                        success = analysis.run_complete_analysis(args.fit_region, args.tag, category_config)
                        
                        # Save workspace
                        if not analysis.save_output_workspace():
                            print("⚠️  Warning: Failed to save output workspace")
                    else:
                        print(f"❌ Category '{cat}' not found. Available: {list(categories.keys())}")
                        return 1
            else:
                # Fallback to old behavior (no category specified)
                # Create output workspace for single category if not already created
                if not analysis.output_workspace:
                    if not analysis.create_output_workspace(args.tag):
                        print("❌ Failed to create output workspace")
                        return 1
                    print("❌ Failed to create output workspace")
                    return 1
                
                success = analysis.run_complete_analysis(args.fit_region, args.tag)
                
                # Save workspace
                if not analysis.save_output_workspace():
                    print("⚠️  Warning: Failed to save output workspace")
        
        # Step 3: Optional multi-category plotting
        if args.plot_all_categories:
            print("\nCreating plots for all categories...")
            categories = analysis.config.get_available_categories()
            for category_config in categories.values():
                plots = analysis.create_plots(args.fit_region, args.tag, category_config)
                print(f"📊 Created {len(plots)} plots for category {cat}")
                    
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
