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
    
    def __init__(self, config: BackgroundModelConfig, category: CategoryConfig = None):
        self.config = config
        
        # Storage for fit results
        self.fit_results: Dict[str, FitResult] = {}
        
        # ROOT objects
        self.workspace: Optional[ROOT.RooWorkspace] = None
        self.data: Optional[ROOT.RooDataSet] = None
        self.mass_var: Optional[ROOT.RooRealVar] = None

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
        self.prompt_data: Optional[ROOT.RooDataSet] = None
        self.prompt_combined_model: Optional[ROOT.RooAbsPdf] = None
        
        # Log file
        self.log_file: Optional[object] = None
        
        print("Background fitter initialized")
        
    def load_workspace(self) -> bool:
        """Load the workspace and extract data and resonant background templates for a specific category"""        
                    
        print(f"Loading workspace for category: {self.category.display_name}...")
        
        dataset_path = self.config.get_dataset_path()
        if not dataset_path.exists():
            print(f"Error: Dataset file not found: {dataset_path}")
            return False
            
        # Open file and get workspace
        root_file = ROOT.TFile.Open(str(dataset_path))
        if not root_file or root_file.IsZombie():
            print(f"Error: Cannot open file {dataset_path}")
            return False
            
        self.workspace = root_file.Get("w")
        if not self.workspace:
            print("Error: Workspace 'w' not found in file")
            root_file.Close()
            return False
            
        # Get category-specific data and shared mass variable
        dataset_name = f"data_obs{self.category.label}"
        
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
        
        # Convert to binned data if requested
        if self.config.use_binned:
            self.data = self._convert_to_binned()
            
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
        print("DEBUG: setting mass va rrange")
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
                
    def _create_bernstein_function(self, func_config: BackgroundFunction):
        """Create Bernstein polynomial function"""
        # Create parameters
        param_list = self._create_vars(func_config)
        # Create function
        func = ROOT.RooBernstein(f"{func_config.name}{self.category.label}",
                                 f"{func_config.name}{self.category.label}", self.mass_var, param_list)
        
        self.background_functions[func_config.name] = func
        
    def _create_poly_exp_function(self, func_config: BackgroundFunction):
        """Create polynomial × exponential function"""
        # Create parameters
        params = self._create_vars(func_config)
            
        # Create polynomial part
        poly_params = [self.workspace.obj(f"{name}{self.category.label}") for name in func_config.param_names[:-1]]
        # poly_params = params[:-1] # (POTENTIALLY) FIXME: doesn't like accessing RooArgList directly

        # poly_params = [self.workspace.obj(name) for name in func_config.param_names[:-1]]
        poly_formula = "(1 + @0*@1 + @0**2 * @2 + @0**3 * @3 + @0**4 * @4 ) > 0 ? (1 + @0*@1 + @0**2 * @2 + @0**3 * @3 + @0**4 * @4 ) : 1e-6"
        poly_args = ROOT.RooArgList([self.mass_var] + poly_params)
        poly_func = ROOT.RooGenericPdf(f"{func_config.name}_poly{self.category.label}", poly_formula, poly_args)
        
        # Create exponential part
        exp_param = self.workspace.obj(f"{func_config.param_names[-1]}{self.category.label}")
        print(f"DEBUG: exp_param = {exp_param}", flush=True)
        # exp_param = params[-1]

        # exp_param = self.workspace.obj(func_config.param_names[-1])
        exp_func = ROOT.RooExponential(f"{func_config.name}_exp{self.category.label}", f"{func_config.name}_exp{self.category.label}", self.mass_var, exp_param)
        
        # Combine
        func = ROOT.RooProdPdf(f"{func_config.name}{self.category.label}",
                               f"{func_config.name}{self.category.label}", poly_func, exp_func)
        self.background_functions[func_config.name] = func
        
    def _create_sum_exp_function(self, func_config: BackgroundFunction):
        """Create sum of exponentials function"""
        # Create parameters
        params = self._create_vars(func_config)
            
        # Create exponential functions
        exp_funcs = []
        for i in range(4):  # 4 exponentials
            param_name = f"c{i}{self.category.label}"
            param = params.find(param_name)
            exp_func = ROOT.RooExponential(f"{func_config.name}_exp{i}{self.category.label}",
                                           f"{func_config.name}_exp{i}{self.category.label}", 
                                           self.mass_var, param)
            exp_funcs.append(exp_func)
            
        # Create sum with coefficients
        coeff_list = ROOT.RooArgList([params.find(f"cc{i}{self.category.label}") for i in range(3)])  # n-1 coefficients
        func = ROOT.RooAddPdf(f"{func_config.name}{self.category.label}", 
                              f"{func_config.name}{self.category.label}", 
                              ROOT.RooArgList(exp_funcs), coeff_list)
        
        self.background_functions[func_config.name] = func
        
    def _create_simple_exp_function(self, func_config: BackgroundFunction):
        """Create simple exponential function"""
        # Create parameters
        param = self._create_vars(func_config)[0]
        
        # Create function
        func = ROOT.RooExponential(f"{func_config.name}{self.category.label}", 
                                   f"{func_config.name}{self.category.label}", self.mass_var, param)
        self.background_functions[func_config.name] = func
        
    def _create_vars(self, func_config: BackgroundFunction) -> ROOT.RooArgList:
        for i, (name, init, limits) in enumerate(zip(func_config.param_names, func_config.param_inits, func_config.param_limits)):
            print(f"DEBUG: creating variable {name}{self.category.label} with init {init}, limits {limits}", flush=True)
            self.workspace.factory(f"{name}{self.category.label}[{init}, {limits[0]}, {limits[1]}]")
        
        pars = ROOT.RooArgList([self.workspace.obj(f"{name}{self.category.label}") for name in func_config.param_names])
        return pars

    def setup_resonant_backgrounds(self):
        """Setup resonant background models (J/psi, psi(2S), etc.) for a specific category"""
        print(f"Setting up resonant background models for category: {self.category.display_name}...")
        
        # Get category-specific resonant background templates from workspace
        jpsi_template = self.workspace.obj(f"Zd_M3.1{self.category.label}")  # J/psi template
        print("DEBUG: jpsi_template = ", jpsi_template, flush = True)
        psi2s_template = self.workspace.obj(f"Zd_M3.7{self.category.label}")  # psi(2S) template
        print("DEBUG: psi2s_template = ", psi2s_template, flush = True)
        
        if not jpsi_template or not psi2s_template:
            print(f"Warning: Resonant background templates not found in workspace for category {self.category.display_name}")
            print(f"  Looking for: Zd_M3.1{self.category.label}, Zd_M3.7{self.category.label}")
            return
        else:
            jpsi_template.SetName("jpsi_model")
            psi2s_template.SetName("psi2s_model")
            
        if self.config.floating_resonant:
            print("DEBUG: creating floating resonant models", flush = True)
            # Create floating resonant background models
            self.resonant_backgrounds = self._create_floating_resonant_models()
        else:
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
        
        for model_name, model_config in self.config.resonant_models.items():
            print(f"    Creating floating {model_name} resonant background for category {self.category.display_name}...", flush=True) #FIXME: remove flush
            
            # Create parameters and import them into workspace for ownership
            params = {}
            for param_name, init_val in model_config["initial_params"].items():
                var_name = f"{model_name}_{param_name}{self.category.label}"
                
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
                
            # Create double-sided Crystal Ball (typical resonant background shape)
            full_model_name = f"{model_name}_resonant_bkg{self.category.label}"
            model = ROOT.RooCrystalBall(
                full_model_name, full_model_name,
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
            
        return models
        
    def setup_normalizations(self):
        """Setup normalization variables"""
        print("Setting up normalizations...")
        
        # Create normalization variables
        for comp_type, params in self.config.normalization_settings.items():
            for var_name, settings in params.items():
                var = ROOT.RooRealVar(f"{var_name}{self.category.label}", var_name, 
                                    settings["init"], settings["min"], settings["max"])
                self.workspace.Import(var, ROOT.RooCmdArg())
                
    def fit_background_to_sidebands(self, fit_region: FitRegion) -> Dict[str, FitResult]:
        """Fit all background functions to sideband regions"""
        print(f"Fitting background functions to sidebands...")
        
        print("DEBUG: setting sidebands range", flush = True)
        sideband_range = self.setup_mass_ranges(fit_region)
        print(f"DEBUG:  Sideband range: {sideband_range}", flush=True)        
        results = {}
        
        background_funcs = self.config.background_functions if self.config.chosen_bkg_function < 0 else [self.config.get_chosen_background_function()]
        print("DEBUG: background_funcs", background_funcs, flush = True)
        for func_config in background_funcs:
            print("DEBUG: func_config", func_config, flush = True)
            func_name = func_config.name
            print(f"  Fitting {func_config.display_name}...", flush = True)
            
            if func_name not in self.background_functions:
                print(f"    Warning: Function {func_name} not created")
                continue
                
            func = self.background_functions[func_name]
            print(func)
            
            # Perform fit
            print("DEBUG: fitting sidebands first", flush = True)
            print("DEBUG: data = ", self.data, flush = True)
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
            print(f"    Fit status: {result.fit_status}, free params: {n_free}", flush = True)
            
        return results
        
    def create_combined_model(self, fit_region: FitRegion):
        """Create combined resonant + non-resonant background model"""
        print("Creating combined background model (resonant + non-resonant)...", flush = True) #FIXME: remove
        
        # Get chosen non-resonant background function
        chosen_bkg = self.get_chosen_background_function()
        if not chosen_bkg:
            raise ValueError("No non-resonant background function chosen")
            
        # Create combined model: resonant backgrounds + non-resonant background
        model_list = ROOT.RooArgList([model for model in self.resonant_backgrounds.values()] + [chosen_bkg])
        norm_list = ROOT.RooArgList([
            self.workspace.obj(f"{norm_name}{self.category.label}") for norm_name in self.config.normalization_settings["background_components"].keys()
        ])

        # for norm in norm_list:
        #     print("DEBUG: norm ", norm.GetName(), " = ", norm.getValV(), flush = True)
        # for model in model_list:
        #     print("DEBUG: model", model, flush=True)

        self.combined_model = ROOT.RooAddPdf("full_bkg_model", "full_bkg_model", model_list, norm_list)
        
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
            
        # Perform fit
        fit_result_obj = self.combined_model.fitTo(self.data,
                                                 ROOT.RooFit.Range(fit_region.name),
                                                 ROOT.RooFit.Save(),
                                                 ROOT.RooFit.NumCPU(8),
                                                 ROOT.RooFit.SumW2Error(True)) #FIXME: True
        
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
            
        print(f"  Fit status: {result.fit_status}, free params: {n_free}")
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
        
        # Load prompt J/psi dataset
        prompt_file = ROOT.TFile.Open("datasets/dataset_jpsi.root")
        if not prompt_file or prompt_file.IsZombie():
            raise FileNotFoundError("Cannot open prompt J/psi dataset file")
            
        prompt_w = prompt_file.Get("w")
        if not prompt_w:
            raise ValueError("Workspace 'w' not found in prompt dataset file")
            
        prompt_data = prompt_w.obj(f'data_obs{self.category.label}')
        print(f"DEBUG: loading dataset 'data_obs{self.category.label}' from prompt workspace", flush=True)

        if not prompt_data:
            raise ValueError(f"Data 'data_obs{self.category.label}' not found in prompt workspace")
            
        print(f"  Loaded prompt dataset with {prompt_data.numEntries()} entries")
        
        # Get resonant background models
        if "jpsi" not in self.resonant_backgrounds or "psi2s" not in self.resonant_backgrounds:
            raise ValueError("Resonant background models not setup")
            
        jpsi_model = self.resonant_backgrounds["jpsi"]
        psi2s_model = self.resonant_backgrounds["psi2s"]
        
        # Create fraction parameter for psi(2S) component
        fraction_psi2s = ROOT.RooRealVar("fraction_psi2s", "fraction_psi2s", 0.3, 0, 1)
        
        # Create combined model
        jpsi_plus_psi2s = ROOT.RooAddPdf("jpsi_plus_psi2s", "jpsi_plus_psi2s", 
                                        ROOT.RooArgList(jpsi_model, psi2s_model), 
                                        ROOT.RooArgList(fraction_psi2s))
        
        # Import the combined model into workspace to maintain ownership
        self.workspace.Import(jpsi_plus_psi2s, ROOT.RooCmdArg())
        # Get the model back from workspace to ensure proper ownership
        jpsi_plus_psi2s = self.workspace.obj("jpsi_plus_psi2s")
        
        # Store prefit parameter values
        prefit_values = {}
        params = jpsi_plus_psi2s.getParameters(prompt_data)
        for param in params:
            prefit_values[param.GetName()] = param.getValV()
            
        # Perform fit
        fit_result_obj = jpsi_plus_psi2s.fitTo(prompt_data, 
                                             ROOT.RooFit.NumCPU(8), 
                                             ROOT.RooFit.Range("unblinded"), 
                                             ROOT.RooFit.Save(), 
                                             ROOT.RooFit.SumW2Error(True))
        
        # Store results
        result = FitResult("jpsi_plus_psi2s_prompt", "unblinded")
        result.fit_status = int(fit_result_obj.status())
        
        # Get parameters
        params = jpsi_plus_psi2s.getParameters(prompt_data)
        n_free = params.selectByAttrib("Constant", False).getSize()
        result.n_free_params = n_free
        
        for param in params:
            param_name = param.GetName()
            prefit_val = prefit_values.get(param_name)
            result.add_parameter(param_name, param, prefit_val)
            
        self.log_print("Fitted jpsi and psi2s models to prompt data")
        for param in params:
            self.log_print(f"param: {param.GetName()}, value: {param.getValV():.5f}, error: {param.getError():.5f} (limits: [{param.getMin():.5g}, {param.getMax():.5g}])")
            
        # Freeze resonant background parameters after fitting to prompt data
        for param in jpsi_model.getParameters(prompt_data):
            param.setConstant(True)
        for param in psi2s_model.getParameters(prompt_data):
            param.setConstant(True)
            
        print(f"  Prompt fit status: {result.fit_status}, free params: {n_free}")
        print("  Resonant background parameters frozen after prompt fit")
        
        # Store the combined model for potential plotting
        self.prompt_combined_model = jpsi_plus_psi2s
        self.prompt_data = prompt_data
        
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
        """Save the workspace with fitted models"""
        print("Saving workspace...")
        
        # Import fitted models to workspace
        if "jpsi" in self.resonant_backgrounds:
            self.workspace.Import(self.resonant_backgrounds["jpsi"], 
                                ROOT.RooFit.RenameVariable(f"jpsi_resonant_bkg", f"jpsi_bkg{self.category.label}"))
        if "psi2s" in self.resonant_backgrounds:
            self.workspace.Import(self.resonant_backgrounds["psi2s"], 
                                ROOT.RooFit.RenameVariable(f"psi2s_resonant_bkg", f"psi2s_bkg{self.category.label}"))
                                
        chosen_bkg = self.get_chosen_background_function()
        if chosen_bkg:
            self.workspace.Import(chosen_bkg, 
                                ROOT.RooFit.RenameVariable("bkg_function", "dy"))
                                
        if self.combined_model:
            self.workspace.Import(self.combined_model, 
                                ROOT.RooFit.RenameVariable(f"full_bkg_model", f"complete_background_model{self.category.label}"))
        
        # Save to file
        output_path = self.config.get_output_workspace_path()
        self.workspace.writeToFile(str(output_path))
        print(f"  Workspace saved to: {output_path}")
        
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
