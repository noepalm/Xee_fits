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
    backgrounds: List[str] = None
    background_fractions: List[float] = None # Fractions for each background
    background_resonant_data: str = ""
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
    
    def __init__(self, categories: Dict[str, CategoryConfig] = None, era: str = "2023"):
        # Category settings (use shared configuration)
        if categories is None:
            print(f"DEBUG: No categories provided, using default categories", flush=True)
            self.categories = get_default_categories()
        else:
            print(f"DEBUG: Using provided categories", flush=True)
            self.categories = categories
            
        # Extract category names for convenience
        self.category_names = list(self.categories.keys())
            
        print(f"Background configuration for categories: {self.category_names}")
        for name, cat_config in self.categories.items():
            print(f"  {name}: {cat_config.cuts}")
        
        # Selected category for fitting (default to inclusive)
        self.selected_category = "inclusive"
        
        # Tag for output files (initialized as empty, set via apply_tag)
        self.tag = ""
        
        # Folder tag for subfolder organization (initialized as empty, set via apply_folder_tag)
        self.folder_tag = ""
        
        # Era setting (stored for use in fit regions and dataset paths)
        self.era = era
        
        # I/O settings
        self.output_dir = Path("/eos/home-n/npalmeri/www/DiElectron/background_model")
        self.base_output_dir = self.output_dir  # Keep original for tag application
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # self.output_dir.mkdir(parents=True, exist_ok=True)
        # # make sure output sub-directories exist
        # for cat in [cat.name for cat in self.categories.values()]:
        #     print(f"DEBUG: Creating output directory {(self.output_dir / cat)}", flush=True)
        #     (self.output_dir / cat).mkdir(parents=True, exist_ok=True)
        
        # Dataset settings
        self.use_data = False  # Load data files (in addition to MinBias when creating datasets)
        self.use_jpsi = False
        self.use_reduced_mass = False
        self.use_binned = False
        self.use_reweighting = True
        
        # Fit settings
        self.fit_data = False  # Use data for fitting/plotting (default: use MinBias)
        self.freeze_bkg_sidebands = False
        self.floating_resonant = False
        self.fit_jpsi_first = False
        self.fit_jpsi_prompt = False
        self.no_res = False  # Use only sidebands, exclude resonant regions
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
            "region0": FitRegion(
                name="region0",
                display_name="Left Background Region (0.2-2.0 GeV)",
                range=(0.3, 2.4), #was 0.3, 2.0
                sidebands=[
                    (0.3, 0.65),
                    (0.85, 0.95),
                    (1.15, 2.4)],
                backgrounds=["phi", "omega"],#, "eta"],
                background_fractions=[0.65, 0.25], # non-recursive fractions
                # background_resonant_data = "/eos/home-n/npalmeri/www/DiElectron/PS_reweighting/fw_output_minBias_resonant_nanov15/zsnap/era2023/",
                # background_resonant_data = "/eos/home-n/npalmeri/www/DiElectron/PS_reweighting/nanov15/fw_output_minBias_resonant_corrected_scaleOnly_elenaSyst/zsnap/era2023/",
                # background_resonant_data = "/eos/home-n/npalmeri/www/DiElectron/PS_reweighting/nanov15/fw_output_minBias_withScaleSyst_IDSF_noeta/zsnap/era2023/",
                # background_resonant_data = f"/eos/home-n/npalmeri/www/DiElectron/PS_reweighting/nanov15/fw_output_minBias_withScaleSyst_IDSF_triggerSF/zsnap/era{self.era}/",
                # background_resonant_data = f"/eos/home-n/npalmeri/www/DiElectron/PS_reweighting/nanov15/per_subera/fw_output_minBias_withScaleSyst_IDSF_triggerSF/zsnap/era{self.era}/",
                background_resonant_data = f"/eos/home-n/npalmeri/www/DiElectron/PS_reweighting/nanov15/per_subera/260312/fw_output_minBias_withScaleSyst_IDSF_triggerSF_isoCut/zsnap/era{self.era}/",
                description="Low mass background region",
            ),
            "region1": FitRegion(
                name="region1",
                display_name="Central Region (2.0-4.2 GeV)",
                range=(1.6, 4.6), #4.6 for overlap, 4.2 for strict
                sidebands=[
                    (1.6, 2.5),    # Left sideband
                    # (3.3, 3.5),    # Central sideband  
                    (3.85, 4.6),    # Right sideband
                ],
                backgrounds=["jpsi", "psi2s"],
                background_fractions=[0.7],
                # background_resonant_data = '/eos/home-n/npalmeri/www/DiElectron/PS_reweighting/fw_output_Jpsi_reweight/zsnap/era2023/',
                # background_resonant_data = '/eos/home-n/npalmeri/www/DiElectron/PS_reweighting/nanov15/fw_output_Jpsi_corrected_scaleOnly_elenaSyst/zsnap/era2023/',
                # background_resonant_data = f'/eos/home-n/npalmeri/www/DiElectron/PS_reweighting/nanov15/fw_output_Jpsi_withScaleSyst_IDSF_triggerSF/zsnap/era{self.era}/',
                # background_resonant_data = f'/eos/home-n/npalmeri/www/DiElectron/PS_reweighting/nanov15/per_subera/fw_output_Jpsi_withScaleSyst_IDSF_triggerSF/zsnap/era{self.era}/',
                background_resonant_data = f'/eos/home-n/npalmeri/www/DiElectron/PS_reweighting/nanov15/per_subera/260312/fw_output_Jpsi_withScaleSyst_IDSF_triggerSF_isoCut/zsnap/era{self.era}/',
                description="Main analysis region containing J/psi and psi(2S)",
            ),
            "region2": FitRegion(
                name="region2", 
                display_name="Right Background Region (4.2-11.0 GeV)",
                range=(3.8, 11), #3.8 for overlap, 4.2 for strict
                sidebands=[
                    (3.8, 8.5),
                    (10.0, 11),
                ],
                backgrounds=["upsilon1s"],
                background_fractions=[],
                # background_resonant_data = '/eos/home-n/npalmeri/www/DiElectron/PS_reweighting/fw_output_Upsilon_reweight/zsnap/era2023/',
                # background_resonant_data = '/eos/home-n/npalmeri/www/DiElectron/PS_reweighting/nanov15/fw_output_Upsilon_corrected_scaleOnly_elenaSyst/zsnap/era2023/',
                # background_resonant_data = f'/eos/home-n/npalmeri/www/DiElectron/PS_reweighting/nanov15/fw_output_Upsilon_withScaleSyst_IDSF_triggerSF/zsnap/era{self.era}/',
                # background_resonant_data = f'/eos/home-n/npalmeri/www/DiElectron/PS_reweighting/nanov15/per_subera/fw_output_Upsilon_withScaleSyst_IDSF_triggerSF/zsnap/era{self.era}/',
                background_resonant_data = f'/eos/home-n/npalmeri/www/DiElectron/PS_reweighting/nanov15/per_subera/260312/fw_output_Upsilon_withScaleSyst_IDSF_triggerSF_isoCut/zsnap/era{self.era}/',
                description="High mass background region"
            ),
            "full": FitRegion(
                name="full",
                display_name="Full Range (1.2-8.0 GeV)",
                range=(0, 11),
                sidebands=[
                    (0, 2.6),
                    (3.8, 11.0)
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
            "inclusive": {
                # "region0" : [-0.03, 0.2, -0.2, 1.6, 2],
                # "region0" : [0, 0.055, -0.25, 1.5, 1.5], #MANUALLY TUNED
                # "region0" : [0, 0.01, -0.07, 1.1, 1.45], #MANUALLY TUNED #2, works for nanov15 W/OVERLAP AND DATA
                "region0" : [0, 0.01, -0.07, 1.1, 1.45, -0.1, -0.1], #DATA, 7th order test
                # "region1" : [1.7, 1.9, -0.06610, 0.52400, 0.19075],  # WORKS FOR EVERYTHING BUT etap0p6, MINBIAS
                # "region1" : [2, 2.6, 1.14, 0.3, 0.2],  # the one above stopped working for region [2, 4.2] w/ nanov15; this now does, MINBIAS
                # "region1" : [0.55, 1.96, -0.31, 0.16, 0.08], # works for nanov15 W/ OVERLAP (1.6-4.6), MINBIAS
                # "region1" : [1.7, 1.9, -0.06610, 0.52400, 0.19075], # works for DATA
                "region1" : [1.7, 1.9, -0.06610, 0.52400, 0.19075, -0.1, +0.1], # DATA, 7th order test
                # "region2" : [1.9, 0.73, -0.015, 0.11, 0.013],
                # "region2" : [1.7, 0.23, 0.13, -0.003, 0.00012],
                # "region2" : [4.4, 0.78, 0.74, 0.44, 0.0045], #FOR NANOV15 AND DATA, ALSO works w/ overlap
                "region2" : [4.4, 0.78, 0.74, 0.44, 0.0045, -0.1, 0.1], #DATA, 7th order test
            },
            # Add category-specific overrides here as needed:
            # "etap0p6": [2.33352, 3.59166, -0.06610, 0.52400, 0.19075],  # WORKS FOR dRp0p3
            # "dRm0p3": [0.36903, 0.11880, -0.46547, 0.56438, -0.58503],  # WORKS FOR dRm0p3
            # "etaHigh" : [2.33352, 3.59166, -0.06610, 0.52400, 0.19075], # TEMPORARILY REMOVED. seems worse results?
        }

        bernstein_limits_by_category = {
            # Add category-specific overrides here as needed
            "inclusive": {
                "region1" : [(-2.5, 2.5) for _ in range(7)]
            },  # Default limits for all #FIXME: was (-5, 5) for all
            "etaHigh" : {
                "region1" : [(-5, 5) for _ in range(5)],
            },
        }
        
        poly_inits_by_category = {
            "inclusive": {
                # ### POLYNOMIAL X EXPONENTIAL
                # # "region1" : [-0.9, 3.2, -1.4, 0.16, 0], #THIS WORKS ON DATA. 
                # # "region1" : [-4.3, 4.2, -1.3, 0.13, 0.1, -0.79], # testing: does this make fit any quicker?
                # "region1" : [-0.9, 3.2, -1.4, 0.16, 0.1, 0], # worked on data, trying init for 5th param
                # "region0" : [-2.7, 4.2, 5, -2, 0.1, -0.07],
                # "region2" : [9.8, -5.0, 0.66, 0.001, 0.1, -1.5],
                # # "region2" : [-2.9, 5, 5, -2, -0.04], # DON'T WORK
                ### POLY ONLY
                "region0" : [-2.7, 4.2, 5, -2, 0.1, 0],
                "region1" : [-3, 3, -1.3, 0.25, -0.01, 0],
                "region2" : [9.8, -5.0, 0.66, 0.001, 0.1, -1.5],
            },

            # Add category-specific overrides here as needed
        }

        poly_limits_by_category = {
            "inclusive" : {
                "region0" : [*[(-10, 10) for _ in range(5)], (0, 0)],
                # "region1" : [*[(-5, 5) for _ in range(5)], (-10, 10)], # poly x exp
                "region1" : [*[(-5, 5) for _ in range(5)], (-5, 0.1)], # poly only
                "region2" : [(-20, 20) for _ in range(6)],
            }
        }
        
        exp_inits_by_category = {
            "inclusive": {
                "region1" : [1, 4, 0.1, -1] + [1./4 * (-1 * (i % 2)) for i in range(3)],
            },
            # Add category-specific overrides here as needed
        }
        
        simple_exp_inits_by_category = {
            "inclusive": {
                "region1" : [-1.5],
            },
            # Add category-specific overrides here as needed
        }

        chebyshev_inits_by_category = {
            "inclusive": {
                "region0" : [1.06946, 0.00463, -0.14197, -0.00807, 0.02420, -0.01174],
                "region1" : [-0.8, -0.115, 0.25, 0.02, -0.076, 0.1],
                "region2" : [-1.3, 0.5, -0.1, -0.001, -0.01, 0.05], #SWITCH TO -1.3, 0.5, -0.01, -0.001, -0.01, 0.05 FOR 2023BPIX
                # "region2" : [-1.4, 0.5, -0.05, -0.02, -0.02, 0.03], #for 2023 chebyshev r2
            },
            # Add category-specific overrides here as needed
        }

        bernsteinexp_inits_by_category = {
            "inclusive" : {
                # "region1" : [1.7, 1.9, -0.06610, 0.52400, 0.19075, -1, 0.9], # first 5 params => bernstein, [-2] => exponential, [-1] => fraction of bernstein wrt exponential
                "region1" : [-0.05, 2, 2, 0.5, -0.5, 0, 0.25,
                             -0.6, 
                             0.5], # first 5 params => bernstein, [-2] => exponential, [-1] => fraction of bernstein wrt exponential
            }
        }

        modifiedbw_inits_by_category = {
            "inclusive" : {
                # "region1" : [1, -0.1, 1, 1, 1], #a1, a2, a3, mu, sigma
                # "region1" : [1, -0.2, 3.2, 3.1, 1.2], #a1, a2, a3, mu, sigma
                "region1" : [2.4, -0.3, -30], #a1, a2, mu
            }
        }

        # Get initial parameters for the current category (fall back to inclusive if not specified)
        current_category = getattr(self, 'selected_category', 'inclusive')
        print(f"DEBUG: trying to retrieve selceted category: {self.selected_category}", flush=True)
        
        print(f"DEBUG: Using category '{current_category}' for background functions", flush=True)

        # Get fit region name safely (may not be defined yet during initialization)
        fit_region_name = getattr(self.chosen_fit_region, 'name', None) if hasattr(self, 'chosen_fit_region') else None

        print(f"DEBUG: Using fit region '{fit_region_name}' for background functions", flush=True)
        

        inits_dict = bernstein_inits_by_category.get(current_category, 
                                                     bernstein_inits_by_category["inclusive"])
        bernstein_inits = inits_dict.get(fit_region_name, inits_dict["region1"])

        limits_dict = bernstein_limits_by_category.get(current_category,
                                                       bernstein_limits_by_category["inclusive"]) 
        bernstein_limits = limits_dict.get(fit_region_name, 
                                          limits_dict["region1"])

        inits_dict = poly_inits_by_category.get(current_category,
                                                poly_inits_by_category["inclusive"])
        poly_inits = inits_dict.get(fit_region_name, inits_dict["region1"])

        limits_dict = poly_limits_by_category.get(current_category, 
                                                  poly_limits_by_category["inclusive"])
        poly_limits = limits_dict.get(fit_region_name,
                                        limits_dict["region1"])

        inits_dict = exp_inits_by_category.get(current_category,
                                               exp_inits_by_category["inclusive"])
        exp_inits = inits_dict.get(fit_region_name, inits_dict["region1"])

        inits_dict = simple_exp_inits_by_category.get(current_category,
                                                      simple_exp_inits_by_category["inclusive"])
        simple_exp_inits = inits_dict.get(fit_region_name,
                                          inits_dict["region1"])

        inits_dict = chebyshev_inits_by_category.get(current_category,
                                                      chebyshev_inits_by_category["inclusive"])
        chebyshev_inits = inits_dict.get(fit_region_name,
                                          inits_dict["region1"])
        chebyshev_inits_4thdeg = chebyshev_inits[:4]  # First 4 params for 4th degree
        chebyshev_inits_5thdeg = chebyshev_inits[:5]  # First 5 params for 5th degree

        inits_dict = bernsteinexp_inits_by_category.get(current_category,
                                                        bernsteinexp_inits_by_category["inclusive"])
        bernsteinexp_inits = inits_dict.get(fit_region_name,  
                                          inits_dict["region1"])

        inits_dict = modifiedbw_inits_by_category.get(current_category,
                                                        modifiedbw_inits_by_category["inclusive"])
        modifiedbw_inits = inits_dict.get(fit_region_name,  
                                          inits_dict["region1"])

        # Bernstein polynomial (5th degree)
        functions.append(BackgroundFunction(
            name="bkg_f0",
            display_name="Bernstein Polynomial",
            formula="Bernstein polynomial of degree 5",
            n_params=7,
            param_names=[f"a{i}" for i in range(7)],
            param_inits=bernstein_inits,
            param_limits=bernstein_limits,
            description="5th degree Bernstein polynomial"
        ))
        
        # Polynomial × Exponential (4th degree polynomial)
        functions.append(BackgroundFunction(
            name="bkg_f1", 
            display_name="Polynomial × Exponential",
            formula="(1 + a0*x + a1*x^2 + a2*x^3 + a3*x^4 + a4*x^5) * exp(b0*x)",
            n_params=6,  # 5 polynomial + 1 exponential
            param_names=[f"b{i}" for i in range(5)] + ["bb0"],
            # n_params=5,  # 5 polynomial + 1 exponential
            # param_names=[f"b{i}" for i in range(5)],
            param_inits=poly_inits,
            param_limits=poly_limits,
            # param_limits=[(-5, 5) for _ in range(4)] + [(-10, 10)],
            description="5th degree polynomial times exponential"
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

        # 4th degree Chebyshev polynomial
        functions.append(BackgroundFunction(
            name="bkg_f4",
            display_name="Chebyshev Polynomial",
            formula="Chebyshev polynomial of degree 4",
            n_params=4,
            param_names=[f"t{i}" for i in range(4)],
            param_inits=chebyshev_inits_4thdeg,
            param_limits=[(-5, 5) for _ in range(4)],
            description="4th degree Chebyshev polynomial"
        ))
        
        # 5th deg Bernstein + exponential
        functions.append(BackgroundFunction(
            name="bkg_f5",
            display_name="Bernstein + exponential",
            formula="5th deg Bernstein polynomial + exponential",
            n_params=9, # 5 bernstein + 1 exponential + 1 fraction in addition
            param_names=[f"be{i}" for i in range(9)],
            param_inits=bernsteinexp_inits,
            param_limits=[*[(-5, 5) for _ in range(8)], (0, 1)],
            description="6th degree Chebyshev polynomial"
        ))

        # Modified BW
        functions.append(BackgroundFunction(
            name="bkg_f6", 
            display_name="Modified BW",
            formula="Modified BW",
            n_params=3,
            param_names=[f"mbw{i}" for i in range(3)],
            param_inits=modifiedbw_inits,
            # param_limits=[(-5, 5) for _ in range(5)],
            # param_limits=[(-2, 2), (-2, 0), (-5, 5), (-10, 10), (0, 10)],
            param_limits=[(0, 3), (-1, 0), (-80, 80)],
            description="Modified BW"
        ))

        # 6th degree Chebyshev polynomial
        functions.append(BackgroundFunction(
            name="bkg_f7",
            display_name="Chebyshev Polynomial deg 6",
            formula="Chebyshev polynomial of degree 6",
            n_params=6,
            param_names=[f"t{i}" for i in range(6)],
            param_inits=chebyshev_inits,
            param_limits=[(-5, 5) for _ in range(6)],
            description="6th degree Chebyshev polynomial"
        ))        

        # 5th degree Chebyshev polynomial
        functions.append(BackgroundFunction(
            name="bkg_f8",
            display_name="Chebyshev Polynomial deg 5",
            formula="Chebyshev polynomial of degree 5",
            n_params=5,
            param_names=[f"t{i}" for i in range(5)],
            param_inits=chebyshev_inits_5thdeg,
            param_limits=[(-5, 5) for _ in range(5)],
            description="5th degree Chebyshev polynomial"
        ))        

        # Validate all functions
        for func in functions:
            func.validate()
            
        return functions
        
    def _define_resonant_models(self) -> Dict[str, Dict[str, Any]]:
        """Define resonant background models (J/psi, psi2s)"""
        models = {
            "eta" : {
                "resonant_bkg_template_name": "Zd_M0.4",
                "mass_range": (0.2, 0.6),
                "initial_params" : {
                    "mean" : 0.36,
                    "sigma" : 0.05,
                    "alphaL" : 1,
                    "nL" : 20,
                    "alphaR" : 2,
                    "nR" : 20,
                },
                "param_limits_override": {"mean": (0.3, 0.5)},
                "title": "#eta"
            },
            "omega" : {
                "resonant_bkg_template_name": "Zd_M0.8",
                "mass_range": (0.5, 1),
                "initial_params" : {
                    "mean" : 0.78,
                    "sigma" : 0.02,
                    "alphaL" : 1,
                    "nL" : 8,
                    "alphaR" : 1,
                    "nR" : 4,
                },
                "title": "#omega"
            },
            "phi" : {
                "resonant_bkg_template_name": "Zd_M1.1",
                "mass_range": (0.8, 1.3),
                "initial_params" : {
                    "mean" : 1,
                    "sigma" : 0.025,
                    "alphaL" : 1.5,
                    "nL" : 1.5,
                    "alphaR" : 3,
                    "nR" : 4,
                },
                # Optional: "param_limits_override": {},
                "title": "#phi"
            },
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
                },
                # Optional: "param_limits_override": {},
                "title": "J/#psi"
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
                },
                # Optional: "param_limits_override": {},
                "title": "#psi(2S)"
            },
            "upsilon1s": {
                "resonant_bkg_template_name": "Zd_M9.5",
                "mass_range": (9.0, 10.0),
                "initial_params": {
                    "mean": 9.46,
                    "sigma": 0.15,
                    "alphaL": 0.5,
                    "nL": 5.5,
                    "alphaR": 1,
                    "nR": 6,
                },
                # Optional: "param_limits_override": {},
                "title": "Y(1S)"
            }
        }
        return models
        
    def _define_normalization_settings(self) -> Dict[str, Dict[str, Any]]:
        """Define normalization settings for different background components"""
        settings = {
            # "background_components": {
            #     "njpsi": {"init": 2e4, "min": 2e2, "max": 1e8},    # J/psi background
            #     "npsi2s": {"init": 2e3, "min": 1e1, "max": 1e7},   # psi(2S) background
            #     "ndy": {"init": 1e6, "min": 3e2, "max": 1e8},     # Non-resonant background
            # },
            "background_components": {
                # with _param, everything is expressed as dataset max * <value>
                # "nphi" : {"init_param" : 0.02, "min_param" : 1e-6, "max_param" : 1}, # phi background
                "nphi" : {"init_param" : 0.01, "min_param" : 1e-6, "max_param" : 1}, # phi background
                # "nomega" : {"init_param" : 0.007, "min_param" : 1e-6, "max_param" : 1}, # omega background
                "nomega" : {"init_param" : 0.0035, "min_param" : 1e-6, "max_param" : 1}, # omega background
                # "neta" : {"init_param" : 0.001, "min_param" : 1e-6, "max_param" : 1}, # eta background ### FOR DATA
                "neta" : {"init_param" : 0, "min_param" : 1e-6, "max_param" : 1}, # eta background
                # "njpsi": {"init_param": 0.9, "min_param": 1e-4, "max_param": 1e2},    # J/psi background ### FOR DATA
                # "npsi2s": {"init_param": 0.2, "min_param": 1e-4, "max_param": 1e4},   # psi(2S) background ### FOR DATA
                "njpsi": {"init_param": 0.09, "min_param": 1e-4, "max_param": 1e2},    # J/psi background
                "npsi2s": {"init_param": 0.02, "min_param": 1e-4, "max_param": 1e4},   # psi(2S) background
                # "nupsilon1s": {"init_param": 0.2, "min_param": 1e-4, "max_param": 1e4}, # Upsilon(1S) background
                # "nupsilon1s": {"init_param": 0.01, "min_param": 1e-4, "max_param": 1e4}, # Upsilon(1S) background FOR NANOV15 ### FOR DATA
                # "nupsilon1s": {"init_param": 0.001, "min_param": 1e-4, "max_param": 1e4}, # Upsilon(1S) background
                # UPSILON: 0.005 worked for all regions all suberas except 2023BPix region 2 (0.001) and 2023 region 2 region (0.0005)
                "nupsilon1s": {"init_param": 0.001, "min_param": 1e-4, "max_param": 1e4}, # Upsilon(1S) background
                "ndy": {"init_param": 0.3, "min_param": 1e-4, "max_param": 1e4},     # Non-resonant background
            },
            "fractions": {
                "fjpsi": {"init": 0.9, "min": 0, "max": 1},       # J/psi background fraction
                "fpsi2s": {"init": 0.2, "min": 0, "max": 1},     # psi(2S) background fraction  
                # "ndy": {"init": 0.08, "min": 0, "max": 1},       # Non-resonant background fraction
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
        if index == -1:
            print("Using all background functions for fitting", flush=True)
            self.chosen_bkg_function = -1
            return
        elif 0 <= index < len(self.background_functions):
            self.chosen_bkg_function = index
        else:
            raise ValueError(f"Invalid background function index: {index}")
            
    # TODO FIXME: merge the two functions below, basically same return value
    def get_dataset_path(self) -> Path:
        """Get the path to the input dataset (single workspace with all categories)"""
        sample_suffix = "_data" if self.use_data else "_jpsi" if self.use_jpsi else "_minbias"
        mass_suffix = "_reducedMass" if self.use_reduced_mass else ""
        binning_suffix = "_binned" if self.use_binned else ""
        reweight_suffix = "" if self.use_reweighting else "_noReweight" 
        tag_suffix = f"_{self.tag}" if self.tag else ""
        envelope_suffix = "_envelope" if self.chosen_bkg_function == -1 else ""
        folder_tag_prefix = f"{self.folder_tag}/" if self.folder_tag else ""

        # Single workspace file contains all categories
        # TODO FIXME: is the non _full one even used? REVERT BACK IF NEEDED
        return Path(f"datasets/{folder_tag_prefix}dataset{sample_suffix}_{self.chosen_fit_region.name}{mass_suffix}{binning_suffix}{tag_suffix}{reweight_suffix}{envelope_suffix}_full.root")
        
    def get_output_workspace_path(self) -> Path:
        """Get the path for the output workspace (single workspace with all categories)"""
        sample_suffix = "_data" if self.use_data else "_jpsi" if self.use_jpsi else "_minbias"
        mass_suffix = "_reducedMass" if self.use_reduced_mass else ""
        binning_suffix = "_binned" if self.use_binned else ""
        reweight_suffix = "" if self.use_reweighting else "_noReweight" 
        tag_suffix = f"_{self.tag}" if self.tag else ""
        envelope_suffix = "_envelope" if self.chosen_bkg_function == -1 else ""
        folder_tag_prefix = f"{self.folder_tag}/" if self.folder_tag else ""
        
        # Single workspace file contains all categories
        return Path(f"datasets/{folder_tag_prefix}dataset{sample_suffix}_{self.chosen_fit_region.name}{mass_suffix}{binning_suffix}{tag_suffix}{reweight_suffix}{envelope_suffix}_full.root")
        
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
        
    def apply_folder_tag(self, folder_tag: str):
        """Apply folder tag to create subfolder structure for outputs
        
        This should be called before apply_tag to set up the subfolder structure.
        """
        if not folder_tag:
            return
            
        self.folder_tag = folder_tag
        
        # Update base_output_dir to include subfolder (supports nested paths)
        self.base_output_dir = self.base_output_dir / folder_tag
        self.output_dir = self.base_output_dir
        
        # Ensure all parent directories are created
        self.base_output_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"Applied folder tag '{folder_tag}': base output dir set to {self.base_output_dir}")
        
    def apply_tag(self, tag: str):
        """Apply a tag to output files and directories"""
        binning_suffix = "_binned" if self.use_binned else ""            
        reweight_suffix = "" if self.use_reweighting else "_noReweight"
        tag_suffix = f"_{self.tag}" if self.tag else ""
            
        self.tag = tag  # Store the tag for later use
        tag_label = f"_{tag}" if tag != "" else tag
        self.output_dir = self.base_output_dir / f"fit{binning_suffix}{reweight_suffix}{tag_label}"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Recreate category subdirectories with new tagged path
        for cat in [cat.name for cat in self.categories.values()]:
            category_dir = self.output_dir / cat
            print(f"DEBUG: Creating tagged output directory {category_dir}", flush=True)
            category_dir.mkdir(parents=True, exist_ok=True)
        
        # Create dataset directory - use folder_tag if provided (already includes era), else add era
        if self.folder_tag:
            dataset_dir = Path("datasets") / self.folder_tag
        else:
            dataset_dir = Path("datasets") / self.era
        dataset_dir.mkdir(parents=True, exist_ok=True)
        print(f"DEBUG: Ensuring dataset directory exists: {dataset_dir}", flush=True)
    
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
           - chebyshev_inits_by_category for bkg_f4 (Chebyshev polynomial)
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
        print(f"  Chosen background function: {self.chosen_bkg_function} ({self.get_chosen_background_function().display_name if self.chosen_bkg_function != -1 else 'All -- envelope'})")
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
