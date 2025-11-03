import ROOT
import os
import numpy as np
from scipy.optimize import curve_fit
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import argparse

# Import the utilities
import sys
sys.path.append('utilities')
# from utilities.get_signal_effs_xsecs import effs, effs_err, xsecs, xsecs_err
from utilities.get_signal_effs_xsecs import fit_effs, fit_xsecs

# Import shared configuration
from shared_config import CategoryConfig, get_default_categories
from background_config import FitRegion


class DatasetCreator:
    """This module handles the creation of RooDatasets from root files,
    importing resonant background templates, and interpolating cross-sections and efficiencies."""

    def __init__(self, use_jpsi: bool = False, use_reduced_mass: bool = False,
                 categories: Dict[str, CategoryConfig] = None,
                 fit_region: FitRegion = None,
                 output_workspace: "ROOT.RooWorkspace" = None, use_reweighting: bool = True,
                 use_binned: bool = False, weight_multiplier: float = 1.0,
                 tag: str = ""):

        self.use_jpsi = use_jpsi
        self.use_reduced_mass = use_reduced_mass
        self.use_reweighting = use_reweighting
        self.use_binned = use_binned
        self.fit_region = fit_region
        print(f"DEBUG REMOVEME: fit_region = {fit_region}")
        self.tag = tag
        
        # Category definitions (use shared configuration)
        if categories is None:
            self.categories = get_default_categories()
        else:
            self.categories = categories
        
        # Extract category names for convenience
        self.category_names = list(self.categories.keys())
            
        print(f"Categories: {self.category_names}")
        for name, cat_config in self.categories.items():
            print(f"  {name}: {cat_config.cuts}")
        
        # Use shared workspace or create new one
        if output_workspace is not None:
            self.workspace = output_workspace
            self._using_shared_workspace = True
            print("Using shared output workspace from main analysis")
        else:
            # Create single workspace (like signal modeling) - fallback for standalone usage
            self.workspace = ROOT.RooWorkspace('w')
            self._using_shared_workspace = False
            print("Creating new workspace for standalone usage")

        # Set file paths based on sample type
        if use_jpsi:
            self.filepath = fit_region.background_resonant_data
        else:
            self.filepath = '/eos/home-n/npalmeri/www/DiElectron/PS_reweighting/fw_output_actualReweight/zsnap/era2023/'

        if use_reweighting:
            self.filepath += 'base_8_TriggerPSReweight/'
        else:
            self.filepath += 'base_7_ID/'

        self.weight_multiplier = weight_multiplier
            
        # Output settings
        self.output_dir = Path("datasets")
        self.output_dir.mkdir(exist_ok=True)
        
        # Resonant background workspace settings
        suffix = "" if not use_reduced_mass else "_reducedMass"
        # TODO FIXME: all file names are hardcoded. Write them in common config file.
        if self.use_reweighting:
            self.signal_ws_file = f'../signal_modelling/workspaces/signal_model_withReweight_Categories{suffix}.root'
        else:
            self.signal_ws_file = f'../signal_modelling/workspaces/signal_model_no_reweight{suffix}.root'
        
        # Luminosity and cross-section data
        self.luminosity = 7.98 * 1e3  # pb-1
        self.lumi_rescale = 58.9/7.98  # 22+23 lumi rescale wrt processed
        
        print(f"Dataset creator initialized:")
        print(f"  Sample type: {'J/psi' if use_jpsi else 'MinBias'}")
        print(f"  Mass type: {'Reduced' if use_reduced_mass else 'Fitted'}")
        print(f"  Use reweighting: {use_reweighting}")
        print(f"  Use binned: {use_binned}")
        print(f"  Tag: {tag if tag else '(none)'}")
        print(f"  Input path: {self.filepath}")
        print(f"  Signal workspace: {self.signal_ws_file}")
        
    def set_reweighting(self, use_reweighting: bool):
        """Update the reweighting flag"""
        self.use_reweighting = use_reweighting
        print(f"Updated reweighting setting: {use_reweighting}")
        
    def setup_mass_variable(self) -> ROOT.RooRealVar:
        """Setup the shared mass variable from signal workspace"""
        print("Setting up shared mass variable...")
        
        # Check if mass variable already exists in workspace (from main analysis)
        existing_mass_var = self.workspace.var("mass")
        if existing_mass_var:
            print("  Using existing mass variable from shared workspace")
            return existing_mass_var
        
        # Open signal workspace to get mass variable definition
        if not os.path.exists(self.signal_ws_file):
            raise FileNotFoundError(f"Signal workspace not found: {self.signal_ws_file}")
            
        signal_file = ROOT.TFile.Open(self.signal_ws_file)
        signal_ws = signal_file.Get('w')
        
        if not signal_ws:
            raise ValueError(f"Workspace 'w' not found in {self.signal_ws_file}")
        
        # Get mass variable and setup for background analysis (following create_dataset.py pattern)
        m = signal_ws.var("mass_test")
        if not m:
            signal_file.Close()
            raise ValueError("Variable 'mass_test' not found in resonant background workspace")
            
        # Set up mass variable like in create_dataset.py
        m.SetName("mass")
        if self.fit_region:
            m.setMin(self.fit_region.range[0])
            m.setMax(self.fit_region.range[1])
        else:
            print(f"  No fit region specified, using full range from signal workspace")
        
        # Import to workspace (single shared variable)
        self.workspace.Import(m, ROOT.RooCmdArg())
        mass_var_final = self.workspace.var("mass")
        
        signal_file.Close()
        print(f"  Mass variable setup: range [{mass_var_final.getMin()}, {mass_var_final.getMax()}] GeV")
        
        return mass_var_final
    
    def _check_category_conditions(self, category: CategoryConfig, cat_vars: Dict, j: int) -> bool:
        """Check if event passes category selection"""
        for var, ranges in category.cuts.items():
            if var in cat_vars:
                cat_var_value = cat_vars[var][j] if hasattr(cat_vars[var], '__len__') else cat_vars[var]
                range_check = any(
                    r[0] <= cat_var_value <= r[1] for r in ranges
                )
                if not range_check:
                    return False
        return True
        
    def create_dataset_from_files(self, mass_var: ROOT.RooRealVar) -> Dict[str, Any]:
        """Create RooDataSet from root files for each category using shared mass variable"""
        print("Creating datasets from files for all categories...")
        
        mass_var.setBins(100)  # Set binning if needed # USELESS, VAR IS NOT SAVED AGAIN

        # Create datasets for each category (using signal modeling naming convention)
        datasets = {}
        for category_name, category_config in self.categories.items():
            # Dataset name with category label (like signal modeling)
            dataset_name = f'data_obs{category_config.label}{"_resonant" if self.use_jpsi else ""}'
            
            # Setup dataset arguments using shared mass variable
            dataset_args = [ROOT.RooArgSet(mass_var)]
            
            # Add weight variable if dataset not binned
            if not self.use_binned:
                weight_var_name = f"weight{category_config.label}"
                weight_var = ROOT.RooRealVar(weight_var_name, weight_var_name, 1)
                self.workspace.Import(weight_var, ROOT.RooCmdArg())
                dataset_args.append(ROOT.RooFit.WeightVar(weight_var))
                
            # Create dataset
            if self.use_binned:
                datasets[category_name] = ROOT.RooDataHist(dataset_name, dataset_name, *dataset_args)
            else:
                datasets[category_name] = ROOT.RooDataSet(dataset_name, dataset_name, *dataset_args)
        
        # Process files
        n_files = 0
        category_events = {cat: 0 for cat in self.category_names}
        
        for filename in os.listdir(self.filepath):
            if not filename.endswith('.root') or "DoubleElectronNANO" in filename:
                continue
                
            print(f"  Processing: {filename}")
            file_path = os.path.join(self.filepath, filename)
            
            try:
                root_file = ROOT.TFile.Open(file_path)
                if not root_file or root_file.IsZombie():
                    print(f"    Warning: Cannot open {filename}")
                    continue
                    
                tree = root_file.Get('Events')
                if not tree:
                    print(f"    Warning: No 'Events' tree in {filename}")
                    root_file.Close()
                    continue

                for branch in tree.GetListOfBranches():
                    print(f"  {branch.GetName()}", flush=True)

                # Process entries
                file_events = {cat: 0 for cat in self.category_names}
                for i in range(tree.GetEntries()):
                    tree.GetEntry(i)

                    # Calculate weight
                    weight = tree.weight * self.lumi_rescale * self.weight_multiplier #NOTE: weight includes lumi [7.98/fb] * xsec * filter eff. for minbias; depending on file, trigger PS is also there.
                    
                    # Get category variables for this event
                    cat_vars = {}
                    for category_name, category_config in self.categories.items():
                        for var_name in category_config.cuts.keys():
                            if not hasattr(tree, var_name):
                                raise ValueError(f"Variable '{var_name}' not found in tree. Rerun flow and save it.")
                            if var_name not in cat_vars:
                                cat_vars[var_name] = getattr(tree, var_name)

                    # Check category cuts for each dielectron pair
                    for j, mass_val in enumerate(tree.DiElectron_fitted_mass):
                        # Determine which categories this event belongs to
                        event_categories = []
                        for category_name, category_config in self.categories.items():
                            if self._check_category_conditions(category_config, cat_vars, j):
                                event_categories.append(category_name)
                        
                        # Add to appropriate datasets using shared mass variable
                        for category_name in event_categories:
                            mass_var.setVal(mass_val)
                            if self.fit_region:
                                if mass_val < self.fit_region.range[0] or mass_val > self.fit_region.range[1]:
                                    continue
                            datasets[category_name].add(ROOT.RooArgSet(mass_var), weight)
                            file_events[category_name] += 1
                        
                for cat in self.category_names:
                    category_events[cat] += file_events[cat]
                    
                n_files += 1
                print(f"    Added events: {', '.join([f'{cat}={file_events[cat]}' for cat in self.category_names])}")
                
                root_file.Close()
                
            except Exception as e:
                print(f"    Error processing {filename}: {e}")
                continue
                
        print(f"Dataset creation complete:")
        print(f"  Files processed: {n_files}")
        for category_name in self.category_names:
            print(f"  {category_name}: {category_events[category_name]} events, {datasets[category_name].numEntries()} dataset entries")
        
        return datasets
        
    def import_resonant_background_templates(self) -> Dict[str, List[str]]:
        """Import all resonant background templates from workspace for each category"""
        print("Importing resonant background templates for all categories...")
        
        # Open resonant background workspace
        signal_file = ROOT.TFile.Open(self.signal_ws_file)
        print("DEBUG: signal file = ", signal_file)
        signal_ws = signal_file.Get('w')
        
        imported_models = {cat: [] for cat in self.category_names}
        
        # Import models for each category
        for category_name, category_config in self.categories.items():
            print(f"  Importing for category: {category_name}")
            
            # Find all models for this category (using category.label)
            for model in signal_ws.allGenericObjects():
                model_name = model.GetName()
                if model_name.startswith(f'model_test_M') and category_config.is_object_in_category(model_name):
                    # Create new name: model_test_cat_central_M3p1 -> Zd_cat_central_M3.1
                    mass_part = model_name.split("_M")[1].split("_cat")[0].replace("p", ".")
                    new_name = f'Zd_M{mass_part}{category_config.label}'
                    
                    # Import with new name to single workspace
                    self.workspace.Import(model, ROOT.RooFit.RenameVariable(model_name, new_name))
                    imported_models[category_name].append(mass_part)
                    print(f"    Imported: {model_name} -> {new_name}")
                    
        signal_file.Close()
        
        # Remove duplicates and sort
        for category_name in self.category_names:
            imported_models[category_name] = sorted(list(set(imported_models[category_name])), key=float)
            print(f"  {category_name}: {len(imported_models[category_name])} templates")
        
        return imported_models
        
    def interpolate_efficiencies_xsecs(self, imported_models: Dict[str, List[str]], datasets: Dict[str, ROOT.RooDataSet]):
        """Interpolate and store efficiencies and cross-sections for each category"""
        print("Interpolating efficiencies and cross-sections for all categories...")

        print(f"DEBUG: interpolating xsec, effs for fit region {self.fit_region} (name: {self.fit_region.name if self.fit_region else 'none'})")
        
        eff_fit_func, eff_fit_params = fit_effs(use_old=False, 
                                                use_crystalball = (self.fit_region.name == "region2")).values()
        xsec_fit_func, xsec_fit_params = fit_xsecs(use_old=False).values()

        # # Mass points for interpolation
        # mass_points = np.array([1, 3.1, 5, 5.5, 6, 6.5])
        
        # # Fit efficiency with polynomial
        # try:
        #     popt_eff, _ = curve_fit(
        #         lambda x, a, b, c, d: np.polyval((a, b, c, d), x), 
        #         mass_points, effs, 
        #         sigma=effs_err, 
        #         absolute_sigma=True
        #     )
        #     print(f"  Efficiency fit coefficients: {popt_eff}")
            
        # except Exception as e:
        #     print(f"  Warning: Efficiency fit failed: {e}")
        #     # Use simple interpolation as fallback
        #     popt_eff = np.polyfit(mass_points, effs, 3)
            
        # # Fit cross-section with polynomial
        # try:
        #     popt_xsec, _ = curve_fit(
        #         lambda x, a, b, c, d, e: np.polyval((a, b, c, d, e), x), 
        #         mass_points, xsecs, 
        #         sigma=xsecs_err, 
        #         absolute_sigma=True
        #     )
        #     print(f"  Cross-section fit coefficients: {popt_xsec}")
            
        # except Exception as e:
        #     print(f"  Warning: Cross-section fit failed: {e}")
        #     # Use simple interpolation as fallback
        #     popt_xsec = np.polyfit(mass_points, xsecs, 4)
            
        # Calculate category fractions from inclusive dataset
        inclusive_events = datasets["inclusive"].sumEntries() if "inclusive" in datasets else 1.0
        category_fractions = {}
        for category_name in self.category_names:
            if category_name == "inclusive":
                category_fractions[category_name] = 1.0
            else:
                category_fractions[category_name] = datasets[category_name].sumEntries() / inclusive_events
        
        print("Category fractions:")
        for cat, frac in category_fractions.items():
            print(f"  {cat}: {frac:.4f}")
            
        # Create variables for each mass point and category
        for category_name, category_config in self.categories.items():
            masses = imported_models.get(category_name, [])
            print(f"DEBUG: interpolating for {category_name} masses: {masses}")
            
            for mass_str in masses:
                mass_val = float(mass_str)
                
                # Calculate expected signal events
                efficiency = eff_fit_func(mass_val, *eff_fit_params)
                cross_section = xsec_fit_func(mass_val, *xsec_fit_params)

                print(f"DEBUG: efficiency for M={mass_val} GeV: {efficiency}, cross-section: {cross_section} pb", flush=True)

                # efficiency = np.polyval(popt_eff, mass_val)
                # cross_section = np.polyval(popt_xsec, mass_val)

                n_expected_total = self.luminosity * efficiency * cross_section
                n_expected = n_expected_total * category_fractions[category_name]
                
                print(f"  {category_name} M={mass_val} GeV: eff={efficiency:.4f}, xsec={cross_section:.3f} pb, frac={category_fractions[category_name]:.4f}, N_exp={n_expected:.1f}", flush=True)
                
                # Create RooRealVar for expected events (using category label)
                norm_var = ROOT.RooRealVar(f'Zd{category_config.label}_M{mass_str}_expected', f'Zd{category_config.label}_M{mass_str}_expected', n_expected)
                self.workspace.Import(norm_var, ROOT.RooCmdArg())
                
                # Also save efficiency, cross-section, and fraction separately
                eff_var = ROOT.RooRealVar(f'Zd{category_config.label}_M{mass_str}_efficiency', f'Zd{category_config.label}_M{mass_str}_efficiency', efficiency)
                eff_var.setConstant(True)
                self.workspace.Import(eff_var, ROOT.RooCmdArg())

                xsec_var = ROOT.RooRealVar(f'Zd{category_config.label}_M{mass_str}_xsec', f'Zd{category_config.label}_M{mass_str}_xsec', cross_section)
                xsec_var.setConstant(True)
                self.workspace.Import(xsec_var, ROOT.RooCmdArg())
                
                frac_var = ROOT.RooRealVar(f'Zd{category_config.label}_M{mass_str}_fraction', f'Zd{category_config.label}_M{mass_str}_fraction', category_fractions[category_name])
                frac_var.setConstant(True)
                self.workspace.Import(frac_var, ROOT.RooCmdArg())
            
    def add_resonant_normalizations(self, datasets: Dict[str, ROOT.RooDataSet]):
        """Add normalization variables for resonant backgrounds (J/psi, psi2s) for each category"""
        print("Adding resonant background normalizations for all categories...")
        
        # Calculate inclusive J/psi expected events
        n_jpsi_exp_total = self.luminosity  # pb-1
        n_jpsi_exp_total *= 5.352e5  # xsec * filter eff (/pb)
        n_jpsi_exp_total *= 5.971/100  # branching ratio Jpsi -> ee
        # TODO FIXME: retrieve efficiency dynamically from csv in input fw output folder
        n_jpsi_exp_total *= 0.677/100  # analyzer selection efficiency
        
        # Calculate category fractions
        inclusive_events = datasets["inclusive"].sumEntries() if "inclusive" in datasets else 1.0
        
        for category_name, category_config in self.categories.items():
            if category_name == "inclusive":
                category_fraction = 1.0
            else:
                category_fraction = datasets[category_name].sumEntries() / inclusive_events
                
            n_jpsi_exp = n_jpsi_exp_total * category_fraction
            
            # J/psi expected events (using category label)
            norm_jpsi = ROOT.RooRealVar(f"jpsi{category_config.label}_expected", f"jpsi{category_config.label}_expected", n_jpsi_exp)
            self.workspace.Import(norm_jpsi, ROOT.RooCmdArg())
            
            # psi(2S) expected events (can be rescaled later)
            norm_psi2s = ROOT.RooRealVar(f"psi2s{category_config.label}_expected", f"psi2s{category_config.label}_expected", n_jpsi_exp)
            self.workspace.Import(norm_psi2s, ROOT.RooCmdArg())
            
            print(f"  {category_name}: J/psi expected: {n_jpsi_exp:.1f}, psi(2S) expected: {n_jpsi_exp:.1f}")
        
    def add_data_normalization(self, datasets: Dict[str, ROOT.RooDataSet]):
        """Add normalization for the data for each category"""
        print("Adding data normalization for all categories...")
        
        for category_name, category_config in self.categories.items():
            # Get total data events for this category
            n_data = datasets[category_name].sumEntries()
            data_norm = ROOT.RooRealVar(f'data_obs{category_config.label}_expected', f'data_obs{category_config.label}_expected', n_data)
            self.workspace.Import(data_norm, ROOT.RooCmdArg())
            
            print(f"  {category_name}: {n_data:.1f} events")
        
    def create_full_dataset(self) -> str:
        """Main method to create the complete dataset for all categories"""
        print("="*60)
        print("CREATING DATASETS FOR ALL CATEGORIES")
        print("="*60)
        
        # Setup mass variable (single shared variable)
        mass_var = self.setup_mass_variable()
        
        # Create datasets from files
        datasets = self.create_dataset_from_files(mass_var)
        
        print("DEBUG: datasets created. Applying cuts to mass", flush=True)
        
        # Apply mass cuts and import datasets to single workspace
        for category_name, category_config in self.categories.items():
            # Apply mass cuts
            if self.fit_region:
                print(f"  Applying mass cut for {category_name}: {self.fit_region.range[0]} < mass < {self.fit_region.range[1]}", flush=True)
                datasets[category_name] = datasets[category_name].reduce(ROOT.RooFit.Cut(f"mass > {self.fit_region.range[0]} && mass < {self.fit_region.range[1]}"))
            
            # Import dataset to single workspace (datasets already have correct names with category labels)
            self.workspace.Import(datasets[category_name], ROOT.RooCmdArg())
        
        # Import resonant background templates
        imported_models = self.import_resonant_background_templates()

        # Interpolate efficiencies and cross-sections
        if any(imported_models.values()):
            self.interpolate_efficiencies_xsecs(imported_models, datasets)
            
        # Add resonant background normalizations
        self.add_resonant_normalizations(datasets)

        # Add data normalization
        self.add_data_normalization(datasets)
        
        # Save workspace
        output_file = None
        if not hasattr(self, '_using_shared_workspace') or not self._using_shared_workspace or self.use_jpsi:
            sample_suffix = "_jpsi" if self.use_jpsi else "_minbias"
            mass_suffix = "_reducedMass" if self.use_reduced_mass else ""
            binning_suffix = "_binned" if self.use_binned else ""            
            reweight_suffix = "_reweight" if self.use_reweighting else "_noReweight"
            tag_suffix = f"_{self.tag}" if self.tag else ""
            
            output_file = self.output_dir / f"dataset{sample_suffix}{mass_suffix}{binning_suffix}{reweight_suffix}{tag_suffix}.root"
            self.workspace.writeToFile(str(output_file))
            print(f"Dataset workspace saved to: {output_file}")
        else:
            print("Dataset added to shared workspace (no separate file created)")
        
        print("="*60)
        print(f"DATASET CREATION COMPLETE")
        if output_file:
            print(f"Output file: {output_file}")
        else:
            print("Objects added to shared workspace")
        for category_name in self.category_names:
            n_entries = datasets[category_name].numEntries()
            n_models = len(imported_models.get(category_name, []))
            mass_range = f"[{imported_models[category_name][0]}, {imported_models[category_name][-1]}]" if imported_models.get(category_name) else "[]"
            print(f"  {category_name}: {n_entries} entries, {n_models} models {mass_range} GeV")
        print("="*60)
        
        return str(output_file) if output_file else "shared_workspace"


