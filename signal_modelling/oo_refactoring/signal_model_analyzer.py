"""
Signal Model Analyzer - Object-oriented approach for signal modeling in physics analysis

This module provides a comprehensive object-oriented framework for signal modeling
in particle physics analysis, replacing the previous function-based approach.
"""

import ROOT
import numpy as np
import os
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from pathlib import Path


class SampleConfig:
    """Configuration for a single sample"""
    
    def __init__(self, label: str, filename: str, nominal_mass: float, nominal_width: float,
                 mass_range: List[float], mass_GEN_range: List[float], 
                 mean_BW_range: List[float], file: Optional[str] = None, 
                 file_GEN: Optional[str] = None, **kwargs):
        self.label = label
        self.filename = filename
        self.nominal_mass = nominal_mass
        self.nominal_width = nominal_width
        self.mass_range = mass_range
        self.mass_GEN_range = mass_GEN_range
        self.mean_BW_range = mean_BW_range
        self.file = file
        self.file_GEN = file_GEN
        
        # Allow additional parameters for ranges
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def __repr__(self):
        return f"SampleConfig(label='{self.label}', filename='{self.filename}', nominal_mass={self.nominal_mass})"


@dataclass
class CategoryConfig:
    """Configuration for a single category"""
    name: str
    cuts: Dict[str, List[List[float]]]

    def __post_init__(self):
        self.label = f"_cat_{self.name}" if self.name != "" else ""



class WorkspaceManager:
    """Manages ROOT workspace operations and file I/O"""
    
    def __init__(self, wsfile: str):
        self.wsfile = wsfile
        self._workspace = None
        self._ensure_workspace_dir()
    
    def _ensure_workspace_dir(self):
        """Ensure workspace directory exists"""
        Path(self.wsfile).parent.mkdir(parents=True, exist_ok=True)
    
    @property
    def workspace(self) -> ROOT.RooWorkspace:
        """Get or create workspace"""
        if self._workspace is None:
            if os.path.exists(self.wsfile):
                try:
                    f = ROOT.TFile.Open(self.wsfile)
                    if f and not f.IsZombie():
                        self._workspace = f.Get("w")
                        f.Close()
                    else:
                        self._workspace = ROOT.RooWorkspace("w")
                except:
                    self._workspace = ROOT.RooWorkspace("w")
            else:
                self._workspace = ROOT.RooWorkspace("w")
        return self._workspace
    
    def save(self):
        """Save workspace to file"""
        self.workspace.writeToFile(self.wsfile, True)
    
    def delete_workspace_file(self):
        """Delete existing workspace file"""
        print("checking for ", self.wsfile)
        if os.path.exists(self.wsfile):
            print(f"Deleting existing workspace: {self.wsfile}")
            os.remove(self.wsfile)
        else:
            print(f"Workspace file does not exist: {self.wsfile}")


