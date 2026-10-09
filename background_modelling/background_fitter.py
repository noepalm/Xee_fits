"""
Background fitter - Object-oriented approach

This module handles the fitting of background models to data,
including resonant and non-resonant components.
"""
import ROOT
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import random
import time

from background_config import BackgroundModelConfig, FitRegion, BackgroundFunction
from shared_config import CategoryConfig

class FitResult:
    """Class to store fit results and statistics"""
    
    def __init__(self, name: str, fit_region: str):
        self.name = name
        self.fit_region = fit_region
        
        # Fit status
        self.fit_status: int = -1
        self.chi2: float = -1
        self.ndf: int = -1
        self.chi2_ndf: float = -1
        
        # Parameters
        self.parameters: Dict[str, float] = {}
        self.parameter_errors: Dict[str, float] = {}
        self.parameter_limits: Dict[str, Tuple[float, float]] = {}
        self.prefit_parameters: Dict[str, float] = {}
        
        # Free parameters count
        self.n_free_params: int = 0
        
        # Integrals
        self.integrals: Dict[str, float] = {}

    # def add_parameter(self, name: str, value: float, error: float, prefit_value: Optional[float] = None):
    #     """Add parameter information"""
    #     self.parameters[name] = value
    #     self.parameter_errors[name] = error
    #     if prefit_value is not None:
    #         self.prefit_parameters[name] = prefit_value

    def add_parameter(self, name: str, parameter: ROOT.RooRealVar, prefit_value: Optional[float] = None):
        """Add parameter information"""
        self.parameters[name] = parameter.getValV()
        self.parameter_errors[name] = parameter.getError()
        self.parameter_limits[name] = (parameter.getMin(), parameter.getMax())
        if prefit_value is not None:
            self.prefit_parameters[name] = prefit_value
            
    def calculate_chi2_ndf(self, chi2: float, n_free_params: int):
        """Calculate and store chi2/ndf"""
        self.chi2 = chi2
        self.n_free_params = n_free_params
        self.ndf = max(1, self.n_free_params)  # Avoid division by zero
        self.chi2_ndf = chi2 / self.ndf if self.ndf > 0 else -1


