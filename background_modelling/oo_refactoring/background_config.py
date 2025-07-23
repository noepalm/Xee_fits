"""
Background modeling configuration - Object-oriented approach

This module defines the configuration classes for background modeling,
including fit regions, background functions, and analysis parameters.
"""
import ROOT
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from pathlib import Path

# Import shared configuration
from shared_config import CategoryConfig, get_default_categories


@dataclass
class FitRegion:
    """Configuration for a fit region"""
    name: str
    display_name: str
    range: Tuple[float, float]  # (min, max) in GeV
    sidebands: List[Tuple[float, float]]  # List of sideband regions
    description: str = ""
    
    def __post_init__(self):
        """Validate the region configuration"""
        if self.range[0] >= self.range[1]:
            raise ValueError(f"Invalid range for {self.name}: {self.range}")
        for sb in self.sidebands:
            if sb[0] >= sb[1]:
                raise ValueError(f"Invalid sideband for {self.name}: {sb}")


@dataclass 
class BackgroundFunction:
    """Configuration for a background function"""
    name: str
    display_name: str
    formula: str
    n_params: int
    param_names: List[str]
    param_inits: List[float]
    param_limits: List[Tuple[float, float]]
    description: str = ""
    
    def validate(self):
        """Validate function configuration"""
        if len(self.param_names) != self.n_params:
            raise ValueError(f"Mismatch in parameter count for {self.name}")
        if len(self.param_inits) != self.n_params:
            raise ValueError(f"Mismatch in initial values for {self.name}")
        if len(self.param_limits) != self.n_params:
            raise ValueError(f"Mismatch in parameter limits for {self.name}")