class DatasetLoader:
    """Handles loading and processing of ROOT datasets"""
    
    def __init__(self, workspace: ROOT.RooWorkspace):
        self.workspace = workspace
    
    def _check_category_conditions(self, category: CategoryConfig, cat_vars: Dict, j: int) -> bool:
        """Check if event passes category selection"""
        for var, ranges in category.cuts.items():
            if var in cat_vars:
                cat_var_value = cat_vars[var][j]
                range_check = any(
                    r[0] < cat_var_value <= r[1] for r in ranges
                )
                if not range_check:
                    return False
        return True
    
    def load_response_dataset(self, sample: SampleConfig, category: CategoryConfig, 
                            observable_name: str, use_reco_mass: bool = False) -> ROOT.RooDataSet:
        """Load response function dataset"""
        
        # Check if dataset already exists
        data_name = f"response_data_{sample.label}{category.label}"
        existing_data = self.workspace.data(data_name)
        if existing_data:
            return existing_data
        
        # Create new dataset
        f = ROOT.TFile.Open(sample.file)
        t = f.Get("Events")
        
        weight_var = ROOT.RooRealVar(f"weightVar_{sample.label}{category.label}", 
                                   f"weightVar_{sample.label}{category.label}", 1.0)
        self.workspace.Import(weight_var, ROOT.RooCmdArg())
        
        obs_var = self.workspace.var(observable_name)
        data = ROOT.RooDataSet(data_name, data_name, 
                             ROOT.RooArgSet(obs_var), 
                             ROOT.RooFit.WeightVar(weight_var.GetName()))
        
        # Get range for filtering
        range_key = "mass_range" if use_reco_mass else "reduced_mass_range"
        min_val, max_val = sample.__dict__[range_key][1], sample.__dict__[range_key][2]
        
        for i in range(t.GetEntries()):
            t.GetEntry(i)
            weight = getattr(t, 'trigger_PS_weight', 1.0) #was 'weight'
            
            # Get category variables for this event
            cat_vars = {var: getattr(t, var) for var in category.cuts.keys()}
            
            for j, val in enumerate(t.SelectedDiEle_fitted_mass):
                # Check category conditions
                if not self._check_category_conditions(category, cat_vars, j):
                    continue
                
                # Calculate fill value
                gen_mass = t.GenZd_invMass
                fill_value = val if use_reco_mass else val/gen_mass - 1
                
                # Apply range cut
                if not (min_val <= fill_value <= max_val):
                    continue
                
                obs_var.setVal(fill_value)
                data.add(ROOT.RooArgSet(obs_var), weight)
        
        f.Close()
        self.workspace.Import(data)
        
        return data
    
    def load_signal_dataset(self, sample: SampleConfig, category: CategoryConfig) -> ROOT.RooDataSet:
        """Load signal model dataset"""
       
        # Check if dataset already exists
        data_name = f"data_{sample.label}{category.label}"
        existing_data = self.workspace.data(data_name)
        if existing_data:
            return existing_data
        
        # Create new dataset
        f = ROOT.TFile.Open(sample.file)
        t = f.Get("Events")
        
        weight_var = ROOT.RooRealVar(f"weightVar_{sample.label}{category.label}", 
                                   f"weightVar_{sample.label}{category.label}", 1.0)
        self.workspace.Import(weight_var, ROOT.RooCmdArg())
        
        mass_var = self.workspace.var(f"mass_{sample.label}")
        data = ROOT.RooDataSet(data_name, data_name, 
                             ROOT.RooArgSet(mass_var), 
                             ROOT.RooFit.WeightVar(weight_var.GetName()))
        
        min_val, max_val = sample.mass_range[1], sample.mass_range[2]
        
        for i in range(t.GetEntries()):
            t.GetEntry(i)
            weight = getattr(t, 'trigger_PS_weight', 1.0) #was 'weight'
            
            cat_vars = {var: getattr(t, var) for var in category.cuts.keys()}
            
            for j, val in enumerate(t.SelectedDiEle_fitted_mass):
                if not self._check_category_conditions(category, cat_vars, j):
                    continue
                
                if not (min_val <= val <= max_val):
                    continue
                
                mass_var.setVal(val)
                data.add(ROOT.RooArgSet(mass_var), weight)
        
        f.Close()
        self.workspace.Import(data, True)
        return data
    
    def get_dataset_entry_count(self, dataset_name: str, weighted: bool = False) -> int:
        """Get number of entries in a dataset"""
        dataset = self.workspace.data(dataset_name)
        if dataset:
            if weighted:
                return int(dataset.sumEntries())
            else:
                return int(dataset.numEntries())
        return 0
    
    def get_entry_counts_for_category(self, samples: Dict[str, SampleConfig], 
                                    category: CategoryConfig, 
                                    dataset_type: str = "response", weighted: bool = False) -> Dict[str, int]:
        """Get entry counts for all samples in a category
        
        Args:
            samples: Dictionary of sample configurations
            category: Category configuration  
            dataset_type: Type of dataset ("response" or "signal")
            
        Returns:
            Dictionary mapping sample_name+category_label to entry count
        """
        entry_counts = {}
        for name, sample in samples.items():
            if dataset_type == "response":
                dataset_name = f"response_data_{sample.label}{category.label}"
            else:
                dataset_name = f"data_{sample.label}{category.label}"
            
            count = self.get_dataset_entry_count(dataset_name)
            entry_counts[f"{name}{category.label}"] = count
            
        return entry_counts

