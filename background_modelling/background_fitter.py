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
            root_file.Close()
            return False
            
        print(f"  Loaded dataset '{dataset_name}' with {self.data.numEntries()} entries")
        print(f"  Mass variable range: [{self.mass_var.getMin():.2f}, {self.mass_var.getMax():.2f}] GeV")
        
        # # Convert to binned data if requested
        # if self.config.use_binned:
        #     self.data = self._convert_to_binned()
            
        return True
        
    def _convert_to_binned(self) -> ROOT.RooDataHist:
        """Convert dataset to binned format"""
        print("Converting to binned dataset...")
        
        self.mass_var.setBins(100)
        data_binned = ROOT.RooDataHist("data_obs", "data_obs", ROOT.RooArgSet(self.mass_var))
        
        for i in range(self.data.numEntries()):
            self.data.get(i)
            weight = self.data.weight()
            data_binned.add(ROOT.RooArgSet(self.mass_var), weight)
            
        self.workspace.Import(data_binned, True)
        return data_binned
        
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
            print(f"  Creating {func_config.display_name}...")
            
            if func_config.name == "bkg_f0":
                # Bernstein polynomial
                self._create_bernstein_function(func_config)
            elif func_config.name == "bkg_f1":
                # Polynomial × Exponential
                self._create_poly_exp_function(func_config)
            elif func_config.name == "bkg_f2":
                # Sum of exponentials
                self._create_sum_exp_function(func_config)
            elif func_config.name == "bkg_f3":
                # Simple exponential
                self._create_simple_exp_function(func_config)
            elif func_config.name == "bkg_f4":
                # Chebyshev polynomial
                self._create_chebyshev_function(func_config)
            elif func_config.name == "bkg_f5":
                # Bernstein + exponential
                self._create_bernstein_exp_function(func_config)
            elif func_config.name == "bkg_f6":
                # modified BW
                self._create_modified_bw(func_config)
            elif func_config.name == "bkg_f7":
                # 6th deg Chebyshev
                self._create_chebyshev_function(func_config)
            elif func_config.name == "bkg_f8":
                # 5th deg Chebyshev
                self._create_chebyshev_function(func_config)
                
    def _create_bernstein_function(self, func_config: BackgroundFunction):
        """Create Bernstein polynomial function"""
        # Create parameters
        param_list = self._create_vars(func_config)
        # Create function
        func = ROOT.RooBernstein(f"{func_config.name}{self.category.label}_{self.era}",
                                 f"{func_config.name}{self.category.label}_{self.era}", self.mass_var, param_list)
        
        self.background_functions[func_config.name] = func
        
    def _create_poly_exp_function(self, func_config: BackgroundFunction):
        """Create polynomial × exponential function"""
        # Create parameters
        params = self._create_vars(func_config)
            
        # Create polynomial part
        poly_params = [self.workspace.obj(f"{name}{self.category.label}_{self.era}") for name in func_config.param_names[:-1]]
        # poly_params = [self.workspace.obj(f"{name}{self.category.label}_{self.era}") for name in func_config.param_names]

        ## POLYNOMIAL X EXPONENTIAL ###

        # # APPROACH 1 FOR POLYNOMIAL: regularize it (positive definite)
        # # poly_params = [self.workspace.obj(name) for name in func_config.param_names[:-1]]
        # poly_formula = "(1 + @0*@1 + @0**2 * @2 + @0**3 * @3 + @0**4 * @4 + @0**5 * @5) > 0 ? (1 + @0*@1 + @0**2 * @2 + @0**3 * @3 + @0**4 * @4 + @0**5 * @5) : 1e-6"
        # poly_args = ROOT.RooArgList([self.mass_var] + poly_params)
        # poly_func = ROOT.RooGenericPdf(f"{func_config.name}_poly{self.category.label}_{self.era}", poly_formula, poly_args)

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

        # ### JUST POLYNOMIAL ###
        # func = ROOT.RooPolynomial(f"{func_config.name}{self.category.label}_{self.era}", f"{func_config.name}{self.category.label}_{self.era}", 
        #                               self.mass_var, poly_params)

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
                if param_name == "mean":
                    limits = (init_val * 0.95, init_val * 1.05)
                elif param_name == "sigma":
                    # limits = (0.01, 0.2)
                    limits = (init_val * 0.5, init_val * 2)
                elif param_name in ["alphaL", "alphaR"]:
                    # limits = (0.1, 10)
                    limits = (init_val * 0.5, init_val * 2)
                elif param_name in ["nL", "nR"]:
                    # limits = (0.1, 50)
                    limits = (init_val * 0.5, init_val * 2)
                else:
                    # limits = (0.1, 10)
                    limits = (init_val * 0.5, init_val * 2)
                    
                param = ROOT.RooRealVar(var_name, var_name, init_val, limits[0], limits[1])
                print("DEBUG: created parameter", param, "with name", var_name, flush = True)
                
                # Import parameter into workspace to maintain ownership
                self.workspace.Import(param, ROOT.RooCmdArg())
                # Get the parameter back from workspace to ensure proper ownership
                params[param_name] = self.workspace.obj(var_name)

                print(f"DEBUG: imported parameter {var_name} into workspace (is constant? {params[param_name].isConstant()})", flush = True)
                
            # Create double-sided Crystal Ball (typical resonant background shape)
            full_model_name = f"{model_name}_resonant_bkg{self.category.label}_{self.era}"
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
        
    def get_chosen_background_function(self) -> Optional[ROOT.RooAbsPdf]:
        """Get the chosen background function"""
        func_config = self.config.get_chosen_background_function()
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

        # # DEBUG: set resonant bkg params to +-inf
        # for resonant_bkg in self.resonant_backgrounds.values():
        #     res_params = resonant_bkg.getParameters(self.data)
        #     for param in res_params:
        #         param.setRange(0, 1000)
            
        print("DEBUG: fitting combined model", flush = True)
        print(f"DEBUG: data entries = {self.data.sumEntries()}", flush = True)
        print(f"DEBUG: normalizations:", flush = True)
        for norm_name in self.config.normalization_settings['background_components'].keys():
            print(f"  {norm_name}: {self.workspace.obj(f'{norm_name}{self.category.label}_{self.era}').getValV()}", flush = True)

        # Perform fit
        fit_result_obj = self.combined_model.fitTo(self.data,
                                                 ROOT.RooFit.Range(fit_region.name),
                                                 ROOT.RooFit.Save(),
                                                 ROOT.RooFit.NumCPU(8),
                                                 ROOT.RooFit.SumW2Error(True))
        
        # Store results
        result = FitResult("full_bkg_model", fit_region.name)
        result.fit_status = int(fit_result_obj.status())
        
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
                    print("  Resonant parameters frozen on prompt MC already, skipping...", flush = True)
                    continue
                else:
                    param.setConstant(True)
                    print(f"  Frozen: {param.GetName()} (on MinBias sample)", flush = True)

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
        """Fit floating resonant background models to prompt J/psi dataset"""
        print("Fitting floating resonant background models to prompt J/psi dataset...")
        
        # # Load prompt J/psi dataset
        # resonant_file = ROOT.TFile.Open("datasets/dataset_jpsi_test.root") #FIXME: must match output format in dataset_creator.py
        # if not resonant_file or resonant_file.IsZombie():
        #     raise FileNotFoundError("Cannot open prompt J/psi dataset file")
            
        # resonant_w = resonant_file.Get("w")
        # if not resonant_w:
        #     raise ValueError("Workspace 'w' not found in prompt dataset file")
            
        # resonant_data = resonant_w.obj(f'data_obs{self.category.label}')
        # print(f"DEBUG: loading dataset 'data_obs{self.category.label}' from prompt workspace", flush=True)

        # if not resonant_data:
        #     raise ValueError(f"Data 'data_obs{self.category.label}' not found in prompt workspace")

        resonant_data = self.workspace.data(f"data_obs{self.category.label}_resonant")
        if not resonant_data:
            print(f"DEBUG: ERROR LOADING PROMPT DATASET. Workspace content:", flush=True)
            for obj in self.workspace.allData():
                print(f"  {obj.GetName()}", flush=True)
            raise ValueError(f"Prompt dataset 'data_obs{self.category.label}_resonant' not found in workspace")
            
        print(f"  Loaded prompt dataset with {resonant_data.numEntries()} entries")
        
        for resonant_bkg in self.config.chosen_fit_region.backgrounds:
            if resonant_bkg not in self.resonant_backgrounds:
                raise ValueError(f"Resonant background model '{resonant_bkg}' not setup")

        # # Get resonant background models
        # if "jpsi" not in self.resonant_backgrounds or "psi2s" not in self.resonant_backgrounds:
        #     raise ValueError("Resonant background models not setup")

        # jpsi_model = self.resonant_backgrounds["jpsi"]
        # psi2s_model = self.resonant_backgrounds["psi2s"]
        
        # # Create fraction parameter for psi(2S) component
        # fraction_psi2s = ROOT.RooRealVar("fraction_psi2s", "fraction_psi2s", 0.7, 0, 1)

        # # Create combined model
        # jpsi_plus_psi2s = ROOT.RooAddPdf("jpsi_plus_psi2s", "jpsi_plus_psi2s", 
        #                                 ROOT.RooArgList(jpsi_model, psi2s_model), 
        #                                 ROOT.RooArgList(fraction_psi2s))

        models = self.resonant_backgrounds.values()
        fractions = []
        for model_name, frac in zip(self.config.chosen_fit_region.backgrounds[:-1],
                                    self.config.chosen_fit_region.background_fractions):
            frac_var = ROOT.RooRealVar(f"fraction_{model_name}", f"fraction_{model_name}", frac, 0, 1)
            fractions.append(frac_var)

        print(f"DEBUG: creating addPdf with models:")
        for model in models:
            print(model, flush=True)
        print(f"DEBUG: and fractions:")
        for frac in fractions:
            print(frac, flush=True)
            
        # FIXME: change model name to combined_resonant_bkg AND FIX THIS IN PLOTTER TOO
        jpsi_plus_psi2s = ROOT.RooAddPdf("jpsi_plus_psi2s", "jpsi_plus_psi2s",
                                         ROOT.RooArgList(*models),
                                         ROOT.RooArgList(*fractions))

        print(f"DEBUG: combined resonant bkg model: {jpsi_plus_psi2s}", flush=True)
        
        # Import the combined model into workspace to maintain ownership
        self.workspace.Import(jpsi_plus_psi2s, ROOT.RooCmdArg())
        # Get the model back from workspace to ensure proper ownership
        jpsi_plus_psi2s = self.workspace.obj("jpsi_plus_psi2s")
        
        # Store prefit parameter values
        prefit_values = {}
        params = jpsi_plus_psi2s.getParameters(resonant_data)
        for param in params:
            print(f"DEBUG: resonant param before fit: {param.GetName()} = {param.getValV()} (is constant? {param.isConstant()})", flush=True)
            prefit_values[param.GetName()] = param.getValV()

        print(f"DEBUG: fitting resonant model in range {self.config.chosen_fit_region.range[0]} - {self.config.chosen_fit_region.range[1]}", flush=True)
            
        # Perform fit
        fit_result_obj = jpsi_plus_psi2s.fitTo(resonant_data, 
                                               ROOT.RooFit.NumCPU(8), 
                                               ROOT.RooFit.Range(self.config.chosen_fit_region.name), 
                                               ROOT.RooFit.Save())
                                            #    ROOT.RooFit.SumW2Error(True))
                                            #    ROOT.RooFit.RecoverFromUndefinedRegions(4),
        
        print(f"DEBUG: resonant model fit completed", flush=True)
        print(f"DEBUG: fit_result_obj = {fit_result_obj}", flush=True)

        # Store results
        print(f"DEBUG: storing fit results", flush=True)
        result = FitResult("jpsi_plus_psi2s_prompt", self.config.chosen_fit_region.name)
        if not fit_result_obj:
            print("Warning: Fit result object is None")
            result.fit_status = -1
        else:
            result.fit_status = int(fit_result_obj.status())
        
        # Get parameters
        print("DEBUG: getting fit parameters", flush=True)
        params = jpsi_plus_psi2s.getParameters(resonant_data)
        n_free = params.selectByAttrib("Constant", False).getSize()
        result.n_free_params = n_free
        
        for param in params:
            print("DEBUG: processing param", param.GetName(), flush=True)
            param_name = param.GetName()
            prefit_val = prefit_values.get(param_name)
            result.add_parameter(param_name, param, prefit_val)
            
        self.log_print("Fitted jpsi and psi2s models to prompt data")
        for param in params:
            self.log_print(f"param: {param.GetName()}, value: {param.getValV():.5f}, error: {param.getError():.5f} (limits: [{param.getMin():.5g}, {param.getMax():.5g}])")
            
        # Freeze resonant background parameters after fitting to prompt data
        # if self.config.chosen_fit_region.name != "region1":
        print(f"DEBUG: freezing resonant background parameters", flush=True)
        for model in models:
            # skip the jpsi
            if "jpsi" in model.GetName():
                continue
            for param in model.getParameters(resonant_data):
                param.setConstant(True)

        # # CONSTRAINING resonant background parameters after fitting to prompt data
        # print(f"DEBUG: constraining resonant background parameters", flush=True)
        # for model in models:
        #     for param in model.getParameters(resonant_data):
        #         if not param.isConstant():
        #             central_val = param.getValV()
        #             error = param.getError()
        #             # Set limits to ±20% fitted value
        #             tol = 0.2
        #             new_min = max(param.getMin(), central_val*(1 - tol))
        #             new_max = min(param.getMax(), central_val*(1 + tol))
        #             param.setRange(new_min, new_max)
        #             print(f"  Constrained: {param.GetName()} = {central_val:.5f} ± {error:.5f} to [{new_min:.5f}, {new_max:.5f}]")
            
        # for param in jpsi_model.getParameters(resonant_data):
        #     param.setConstant(True)
        # for param in psi2s_model.getParameters(resonant_data):
        #     param.setConstant(True)
            
        print(f"  Prompt fit status: {result.fit_status}, free params: {n_free}", flush = True)
        print("  Resonant background parameters frozen after prompt fit", flush = True)
        
        # Store the combined model for potential plotting
        self.resonant_combined_model = jpsi_plus_psi2s
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
            self.output_workspace.Import(self.combined_model, ROOT.RooCmdArg()) #True)#ROOT.RooFit.RenameVariable(self.combined_model.GetName(), model_name))
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