class BackgroundModelConfig:
    """Main configuration class for background modeling"""
    
    def __init__(self, categories: Dict[str, CategoryConfig] = None):
        # Category settings (use shared configuration)
        if categories is None:
            self.categories = get_default_categories()
        else:
            self.categories = categories
            
        # Extract category names for convenience
        self.category_names = list(self.categories.keys())
            
        print(f"Background configuration for categories: {self.category_names}")
        for name, cat_config in self.categories.items():
            print(f"  {name}: {cat_config.cuts}")
        
        # Selected category for fitting (default to inclusive)
        self.selected_category = "inclusive"
        
        # I/O settings
        self.output_dir = Path("/eos/home-n/npalmeri/www/DiElectron/background_model/fit_tests_reweight_NEW")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # make sure output sub-directories exist
        for cat in [cat.name for cat in self.categories.values()]:
            print(f"DEBUG: Creating output directory {(self.output_dir / cat)}", flush=True)
            (self.output_dir / cat).mkdir(parents=True, exist_ok=True)
        
        # Dataset settings
        self.use_jpsi = False
        self.use_reduced_mass = False
        self.use_binned = False
        
        # Fit settings
        self.freeze_bkg_sidebands = False
        self.floating_resonant = False
        self.fit_jpsi_first = False
        self.fit_jpsi_prompt = False
        self.chosen_bkg_function = 0  # Index of background function to use
        
        # Define fit regions
        self.fit_regions = self._define_fit_regions()
        
        # Define background functions (per category)
        self.background_functions = self._define_background_functions()
        
        # Resonant background settings (per category)
        self.resonant_models = self._define_resonant_models()
        
        # Normalization settings (per category)
        self.normalization_settings = self._define_normalization_settings()
        
        print("Background model configuration initialized")
        
    def _define_fit_regions(self) -> Dict[str, FitRegion]:
        """Define the available fit regions"""
        regions = {
            "region1": FitRegion(
                name="region1",
                display_name="Central Region (2.0-4.2 GeV)",
                range=(2.0, 4.2),
                sidebands=[
                    (2.0, 2.6),    # Left sideband
                    (3.3, 3.5),    # Central sideband  
                    (3.8, 4.2)     # Right sideband
                ],
                description="Main analysis region containing J/psi and psi(2S)"
            ),
            "region0": FitRegion(
                name="region0",
                display_name="Left Background Region (1.2-2.6 GeV)",
                range=(1.2, 2.6),
                sidebands=[(1.2, 2.6)],  # Entire region is sideband
                description="Low mass background region"
            ),
            "region2": FitRegion(
                name="region2", 
                display_name="Right Background Region (4.2-8.0 GeV)",
                range=(4.2, 8.0),
                sidebands=[(4.2, 8.0)],  # Entire region is sideband
                description="High mass background region"
            ),
            "full": FitRegion(
                name="full",
                display_name="Full Range (1.2-8.0 GeV)",
                range=(1.2, 8.0),
                sidebands=[
                    (1.2, 2.6),
                    (4.2, 8.0)
                ],
                description="Complete mass range"
            )
        }
        
        # Also define special sub-regions for peak fits
        regions.update({
            "jpsi": FitRegion(
                name="jpsi",
                display_name="J/psi Region (3.05-3.12 GeV)",
                range=(3.05, 3.12),
                sidebands=[],
                description="J/psi peak region"
            ),
            "psi2s": FitRegion(
                name="psi2s",
                display_name="psi(2S) Region (3.6-3.8 GeV)",
                range=(3.6, 3.8),
                sidebands=[],
                description="psi(2S) peak region"
            )
        })
        
        return regions
        
    def _define_background_functions(self) -> List[BackgroundFunction]:
        """Define available background functions with category-specific initial parameters"""
        functions = []
        
        # Define initial parameters per category
        # Default values are for 'inclusive' category and used for all others unless overridden
        bernstein_inits_by_category = {
            "inclusive": [1.7, 1.9, -0.06610, 0.52400, 0.19075],  # WORKS FOR EVERYTHING BUT etap0p6
            # Add category-specific overrides here as needed:
            # "etap0p6": [2.33352, 3.59166, -0.06610, 0.52400, 0.19075],  # WORKS FOR dRp0p3
            # "dRm0p3": [0.36903, 0.11880, -0.46547, 0.56438, -0.58503],  # WORKS FOR dRm0p3
            "etaHigh" : [2.33352, 3.59166, -0.06610, 0.52400, 0.19075],
        }

        bernstein_limits_by_category = {
            # Add category-specific overrides here as needed
            "inclusive": [(-2, 2) for _ in range(5)],  # Default limits for all #FIXME: was (-5, 5) for all
            "etaHigh" : [(-5, 5) for _ in range(5)],
        }
        
        poly_inits_by_category = {
            "inclusive": [-0.9, 3.2, -1.4, 0.16, 0],
            # Add category-specific overrides here as needed
        }
        
        exp_inits_by_category = {
            "inclusive": [1, 4, 0.1, -1] + [1./4 * (-1 * (i % 2)) for i in range(3)],
            # Add category-specific overrides here as needed
        }
        
        simple_exp_inits_by_category = {
            "inclusive": [-1.5],
            # Add category-specific overrides here as needed
        }
        
        # Get initial parameters for the current category (fall back to inclusive if not specified)
        current_category = getattr(self, 'selected_category', 'inclusive')
        print(f"DEBUG: trying to retrieve selceted cateogyr: {self.selected_category}", flush=True)
        
        print(f"DEBUG: Using category '{current_category}' for background functions", flush=True)
        bernstein_inits = bernstein_inits_by_category.get(current_category, 
                                                         bernstein_inits_by_category["inclusive"])
        bernstein_limits = bernstein_limits_by_category.get(current_category, 
                                                           bernstein_limits_by_category["inclusive"])
        poly_inits = poly_inits_by_category.get(current_category,
                                               poly_inits_by_category["inclusive"])
        exp_inits = exp_inits_by_category.get(current_category,
                                             exp_inits_by_category["inclusive"])
        simple_exp_inits = simple_exp_inits_by_category.get(current_category,
                                                           simple_exp_inits_by_category["inclusive"])

        # Bernstein polynomial (5th degree)
        functions.append(BackgroundFunction(
            name="bkg_f0",
            display_name="Bernstein Polynomial",
            formula="Bernstein polynomial of degree 5",
            n_params=5,
            param_names=[f"a{i}" for i in range(5)],
            param_inits=bernstein_inits,
            param_limits=bernstein_limits,
            description="5th degree Bernstein polynomial"
        ))
        
        # Polynomial × Exponential (4th degree polynomial)
        functions.append(BackgroundFunction(
            name="bkg_f1", 
            display_name="Polynomial × Exponential",
            formula="(1 + a0*x + a1*x^2 + a2*x^3 + a3*x^4) * exp(b0*x)",
            n_params=5,  # 4 polynomial + 1 exponential
            param_names=[f"b{i}" for i in range(4)] + ["bb0"],
            param_inits=poly_inits,
            param_limits=[(-5, 5) for _ in range(4)] + [(-10, 10)],
            description="4th degree polynomial times exponential"
        ))
        
        # Sum of exponentials
        functions.append(BackgroundFunction(
            name="bkg_f2",
            display_name="Sum of Exponentials", 
            formula="Sum of 4 exponential functions",
            n_params=7,  # 4 exponential slopes + 3 coefficients
            param_names=[f"c{i}" for i in range(4)] + [f"cc{i}" for i in range(3)],
            param_inits=exp_inits,
            param_limits=[(-10, 10) for _ in range(4)] + [(-1, 1) for _ in range(3)],
            description="Sum of 4 exponential functions"
        ))
        
        # Simple exponential
        functions.append(BackgroundFunction(
            name="bkg_f3",
            display_name="Simple Exponential",
            formula="exp(alpha * x)",
            n_params=1,
            param_names=["alpha"],
            param_inits=simple_exp_inits,
            param_limits=[(-10, 10)],
            description="Single exponential function"
        ))
        
        # Validate all functions
        for func in functions:
            func.validate()
            
        return functions
        
    def _define_resonant_models(self) -> Dict[str, Dict[str, Any]]:
        """Define resonant background models (J/psi, psi2s)"""
        models = {
            "jpsi": {
                "resonant_bkg_template_name": "Zd_M3.1",
                "mass_range": (3.05, 3.12),
                "initial_params": {
                    "mean": 3.1,
                    "sigma": 0.045,
                    "alphaL": 0.60,
                    "nL": 3.1,
                    "alphaR": 1.5,
                    "nR": 2.9,
                }
            },
            "psi2s": {
                "resonant_bkg_template_name": "Zd_M3.7",
                "mass_range": (3.6, 3.8),
                "initial_params": {
                    "mean": 3.7,
                    "sigma": 0.05,
                    "alphaL": 0.5,
                    "nL": 5.5,
                    "alphaR": 1,
                    "nR": 6,
                }
            }
        }
        return models
        
    def _define_normalization_settings(self) -> Dict[str, Dict[str, Any]]:
        """Define normalization settings for different background components"""
        settings = {
            "background_components": {
                "njpsi": {"init": 2e4, "min": 2e2, "max": 1e8},    # J/psi background
                "npsi2s": {"init": 2e3, "min": 1e1, "max": 1e7},   # psi(2S) background
                "nbkg": {"init": 1e6, "min": 3e2, "max": 1e8},     # Non-resonant background
            },
            "fractions": {
                "fjpsi": {"init": 0.02, "min": 0, "max": 1},       # J/psi background fraction
                "fpsi2s": {"init": 0.005, "min": 0, "max": 1},     # psi(2S) background fraction  
                "fbkg": {"init": 0.975, "min": 0, "max": 1},       # Non-resonant background fraction
            }
        }
        return settings
        
    def get_fit_region(self, name: str) -> Optional[FitRegion]:
        """Get fit region by name"""
        return self.fit_regions.get(name)
        
    def get_background_function(self, index: int) -> Optional[BackgroundFunction]:
        """Get background function by index"""
        if 0 <= index < len(self.background_functions):
            return self.background_functions[index]
        return None
        
    def get_chosen_background_function(self) -> BackgroundFunction:
        """Get the currently chosen background function"""
        return self.get_background_function(self.chosen_bkg_function)
        
    def set_background_function(self, index: int):
        """Set the background function to use"""
        if 0 <= index < len(self.background_functions):
            self.chosen_bkg_function = index
        else:
            raise ValueError(f"Invalid background function index: {index}")
            
    def get_dataset_path(self) -> Path:
        """Get the path to the input dataset (single workspace with all categories)"""
        sample_suffix = "_jpsi" if self.use_jpsi else "_minbias"
        mass_suffix = "_reducedMass" if self.use_reduced_mass else ""
        
        # Single workspace file contains all categories
        return Path(f"datasets/dataset{sample_suffix}{mass_suffix}.root")
        
    def get_output_workspace_path(self) -> Path:
        """Get the path for the output workspace (single workspace with all categories)"""
        sample_suffix = "_jpsi" if self.use_jpsi else "_minbias"
        mass_suffix = "_reducedMass" if self.use_reduced_mass else ""
        binning_suffix = "_binned" if self.use_binned else ""
        
        # Single workspace file contains all categories
        return Path(f"datasets/dataset{sample_suffix}{mass_suffix}{binning_suffix}_full.root")
        
    def get_log_file_path(self, fit_region: str, tag: str = "", category: str = None) -> Path:
        """Get the log file path for a specific category"""
        if category is None:
            category = self.selected_category
        side_suffix = f"_{fit_region}"
        tag_suffix = f"_{tag}" if tag else ""
        binning_suffix = "_binned" if self.use_binned else ""
        category_suffix = f"_{category}" if category else ""

        category_folder = category if category != "inclusive" else ""
        
        return self.output_dir / category_folder / f"post_fit_params{side_suffix}{category_suffix}{tag_suffix}{binning_suffix}.log"
        
    def get_plot_file_path(self, fit_region: str, tag: str = "", log_scale: bool = False, 
                          file_format: str = "png", category: str = None) -> Path:
        """Get the plot file path for a specific category"""
        if category is None:
            category = self.selected_category
        sample_suffix = "_jpsi" if self.use_jpsi else "_minbias"
        side_suffix = f"_{fit_region}"
        tag_suffix = f"_{tag}" if tag else ""
        binning_suffix = "_binned" if self.use_binned else ""
        log_suffix = "_log" if log_scale else ""
        category_suffix = f"_{category}" if category else ""

        category_folder = category if category != "inclusive" else ""
        
        return self.output_dir / category_folder / f"dataset{sample_suffix}{side_suffix}{category_suffix}{tag_suffix}{binning_suffix}{log_suffix}.{file_format}"
        
    def apply_tag(self, tag: str):
        """Apply a tag to output files"""
        if tag:
            # This could modify output paths, but for now we'll handle it in the path methods
            pass
    
    def set_category(self, category: str):
        """Set the selected category for fitting"""
        if category not in self.category_names:
            raise ValueError(f"Invalid category: {category}. Available: {self.category_names}")
        self.selected_category = category
        print(f"Selected category for fitting: {category}", flush = True)
        
        # Update background functions with category-specific parameters
        self.background_functions = self._define_background_functions()
    
    def get_available_categories(self) -> Dict[str, CategoryConfig]:
        """Get all available categories"""
        return self.categories
    
    def select_category(self, category_config):
        """Select a specific category using CategoryConfig object or string"""
        if hasattr(category_config, 'display_name'):  # CategoryConfig object
            self.set_category(category_config.display_name)
        else:  # String input for backward compatibility
            self.set_category(category_config)
    
    def add_category_specific_init_params(self, category_name: str, function_name: str, 
                                         param_inits: List[float]):
        """Helper method to document how to add category-specific initial parameters
        
        To add category-specific initial parameters:
        1. Edit the _define_background_functions() method
        2. Find the appropriate *_inits_by_category dictionary for your function:
           - bernstein_inits_by_category for bkg_f0 (Bernstein polynomial)
           - poly_inits_by_category for bkg_f1 (Polynomial × Exponential)  
           - exp_inits_by_category for bkg_f2 (Sum of exponentials)
           - simple_exp_inits_by_category for bkg_f3 (Simple exponential)
        3. Add an entry: "category_name": [param1, param2, ...]
        
        Example:
            "etap0p6": [2.33352, 3.59166, -0.06610, 0.52400, 0.19075],
            
        Args:
            category_name: Name of the category (e.g., 'etap0p6', 'dRm0p3')
            function_name: Name of the function ('bkg_f0', 'bkg_f1', 'bkg_f2', 'bkg_f3')
            param_inits: List of initial parameter values
        """
        print(f"To add category-specific parameters for {category_name} and {function_name}:")
        print(f"  Edit _define_background_functions() method")
        print(f"  Add to appropriate dictionary: '{category_name}': {param_inits}")
            
    def print_summary(self):
        """Print configuration summary"""
        print("="*60)
        print("BACKGROUND MODEL CONFIGURATION")
        print("="*60)
        print(f"Dataset settings:")
        print(f"  Use J/psi sample: {self.use_jpsi}")
        print(f"  Use reduced mass: {self.use_reduced_mass}")
        print(f"  Use binned data: {self.use_binned}")
        print(f"  Dataset path: {self.get_dataset_path()}")
        print()
        print(f"Fit settings:")
        print(f"  Chosen background function: {self.chosen_bkg_function} ({self.get_chosen_background_function().display_name})")
        print(f"  Freeze background in sidebands: {self.freeze_bkg_sidebands}")
        print(f"  Floating resonant backgrounds: {self.floating_resonant}")
        print(f"  Fit J/psi first: {self.fit_jpsi_first}")
        print(f"  Fit J/psi from prompt: {self.fit_jpsi_prompt}")
        print()
        print(f"Available fit regions:")
        for name, region in self.fit_regions.items():
            print(f"  {name}: {region.display_name} [{region.range[0]:.1f}, {region.range[1]:.1f}] GeV")
        print()
        print(f"Available background functions:")
        for i, func in enumerate(self.background_functions):
            marker = "→" if i == self.chosen_bkg_function else " "
            print(f"  {marker} {i}: {func.display_name} ({func.n_params} params)")
        print()
        print(f"Output directory: {self.output_dir}")
        print("="*60)