class ParameterManager:
    """Manages fit parameters and their ranges"""
    
    def __init__(self, workspace: ROOT.RooWorkspace):
        self.workspace = workspace
        
        # Define parameter configurations
        self.response_vars = ["response_mean", "response_sigma", "response_alphaL", 
                            "response_nL", "response_alphaR", "response_nR"]
        self.dcb_vars = ["mean", "sigma", "alphaL", "nL", "alphaR", "nR"]
        self.bw_vars = ["mean_BW", "width_BW"]
        
    def create_variables(self, sample: SampleConfig, category: CategoryConfig, 
                        var_list: List[str], tag: str = ""):
        """Create RooRealVar objects for given variables"""
        
        for var in var_list:
            var_name = f"{var}{tag}_{sample.label}{category.label}"
            range_key = f"{var}_range"
            
            if hasattr(sample, range_key):
                var_range = getattr(sample, range_key)
                print("building var", var_name, "with range", var_range)
                self.workspace.factory(f"{var_name}[{','.join(map(str, var_range))}]")
    
    def create_parametric_variable(self, var_name: str, formula: str, 
                                 dependencies: List[str]) -> ROOT.RooFormulaVar:
        """Create parametric variable using formula"""
        dep_objects = [self.workspace.obj(dep) if not dep.replace(".", "").isdigit() else float(dep) for dep in dependencies]
        param_var = ROOT.RooFormulaVar(var_name, var_name, formula, 
                                     ROOT.RooArgList(dep_objects))
        self.workspace.Import(param_var, ROOT.RooCmdArg())
        return param_var
    
    def set_constant_parameter(self, var_name: str, value: float, error: float = 0.0):
        """Set parameter to constant value"""
        var = self.workspace.var(var_name)
        if var:
            var.setVal(value)
            if error > 0:
                var.setError(error)
            var.setConstant(True)


class ModelBuilder:
    """Builds and manages physics models"""
    
    def __init__(self, workspace: ROOT.RooWorkspace, param_manager: ParameterManager):
        self.workspace = workspace
        self.param_manager = param_manager
    
    def build_response_function(self, sample: SampleConfig, category: CategoryConfig, 
                              observable_name: str) -> ROOT.RooAbsPdf:
        """Build Crystal Ball response function"""
        
        model_name = f"response_function_{sample.label}{category.label}"
        
        # Build variable list for Crystal Ball
        var_names = [observable_name] + [f"{var}_{sample.label}{category.label}" for var in self.param_manager.response_vars]
        var_string = ",".join(var_names)
        
        self.workspace.factory(f"CrystalBall::{model_name}({var_string})")
        return self.workspace.pdf(model_name)
    
    def build_signal_model(self, sample: SampleConfig, category: CategoryConfig, 
                         parametrized_vars: List[str], tag: str = "param", 
                         use_reco_mass: bool = False, use_shared_mass: bool = False) -> ROOT.RooAbsPdf:
        """Build complete signal model (dCB * BW convolution or dCB only)"""
        
        # Build Crystal Ball part
        dcb_vars = [f"{var}_{tag}_{sample.label}{category.label}" for var in self.param_manager.dcb_vars]
        mass_string = f"mass_{tag}," if use_shared_mass else f"mass_{sample.label},"
        dcb_var_string = mass_string + ",".join(dcb_vars)
        
        dcb_name = f"crystalBall_{tag}_{sample.label}{category.label}"
        self.workspace.factory(f"CrystalBall::{dcb_name}({dcb_var_string})")

        if use_reco_mass:
            # Return Crystal Ball only
            model = self.workspace.pdf(dcb_name).Clone(f"model_{tag}_{sample.label}{category.label}")
            self.workspace.Import(model, True)
            return model
        else:
            # Build Breit-Wigner and convolution
            return self._build_convolution_model(sample, category, tag, dcb_name)
    
    def _build_convolution_model(self, sample: SampleConfig, category: CategoryConfig, 
                               tag: str, dcb_name: str) -> ROOT.RooAbsPdf:
        """Build convolution of Crystal Ball and Breit-Wigner"""
        
        # Build Breit-Wigner
        bw_vars = [self.workspace.obj(f"{var}_{tag}_{sample.label}{category.label}") 
                  for var in self.param_manager.bw_vars]
        mass_var = self.workspace.var(f"mass_{sample.label}")
        bw_vars.insert(0, mass_var)
        
        # Relativistic Breit-Wigner formula
        relBW_formula = ("2*sqrt(2)/pi * @1**2 * @2*sqrt(@1**2 + @2**2) / "
                        "((@0**2 - @1**2)*(@0**2 - @1**2) + @1**2 * @2**2) / "
                        "(sqrt(@1**2 + @1*sqrt(@2**2 + @1**2)))")
        
        relBW_name = f"relBW_{tag}_{sample.label}{category.label}"
        relBW = ROOT.RooGenericPdf(relBW_name, relBW_formula, bw_vars)
        self.workspace.Import(relBW)
        
        # Setup convolution
        mass_var.setBins(10000, "cache")
        mass_var.setMin("cache", -20)
        mass_var.setMax("cache", 20)
        
        # Build convolution
        conv_name = f"model_{tag}_{sample.label}{category.label}"
        self.workspace.factory(f"FFTConvPdf::{conv_name}(mass_{sample.label}, {dcb_name}, {relBW_name})")
        
        return self.workspace.pdf(conv_name)