class BackgroundFitter:
    """Main class for fitting background models"""
    
    def __init__(self, config: BackgroundModelConfig, category: CategoryConfig = None, 
                 output_workspace: "ROOT.RooWorkspace" = None, era: str = "2023"):
        self.config = config
        self.era = era
        
        # Storage for fit results
        self.fit_results: Dict[str, FitResult] = {}
        
        # ROOT objects
        self.workspace: Optional[ROOT.RooWorkspace] = None
        self.data: Optional[ROOT.RooDataSet] = None
        self.mass_var: Optional[ROOT.RooRealVar] = None
        
        # Centralized output workspace (shared across categories)
        self.output_workspace = output_workspace

        # Category
        if category is None:
            # Get default category (inclusive) if none specified
            from shared_config import get_default_categories
            categories = get_default_categories()
            self.category = categories.get("inclusive")
        else:
            self.category = category
        
        # Background functions
        self.background_functions: Dict[str, ROOT.RooAbsPdf] = {}
        
        # Resonant background models (J/psi, psi(2S), etc.)
        self.resonant_backgrounds: Dict[str, ROOT.RooAbsPdf] = {}
        
        # Store parameters to maintain ownership
        self.resonant_parameters: Dict[str, ROOT.RooRealVar] = {}
        
        # Combined models
        self.combined_model: Optional[ROOT.RooAbsPdf] = None
        
        # Prompt data and models (for resonant background fitting)
        self.resonant_data: Optional[ROOT.RooDataSet] = None
        self.resonant_combined_model: Optional[ROOT.RooAbsPdf] = None
        
        # Log file
        self.log_file: Optional[object] = None
        
        print("Background fitter initialized")
        
    def load_workspace(self) -> bool:
        """Load the workspace and extract data and resonant background templates for a specific category"""        
                    
        print(f"Loading workspace for category: {self.category.display_name}...")
        
        # dataset_path = self.config.get_dataset_path()
        # if not dataset_path.exists():
        #     print(f"Error: Dataset file not found: {dataset_path}")
        #     return False
            
        # # Open file and get workspace
        # root_file = ROOT.TFile.Open(str(dataset_path))
        # if not root_file or root_file.IsZombie():
        #     print(f"Error: Cannot open file {dataset_path}")
        #     return False
            
        # self.workspace = root_file.Get("w")
        # if not self.workspace:
        #     print("Error: Workspace 'w' not found in file")
        #     root_file.Close()
        #     return False

        # FIXME: testing if this is enough.
        self.workspace = self.output_workspace
            
        # Get category-specific data and shared mass variable
        # When fit_data=True and use_data=True: use real data for fitting
        # When fit_data=False (default): use MinBias for fitting
        if self.config.fit_data and self.config.use_data:
            dataset_name = f"data_obs{self.category.label}"
            print(f"  Using REAL DATA for fitting: {dataset_name}")
        elif self.config.use_data:
            dataset_name = f"data_obs{self.category.label}_minbias"
            print(f"  Using MinBias for fitting (data loaded but not used for fit): {dataset_name}")
        else:
            dataset_name = f"data_obs{self.category.label}"
            print(f"  Using MinBias for fitting: {dataset_name}")
        
        self.data = self.workspace.obj(dataset_name)
        self.mass_var = self.workspace.obj("mass")  # Shared mass variable
        
        if not self.data or not self.mass_var:
            print(f"Error: Required objects not found in workspace")
            print(f"  Looking for dataset: {dataset_name}")
            print(f"  Available datasets: {[obj.GetName() for obj in self.workspace.allData()]}")
            return False
            
        print(f"  Loaded dataset '{dataset_name}' with {self.data.numEntries()} entries")
        print(f"  Mass variable range: [{self.mass_var.getMin():.2f}, {self.mass_var.getMax():.2f}] GeV")
        
        # # Convert to binned data if requested
        # if self.config.use_binned:
        #     self.data = self._convert_to_binned()
            
        return True
        
    def setup_mass_ranges(self, fit_region: FitRegion):
        """Setup mass ranges for fitting"""
        print(f"Setting up mass ranges for {fit_region.display_name}...")
        
        # Set main range
        self.mass_var.setRange(fit_region.name, fit_region.range[0], fit_region.range[1])
        
        # Set sideband ranges
        sideband_names = []
        for i, (min_val, max_val) in enumerate(fit_region.sidebands):
            range_name = f"sideband_{i}"
            self.mass_var.setRange(range_name, min_val, max_val)
            sideband_names.append(range_name)
            
        # Combined sideband range
        if sideband_names:
            combined_sidebands = ",".join(sideband_names)
            print(f"  Sideband ranges: {combined_sidebands}")
            return combined_sidebands
        else:
            return fit_region.name


    def create_background_functions(self):
        """Create all background functions"""

        print(f"Creating background functions for category {self.category.display_name}...")

        for func_config in self.config.background_functions:
            # Skip if a specific function is chosen and this isn't it
            if self.config.chosen_bkg_function >= 0 and func_config.name != self.config.get_chosen_background_function().name:
                continue
            print(f"  Creating {func_config.display_name}...")
            
            if func_config.name in ["bkg_f0", "bkg_f9", "bkg_f10", "bkg_f11", "bkg_f18", "bkg_f19", "bkg_f20", "bkg_f21", "bkg_f22", "bkg_f23", "bkg_f29", "bkg_f30"]:
                # Bernstein polynomial (different degrees)
                self._create_bernstein_function(func_config)
            elif func_config.name in ["bkg_f4", "bkg_f7", "bkg_f8", "bkg_f24", "bkg_f25", "bkg_f26", "bkg_f27", "bkg_f28", "bkg_f31", "bkg_f32", "bkg_f33"]:
                # Chebyshev polynomial
                self._create_chebyshev_function(func_config)
            elif func_config.name in ["bkg_f1", "bkg_f12", "bkg_f13", "bkg_f14"]:
                # Polynomial × Exponential
                self._create_poly_exp_function(func_config)
            elif func_config.name == "bkg_f2":
                # Sum of exponentials
                self._create_sum_exp_function(func_config)
            elif func_config.name == "bkg_f3":
                # Simple exponential
                self._create_simple_exp_function(func_config)
            elif func_config.name == "bkg_f5":
                # Bernstein + exponential
                self._create_bernstein_exp_function(func_config)
            elif func_config.name == "bkg_f6":
                # modified BW
                self._create_modified_bw(func_config)
            elif func_config.name == "bkg_f15":
                # expoenntial of polynomial, 4th deg
                self._create_exppoly_function(func_config)
            elif func_config.name == "bkg_f16":
                # Dijet function
                self._create_dijet_function(func_config)
            elif func_config.name == "bkg_f17":
                # chebyshev times fermi
                self._create_chebyshev_times_fermi(func_config)
                
    def _create_bernstein_function(self, func_config: BackgroundFunction):
        """Create Bernstein polynomial function"""
        # Create parameters
        param_list = self._create_vars(func_config)
        # Create function
        func = ROOT.RooBernstein(f"{func_config.name}{self.category.label}_{self.era}",
                                 f"{func_config.name}{self.category.label}_{self.era}", self.mass_var, param_list)
        
        self.background_functions[func_config.name] = func
        
    def _create_bern_exp_function(self, func_config: BackgroundFunction):
        """Create polynomial × exponential function"""
        # Create parameters
        params = self._create_vars(func_config)

        # Create polynomial part
        bern_params = [self.workspace.obj(f"{name}{self.category.label}_{self.era}") for name in func_config.param_names[:-1]]
        print("DEBUG: bernstein params in bern * exp", bern_params, flush=True)
        bern_func = ROOT.RooBernstein(f"{func_config.name}{self.category.label}_{self.era}",
                                 f"{func_config.name}{self.category.label}_{self.era}", self.mass_var, bern_params)

        # Create exponential part
        exp_param = self.workspace.obj(f"{func_config.param_names[-1]}{self.category.label}_{self.era}")
        print(f"DEBUG: exp_param in bern * exp = {exp_param}", flush=True)
        exp_func = ROOT.RooExponential(f"{func_config.name}_exp{self.category.label}_{self.era}", f"{func_config.name}_exp{self.category.label}_{self.era}", self.mass_var, exp_param)
        
        # store exp and poly funcs inside background_functions for ownership
        self.background_functions[f"{func_config.name}_bern"] = bern_func
        self.background_functions[f"{func_config.name}_exp"] = exp_func
        
        # Combine
        func = ROOT.RooProdPdf(f"{func_config.name}{self.category.label}_{self.era}",
                               f"{func_config.name}{self.category.label}_{self.era}", bern_func, exp_func)

        self.background_functions[func_config.name] = func
        
    def _create_poly_exp_function(self, func_config: BackgroundFunction):
        """Create polynomial × exponential function"""
        # Create parameters
        params = self._create_vars(func_config)
            
        # Create polynomial part
        poly_params = [self.workspace.obj(f"{name}{self.category.label}_{self.era}") for name in func_config.param_names[:-1]]
        # poly_params = [self.workspace.obj(f"{name}{self.category.label}_{self.era}") for name in func_config.param_names]

        # APPROACH 2: Use built-in RooPolynomial
        poly_func = ROOT.RooPolynomial(f"{func_config.name}_poly{self.category.label}_{self.era}", f"{func_config.name}_poly{self.category.label}_{self.era}", self.mass_var, poly_params)

        # Create exponential part
        exp_param = self.workspace.obj(f"{func_config.param_names[-1]}{self.category.label}_{self.era}")
        print(f"DEBUG: exp_param = {exp_param}", flush=True)
        # exp_param = params[-1]

        # exp_param = self.workspace.obj(func_config.param_names[-1])
        exp_func = ROOT.RooExponential(f"{func_config.name}_exp{self.category.label}_{self.era}", f"{func_config.name}_exp{self.category.label}_{self.era}", self.mass_var, exp_param)
        
        # store exp and poly funcs inside background_functions for ownership
        self.background_functions[f"{func_config.name}_poly"] = poly_func
        self.background_functions[f"{func_config.name}_exp"] = exp_func
        
        # Combine
        func = ROOT.RooProdPdf(f"{func_config.name}{self.category.label}_{self.era}",
                               f"{func_config.name}{self.category.label}_{self.era}", poly_func, exp_func)

        self.background_functions[func_config.name] = func

    def _create_exppoly_function(self, func_config: BackgroundFunction):
        """Create polynomial × exponential function"""
        # Create parameters
        params = self._create_vars(func_config)
            
        # Create polynomial part
        exppoly_params = [self.workspace.obj(f"{name}{self.category.label}_{self.era}") for name in func_config.param_names]

        exppoly_formula = "exp(@1/5 * @0 + @2/5**2 * @0**2 + @3/5**3 * @0**3 + @4/5**4 * @0**4)"

        func = ROOT.RooGenericPdf(
            f"{func_config.name}{self.category.label}_{self.era}",
            f"{func_config.name}{self.category.label}_{self.era}",
            exppoly_formula,
            ROOT.RooArgList(self.mass_var, *exppoly_params)
        )

        self.background_functions[func_config.name] = func
        
    def _create_dijet_function(self, func_config: BackgroundFunction):
        """Create CMS empirical dijet function"""
        # Create parameters
        params = self._create_vars(func_config)
            
        # Retrieve parameters: [0] = mass, [1] = p1, [2] = p2, [3] = p3
        dijet_params = [self.workspace.obj(f"{name}{self.category.label}_{self.era}") for name in func_config.param_names]

        # Center of mass energy is hardcoded to 13600.0 GeV for Run 3
        dijet_formula = "pow(@0, @1 + @2*log(@0) + @3*pow(log(@0),2))"# * pow((1-@0), @3)"

        func = ROOT.RooGenericPdf(
            f"{func_config.name}{self.category.label}_{self.era}",
            f"{func_config.name}{self.category.label}_{self.era}",
            dijet_formula,
            ROOT.RooArgList(self.mass_var, *dijet_params)
        )
        self.background_functions[func_config.name] = func

    def _create_sum_exp_function(self, func_config: BackgroundFunction):
        """Create sum of exponentials function"""
        # Create parameters
        params = self._create_vars(func_config)
            
        # Create exponential functions
        exp_funcs = []
        for i in range(4):  # 4 exponentials
            param_name = f"c{i}{self.category.label}_{self.era}"
            param = params.find(param_name)
            exp_func = ROOT.RooExponential(f"{func_config.name}_exp{i}{self.category.label}_{self.era}",
                                           f"{func_config.name}_exp{i}{self.category.label}_{self.era}", 
                                           self.mass_var, param)
            exp_funcs.append(exp_func)
            # store exp funcs inside background_functions for ownership
            self.background_functions[f"{func_config.name}_exp{i}"] = exp_func

        # Create sum with coefficients
        coeff_list = ROOT.RooArgList([params.find(f"cc{i}{self.category.label}_{self.era}") for i in range(3)])  # n-1 coefficients
        func = ROOT.RooAddPdf(f"{func_config.name}{self.category.label}_{self.era}", 
                              f"{func_config.name}{self.category.label}_{self.era}", 
                              ROOT.RooArgList(exp_funcs), coeff_list)
        
        self.background_functions[func_config.name] = func
        
    def _create_simple_exp_function(self, func_config: BackgroundFunction):
        """Create simple exponential function"""
        # Create parameters
        param = self._create_vars(func_config)[0]
        
        # Create function
        func = ROOT.RooExponential(f"{func_config.name}{self.category.label}_{self.era}", 
                                   f"{func_config.name}{self.category.label}_{self.era}", self.mass_var, param)
        self.background_functions[func_config.name] = func

    def _create_chebyshev_function(self, func_config: BackgroundFunction):
        """Create Chebyshev polynomial function"""
        # Create parameters
        param_list = self._create_vars(func_config)
        # Create function
        func = ROOT.RooChebychev(f"{func_config.name}{self.category.label}_{self.era}",
                                 f"{func_config.name}{self.category.label}_{self.era}", self.mass_var, param_list)
        self.background_functions[func_config.name] = func
        
    def _create_chebyshev_times_fermi(self, func_config: BackgroundFunction):
        """Create Chebyshev polynomial function modulated by a Fermi turn-on"""
        # Create parameters
        param_list = self._create_vars(func_config)
        chebyshev_params = [self.workspace.obj(f"{name}{self.category.label}_{self.era}") for name in func_config.param_names[:-2]]
        fermi_params = [self.workspace.obj(f"{name}{self.category.label}_{self.era}") for name in func_config.param_names[-2:]]

        # Implement * unpacking for the RooArgList
        cheb_func = ROOT.RooChebychev(f"{func_config.name}_cheb{self.category.label}_{self.era}",
                                      f"{func_config.name}_cheb{self.category.label}_{self.era}", 
                                      self.mass_var, ROOT.RooArgList(*chebyshev_params))
        
        # Declare the Fermi turn-on as a RooFormulaVar (RooAbsReal), NOT a RooGenericPdf
        fermi_func = ROOT.RooFormulaVar(f"{func_config.name}_fermi{self.category.label}_{self.era}",
                                        f"{func_config.name}_fermi{self.category.label}_{self.era}", 
                                        "1/(1 + exp(@2*(@0 - @1)))", 
                                        ROOT.RooArgList(self.mass_var, *fermi_params))
        
        # Store intermediate functions for ownership
        self.background_functions[f"{func_config.name}_cheb"] = cheb_func
        self.background_functions[f"{func_config.name}_fermi"] = fermi_func

        # Construct the shape * efficiency product
        func = ROOT.RooEffProd(f"{func_config.name}{self.category.label}_{self.era}",
                               f"{func_config.name}{self.category.label}_{self.era}", 
                               cheb_func, fermi_func)
        
        self.background_functions[func_config.name] = func
        return func

    def _create_bernstein_exp_function(self, func_config: BackgroundFunction):
        """Create Bernstein polynomial function"""
        # Create parameters
        params = self._create_vars(func_config)

        # retrieve Bernstein params
        bernstein_params = [self.workspace.obj(f"{name}{self.category.label}_{self.era}") for name in func_config.param_names[:-2]]
        # retrieve Exponential param
        exp_param = self.workspace.obj(f"{func_config.param_names[-2]}{self.category.label}_{self.era}")

        # create additive fraction
        bernstein_frac = self.workspace.obj(f"{func_config.param_names[-1]}{self.category.label}_{self.era}")

        # Create bernstein func
        bernstein_func = ROOT.RooBernstein(f"{func_config.name}_bernstein{self.category.label}_{self.era}",
                                          f"{func_config.name}_bernstein{self.category.label}_{self.era}", self.mass_var, bernstein_params)
        # Create exponential func
        exp_func = ROOT.RooExponential(f"{func_config.name}_exp{self.category.label}_{self.era}",
                                       f"{func_config.name}_exp{self.category.label}_{self.era}", self.mass_var, exp_param)

        # store intermediate funcs for ownership
        self.background_functions[f"{func_config.name}_bernstein"] = bernstein_func
        self.background_functions[f"{func_config.name}_exp"] = exp_func

        # Final function is sum of the two
        func = ROOT.RooAddPdf(f"{func_config.name}{self.category.label}_{self.era}",
                              f"{func_config.name}{self.category.label}_{self.era}",
                              ROOT.RooArgList(bernstein_func, exp_func),
                              ROOT.RooArgList(bernstein_frac))
        
        self.background_functions[func_config.name] = func

    def _create_modified_bw(self, func_config: BackgroundFunction):
        """Create polynomial × exponential function"""
        # Create parameters
        params = self._create_vars(func_config)

        modifiedbw_params = [self.workspace.obj(f"{name}{self.category.label}_{self.era}") for name in func_config.param_names]
        args = ROOT.RooArgList([self.mass_var] + modifiedbw_params)

        # # formula = e^(a_1 x + a_2 x^2) / ((x - mu)^a_3 + (sigma)^a_3)
        # formula = "exp(@0 * @1 + @2 * @0**2) / (TMath::Power((@0 - @4), @3) + TMath::Power(@5, @3))"

        # formula = e^(a_1 x + a_2 x^2) / ((x - mu))
        formula = "exp(@0 * @1 + @2 * @0**2) / (@0 - @3)"

        func = ROOT.RooGenericPdf(f"{func_config.name}{self.category.label}_{self.era}", formula, args)

        self.background_functions[func_config.name] = func
        
    def _create_vars(self, func_config: BackgroundFunction) -> ROOT.RooArgList:
        for i, (name, init, limits) in enumerate(zip(func_config.param_names, func_config.param_inits, func_config.param_limits)):
            print(f"DEBUG: creating variable {name}{self.category.label}_{self.era} with init {init}, limits {limits}", flush=True)
            self.workspace.factory(f"{name}{self.category.label}_{self.era}[{init}, {limits[0]}, {limits[1]}]")
        
        pars = ROOT.RooArgList([self.workspace.obj(f"{name}{self.category.label}_{self.era}") for name in func_config.param_names])
        return pars

    def setup_resonant_backgrounds(self):
        """Setup resonant background models (J/psi, psi(2S), etc.) for a specific category"""
        print(f"Setting up resonant background models for category {self.category.display_name}, region: {self.config.chosen_fit_region.name}...")
        
        if self.config.floating_resonant:
            print("DEBUG: creating floating resonant models", flush = True)
            # Create floating resonant background models
            self.resonant_backgrounds = self._create_floating_resonant_models()
        else:
            # FIXME: make also this flexible
            # Get category-specific resonant background templates from workspace
            jpsi_template = self.workspace.obj(f"Zd_M3.1{self.category.label}_{self.era}")  # J/psi template
            print("DEBUG: jpsi_template = ", jpsi_template, flush = True)
            psi2s_template = self.workspace.obj(f"Zd_M3.7{self.category.label}_{self.era}")  # psi(2S) template
            print("DEBUG: psi2s_template = ", psi2s_template, flush = True)
            
            if not jpsi_template or not psi2s_template:
                print(f"Warning: Resonant background templates not found in workspace for category {self.category.display_name}")
                print(f"  Looking for: Zd_M3.1{self.category.label}, Zd_M3.7{self.category.label}")
                return
            else:
                # Add era suffix at rename time (don't assume it's already in input)
                jpsi_template.SetName(f"jpsi_model_{self.era}")
                psi2s_template.SetName(f"psi2s_model_{self.era}")

            # Use fixed resonant background templates from workspace
            self.resonant_backgrounds["jpsi"] = jpsi_template
            self.resonant_backgrounds["psi2s"] = psi2s_template
        
        print("DEBUG: resonant backgrounds = ", self.resonant_backgrounds, flush = True)
        for name, model in self.resonant_backgrounds.items():
            print("DEBUG: ", name, flush = True)
            print("\t DEBUG: ", model, flush = True)
            
        print(f"  Setup {len(self.resonant_backgrounds)} resonant background models")
        
    def _create_floating_resonant_models(self) -> Dict[str, ROOT.RooAbsPdf]:
        """Create floating resonant background models with configurable parameters"""
        models = {}

        # retrieve list of resonant backgrounds 
        resonant_bkg_list = self.config.chosen_fit_region.backgrounds

        for model_name in resonant_bkg_list:
            print(f"    Creating floating {model_name} resonant background for category {self.category.display_name}, region {self.config.chosen_fit_region}...", flush=True) #FIXME: remove flush
            model_config = self.config.resonant_models.get(model_name)        
            
            # Create parameters and import them into workspace for ownership
            params = {}
            for param_name, init_val in model_config["initial_params"].items():
                var_name = f"{model_name}_{param_name}{self.category.label}_{self.era}"
                
                # Set reasonable limits based on parameter type
                if "mean" in param_name:
                    # limits = (init_val * 0.95, init_val * 1.05)
                    limits = (init_val * 0.98, init_val * 1.02)
                elif "sigma" in param_name:
                    # limits = (0.01, 0.2)
                    limits = (init_val * 0.1, init_val * 3) #0.5,2
                    # limits = (init_val * 0.5, init_val * 2) #0.5,2
                elif param_name in ["alphaL", "alphaR"]:
                    # limits = (0.1, 10)
                    limits = (init_val * 0.5, init_val * 2)
                    # limits = (init_val * 0.25, init_val * 8)
                elif param_name in ["nL", "nR"]:
                    # limits = (3, 50)
                    limits = (0.1, 50)
                    # limits = (init_val * 0.5, init_val * 2)
                else:
                    limits = (0.1, 10)
                    # limits = (init_val * 0.5, init_val * 2)
                    
                param = ROOT.RooRealVar(var_name, var_name, init_val, limits[0], limits[1])
                print("DEBUG: created parameter", param, "with name", var_name, flush = True)
                
                # Import parameter into workspace to maintain ownership
                self.workspace.Import(param, ROOT.RooCmdArg())
                # Get the parameter back from workspace to ensure proper ownership
                params[param_name] = self.workspace.obj(var_name)

                print(f"DEBUG: imported parameter {var_name} into workspace (is constant? {params[param_name].isConstant()})", flush = True)
                
            # Create double-sided Crystal Ball (typical resonant background shape)
            full_model_name = f"{model_name}_resonant_bkg{self.category.label}_{self.era}"

            if model_name == "jpsi":
                mean_init = model_config["initial_params"].get("mean")
                sigma_init = model_config["initial_params"].get("sigma")

                mean_core_name = f"{model_name}_mean_core{self.category.label}_{self.era}"
                sigma_core_name = f"{model_name}_sigma_core{self.category.label}_{self.era}"

                mean_core = ROOT.RooRealVar(
                    mean_core_name,
                    mean_core_name,
                    mean_init,
                    mean_init * 0.95,
                    mean_init * 1.05,
                )
                sigma_core = ROOT.RooRealVar(
                    sigma_core_name,
                    sigma_core_name,
                    sigma_init,
                    0.01,
                    0.2,
                )

                self.workspace.Import(mean_core, ROOT.RooCmdArg())
                self.workspace.Import(sigma_core, ROOT.RooCmdArg())
                mean_core = self.workspace.obj(mean_core_name)
                sigma_core = self.workspace.obj(sigma_core_name)

                frac_name = f"{model_name}_core_frac{self.category.label}_{self.era}"
                core_frac = ROOT.RooRealVar(frac_name, frac_name, 0.0, 0.0, 1.0) #try starting from ~0.5
                self.workspace.Import(core_frac, ROOT.RooCmdArg())
                core_frac = self.workspace.obj(frac_name)

                cb_model = ROOT.RooCrystalBall(
                    f"{model_name}_cb{self.category.label}_{self.era}",
                    model_config["title"],
                    self.mass_var,
                    params["mean"], params["sigma"],
                    params["alphaL"], params["nL"],
                    params["alphaR"], params["nR"],
                )

                gauss_model = ROOT.RooGaussian(
                    f"{model_name}_gauss{self.category.label}_{self.era}",
                    model_config["title"],
                    self.mass_var,
                    mean_core,
                    sigma_core,
                )

                self.workspace.Import(cb_model, ROOT.RooCmdArg())
                self.workspace.Import(gauss_model, ROOT.RooCmdArg())

                cb_model = self.workspace.obj(f"{model_name}_cb{self.category.label}_{self.era}")
                gauss_model = self.workspace.obj(f"{model_name}_gauss{self.category.label}_{self.era}")

                model = ROOT.RooAddPdf(
                    full_model_name,
                    model_config["title"],
                    ROOT.RooArgList(cb_model, gauss_model),
                    ROOT.RooArgList(core_frac),
                )
            else:
                model = ROOT.RooCrystalBall(
                    full_model_name, model_config["title"],
                    self.mass_var,
                    params["mean"], params["sigma"],
                    params["alphaL"], params["nL"],
                    params["alphaR"], params["nR"]
                )
            
            print("DEBUG: created floating model", model, flush = True)
            
            # Import model into workspace to maintain ownership
            self.workspace.Import(model, ROOT.RooCmdArg())
            # Get the model back from workspace to ensure proper ownership
            models[model_name] = self.workspace.obj(full_model_name)
            
        print(f"DEBUG: Resonant models = {models}", flush = True)
        return models
        
    def setup_normalizations(self):
        """Setup normalization variables"""
        print("Setting up normalizations...")
        
        # Create normalization variables
        for comp_type, params in self.config.normalization_settings.items():
            for var_name, settings in params.items():
                if "init_param" in settings.keys():
                    # extract maximum value from self.data
                    # first, extract bin width from mass var
                    max_val = self.data.sumEntries()
                    var = ROOT.RooRealVar(f"{var_name}{self.category.label}_{self.era}", var_name, 
                                        max_val * settings["init_param"], max_val * settings["min_param"], max_val * settings["max_param"])
                else:
                    var = ROOT.RooRealVar(f"{var_name}{self.category.label}_{self.era}", var_name, 
                                        settings["init"], settings["min"], settings["max"])
                print(f"DEBUG: created normalization variable {var}", flush = True)
                self.workspace.Import(var, ROOT.RooCmdArg())
                
    def fit_background_to_sidebands(self, fit_region: FitRegion) -> Dict[str, FitResult]:
        """Fit all background functions to sideband regions"""
        print(f"Fitting background functions to sidebands...")
        
        print("DEBUG: setting sidebands range", flush = True)
        sideband_range = self.setup_mass_ranges(fit_region)
        print(f"DEBUG:  Sideband range: {sideband_range}", flush=True)
        results = {}
        
        background_funcs = self.config.background_functions if self.config.chosen_bkg_function < 0 else [self.config.get_chosen_background_function()]
        print("DEBUG: chosen background function index", self.config.chosen_bkg_function, flush = True)
        print("DEBUG: chosen_background_function?", self.config.get_chosen_background_function(), flush = True)
        print("DEBUG: background_funcs", background_funcs, flush = True)
        for func_config in background_funcs:
            print("DEBUG: func_config", func_config, flush = True)
            func_name = func_config.name
            print(f"  Fitting {func_config.display_name}...", flush = True)
            
            if func_name not in self.background_functions:
                print(f"    Warning: Function {func_name} not created")
                continue
            
            print("DEBUG: retrieving function", flush = True)
            func = self.background_functions[func_name]
            print(func)
            
            # Perform fit
            print("DEBUG: fitting sidebands first", flush = True)
            print(f"DEBUG: data = {self.data}; num entries = {self.data.sumEntries()}", flush = True)
            print("DEBUG: func = ", func, flush = True)
            print("DEBUG: range = ", sideband_range, flush = True)

            fit_result_obj = func.fitTo(self.data,
                                      ROOT.RooFit.Range(sideband_range), 
                                      ROOT.RooFit.Save(),
                                      ROOT.RooFit.NumCPU(8),
                                      ROOT.RooFit.SumW2Error(True))  #FIXME: True
            
            # Store results
            result = FitResult(func_name, fit_region.name)
            result.fit_status = int(fit_result_obj.status())
            
            # Get parameters
            params = func.getParameters(self.data)
            n_free = params.selectByAttrib("Constant", False).getSize()
            result.n_free_params = n_free
            
            for param in params:
                param_name = param.GetName()
                result.add_parameter(param_name, param)
                
            results[func_name] = result
            print(f"    DEBUG: post-sidebands fit parameters:", flush = True)
            for pname, pval in result.parameters.items():
                print(f"      {pname} = {pval:.4f} ± {result.parameter_errors[pname]:.4f}", flush = True)
            print(f"    Fit status: {result.fit_status}, free params: {n_free}", flush = True)
            
        return results
        
    def create_combined_model(self, fit_region: FitRegion):
        """Create combined resonant + non-resonant background model"""
        
        # Get chosen non-resonant background function
        chosen_bkg = self.get_chosen_background_function()
        print("DEBUG: chosen bkg f = ", chosen_bkg, flush = True)
        if not chosen_bkg:
            raise ValueError("No non-resonant background function chosen")
        
        # When no_res is set, create a simple combined model with just the background function
        # but keep the naming consistent (full_bkg_model)
        if self.config.no_res:
            print("Creating combined model (background-only for no_res mode)...", flush=True)
            # Clone chosen_bkg function and rename it
            self.combined_model = chosen_bkg.Clone(f"full_bkg_model{self.category.label}_{self.era}")
            print("  Combined model created (background-only)", flush=True)
            return
            
        # Normal case: create combined model with resonant backgrounds
        print("Creating combined background model (resonant + non-resonant)...", flush = True)
        
        # Create combined model: resonant backgrounds + non-resonant background
        model_list = ROOT.RooArgList([model for model in self.resonant_backgrounds.values()] + [chosen_bkg])
        norm_list = ROOT.RooArgList([
            self.workspace.obj(f"{norm_name}{self.category.label}_{self.era}") for norm_name in self.config.normalization_settings["background_components"].keys()
            if norm_name[1:] in self.resonant_backgrounds.keys() or norm_name == "ndy"
        ])

        for norm in norm_list:
            print("DEBUG: norm ", norm.GetName(), " = ", norm.getValV(), flush = True)
        for model in model_list:
            print("DEBUG: model", model, flush=True)

        self.combined_model = ROOT.RooAddPdf(f"full_bkg_model{self.category.label}_{self.era}", f"full_bkg_model{self.category.label}_{self.era}", model_list, norm_list)
        
        print("  Combined background model created", flush = True)
        self.combined_model.Print()
        
    def get_chosen_background_function(self) -> Optional[ROOT.RooAbsPdf]:
        """Get the chosen background function"""
        func_config = self.config.get_chosen_background_function()
        print(f"DEBUG: background functions = {self.background_functions}; retrieving {func_config.name}", flush = True)
        return self.background_functions.get(func_config.name)
        
    def fit_combined_model(self, fit_region: FitRegion) -> FitResult:
        """Fit the combined background model"""
        print(f"Fitting combined background model to {fit_region.display_name}...")
        
        if not self.combined_model:
            raise ValueError("Combined model not created")

        # Store prefit parameter values
        prefit_values = {}
        params = self.combined_model.getParameters(self.data)
        for param in params:
            prefit_values[param.GetName()] = param.getValV()            

        print("DEBUG: fitting combined model", flush = True)
        print(f"DEBUG: data entries = {self.data.sumEntries()}", flush = True)
        print(f"DEBUG: normalizations:", flush = True)
        for norm_name in self.config.normalization_settings['background_components'].keys():
            print(f"  {norm_name}: {self.workspace.obj(f'{norm_name}{self.category.label}_{self.era}').getValV()}", flush = True)

        # Setup fit arguments dynamically for easy commenting/iteration
        fit_args = [
            ROOT.RooFit.Range(fit_region.name),
            ROOT.RooFit.Save(),
            ROOT.RooFit.NumCPU(8),
            ROOT.RooFit.SumW2Error(True),
            ROOT.RooFit.Verbose(False),
            ROOT.RooFit.PrintLevel(-1),
            ROOT.RooFit.Warnings(False),
            ROOT.RooFit.PrintEvalErrors(-1),
        ]

        # constraint_pdfs = ROOT.RooArgSet()
        # constraint_objs = []

        # # Do fit (OLD COMMAND)
        # fit_result_obj = self.combined_model.fitTo(self.data, *fit_args)

        # =========================================================================
        # START: OPTIONAL GAUSSIAN CONSTRAINTS FOR RESONANT TAILS
        # =========================================================================
        # Set to False to quickly disable all constraints below
        use_constraints = True
        
        constraint_pdfs = ROOT.RooArgSet()
        constraint_objects = [] # Prevents PyROOT garbage collector from deleting PDFs
        
        if use_constraints:
            print("DEBUG: Building Gaussian constraints for resonant tail parameters", flush=True)
            for res_name, res_model in self.resonant_backgrounds.items():
                
                if not any(res in res_name for res in ["upsilon1s", "upsilon2s", "omega", "phi"]):
                    continue  # Only apply constraints to Upsilon1S/2S and omega, phi

                res_params = res_model.getParameters(self.data)
                
                for param in res_params:
                    p_name = param.GetName()
                    
                    # Target tail parameters (alphaL, alphaR, nL, nR)
                    if not param.isConstant() and any(tail in p_name for tail in ["alpha", "nL", "nR"]):

                        # for omega, phi: only constrain nL/nR
                        if res_name in ["omega", "phi"] and "alpha" in p_name:
                            continue
                        
                        # 1. Use the current value (from the prompt fit) as the target
                        central_val = 1 if "alpha" in p_name else 10  # Default central value for nL/nR
                        
                        # 2. Define the sigma (pull strength). Tune these as needed!
                        if "alpha" in p_name:
                            sigma_val = 0.1  # Absolute width for alpha
                        else:
                            sigma_val = 1.0  # Absolute width for n
                            
                        # Create RooConstVars for mean and sigma
                        mean_var = ROOT.RooConstVar(f"{p_name}_target", f"Target for {p_name}", central_val)
                        sigma_var = ROOT.RooConstVar(f"{p_name}_sigma", f"Sigma for {p_name}", sigma_val)
                        
                        # Create the Gaussian constraint PDF
                        constraint = ROOT.RooGaussian(
                            f"{p_name}_constraint", f"Constraint on {p_name}",
                            param, mean_var, sigma_var
                        )
                        
                        constraint_pdfs.add(constraint)
                        constraint_objects.extend([mean_var, sigma_var, constraint])
                        
                        print(f"  Added constraint for {p_name}: mean = {central_val:.3f}, sigma = {sigma_val:.3f}")
        # =========================================================================
        # END: GAUSSIAN CONSTRAINTS BLOCK
        # =========================================================================        

        # Inject constraints if they were created
        if use_constraints and constraint_pdfs.getSize() > 0:
            fit_args.append(ROOT.RooFit.ExternalConstraints(constraint_pdfs))


        # =========================================================================
        # START: ITERATIVE TWO-STEP FIT (REGION 0 ONLY)
        # =========================================================================
        # Toggle this to quickly enable/disable the iterative approach
        use_iterative_fit = False
        max_iterations = 30
        nll_threshold = 0.01
        chi2_threshold = 2.0 #refers to chi2/ndf
        
        if use_iterative_fit and fit_region.name == "region0":
            print("DEBUG: Executing iterative two-step fit for region 0", flush=True)
            
            all_params = self.combined_model.getParameters(self.data)
            
            # 1. Catalog initially floating parameters so we don't unfreeze fixed tails
            floating_res = []
            floating_nonres = []
            
            # Simple string matching to separate them based on resonant names (e.g. 'omega', 'phi')
            res_prefixes = list(self.resonant_backgrounds.keys())
            
            for param in all_params:
                if param.isConstant():
                    continue
                # also exclude normalization parameters (ndy, njpsi, npsi2s, etc.)
                if any (norm in param.GetName() for norm in ["ndy", "njpsi", "npsi2s", "nphi", "nomega", "nupsilon1s", "nupsilon2s"]):
                    continue
                    
                p_name = param.GetName()
                is_res_param = any(res in p_name for res in res_prefixes)
                
                if is_res_param:
                    floating_res.append(param)
                else:
                    floating_nonres.append(param)

            prev_nll = float('inf')
            fit_result_obj = None

            chi2_iter = 999
            n_max_perturbations = 3
            n_iter = 0

            # save initial params (for perturbation)
            pars_init = {}
            for param in floating_nonres:
                pars_init[param.GetName()] = param.getValV()
            for param in floating_res:
                pars_init[param.GetName()] = param.getValV()

            while chi2_iter > chi2_threshold and n_iter < n_max_perturbations:
                n_iter += 1
                print(f"  [Trial {n_iter}/{n_max_perturbations}]: Attempting alternate-freezing fit (resonant/nonresonant)...", flush=True)
                
                # only perturb if first iteration failed
                if n_iter > 1:
                    for param in floating_nonres:
                        # Randomize within ±30% of current value
                        # rand_val = param.getValV() * (1 + random.uniform(-0.3, 0.3))
                        rand_val = pars_init[param.GetName()] * (1 + random.uniform(-0.1, 0.1))
                        param.setVal(rand_val)
                        print(f"    {param.GetName()} randomized to {rand_val:.4f} (range: [{param.getMin():.4f}, {param.getMax():.4f}])", flush=True)
                    for param in floating_res:
                        rand_val = pars_init[param.GetName()] * (1 + random.uniform(-0.1, 0.1))
                        param.setVal(pars_init[param.GetName()])

                for iteration in range(1, max_iterations + 1):
                    print(f"  [Iteration {iteration}/{max_iterations}]", flush=True)
                    
                    # STEP 1: Float non-resonant, freeze resonant
                    for p in floating_res: p.setConstant(True)
                    for p in floating_nonres: p.setConstant(False)
                    self.combined_model.fitTo(self.data, *fit_args)
                    
                    # STEP 2: Float resonant, freeze non-resonant
                    for p in floating_res: p.setConstant(False)
                    for p in floating_nonres: p.setConstant(True)
                    fit_result_obj = self.combined_model.fitTo(self.data, *fit_args)
                    
                    if not fit_result_obj:
                        print("  Fit failed to return a result object. Breaking loop.", flush=True)
                        break
                        
                    current_nll = fit_result_obj.minNll()
                    nll_diff = abs(prev_nll - current_nll)
                    print(f"    NLL: {current_nll:.3f} (delta: {nll_diff:.5f})", flush=True)
                    
                    if nll_diff < nll_threshold:
                        print(f"  Convergence reached at iteration {iteration}.", flush=True)
                        break
                        
                    prev_nll = current_nll

                # final global fit with all parameters floating
                for p in all_params: p.setConstant(False)
                fit_result_obj = self.combined_model.fitTo(self.data, *fit_args)

                # compute chi2 on the fly
                # retrieve number of bins
                chi2_iter = self.combined_model.createChi2(self.data, ROOT.RooFit.Range(fit_region.name)).getVal() / (self.data.numEntries() - len(all_params) - 1)
                print(f"  Final chi2/ndf after iterative fit: {chi2_iter:.3f}", flush=True)
                if chi2_iter < chi2_threshold:
                    print(f"  Iterative fit successful with chi2/ndf < {chi2_threshold:.1f}. Exiting perturbation loop.", flush=True)
                    break
                else:
                    print(f"  Iterative fit did not converge to a good chi2/ndf. Current chi2/ndf = {chi2_iter:.3f}. Retrying with init param perturbation...", flush=True)

            # finally, unfreeze non-resonant parameters (must be floating in combine)
            for p in floating_nonres: p.setConstant(False)
        ### OPTION 1: annealing fit
        else:
            print("DEBUG: Executing Brute-Force Multi-Start Annealing", flush=True)

            all_floating = [p for p in self.combined_model.getParameters(self.data) if not p.isConstant()]
            
            res_params = []
            nonres_params = []
            res_prefixes = list(self.resonant_backgrounds.keys())
            
            for p in all_floating:
                if any(res in p.GetName() for res in res_prefixes):
                    res_params.append(p)
                else:
                    nonres_params.append(p)

            # =====================================================================
            # STEP A: COARSE MULTI-START SEARCH
            # =====================================================================
            print("  [Step A] Randomizing initial conditions to map the global minimum...", flush=True)
            
            # Freeze resonances to prompt-MC values to stabilize the background search
            for p in res_params: p.setConstant(True)

            # # do a few alternate freezing rounds for init
            # for p in nonres_params: p.setConstant(False)
            # for p in res_params: p.setConstant(True)
            # fit_result_obj = self.combined_model.fitTo(self.data, *fit_args)
            # print("DEBUG: Fitting with resonant frozen, non-resonant floating. Result:", flush=True)
            # fit_result_obj.Print()
            # for p in nonres_params: p.setConstant(True)
            # for p in res_params: p.setConstant(False)
            # fit_result_obj = self.combined_model.fitTo(self.data, *fit_args)
            # print("DEBUG: Fitting with non-resonant frozen, resonant floating. Result:", flush=True)
            # fit_result_obj.Print()

            # unfreeze everything again
            for p in nonres_params: p.setConstant(False)
            for p in res_params: p.setConstant(False)

            best_coarse_nll = float('inf')
            best_coarse_chi2 = float('inf')
            best_coarse_snapshot = None
            best_coarse_fit_status = -999
            
            CHI2_THRESHOLD = 1.15
            ROUNDS_INCREMENT = 15
            n_trials = ROUNDS_INCREMENT # Number of random starts
            n_trial_rounds = 10
            trial = 0 # trial counter
            nround = 0 # round counter (rerunning 20 trials is expensive)
            
            # save parameter initial values
            pars_init = {}
            for param in nonres_params:
                pars_init[param.GetName()] = param.getValV()
            for param in res_params:
                pars_init[param.GetName()] = param.getValV()

            while trial < n_trials:
                trial += 1

                # 1. Randomize non-resonant shape parameters across their allowed bounds
                for param in nonres_params:
                    # Do not wildly randomize the overall normalizations (ndy, njpsi) 
                    if any(norm in param.GetName() for norm in ["ndy", "njpsi", "npsi2s", "nphi", "nomega", "nupsilon1s"]):
                        continue

                    # update seed -- otherwise same perturbation across all trials
                    random.seed(trial + nround * n_trials + int(time.time() * 1000) % 100000)
                    rand_val = param.getValV() * (1 + random.uniform(-0.3, 0.3))  # Randomize within ±30% of current value
                    # rand_val = pars_init[param.GetName()] * (1 + random.uniform(-0.3, 0.3))  # Randomize within ±30% of current value
                    param.setVal(rand_val)

                for param in res_params:
                    # Do not wildly randomize the overall normalizations (ndy, njpsi) 
                    if any(norm in param.GetName() for norm in ["ndy", "njpsi", "npsi2s", "nphi", "nomega", "nupsilon1s"]):
                        continue

                    rand_val = pars_init[param.GetName()] * (1 + random.uniform(-0.1, 0.1))  # Randomize within ±30% of current value
                    param.setVal(rand_val)
                
                print("DEBUG:   Trial", trial + 1, "/", n_trials, "randomized initial values:", flush=True)
                for param in nonres_params:
                    print(f"      {param.GetName()} = {param.getValV():.4f} (range: [{param.getMin():.4f}, {param.getMax():.4f}])", flush=True)
                    
                # 2. Quick coarse fit 
                res = self.combined_model.fitTo(self.data, *fit_args)
                print("DEBUG:       Fit result: ", flush=True)
                res.Print()
                
                # 3. Evaluate (Status 3 is acceptable here, it just means HESSE forced pos-def)
                if res and (res.status() == 0 or res.status() == 3):
                    trial_nll = res.minNll()
                    chi2_temp = self.combined_model.createChi2(self.data, ROOT.RooFit.Range(fit_region.name)).getVal() / (self.data.numEntries() - len(all_floating) - 1)
                    
                    if chi2_temp < best_coarse_chi2:
                        best_coarse_chi2 = chi2_temp
                        best_coarse_nll = trial_nll
                        best_coarse_fit_status = res.status() if res else -1
                        floating_now = self.combined_model.getParameters(self.data).selectByAttrib("Constant", False)
                        best_coarse_snapshot = floating_now.snapshot()
                        print(f"    Trial {trial}/{n_trials}: Found new best coarse chi2/ndf = {chi2_temp:.3f}", flush=True)

                    # if trial_nll < best_coarse_nll:
                    #     best_coarse_nll = trial_nll
                    #     floating_now = self.combined_model.getParameters(self.data).selectByAttrib("Constant", False)
                    #     best_coarse_snapshot = floating_now.snapshot()
                    #     print(f"    Trial {trial+1}/{n_trials}: Found new best coarse NLL = {trial_nll:.3f}", flush=True)
                    #     # compute chi2 on the fly 
                    #     chi2_temp = self.combined_model.createChi2(self.data, ROOT.RooFit.Range(fit_region.name)).getVal() / (self.data.numEntries() - len(all_floating) - 1)
                    #     print(f"    Trial {trial+1}/{n_trials}: Coarse fit chi2/ndf = {chi2_temp:.3f}", flush=True)
                    #     best_coarse_fit_status = res.status() if res else -1
                else:
                    status = res.status() if res else -1
                    print(f"    Trial {trial+1}/{n_trials}: Failed convergence (Status {status})", flush=True)
                
                # if at the last trial, compute chi2 and check that it's not too bad
                if trial == n_trials:
                    # restore best coarse snapshot for final fit
                    if best_coarse_snapshot:
                        floating_params = self.combined_model.getParameters(self.data).selectByAttrib("Constant", False)
                        floating_params.assignValueOnly(best_coarse_snapshot)
                    else:
                        print("  [Warning] All coarse trials failed. Proceeding with default initialization.", flush=True)
                    chi2_iter = self.combined_model.createChi2(self.data, ROOT.RooFit.Range(fit_region.name)).getVal() / (self.data.numEntries() - len(all_floating) - 1)
                    print(f"  Final coarse fit chi2/ndf: {chi2_iter:.3f}", flush=True)
                    if chi2_iter > CHI2_THRESHOLD:
                        print("  Warning: Coarse fit did not converge to a good chi2/ndf.")
                        if nround < n_trial_rounds - 1:
                            print(f"  Retrying coarse fit with new random initializations (round {nround + 2}/{n_trial_rounds})...", flush=True)
                            n_trials += ROUNDS_INCREMENT
                            nround += 1
                            # reset parameters to initial values
                            for param in nonres_params:
                                param.setVal(pars_init[param.GetName()])
                            for param in res_params:
                                param.setVal(pars_init[param.GetName()])
                        else:
                            print("  ERROR: Maximum trial rounds reached with bad chi2. Check this out.", flush=True)
                            break
                        

            # =====================================================================
            # STEP B: RESTORE BEST AND FLOAT ALL (GLOBAL FIT)
            # =====================================================================
            if best_coarse_snapshot:
                print(f"  [Step B] Restoring best coarse minimum (NLL={best_coarse_nll:.3f}) and floating resonances...", flush=True)
                floating_params = self.combined_model.getParameters(self.data).selectByAttrib("Constant", False)
                floating_params.assignValueOnly(best_coarse_snapshot)
            else:
                print("  [Warning] All coarse trials failed. Proceeding with default initialization.", flush=True)

            # # Unfreeze resonances for the final fit
            # for p in res_params: p.setConstant(False)
            
            # print("  [Step C] Executing final high-precision global fit...", flush=True)
            
            # # Optional: Tell MINUIT to compute a more rigorous Hessian for the final error matrix
            # ROOT.Math.MinimizerOptions.SetDefaultStrategy(2)
            # ROOT.Math.MinimizerOptions.SetDefaultTolerance(0.001)
            
            # fit_result_obj = self.combined_model.fitTo(self.data, *fit_args)
            # print("DEBUG: Final fit result:", flush=True)
            # fit_result_obj.Print()

        # =========================================================================
        # END: ITERATIVE FIT
        # =========================================================================
        
        # ##### REMOVE ME #######
        # fit_result_obj = self.combined_model.fitTo(self.data, *fit_args)
        # print("DEBUG: Final fit result:", flush=True)
        # fit_result_obj.Print()

        # Store results
        result = FitResult("full_bkg_model", fit_region.name)
        result.fit_status = int(best_coarse_fit_status) if not use_iterative_fit else int(fit_result_obj.status())
        # result.fit_status = 999
        
        # Get parameters
        params = self.combined_model.getParameters(self.data)
        n_free = params.selectByAttrib("Constant", False).getSize()
        result.n_free_params = n_free
        
        for param in params:
            param_name = param.GetName()
            prefit_val = prefit_values.get(param_name)
            result.add_parameter(param_name, param, prefit_val)
        
        print(f"  DEBUG: post-total fit parameters:", flush = True)
        for pname, pval in result.parameters.items():
            print(f"      {pname} = {pval:.4f} ± {result.parameter_errors[pname]:.4f}", flush = True)
        print(f"  Fit status: {result.fit_status}, free params: {n_free}")

        print(f"DEBUG: freezing resonant bkg parameters on total fit result", flush = True)
        for resonant_bkg in self.resonant_backgrounds.values():
            res_params = resonant_bkg.getParameters(self.data)
            for param in res_params:
                if param.isConstant():
                    print(f"  Resonant parameter {param.GetName()} frozen on prompt MC already, skipping...", flush = True)
                    continue
                else:
                    param.setConstant(True)
                    print(f"  Frozen: {param.GetName()} to data", flush = True)

        return result
        
    def freeze_background_parameters(self):
        """Freeze background parameters after sideband fit"""
        if not self.config.freeze_bkg_sidebands:
            return
            
        print("Freezing background parameters...")
        chosen_bkg = self.get_chosen_background_function()
        if not chosen_bkg:
            return
            
        params = chosen_bkg.getParameters(self.data)
        for param in params:
            param.setConstant(True)
            print(f"  Frozen: {param.GetName()}")
        
    def fit_floating_resonant_to_prompt(self) -> FitResult:
        """Fit floating resonant background models to prompt dataset(s)"""
        print("Fitting floating resonant background models to prompt dataset(s)...")
        
        region = self.config.chosen_fit_region
        res_data_config = region.background_resonant_data
        result = FitResult("resonant_prompt_fits", region.name)

        print("DEBUG: fitting prompt MC", flush=True)
        
        def apply_post_fit_constraints(model, data, is_individual, freeze=False):
            """Helper to constrain parameters post-fit to prevent code duplication."""
            for param in model.getParameters(data):
                if freeze:
                    param.setConstant(True)
                    print(f"  Frozen parameter: {param.GetName()} = {param.getValV():.5f}")
                elif not param.isConstant():
                    central_val = param.getValV()
                    if is_individual:
                        # 5% core tolerance, strictly freeze tails
                        if any(x in param.GetName() for x in ["alpha", "nL", "nR"]):
                            param.setConstant(True)
                            print(f"  Frozen tail parameter: {param.GetName()} = {central_val:.5f}")
                        else:
                            tol = 0.3
                            param.setRange(central_val*(1 - tol), central_val*(1 + tol))
                            print(f"  Constrained core: {param.GetName()} to [{param.getMin():.5f}, {param.getMax():.5f}]")
                    else:
                        # Legacy tolerance logic for merged fits
                        tol = 0.3
                        # if "alphaR" in param.GetName() and "omega" in model.GetName():
                        #     tol = 0.8
                        # if any(x in param.GetName() for x in ["nL", "nR"]) and "phi" in model.GetName():
                        #     tol = 0.8
                        param.setRange(max(param.getMin(), central_val*(1 - tol)), 
                                       min(param.getMax(), central_val*(1 + tol)))

        # ---------------------------------------------------------
        # DICT LOGIC: Fit models independently using separate datasets
        # ---------------------------------------------------------
        if isinstance(res_data_config, dict):
            for model_name, _ in res_data_config.items():
                dataset_name = f"data_obs{self.category.label}_{model_name}"
                resonant_data = self.workspace.data(dataset_name)
                
                if not resonant_data:
                    raise ValueError(f"Prompt dataset '{dataset_name}' not found in workspace.")
                    
                model = self.resonant_backgrounds[model_name]
                print(f"Fitting {model_name} independently on dataset {dataset_name}...")
                
                fit_result_obj = model.fitTo(resonant_data, ROOT.RooFit.NumCPU(8), 
                                             ROOT.RooFit.Range(region.name), ROOT.RooFit.Save())
                
                if fit_result_obj:
                    result.fit_status = max(result.fit_status, int(fit_result_obj.status()))
                
                # FIXME: all resonances are frozen. just skip the freezing altogether
                if "jpsi" in model.GetName() or "psi2s" in model.GetName() or "phi" in model.GetName() or "omega" in model.GetName() or "upsilon1s" in model.GetName() or "upsilon2s" in model.GetName():
                    continue
                # CURRENT IMPLEMENTATION: Just freeze all resonant params (can change limits, add soft constraint, etc)                    
                apply_post_fit_constraints(model, resonant_data, is_individual=False, freeze=True)
                
        # ---------------------------------------------------------
        # STRING LOGIC: Fit RooAddPdf using a single shared dataset
        # ---------------------------------------------------------
        else:
            resonant_data = self.workspace.data(f"data_obs{self.category.label}_resonant")
            if not resonant_data:
                raise ValueError(f"Prompt dataset 'data_obs{self.category.label}_resonant' not found in workspace")
                
            models = list(self.resonant_backgrounds.values())
            fractions = [ROOT.RooRealVar(f"fraction_{m}", f"fraction_{m}", f, 0, 1) 
                         for m, f in zip(region.backgrounds[:-1], region.background_fractions)]
            
            combined_resonant_model = ROOT.RooAddPdf("combined_resonant_bkg", "combined_resonant_bkg",
                                                     ROOT.RooArgList(*models), ROOT.RooArgList(*fractions))
                                                     
            self.workspace.Import(combined_resonant_model, ROOT.RooCmdArg())
            combined_resonant_model = self.workspace.obj("combined_resonant_bkg")
            
            prefit_values = {p.GetName(): p.getValV() for p in combined_resonant_model.getParameters(resonant_data)}
            
            # fit_result_obj = combined_resonant_model.fitTo(resonant_data, ROOT.RooFit.NumCPU(8), 
            #                                                ROOT.RooFit.Range(region.name), ROOT.RooFit.Save())
            fit_result_obj = None

            result.fit_status = int(fit_result_obj.status()) if fit_result_obj else -1
            
            params = combined_resonant_model.getParameters(resonant_data)
            result.n_free_params = params.selectByAttrib("Constant", False).getSize()
            for param in params:
                result.add_parameter(param.GetName(), param, prefit_values.get(param.GetName()))
                
            for model in models:
                if "jpsi" in model.GetName() or "psi2s" in model.GetName() or "phi" in model.GetName() or "omega" in model.GetName() or "upsilon1s" in model.GetName() or "upsilon2s" in model.GetName():
                    continue
                # CURRENT IMPLEMENTATION: Just freeze all resonant params (can change limits, add soft constraint, etc)
                apply_post_fit_constraints(model, resonant_data, is_individual=False, freeze=True)
                
            self.resonant_combined_model = combined_resonant_model
            self.resonant_data = resonant_data
            
        return result

    def calculate_integrals(self, fit_region: FitRegion) -> Dict[str, float]:
        """Calculate integrals of model components"""
        if not self.combined_model:
            return {}
            
        integrals = {}
        
        # Calculate integrals for each component
        components = {
            "jpsi_bkg": self.resonant_backgrounds.get("jpsi"),
            "psi2s_bkg": self.resonant_backgrounds.get("psi2s"),
            "nonresonant_bkg": self.get_chosen_background_function()
        }
        
        for name, component in components.items():
            if component:
                integral_obj = component.createIntegral(ROOT.RooArgSet(self.mass_var), 
                                                      ROOT.RooFit.Range(fit_region.name))
                integrals[name] = integral_obj.getVal()
                
        return integrals
        
    def save_workspace(self):
        """Save fitted models to the centralized output workspace"""
        print(f"Adding fitted models to centralized workspace for category {self.category.name}...")
        
        if not self.output_workspace:
            print("⚠️  Warning: No centralized output workspace available, using local workspace")
            # Fallback to old behavior
            output_path = self.config.get_output_workspace_path()
            self.workspace.writeToFile(str(output_path))
            print(f"  Workspace saved to: {output_path}")
            return
        
        # Import fitted models to centralized output workspace with category-specific names
        category_label = self.category.label
        
        for model_name, model in self.resonant_backgrounds.items():
            print(f"DEBUG: resonant background model {model_name}: {model}", flush=True)

            # NEW APPROACH
            # Clone the model with a new name before importing
            new_name = f"{model_name}{category_label}_{self.era}"
            model_clone = model.Clone(new_name)
            self.output_workspace.Import(model_clone, ROOT.RooFit.RecycleConflictNodes())            

            # # OLD APPROACH
            # # Rename pdf inline while importing -- stopped working at some point
            # self.output_workspace.Import(model, ROOT.RooFit.RenameVariable(model.GetName(), f"{model_name}{category_label}"))

            print(f"  ✅ Added {model_name} model: {new_name}")

        # # Import resonant background models
        # if "jpsi" in self.resonant_backgrounds:
        #     model_name = f"jpsi{category_label}"
        #     # self.resonant_backgrounds["jpsi"].SetName(model_name)
        #     self.output_workspace.Import(self.resonant_backgrounds["jpsi"],
        #                                  ROOT.RooFit.RenameVariable(self.resonant_backgrounds["jpsi"].GetName(), model_name))
        #     print(f"  ✅ Added J/psi model: {model_name}")
            
        # if "psi2s" in self.resonant_backgrounds:
        #     model_name = f"psi2s{category_label}"
        #     # self.resonant_backgrounds["psi2s"].SetName(model_name)
        #     self.output_workspace.Import(self.resonant_backgrounds["psi2s"], 
        #                                  ROOT.RooFit.RenameVariable(self.resonant_backgrounds["psi2s"].GetName(), model_name))
        #     print(f"  ✅ Added ψ(2S) model: {model_name}")
                                
        # Import non-resonant background function
        chosen_bkg = self.get_chosen_background_function()
        if chosen_bkg:
            print(f"DEBUG: IMPORTING CHOSEN BACKGROUND FUNCTION: {chosen_bkg.GetName()}", flush=True)
            model_name = f"dy{category_label}_{self.era}"
            self.output_workspace.Import(chosen_bkg, ROOT.RooFit.RenameVariable(chosen_bkg.GetName(), model_name))
            print(f"  ✅ Added non-resonant background: {model_name}")
                                
        # Import combined model
        if self.combined_model:
            model_name = f"full_bkg_model{category_label}_{self.era}"
            # self.output_workspace.Import(self.combined_model, ROOT.RooCmdArg()) #True)#ROOT.RooFit.RenameVariable(self.combined_model.GetName(), model_name))
            self.output_workspace.Import(self.combined_model, ROOT.RooFit.RecycleConflictNodes()) #True)#ROOT.RooFit.RenameVariable(self.combined_model.GetName(), model_name))

            print(f"  ✅ Added combined model: {model_name}")
            
        # Import category-specific dataset if available
        if self.data:
            self.output_workspace.Import(self.data)
            print(f"  ✅ Added dataset: {self.data.GetName()}")

        # print parameter values for each model EXCLUDING SIGNAL:
        for model in self.output_workspace.allPdfs():
            if not model.GetName().startswith("Zd"):
                print(f"  Model: {model.GetName()}")
                params = model.getParameters(self.data)
                model.Print()
                print(f"DEBUG: Parameters for model {model.GetName()}, category {category_label}:")
                for param in params:
                    # Check if parameter is close to boundary
                    val = param.getValV()
                    min_val = param.getMin()
                    max_val = param.getMax()
                    range_size = max_val - min_val
                    
                    # Check if within 1% of boundary
                    boundary_warning = ""
                    if abs(val - min_val) < 0.01 * range_size or abs(val - max_val) < 0.01 * range_size:
                        boundary_warning = " ⚠️  BOUNDARY WARNING (within 1%)"
                    
                    print(f"    {param.GetName()}: {val:.5f} ± {param.getError():.5f} (limits: [{min_val:.5g}, {max_val:.5g}]){boundary_warning}", flush = True)
        
        print(f"✅ Category {self.category.name} models added to centralized workspace")
        
    def open_log_file(self, fit_region: str, tag: str = "", category: str = ""):
        """Open log file for writing results"""
        log_path = self.config.get_log_file_path(fit_region, tag, category)
        self.log_file = open(log_path, "w")
        print(f"Logging to: {log_path}")
        
    def close_log_file(self):
        """Close log file"""
        if self.log_file:
            self.log_file.close()
            self.log_file = None
            
    def log_print(self, message: str):
        """Print and log message"""
        print(message)
        if self.log_file:
            self.log_file.write(message + "\n")
            self.log_file.flush()