def main():
    """Main function for command line usage"""
    parser = argparse.ArgumentParser(description='Create dataset for background modeling')
    parser.add_argument('--use_jpsi', action='store_true', default=False,
                       help='Use J/psi sample instead of MinBias sample')
    parser.add_argument('--use_reduced_mass', action='store_true', default=False,
                       help='Use reduced mass instead of fitted mass')
    parser.add_argument('--binned', action='store_true', default=False,
                       help='Use binned data (RooDataHist) instead of unbinned (RooDataSet)')
    parser.add_argument('--no_reweighting', action='store_true', default=False,
                       help='Disable reweighting (set weights to luminosity rescale only)')
    parser.add_argument('--tag', type=str, default="",
                       help='Tag to append to output files')
    parser.add_argument('--categories', nargs='+', default=None,
                       help='Categories to create (specify as key=value pairs, e.g. central="pt_1>20&&pt_2>20")')
    
    args = parser.parse_args()
    
    # Parse categories if provided
    categories = None
    if args.categories:
        from shared_config import parse_category_args
        categories = parse_category_args(args.categories)
    
    try:
        # Create dataset creator
        use_reweighting = not args.no_reweighting
        creator = DatasetCreator(
            use_jpsi=args.use_jpsi,
            use_reduced_mass=args.use_reduced_mass,
            categories=categories,
            use_reweighting=use_reweighting,
            use_binned=args.binned,
            tag=args.tag
        )
        
        # Create datasets
        output_file = creator.create_full_dataset()
        
        print(f"\n✅ Dataset creation successful!")
        print(f"Output file: {output_file}")
        
    except Exception as e:
        print(f"\n❌ Dataset creation failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
        
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