class FitManager:
    """Manages fitting operations"""
    
    def __init__(self, workspace: ROOT.RooWorkspace):
        self.workspace = workspace
    
    def fit_model(self, model: ROOT.RooAbsPdf, dataset: ROOT.RooDataSet, 
                 save_result: bool = True, **fit_options) -> Optional[ROOT.RooFitResult]:
        """Fit model to dataset"""
        default_options = {
            'Save': True,
            'NumCPU': 8,
            'SumW2Error': False
        }
        default_options.update(fit_options)
        
        # Convert to RooFit command arguments
        fit_args = []
        for key, value in default_options.items():
            if hasattr(ROOT.RooFit, key):
                fit_args.append(getattr(ROOT.RooFit, key)(value))
        
        result = model.fitTo(dataset, *fit_args)

        # import updated model to workspace
        self.workspace.Import(model, ROOT.RooCmdArg())
        
        if save_result and result:
            self.workspace.Import(result, True)
        
        return result
    
    def fit_parameters_vs_mass(self, samples: Dict[str, SampleConfig], 
                             category: CategoryConfig, vars_to_fit: List[str], 
                             parametrized_vars: List[str], gen: bool = False,
                             min_entries: int = 10,
                             entry_counts: Optional[Dict[str, int]] = None) -> Dict[str, ROOT.TF1]:
        """Fit parameters as function of mass
        
        Args:
            samples: Dictionary of sample configurations
            category: Category configuration
            vars_to_fit: List of variables to fit
            parametrized_vars: List of variables to parametrize
            gen: Whether to use GEN variables
            min_entries: Minimum number of entries required to include a point
            entry_counts: Dictionary with keys like 'sample_name_category_label' containing entry counts
        """
        # Filter out JPsi samples for parameter fitting
        fit_samples = {name: sample for name, sample in samples.items() 
                      if "JPsi" not in name}
                
        # Create graphs for each variable
        graphs = {var: ROOT.TGraphErrors() for var in vars_to_fit}
        
        # Fill graphs with data points
        for name, sample in fit_samples.items():
            # Check if we have enough entries for this sample-category combination
            if entry_counts is not None:
                entry_key = f"{name}{category.label}"
                if entry_key in entry_counts and entry_counts[entry_key] < min_entries:
                    print(f"Skipping {name} in category {category.name}: only {entry_counts[entry_key]} entries (< {min_entries})")
                    continue
            
            for var in vars_to_fit:
                input_var = f"{var}_GEN_fit_{name}{category.label}" if gen else f"response_{var}_{name}{category.label}"
                val = self.workspace.var(input_var).getVal()
                err = self.workspace.var(input_var).getError()
                print(f"Setting point for {var} at mass {sample.nominal_mass}: value = {val}, error = {err}")
                graphs[var].SetPoint(graphs[var].GetN(), sample.nominal_mass, val)
                graphs[var].SetPointError(graphs[var].GetN()-1, 0, err)
        
        # Fit parametrized variables with linear functions
        fits = {}
        tag = "_GEN" if gen else ""
        
        for var in parametrized_vars:
            if var in vars_to_fit:
                print("Fitting graph for var ", var, " category ", category.label)
                for i in range(graphs[var].GetN()):
                    print(f"\tPoint {i}: x = {graphs[var].GetX()[i]}, y = {graphs[var].GetY()[i]} +- {graphs[var].GetEY()[i]}")
                fit_func = ROOT.TF1(f"fit{tag}_{var}{category.label}", "[0] + [1]*x", 0, 12)
                fit_result = graphs[var].Fit(fit_func, "S")
                fit_result.Print()
                fits[var] = fit_func
                
                # Save fit parameters to workspace
                for i in range(2):
                    param_name = f"{var}{category.label}_fit_par{i}"
                    param_obj = ROOT.RooRealVar(param_name, param_name, fit_func.GetParameter(i))
                    param_obj.setError(fit_func.GetParError(i))
                    param_obj.setConstant()
                    self.workspace.Import(param_obj, True)
        
        # Handle constant variables
        const_vars = set(vars_to_fit) - set(parametrized_vars)
        for var in const_vars:
            y_values = np.array([graphs[var].GetY()[i] for i in range(graphs[var].GetN())])
            y_errors = np.array([graphs[var].GetEY()[i] for i in range(graphs[var].GetN())])
            
            # Weighted mean
            weights = 1.0 / y_errors**2
            mean = np.average(y_values, weights=weights)
            err = np.sqrt(1.0 / np.sum(weights))
            
            const_name = f"{var}{category.label}{tag}_const"
            const_obj = ROOT.RooRealVar(const_name, const_name, mean)
            const_obj.setError(err)
            const_obj.setConstant()
            self.workspace.Import(const_obj, True)
        
        return fits


class SignalModelAnalyzer:
    """Main class that orchestrates the signal modeling analysis"""
    
    def __init__(self, samples: Dict[str, SampleConfig], categories: Dict[str, CategoryConfig], 
                 wsfile: str, parametrized_vars: List[str]):
        self.samples = samples
        self.categories = categories
        self.parametrized_vars = parametrized_vars
        
        # Initialize managers
        self.workspace_manager = WorkspaceManager(wsfile)
        self.dataset_loader = DatasetLoader(self.workspace_manager.workspace)
        self.param_manager = ParameterManager(self.workspace_manager.workspace)
        self.model_builder = ModelBuilder(self.workspace_manager.workspace, self.param_manager)
        self.fit_manager = FitManager(self.workspace_manager.workspace)
        
        # Analysis state
        self._response_functions_built = False
        self._parameters_fitted = False
    
    def delete_workspace(self):
        """Delete existing workspace file"""
        self.workspace_manager.delete_workspace_file()
    
    def build_response_functions(self, use_reco_mass: bool = False):
        """Build response function workspace and fit parameters"""
        print("Building response function workspace...")
        
        observables = ["mass" if use_reco_mass else "reduced_mass"]
        
        for name, sample in self.samples.items():
            print(f"Processing sample: {name}")
            
            for category_label, category in self.categories.items():
                print(f"\tCategory: {category_label}")
                
                # Create variables
                self.param_manager.create_variables(sample, category, 
                                                  observables + self.param_manager.response_vars + ["response_nsgn"])
                
                # Load dataset
                obs_name = f"{observables[0]}_{sample.label}"
                dataset = self.dataset_loader.load_response_dataset(sample, category, obs_name, use_reco_mass)
                print("\t\tLoaded dataset")
                
                # Build and fit model
                model = self.model_builder.build_response_function(sample, category, obs_name)
                self.fit_manager.fit_model(model, dataset)
                print("\t\tFitted model", model.GetName())
                # print all parameters, their names and post-fit values
                for var in model.getParameters(ROOT.RooArgSet()):
                    print(f"\t\tParameter {var.GetName()}: value = {var.getVal()}, error = {var.getError()}")

        
        self.workspace_manager.save()
        self._response_functions_built = True
        print("Response function workspace built successfully!")
    
    def fit_parameters(self, vars_list: Optional[List[str]] = None, gen: bool = False, 
                      min_entries: int = 10):
        """Fit parameters as functions of mass
        
        Args:
            vars_list: List of variables to fit
            gen: Whether to use GEN variables
            min_entries: Minimum number of entries required to include a point
        """
        if not self._response_functions_built and not gen:
            raise RuntimeError("Response functions must be built before fitting parameters")
        
        print("Fitting parameters...")
        
        if vars_list is None:
            vars_list = self.param_manager.dcb_vars if not gen else self.param_manager.bw_vars
        
        for category_label, category in self.categories.items():
            print(f"Fitting parameters for category: {category_label}")
            
            # Get entry counts for this category
            dataset_type = "signal" if gen else "response"
            entry_counts = self.dataset_loader.get_entry_counts_for_category(
                self.samples, category, dataset_type
            )
            
            # Print entry counts for debugging
            for key, count in entry_counts.items():
                if "JPsi" not in key:  # Only show non-JPsi samples
                    print(f"Sample {key}: {count} entries")
            
            fits = self.fit_manager.fit_parameters_vs_mass(
                self.samples, category, vars_list, self.parametrized_vars, gen,
                min_entries, entry_counts
            )
        
        self.workspace_manager.save()
        self._parameters_fitted = True
        print("Parameter fitting completed!")
    
    def build_signal_models(self, use_reco_mass: bool = False, fit_models: bool = False):
        """Build parametric signal models"""
        if not self._parameters_fitted:
            raise RuntimeError("Parameters must be fitted before building signal models")
        
        print("Building signal models...")
        
        for name, sample in self.samples.items():
            print(f"Building signal model for: {name}")
            
            # Create mass observable
            mass_range = ",".join(map(str, sample.mass_range))
            self.workspace_manager.workspace.factory(f"mass_{sample.label}[{mass_range}]")
            
            for category_label, category in self.categories.items():
                
                # Create parametric variables
                self._create_parametric_variables(sample, category, use_reco_mass)
                
                # Load dataset
                dataset = self.dataset_loader.load_signal_dataset(sample, category)
                
                # Build model
                model = self.model_builder.build_signal_model(
                    sample, category, self.parametrized_vars, "param", use_reco_mass
                )
                
                # Optionally fit model
                if fit_models:
                    self.fit_manager.fit_model(model, dataset)
        
        self.workspace_manager.save()
        print("Signal models built successfully!")
    
    def _create_parametric_variables(self, sample: SampleConfig, category: CategoryConfig, 
                                   use_reco_mass: bool):
        """Create parametric variables for signal model"""
        
        all_vars = self.param_manager.dcb_vars if use_reco_mass else (
            self.param_manager.bw_vars + self.param_manager.dcb_vars
        )
        const_vars = set(self.param_manager.dcb_vars) - set(self.parametrized_vars)
        
        for var in all_vars:
            if var in self.parametrized_vars:
                # Create parametric variable
                formula = "@0 + @1 * @2"
                if var == "sigma" and not use_reco_mass:
                    formula = "(@0 + @1 * @2) * @2"
                
                var_name = f"{var}_param_{sample.label}{category.label}"
                dependencies = [f"{var}{category.label}_fit_par0", f"{var}{category.label}_fit_par1", str(sample.nominal_mass)]
                
                self.param_manager.create_parametric_variable(var_name, formula, dependencies)
                
            else:
                # Create regular variable
                self.param_manager.create_variables(sample, category, [var], "_param")
                
                if var in const_vars:
                    # Set to constant value
                    const_val = self.workspace_manager.workspace.obj(f"{var}{category.label}_const").getVal()
                    const_err = self.workspace_manager.workspace.obj(f"{var}{category.label}_const").getError()
                    self.param_manager.set_constant_parameter(f"{var}_param_{sample.label}{category.label}", 
                                                            const_val, const_err)
                
                elif var in self.param_manager.bw_vars:
                    # Set BW parameters
                    if var == "mean_BW":
                        self.param_manager.set_constant_parameter(f"{var}_param_{sample.label}{category.label}", 
                                                                sample.nominal_mass)
                    elif var == "width_BW":
                        self.param_manager.set_constant_parameter(f"{var}_param_{sample.label}{category.label}", 
                                                                sample.nominal_width)
    
    def test_model_for_masses(self, mass_points: List[float], use_reco_mass: bool = False):
        """Test signal model for different mass points"""
        print("Testing signal model for various mass points...")
        
        # Create common mass variable
        mass_var = ROOT.RooRealVar("mass_test", "mass_test", 0, 11)
        self.workspace_manager.workspace.Import(mass_var)
        
        for mass in mass_points:
            print(f"Testing mass: {mass:.1f} GeV")
            name = f"M{mass:.1f}".replace(".", "p")
            
            for category_label, category in self.categories.items():
                # Create variables for this mass point
                self._create_test_variables(mass, name, category, use_reco_mass)
                
                # Build model
                model = self.model_builder.build_signal_model(
                    self._create_test_sample_config(mass), category, 
                    self.parametrized_vars, "test", use_reco_mass, use_shared_mass=True
                )
        
        self.workspace_manager.save()
        print("Mass testing completed!")
    
    def _create_test_variables(self, mass: float, name: str, category: CategoryConfig, 
                             use_reco_mass: bool):
        """Create variables for mass testing"""
        
        all_vars = self.param_manager.dcb_vars if use_reco_mass else (
            self.param_manager.bw_vars + self.param_manager.dcb_vars
        )
        
        for var in all_vars:
            if var in self.parametrized_vars:
                # Create parametric variable
                formula = "@0 + @1 * @2"
                if var == "sigma" and not use_reco_mass:
                    formula = "(@0 + @1 * @2) * @2"
                
                var_name = f"{var}_test_{name}{category.label}"
                dependencies = [f"{var}{category.label}_fit_par0", f"{var}{category.label}_fit_par1", str(mass)]
                
                self.param_manager.create_parametric_variable(var_name, formula, dependencies)
            else:
                # Create and set constant variable
                var_name = f"{var}_test_{name}{category.label}"
                self.workspace_manager.workspace.factory(f"{var_name}[0, -100, 100]")
                
                if var in (set(self.param_manager.dcb_vars) - set(self.parametrized_vars)):
                    # Set to constant value
                    const_val = self.workspace_manager.workspace.obj(f"{var}{category.label}_const").getVal()
                    self.param_manager.set_constant_parameter(var_name, const_val)
                elif var in self.param_manager.bw_vars:
                    # Set BW parameters
                    if var == "mean_BW":
                        val = mass
                    elif var == "width_BW":
                        val = 1e-10  # Very small width
                    self.param_manager.set_constant_parameter(var_name, val)
    
    def _create_test_sample_config(self, mass: float) -> SampleConfig:
        """Create a temporary sample config for testing"""
        name = f"M{mass:.1f}".replace(".", "p")
        return SampleConfig(
            label=name,
            filename=f"{name}.root",
            nominal_mass=mass,
            nominal_width=0.02,
            mass_range=[mass, mass-1, mass+1],
            mass_GEN_range=[mass, mass-0.2, mass+0.2],
            mean_BW_range=[mass, mass-0.2, mass+0.2]
        )
    
    def run_full_analysis(self, use_reco_mass: bool = False, 
                         test_mass_points: Optional[List[float]] = None):
        """Run complete analysis pipeline"""
        print("Starting full signal modeling analysis...")
        
        # Step 1: Build response functions
        self.build_response_functions(use_reco_mass)
        
        # Step 2: Fit parameters
        self.fit_parameters()
        
        # Step 3: Build signal models
        self.build_signal_models(use_reco_mass)
        
        # Step 4: Test with different masses (optional)
        if test_mass_points:
            self.test_model_for_masses(test_mass_points, use_reco_mass)
        
        print("Full analysis completed successfully!")
