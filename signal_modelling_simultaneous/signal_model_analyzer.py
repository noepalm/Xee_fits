"""
Signal Model Analyzer - Object-oriented approach for signal modeling in physics analysis

This module provides a comprehensive object-oriented framework for signal modeling
in particle physics analysis, replacing the previous function-based approach.
"""

import ROOT
import numpy as np
import os
import logging
import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed


def _is_nil_root_obj(obj: Any) -> bool:
    return obj is None or obj == ROOT.nullptr


class FitLogger:
    """Manages comprehensive logging of fit results and analysis progress"""
    
    def __init__(self, log_file_path: str = "signal_model_analysis.log", eos_folder: Optional[str] = None):
        self.log_file_path = Path(log_file_path)
        self.eos_folder = Path(eos_folder) if eos_folder else None
        self.log_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self.logger = logging.getLogger('SignalModelAnalyzer')
        self.logger.setLevel(logging.INFO)
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # File handler
        file_handler = logging.FileHandler(self.log_file_path, mode='w')
        file_handler.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        # Start log
        self.logger.info("="*80)
        self.logger.info("Signal Model Analysis Log Started")
        self.logger.info(f"Timestamp: {datetime.datetime.now()}")
        self.logger.info("="*80)
    
    def log_analysis_start(self, samples: Dict[str, Any], categories: Dict[str, Any], 
                          parametrized_vars: List[str], nuisanced_vars: Dict[str, List[str]], use_reweighting: bool = True):
        """Log analysis configuration"""
        self.logger.info("\nANALYSIS CONFIGURATION:")
        self.logger.info(f"Number of samples: {len(samples)}")
        self.logger.info(f"Samples: {list(samples.keys())}")
        self.logger.info(f"Number of categories: {len(categories)}")
        self.logger.info(f"Categories: {list(categories.keys())}")
        self.logger.info(f"Parametrized variables: {parametrized_vars}")
        self.logger.info(f"Nuisanced variables: {nuisanced_vars}")
        self.logger.info(f"Use reweighting: {use_reweighting}")
    
    def log_fit_result(self, sample_name: str, category_name: str, 
                      model: ROOT.RooAbsPdf, dataset: ROOT.RooDataSet,
                      fit_type: str = "response", model_type: str = "param",
                      fit_result: Optional[ROOT.RooFitResult] = None,
                      chi2_ndf: Optional[Tuple[float, int]] = None):
        """Log fit results for response or signal models
        
        Args:
            sample_name: Name of the sample
            category_name: Name of the category
            model: The fitted model
            dataset: The dataset used for fitting
            fit_type: Type of fit ("response" or "signal")
            model_type: Type of model (e.g., "param", "dcb", etc.) - used for signal fits
            fit_result: Optional RooFitResult object
            chi2_ndf: Optional tuple of (chi2/ndf, ndof)
        """
        # Create appropriate header
        if fit_type == "response":
            header = f"\nRESPONSE FIT RESULT - Sample: {sample_name}, Category: {category_name}"
        else:
            header = f"\n{fit_type.upper()} FIT RESULT ({model_type.upper()}) - Sample: {sample_name}, Category: {category_name}"
        
        self.logger.info(header)
        self.logger.info("-" * 60)
        
        # Log dataset info
        self.logger.info(f"Dataset entries: {dataset.numEntries()}")
        self.logger.info(f"Dataset sum of weights: {dataset.sumEntries():.2f}")
        
        # Log parameters
        params = model.getParameters(ROOT.RooArgSet([]))
        self.logger.info("Parameters:")
        for param in params:
            if hasattr(param, 'getVal'):
                min_val = param.getMin() if hasattr(param, 'getMin') else "N/A"
                max_val = param.getMax() if hasattr(param, 'getMax') else "N/A"
                
                # Show constant status for non-response fits
                if fit_type != "response":
                    is_constant = param.isConstant() if hasattr(param, 'isConstant') else False
                    const_str = " (CONSTANT)" if is_constant else ""
                else:
                    const_str = ""
                
                # Add warning if best fit value is too close to boundary
                if isinstance(min_val, float) and isinstance(max_val, float):
                    if param.getError() > 0:  # Avoid division by zero
                        if abs(param.getVal() - min_val)/param.getError() < 1 or abs(param.getVal() - max_val)/param.getError() < 1:
                        # if abs(param.getVal() - min_val)/(min_val + 1e-9) < 1e-2 or abs(param.getVal() - max_val)/(max_val + 1e-9) < 1e-2:
                            const_str += " (WARNING: boundary within 1sigma of best fit)"
                    else:
                        const_str += " (WARNING: error is 0)"
                
                self.logger.info(f"  {param.GetName()}: {param.getVal():.6f} ± {param.getError():.6f} "
                               f"[{min_val}, {max_val}]{const_str}")
        
        # Log Chi2
        if chi2_ndf is not None:
            self.logger.info(f"Chi2/NDF: {chi2_ndf[0]:.4f}/{chi2_ndf[1]:.0f}")
        
        # Log fit result status if available
        if fit_result:
            self.logger.info(f"Fit status: {fit_result.status()}")
            self.logger.info(f"Covariance quality: {fit_result.covQual()}")
            self.logger.info(f"EDM: {fit_result.edm():.2e}")
    
    def log_response_fit_result(self, sample_name: str, category_name: str, 
                               model: ROOT.RooAbsPdf, dataset: ROOT.RooDataSet,
                               fit_result: Optional[ROOT.RooFitResult] = None,
                               chi2_ndf: Optional[Tuple[float, int]] = None):
        """Log response function fit results (wrapper for backwards compatibility)"""
        self.log_fit_result(sample_name, category_name, model, dataset, 
                           "response", "param", fit_result, chi2_ndf)
    
    def log_signal_fit_result(self, sample_name: str, category_name: str,
                             model: ROOT.RooAbsPdf, dataset: ROOT.RooDataSet,
                             fit_result: Optional[ROOT.RooFitResult] = None,
                             model_type: str = "param",
                             chi2_ndf: Optional[Tuple[float, int]] = None):
        """Log signal model fit results (wrapper for backwards compatibility)"""
        self.log_fit_result(sample_name, category_name, model, dataset, 
                           "signal", model_type, fit_result, chi2_ndf)
    
    def log_parametrization_result(self, category_name: str, var_name: str, 
                                  fit_func: ROOT.TF1, is_constant: bool = False,
                                  const_value: float = None, const_error: float = None):
        """Log parameter vs mass fit results"""
        if is_constant:
            self.logger.info(f"\nPARAMETRIZATION RESULT - Category: {category_name}, Variable: {var_name} (CONSTANT)")
            self.logger.info("-" * 60)
            self.logger.info(f"Constant value: {const_value:.6f} ± {const_error:.6f}")
        else:
            self.logger.info(f"\nPARAMETRIZATION RESULT - Category: {category_name}, Variable: {var_name}")
            self.logger.info("-" * 60)
            self.logger.info(f"Fit function: {fit_func.GetTitle()}")
            self.logger.info(f"Chi2/NDF: {fit_func.GetChisquare():.4f}/{fit_func.GetNDF():.0f} = {fit_func.GetChisquare()/fit_func.GetNDF():.4f}")
            self.logger.info("Parameters:")
            for i in range(fit_func.GetNpar()):
                param_name = "intercept" if i == 0 else "slope"
                self.logger.info(f"  {param_name}: {fit_func.GetParameter(i):.6f} ± {fit_func.GetParError(i):.6f}")
    
    def log_entry_counts(self, entry_counts: Dict[str, int], category_name: str, 
                        dataset_type: str = "response"):
        """Log entry counts for samples in a category"""
        self.logger.info(f"\nENTRY COUNTS - Category: {category_name}, Dataset: {dataset_type}")
        self.logger.info("-" * 40)
        for sample_cat, count in entry_counts.items():
            self.logger.info(f"  {sample_cat}: {count} entries")
    
    def log_analysis_step(self, step_name: str):
        """Log analysis step"""
        self.logger.info(f"\n{'='*20} {step_name.upper()} {'='*20}")
    
    def log_warning(self, message: str):
        """Log warning message"""
        self.logger.warning(message)
    
    def log_error(self, message: str):
        """Log error message"""
        self.logger.error(message)
    
    def log_info(self, message: str):
        """Log info message"""
        self.logger.info(message)
    
    def finalize_log(self):
        """Finalize the log"""
        self.logger.info("\n" + "="*80)
        self.logger.info("Signal Model Analysis Completed")
        self.logger.info(f"Log saved to: {self.log_file_path.absolute()}")
        if self.eos_folder:
            self.copy_log_to_eos()
        self.logger.info("="*80)
    
    def copy_log_to_eos(self):
        """Copy log file to EOS directory"""
        if not self.eos_folder:
            self.logger.warning("No EOS folder specified, cannot copy log file")
            return
        
        try:
            # Ensure EOS directory exists
            self.eos_folder.mkdir(parents=True, exist_ok=True)
            
            # Copy log file to EOS folder
            eos_log_path = self.eos_folder / self.log_file_path.name
            
            # Use os.system for copy to handle potential EOS mounting issues
            import shutil
            shutil.copy2(str(self.log_file_path), str(eos_log_path))
            
            self.logger.info(f"Log file copied to EOS: {eos_log_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to copy log file to EOS: {e}")
    
    def update_eos_folder(self, eos_folder: str):
        """Update the EOS folder path"""
        self.eos_folder = Path(eos_folder) if eos_folder else None


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
    
    def __init__(self, workspace: ROOT.RooWorkspace, use_reweighting: bool = True,
                 use_syst: bool = False, shape_variations: Optional[List[str]] = None,
                 weight_variations: Optional[List[str]] = None, era: str = "2023"):
        self.workspace = workspace
        self.use_reweighting = use_reweighting
        self.use_syst = use_syst
        self.era = era

        self.shape_variations = sorted(set(shape_variations or []))
        self.weight_variations = sorted(set(weight_variations or []))
        self.variations = sorted(set(self.shape_variations) | set(self.weight_variations))

        if self.use_syst:
            self.directions = ["up", "down"]

    def _get_weight_variation(self, tree: Any, variation: str, direction: str,
                              event_weight: float, obj_index: int) -> float:
        """Get varied event weight for a given variation/direction.

        Supports a few branch naming conventions to make integration with existing ntuples easier.
        """
        candidate_branches = [
            f"{variation}_{direction}",
            f"weight_{variation}_{direction}",
            f"weight__{variation}_{direction}",
        ]

        varied_weight = None
        for branch_name in candidate_branches:
            if hasattr(tree, branch_name):
                varied_weight = getattr(tree, branch_name)
                break

        if varied_weight is None:
            raise AttributeError(
                f"Weight variation branch not found for '{variation}_{direction}'. "
                f"Tried: {candidate_branches}"
            )

        if isinstance(varied_weight, (list, tuple, np.ndarray)):
            return float(varied_weight[obj_index])

        return float(varied_weight)
    
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
    
    def load_dataset(self, sample: SampleConfig, category: CategoryConfig,
                     observable_name: str, dataset_type: str = "response",
                     use_reco_mass: bool = False) -> ROOT.RooDataSet:
        """Unified dataset loading for response and signal datasets
        
        Args:
            sample: Sample configuration
            category: Category configuration
            observable_name: Name of observable variable in workspace
            dataset_type: Type of dataset ("response" or "signal")
            use_reco_mass: Whether to use reconstructed mass (True) or reduced mass (False)
        """
        # Construct dataset name based on type
        prefix = "response_data" if dataset_type == "response" else "data"
        data_name = f"{prefix}_{sample.label}{category.label}_{self.era}"
        
        # Check if dataset already exists
        existing_data = self.workspace.data(data_name)
        if not _is_nil_root_obj(existing_data):
            return existing_data
        
        ### Creating datasets
        f = ROOT.TFile.Open(sample.file)
        t = f.Get("Events")
        
        weight_var = ROOT.RooRealVar(f"weightVar_{sample.label}{category.label}_{self.era}", 
                                   f"weightVar_{sample.label}{category.label}_{self.era}", 1.0)
        self.workspace.Import(weight_var, ROOT.RooCmdArg())
        
        obs_var = self.workspace.var(observable_name)
        if _is_nil_root_obj(obs_var):
            raise RuntimeError(f"Observable {observable_name} not found in workspace")
        data = ROOT.RooDataSet(data_name, data_name, 
                             ROOT.RooArgSet([obs_var]),
                             ROOT.RooFit.WeightVar(weight_var.GetName()))

        # Create systematic variation dataset (if requested)
        data_vars = {}
        if self.use_syst:
            for variation in self.variations:
                for direction in self.directions:
                    syst_data_name = f"{prefix}_{sample.label}{category.label}_{variation}_{direction}_{self.era}"
                    dataset = ROOT.RooDataSet(syst_data_name, syst_data_name,
                                         ROOT.RooArgSet([obs_var]), 
                                         ROOT.RooFit.WeightVar(weight_var.GetName()))
                    data_vars[f"{variation}_{direction}"] = dataset
        
        # Determine branch to read and range to use
        # Use corrected mass only when shape variations are enabled.
        mass_var = "DiElectron_fitted_mass_corrected"

        if dataset_type == "response":
            range_key = "mass_range" if use_reco_mass else "reduced_mass_range"
            normalize_by_gen = not use_reco_mass  # Apply gen_mass normalization for response
        else:  # signal
            range_key = "mass_range"
            normalize_by_gen = False
        
        min_val, max_val = sample.__dict__[range_key][1], sample.__dict__[range_key][2]
        
        ### Filling datasets
        for i in range(t.GetEntries()):
            t.GetEntry(i)
            weight = getattr(t, 'trigger_PS_weight', 1.0) if self.use_reweighting else 1.0
            # weight = getattr(t, 'weight', 1.0) if self.use_reweighting else 1.0
            
            # Get category variables for this event
            cat_vars = {var: getattr(t, var) for var in category.cuts.keys()}
            
            for j, val in enumerate(getattr(t, mass_var)):
                # Check category conditions
                if not self._check_category_conditions(category, cat_vars, j):
                    continue
                
                # Calculate fill value
                if normalize_by_gen:
                    gen_mass = t.GenZd_invMass
                    fill_value = val/gen_mass - 1
                else:
                    fill_value = val
                
                # Apply range cut
                if not (min_val <= fill_value <= max_val):
                    continue
                
                obs_var.setVal(fill_value)
                data.add(ROOT.RooArgSet([obs_var]), weight)
                
                # Fill systematic variations
                if self.use_syst:
                    for variation in self.variations:
                        for direction in self.directions:
                            if variation in self.shape_variations:
                                # Shape systematics: shifted mass branch, nominal event weight.
                                syst_var_name = f"DiElectron_fitted_mass_corrected__{variation}_{direction}"
                                syst_val = getattr(t, syst_var_name)[j]

                                if normalize_by_gen:
                                    syst_fill_value = syst_val/gen_mass - 1
                                else:
                                    syst_fill_value = syst_val

                                syst_weight = weight
                            else:
                                # Weight systematics: nominal mass value, shifted event weight.
                                syst_fill_value = fill_value
                                syst_weight = self._get_weight_variation(t, variation, direction, weight, j)

                            obs_var.setVal(syst_fill_value)
                            data_vars[f"{variation}_{direction}"].add(ROOT.RooArgSet([obs_var]), syst_weight)
        
        f.Close()
        self.workspace.Import(data, ROOT.RooCmdArg())
        if self.use_syst:
            for dataset in data_vars.values():
                self.workspace.Import(dataset, ROOT.RooCmdArg())
        
        return data
    
    def get_dataset_entry_count(self, dataset_name: str, weighted: bool = False) -> int:
        """Get number of entries in a dataset"""
        dataset = self.workspace.data(dataset_name)
        if not _is_nil_root_obj(dataset):
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
                dataset_name = f"response_data_{sample.label}{category.label}_{self.era}"
            else:
                dataset_name = f"data_{sample.label}{category.label}_{self.era}"
            
            count = self.get_dataset_entry_count(dataset_name)
            entry_counts[f"{name}{category.label}"] = count
            
        return entry_counts

class ParameterManager:
    """Manages fit parameters and their ranges"""
    
    def __init__(self, workspace: ROOT.RooWorkspace, nuisanced_vars: Dict[str, List[str]] = None,
                 era: str = "2023", single_cb: bool = False, double_gaussian: bool = False):
        self.workspace = workspace
        self.nuisanced_vars = nuisanced_vars if nuisanced_vars else {}
        self.era = era
        self.single_cb = single_cb
        self.double_gaussian = double_gaussian
        
        # Define parameter configurations
        if self.double_gaussian:
            self.response_vars = ["response_mean1", "response_sigma1", "response_mean2", "response_sigma2", "response_sig1frac"]
            self.dcb_vars = ["mean1", "sigma1", "mean2", "sigma2", "sig1frac"]
        else:
            self.response_vars = ["response_mean", "response_sigma", "response_alphaL", "response_nL"]
            self.dcb_vars = ["mean", "sigma", "alphaL", "nL"]
            if not self.single_cb:
                self.response_vars.extend(["response_alphaR", "response_nR"])
                self.dcb_vars.extend(["alphaR", "nR"])
        self.bw_vars = ["mean_BW", "width_BW"]
        
    def create_variables(self, sample: SampleConfig, category: CategoryConfig, 
                        var_list: List[str], tag: str = "", variation_tag: str = ""):
        """Create RooRealVar objects for given variables
        
        Args:
            sample: Sample configuration
            category: Category configuration
            var_list: List of variables to create
            tag: Tag to add to variable name (e.g., "_param")
            variation_tag: Tag for systematic variation (e.g., "_electronSmearing_up")
        """
        
        for var in var_list:
            # All parameters have era suffix (nuisance parameters are shared separately)
            var_name = f"{var}{tag}_{sample.label}{category.label}{variation_tag}_{self.era}"
            range_key = f"{var}_range"
            
            if hasattr(sample, range_key):
                var_range = getattr(sample, range_key)
                if _is_nil_root_obj(self.workspace.var(var_name)):
                    self.create_variable(var_name, var_range)
                # # DEBUG: retrieve variable from workspace and check min/max
                # created_var = self.workspace.var(var_name)
                # print(f"DEBUG:    var {var_name} has range {created_var.getMin()}, {created_var.getMax()} (range string = [{','.join(map(str, var_range))}])")
    
    def create_variable(self, var_name: str, var_range: List[float]):
        """Create a single RooRealVar with specified range
        
        Args:
            var_name: Name of the variable
            var_range: Range as [initial, min, max]
        """
        if _is_nil_root_obj(self.workspace.var(var_name)):
            if len(var_range) == 1:
                rv = ROOT.RooRealVar(var_name, var_name, float(var_range[0]))
            elif len(var_range) == 3:
                rv = ROOT.RooRealVar(var_name, var_name, float(var_range[0]), float(var_range[1]), float(var_range[2]))
            else:
                # Fallback: use first value as initial if range format is unexpected
                rv = ROOT.RooRealVar(var_name, var_name, float(var_range[0]))
            self.workspace.Import(rv, ROOT.RooCmdArg())
    
    def create_parametric_variable(self, var_name: str, formula: str, 
                                 dependencies: List[str]) -> ROOT.RooFormulaVar:
        """Create parametric variable using formula"""
        existing = self.workspace.obj(var_name)
        if not _is_nil_root_obj(existing):
            return existing
        dep_objects = []
        for dep in dependencies:
            # Check if dependency is a numeric constant
            if dep.replace(".", "").replace("-", "").isdigit():
                # Convert numeric string to RooConstVar
                const_val = float(dep)
                const_var = ROOT.RooFit.RooConst(const_val)
                dep_objects.append(const_var)
            else:
                # Try var() first, then generic obj()
                dep_obj = self.workspace.var(dep)
                if _is_nil_root_obj(dep_obj):
                    dep_obj = self.workspace.obj(dep)
                if _is_nil_root_obj(dep_obj):
                    raise ValueError(f"Dependency '{dep}' for parametric variable '{var_name}' not found in workspace.")
                dep_objects.append(dep_obj)
        
        param_var = ROOT.RooFormulaVar(var_name, var_name, formula, 
                                     ROOT.RooArgList(*dep_objects))
        self.workspace.Import(param_var, ROOT.RooCmdArg())
        return param_var
    
    def set_constant_parameter(self, var_name: str, value: float, error: float = 0.0):
        """Set parameter to constant value"""
        var = self.workspace.var(var_name)
        if not _is_nil_root_obj(var):
            var.setVal(value)
            if error > 0:
                var.setError(error)
            var.setConstant(True)


class ModelBuilder:
    """Builds and manages physics models"""
    
    def __init__(self, workspace: ROOT.RooWorkspace, param_manager: ParameterManager,
                 era: str = "2023", gaussian_signal: bool = False,
                 envelope: bool = False):
        self.workspace = workspace
        self.param_manager = param_manager
        self.era = era
        self.gaussian_signal = gaussian_signal
        self.envelope = envelope
    
    def build_response_function(self, sample: SampleConfig, category: CategoryConfig, 
                              observable_name: str, variation_tag: str = "") -> ROOT.RooAbsPdf:
        """Build Crystal Ball response function
        
        Args:
            sample: Sample configuration
            category: Category configuration
            observable_name: Name of observable variable
            variation_tag: Tag for systematic variation (e.g., "_electronSmearing_up")
        """
        
        model_name = f"response_function_{sample.label}{category.label}{variation_tag}_{self.era}"

        obs_var = self.workspace.var(observable_name)
        if _is_nil_root_obj(obs_var):
            raise RuntimeError(f"Observable {observable_name} not found in workspace")

        if self.param_manager.double_gaussian:
            mean1 = f"response_mean1_{sample.label}{category.label}{variation_tag}_{self.era}"
            sigma1 = f"response_sigma1_{sample.label}{category.label}{variation_tag}_{self.era}"
            mean2 = f"response_mean2_{sample.label}{category.label}{variation_tag}_{self.era}"
            sigma2 = f"response_sigma2_{sample.label}{category.label}{variation_tag}_{self.era}"
            frac = f"response_sig1frac_{sample.label}{category.label}{variation_tag}_{self.era}"

            g1_name = f"response_gauss1_{sample.label}{category.label}{variation_tag}_{self.era}"
            g2_name = f"response_gauss2_{sample.label}{category.label}{variation_tag}_{self.era}"

            mean1_var = self.workspace.var(mean1)
            sigma1_var = self.workspace.var(sigma1)
            mean2_var = self.workspace.var(mean2)
            sigma2_var = self.workspace.var(sigma2)
            frac_var = self.workspace.var(frac)
            if any(_is_nil_root_obj(var) for var in [mean1_var, sigma1_var, mean2_var, sigma2_var, frac_var]):
                raise RuntimeError(f"Response parameters missing for {model_name}")

            gauss1 = ROOT.RooGaussian(g1_name, g1_name, obs_var, mean1_var, sigma1_var)
            gauss2 = ROOT.RooGaussian(g2_name, g2_name, obs_var, mean2_var, sigma2_var)
            self.workspace.Import(gauss1, ROOT.RooCmdArg())
            self.workspace.Import(gauss2, ROOT.RooCmdArg())

            sum_pdf = ROOT.RooAddPdf(
                model_name,
                model_name,
                ROOT.RooArgList(gauss1, gauss2),
                ROOT.RooArgList(frac_var),
            )
            self.workspace.Import(sum_pdf, ROOT.RooCmdArg())
            return self.workspace.pdf(model_name)
        
        # Build variable list for Crystal Ball (all parameters have era suffix)
        param_objects = ROOT.RooArgList()
        for var in self.param_manager.response_vars:
            param_name = f"{var}_{sample.label}{category.label}{variation_tag}_{self.era}"
            param_obj = self.workspace.var(param_name)
            if _is_nil_root_obj(param_obj):
                raise RuntimeError(f"Response parameter {param_name} not found in workspace")
            param_objects.add(param_obj)

        model = ROOT.RooCrystalBall(model_name, model_name, obs_var, param_objects)
        self.workspace.Import(model, ROOT.RooCmdArg())
        return self.workspace.pdf(model_name)

    def _get_signal_model_index(self) -> ROOT.RooCategory:
        """Get or create the era-specific signal-model index used by RooMultiPdf."""
        index_name = f"signal_model_index_{self.era}"
        index = self.workspace.cat(index_name)
        if not _is_nil_root_obj(index):
            return index

        index = ROOT.RooCategory(index_name, index_name)
        index.defineType("dcb")
        index.defineType("gaussian")
        self.workspace.Import(index, ROOT.RooCmdArg())
        stored_index = self.workspace.cat(index_name)
        return stored_index if not _is_nil_root_obj(stored_index) else index

    def _build_signal_core_pdf(self, sample: SampleConfig, category: CategoryConfig,
                               tag: str, use_shared_mass: bool, core_type: str) -> str:
        """Build the signal-core PDF used by the full signal model."""
        mass_obs = "mass" if use_shared_mass else f"mass_{sample.label}"

        if core_type == "gaussian":
            mean = f"mean_{tag}_{sample.label}{category.label}_{self.era}"
            sigma = f"sigma_{tag}_{sample.label}{category.label}_{self.era}"
            gauss_name = f"gaussian_{tag}_{sample.label}{category.label}_{self.era}"
            mass_var = self.workspace.var(mass_obs)
            mean_var = self.workspace.var(mean)
            sigma_var = self.workspace.var(sigma)
            if any(_is_nil_root_obj(var) for var in [mass_var, mean_var, sigma_var]):
                raise RuntimeError(f"Gaussian core parameters missing for {gauss_name}")
            gauss = ROOT.RooGaussian(gauss_name, gauss_name, mass_var, mean_var, sigma_var)
            self.workspace.Import(gauss, ROOT.RooCmdArg())
            return gauss_name

        if core_type == "dcb":
            dcb_vars = []
            for dcb_var in self.param_manager.dcb_vars:
                dcb_vars.append(f"{dcb_var}_{tag}_{sample.label}{category.label}_{self.era}")
            dcb_name = f"crystalBall_{tag}_{sample.label}{category.label}_{self.era}"
            mass_var = self.workspace.var(mass_obs)
            if _is_nil_root_obj(mass_var):
                raise RuntimeError(f"Mass observable {mass_obs} not found in workspace")
            param_objects = []
            for param_name in dcb_vars:
                param_obj = self.workspace.obj(param_name)
                if _is_nil_root_obj(param_obj):
                    raise RuntimeError(f"DCB parameter {param_name} not found in workspace")
                param_objects.append(param_obj)
            dcb_pdf = ROOT.RooCrystalBall(dcb_name, dcb_name, mass_var, *param_objects)
            self.workspace.Import(dcb_pdf, ROOT.RooCmdArg())
            return dcb_name

        raise ValueError(f"Unsupported signal core type: {core_type}")
    
    def build_signal_model(self, sample: SampleConfig, category: CategoryConfig, 
                         parametrized_vars: List[str], tag: str = "param", 
                         use_reco_mass: bool = False, use_shared_mass: bool = False,
                         build_variations: bool = False) -> ROOT.RooAbsPdf:
        """Build complete signal model (dCB * BW convolution or dCB only)
        
        Args:
            sample: Sample configuration
            category: Category configuration
            parametrized_vars: List of parametrized variables
            tag: Tag for model naming
            use_reco_mass: Whether to use reconstructed mass
            use_shared_mass: Whether to use shared mass variable
            build_variations: Whether to build systematic variation models
        """
        
        if self.envelope:
            dcb_pdf_name = self._build_signal_core_pdf(sample, category, tag, use_shared_mass, "dcb")
            gaussian_pdf_name = self._build_signal_core_pdf(sample, category, tag, use_shared_mass, "gaussian")

            if use_reco_mass:
                dcb_model = self.workspace.pdf(dcb_pdf_name)
                gaussian_model = self.workspace.pdf(gaussian_pdf_name)
            else:
                dcb_model = self._build_convolution_model(sample, category, tag, dcb_pdf_name, model_suffix="_dcb")
                gaussian_model = self._build_convolution_model(sample, category, tag, gaussian_pdf_name, model_suffix="_gaussian")

            envelope_name = f"model_{tag}_{sample.label}{category.label}_{self.era}"
            pdf_index = self._get_signal_model_index()
            envelope_pdf = ROOT.RooMultiPdf(
                envelope_name,
                envelope_name,
                pdf_index,
                ROOT.RooArgList(dcb_model, gaussian_model),
            )
            self.workspace.Import(envelope_pdf, ROOT.RooCmdArg())
            return self.workspace.pdf(envelope_name)

        if self.gaussian_signal:
            core_pdf_name = self._build_signal_core_pdf(sample, category, tag, use_shared_mass, "gaussian")
        elif self.param_manager.double_gaussian:
            mean1 = f"mean1_{tag}_{sample.label}{category.label}_{self.era}"
            sigma1 = f"sigma1_{tag}_{sample.label}{category.label}_{self.era}"
            mean2 = f"mean2_{tag}_{sample.label}{category.label}_{self.era}"
            sigma2 = f"sigma2_{tag}_{sample.label}{category.label}_{self.era}"
            frac = f"sig1frac_{tag}_{sample.label}{category.label}_{self.era}"

            g1_name = f"gauss1_{tag}_{sample.label}{category.label}_{self.era}"
            g2_name = f"gauss2_{tag}_{sample.label}{category.label}_{self.era}"
            core_name = f"doubleGauss_{tag}_{sample.label}{category.label}_{self.era}"

            mass_obs = "mass" if use_shared_mass else f"mass_{sample.label}"
            mass_var = self.workspace.var(mass_obs)
            mean1_var = self.workspace.var(mean1)
            sigma1_var = self.workspace.var(sigma1)
            mean2_var = self.workspace.var(mean2)
            sigma2_var = self.workspace.var(sigma2)
            frac_var = self.workspace.var(frac)
            if any(_is_nil_root_obj(var) for var in [mass_var, mean1_var, sigma1_var, mean2_var, sigma2_var, frac_var]):
                raise RuntimeError(f"Double-Gaussian parameters missing for {core_name}")

            gauss1 = ROOT.RooGaussian(g1_name, g1_name, mass_var, mean1_var, sigma1_var)
            gauss2 = ROOT.RooGaussian(g2_name, g2_name, mass_var, mean2_var, sigma2_var)
            self.workspace.Import(gauss1, ROOT.RooCmdArg())
            self.workspace.Import(gauss2, ROOT.RooCmdArg())

            sum_pdf = ROOT.RooAddPdf(
                core_name,
                core_name,
                ROOT.RooArgList(gauss1, gauss2),
                ROOT.RooArgList(frac_var),
            )
            self.workspace.Import(sum_pdf, ROOT.RooCmdArg())
            core_pdf_name = core_name
        else:
            core_pdf_name = self._build_signal_core_pdf(sample, category, tag, use_shared_mass, "dcb")
            
        if use_reco_mass:
            model = self.workspace.pdf(core_pdf_name).Clone(f"model_{tag}_{sample.label}{category.label}_{self.era}")
            self.workspace.Import(model, ROOT.RooCmdArg())
        else:
            model = self._build_convolution_model(sample, category, f"{tag}", core_pdf_name)
        
        return model
    
    def _build_convolution_model(self, sample: SampleConfig, category: CategoryConfig, 
                               tag: str, dcb_name: str, model_suffix: str = "") -> ROOT.RooAbsPdf:
        """Build convolution of Crystal Ball and Breit-Wigner"""
        
        # Build Breit-Wigner
        bw_vars = [self.workspace.obj(f"{var}_{tag}_{sample.label}{category.label}_{self.era}") 
                  for var in self.param_manager.bw_vars]
        mass_var = self.workspace.var(f"mass_{sample.label}")
        bw_vars.insert(0, mass_var)
        
        # Relativistic Breit-Wigner formula
        relBW_formula = ("2*sqrt(2)/pi * @1**2 * @2*sqrt(@1**2 + @2**2) / "
                        "((@0**2 - @1**2)*(@0**2 - @1**2) + @1**2 * @2**2) / "
                        "(sqrt(@1**2 + @1*sqrt(@2**2 + @1**2)))")
        
        relBW_name = f"relBW_{tag}_{sample.label}{category.label}{model_suffix}_{self.era}"
        relBW = ROOT.RooGenericPdf(relBW_name, relBW_formula, bw_vars)
        self.workspace.Import(relBW, ROOT.RooCmdArg())
        
        # Setup convolution
        mass_var.setBins(10000, "cache")
        mass_var.setMin("cache", -20)
        mass_var.setMax("cache", 20)
        
        # Build convolution
        conv_name = f"model_{tag}_{sample.label}{category.label}{model_suffix}_{self.era}"
        dcb_pdf = self.workspace.pdf(dcb_name)
        if _is_nil_root_obj(dcb_pdf):
            raise RuntimeError(f"DCB pdf {dcb_name} not found in workspace")
        conv_pdf = ROOT.RooFFTConvPdf(conv_name, conv_name, mass_var, dcb_pdf, relBW)
        self.workspace.Import(conv_pdf, ROOT.RooCmdArg())

        return self.workspace.pdf(conv_name)


class FitManager:
    """Manages fitting operations"""
    
    def __init__(self, workspace: ROOT.RooWorkspace, logger: Optional['FitLogger'] = None, era : str = "2023"):
        self.workspace = workspace
        self.logger = logger
        self.era = era
    
    def compute_chi2(self, model: ROOT.RooAbsPdf, dataset: ROOT.RooDataSet, ndof: Optional[int] = None) -> Optional[float]:
        """Compute Chi2/NDF for model-dataset comparison"""
        try:
            # Get the observable
            obs_set = dataset.get()
            if obs_set.getSize() != 1:
                return None
            
            obs = obs_set.first()
            
            # Create frame and plot (no drawing needed)
            frame = obs.frame()
            dataset.plotOn(frame, ROOT.RooFit.DataError(ROOT.RooAbsData.Poisson))
            model.plotOn(frame)
            
            # Get number of fit parameters (same method as in plotting_oo.py)
            params = model.getParameters(ROOT.RooArgSet([obs]))
            nparams = 0
            for param in params:
                if hasattr(param, 'isConstant') and not param.isConstant():
                    if "model_index" not in param.GetName():
                        nparams += 1

            if ndof is not None:
                nparams = ndof # override if specified
            
            # Compute chi2
            chi2_ndf = frame.chiSquare(nparams)
            return chi2_ndf, nparams
            
        except Exception as e:
            if self.logger:
                self.logger.log_warning(f"Could not compute Chi2: {e}")
            return None
    
    def fit_model(self, model: ROOT.RooAbsPdf, dataset: ROOT.RooDataSet, 
                 save_result: bool = True, sample_name: str = "", category_name: str = "",
                 fit_type: str = "response", **fit_options) -> Optional[ROOT.RooFitResult]:
        """Fit model to dataset"""
        default_options = {
            'Save': True,
            'NumCPU': 8,
            'Hesse' : True,
            'Minos' : True,
            # 'SumW2Error': True,
            # 'AsymptoticError': True,
            'Minimizer': "Minuit2",
            'SplitRange' : True,
            # 'Range' : "Zd_M3p1",
            # 'Offset' : "initial",
        }
        default_options.update(fit_options)
        
        # Convert to RooFit command arguments
        fit_args = []
        for key, value in default_options.items():
            if hasattr(ROOT.RooFit, key):
                fit_args.append(getattr(ROOT.RooFit, key)(value))
            else:
                print("WARNING: RooFit option not recognized:", key)

        print(f"DEBUG: Fitting {model} to {dataset} with options:")
        for arg in fit_args:
            print(f"  - {arg}")
        result = model.fitTo(dataset, *fit_args)

        # import updated model to workspace
        self.workspace.Import(model, ROOT.RooCmdArg())
        
        # Compute Chi2
        chi2_ndf = self.compute_chi2(model, dataset)

        # Define variables for parameter ERROR and COVARIANCE, and import them to the workspace
        # NOTICE: only consider covariance between par0, par1 of same variable
        model_params = {}
        if result is not None:
            for i in range(result.floatParsFinal().getSize()):
                par_i = result.floatParsFinal().at(i)
                par_i_name = par_i.GetName()
                error_var_name = par_i_name.replace("par0", "par0_err").replace("par1", "par1_err")
                
                # Create error variable
                if _is_nil_root_obj(self.workspace.var(error_var_name)):
                    error_var = ROOT.RooRealVar(error_var_name, error_var_name, par_i.getError())
                    self.workspace.Import(error_var, ROOT.RooCmdArg())

                # also store which signal model parameter this was (needed for covariance later)
                var_key = par_i_name.split("_fit")[0]
                if var_key not in model_params:
                    model_params[var_key] = [par_i_name]
                else:
                    model_params[var_key].append(par_i_name)
                
                # # Create covariance variable (only diagonal elements for now)
                # if _is_nil_root_obj(self.workspace.var(cov_var_name)):
                #     cov_value = result.covQual() == 3 and result.correlation(par_i) * par_i.getError() * par_i.getError() or 0.0
                #     cov_var = ROOT.RooRealVar(cov_var_name, cov_var_name, cov_value)
                #     self.workspace.Import(cov_var, ROOT.RooCmdArg())

        # and now save covariances per variable
        cov_matrix = result.covarianceMatrix()
        if result is not None:
            for param, varname in model_params.items():
                cov_var_name = f'{varname[1].replace("par1", "par01_cov")}'

                # find indices of variables for cov matrix
                idx1 = result.floatParsFinal().index(varname[0])
                idx2 = result.floatParsFinal().index(varname[1])
                cov_value = cov_matrix[idx1][idx2]

                cov_var = ROOT.RooRealVar(cov_var_name, cov_var_name, cov_value)
                self.workspace.Import(cov_var, ROOT.RooCmdArg())
        
        # Log fit result
        if self.logger:
            if fit_type == "response":
                self.logger.log_response_fit_result(sample_name, category_name, model, dataset, result, chi2_ndf)
            elif fit_type == "signal":
                model_type = "param"  # Could be extended to support different types
                self.logger.log_signal_fit_result(sample_name, category_name, model, dataset, result, model_type, chi2_ndf)
        
        return result


class SignalModelAnalyzer:
    """Main class that orchestrates the signal modeling analysis"""
    
    def __init__(self, samples: Dict[str, SampleConfig], categories: Dict[str, CategoryConfig], 
                 wsfile: str, parametrized_vars: List[str], nuisanced_vars: Dict[str, List[str]], log_file: str = "signal_model_analysis.log",
                 shape_nuisanced_vars: Optional[Dict[str, List[str]]] = None,
                 weight_nuisanced_vars: Optional[Dict[str, List[str]]] = None,
                 nuisanced_vars_stat: Optional[List[str]] = None,
                 single_cb: bool = False,
                 double_gaussian: bool = False,
                 gaussian_signal: bool = False,
                 envelope: bool = False,
                 use_simultaneous_signal_fit: bool = True,
                 eos_folder: Optional[str] = None, use_reweighting: bool = True, use_syst: bool = False, era: str = "2023"):
        self.samples = samples
        self.categories = categories
        self.parametrized_vars = parametrized_vars
        self.nuisanced_vars = nuisanced_vars
        self.shape_nuisanced_vars = shape_nuisanced_vars if shape_nuisanced_vars is not None else nuisanced_vars
        self.weight_nuisanced_vars = weight_nuisanced_vars if weight_nuisanced_vars is not None else {}
        self.nuisanced_vars_stat = nuisanced_vars_stat if nuisanced_vars_stat is not None else []
        self.single_cb = single_cb
        self.double_gaussian = double_gaussian
        self.gaussian_signal = gaussian_signal
        self.envelope = envelope
        self.use_simultaneous_signal_fit = use_simultaneous_signal_fit
        self.use_reweighting = use_reweighting
        self.use_syst = use_syst
        self.era = era

        if self.gaussian_signal and (self.single_cb or self.double_gaussian or self.envelope):
            raise ValueError("gaussian_signal is only supported with default double-sided Crystal Ball mode")

        if self.envelope and (self.single_cb or self.double_gaussian or self.gaussian_signal):
            raise ValueError("envelope is only supported with default double-sided Crystal Ball mode")
        
        # Initialize logger
        self.logger = FitLogger(log_file, eos_folder)
        self.logger.log_analysis_start(samples, categories, parametrized_vars, nuisanced_vars, use_reweighting)
        
        # Initialize managers
        self.workspace_manager = WorkspaceManager(wsfile)
        shape_variations = set(sum(self.shape_nuisanced_vars.values(), []))
        weight_variations = set(sum(self.weight_nuisanced_vars.values(), []))
        self.dataset_loader = DatasetLoader(
            self.workspace_manager.workspace,
            use_reweighting,
            use_syst,
            shape_variations=list(shape_variations),
            weight_variations=list(weight_variations),
            era=era,
        )
        self.param_manager = ParameterManager(
            self.workspace_manager.workspace,
            nuisanced_vars,
            era,
            single_cb=single_cb,
            double_gaussian=double_gaussian,
        )
        self.model_builder = ModelBuilder(
            self.workspace_manager.workspace,
            self.param_manager,
            era,
            gaussian_signal=gaussian_signal,
            envelope=envelope,
        )
        self.fit_manager = FitManager(self.workspace_manager.workspace, self.logger, era)
        
    
    def get_logger(self) -> FitLogger:
        """Get the logger instance for external use (e.g., plotting)"""
        return self.logger
    
    def set_reweighting(self, use_reweighting: bool):
        """Update the reweighting flag for the analyzer and dataset loader"""
        self.use_reweighting = use_reweighting
        self.dataset_loader.use_reweighting = use_reweighting
    
    def delete_workspace(self):
        """Delete existing workspace file"""
        self.workspace_manager.delete_workspace_file()
    
    
    def _get_main_signal_samples(self) -> Dict[str, SampleConfig]:
        """Return the signal samples used for the simultaneous fit, excluding J/psi."""
        return {name: sample for name, sample in self.samples.items() if "JPsi" not in name}

    def _ensure_mass_observable(self, mass_min: float, mass_max: float) -> ROOT.RooRealVar:
        """Create the shared mass observable used by the simultaneous fit."""
        mass_var = self.workspace_manager.workspace.var("mass")
        # Check if it's actually valid (not a nil pointer)
        if _is_nil_root_obj(mass_var):
            mass_var = ROOT.RooRealVar("mass", "mass", float(mass_min), float(mass_min), float(mass_max))
            self.workspace_manager.workspace.Import(mass_var, ROOT.RooCmdArg())
            mass_var = self.workspace_manager.workspace.var("mass")
            if _is_nil_root_obj(mass_var):
                raise RuntimeError("Failed to create mass observable in workspace")
        return mass_var

    def _ensure_sample_category(self, category: CategoryConfig, sample_names: List[str]) -> ROOT.RooCategory:
        """Create or reuse the RooCategory used to switch between mass points."""
        category_name = f"signal_sample_{category.name or 'inclusive'}_{self.era}"
        sample_category = self.workspace_manager.workspace.cat(category_name)
        if not _is_nil_root_obj(sample_category):
            return sample_category

        sample_category = ROOT.RooCategory(category_name, category_name)
        for sample_name in sample_names:
            sample_category.defineType(sample_name)
        self.workspace_manager.workspace.Import(sample_category, ROOT.RooCmdArg())
        stored_category = self.workspace_manager.workspace.cat(category_name)
        return stored_category if not _is_nil_root_obj(stored_category) else sample_category

    def _simultaneous_parameter_name(self, category: CategoryConfig, var: str, coef_index: int) -> str:
        """Name a shared linear coefficient for the simultaneous fit."""
        return f"{var}_fit_par{coef_index}_{self.era}"

    def _build_simultaneous_signal_component(self, sample: SampleConfig, category: CategoryConfig) -> ROOT.RooAbsPdf:
        """Build one dCB component for the simultaneous signal fit."""
        mass_value = sample.nominal_mass
        component_tag = f"sim_{sample.label}"

        for var in self.param_manager.dcb_vars:
            par0_name = self._simultaneous_parameter_name(category, var, 0)
            par1_name = self._simultaneous_parameter_name(category, var, 1)
            param_name = f"{var}_{component_tag}_{category.label}_{self.era}"

            # if var in ["mean", "mean1", "mean2"]:
            #     param_range = [0, -1, 1]
            # elif var in ["sigma", "sigma1", "sigma2"]:
            #     param_range = [0.05, 1e-3, 5]
            # elif var in ["alphaL", "alphaR"]:
            #     param_range = [1, 0.1, 10]
            # else:
            #     param_range = [1, 0.1, 20]

            param_ranges = {
                "par0" : {
                    "mean" : [0, -0.5, 0.5],
                    "sigma" : [0, -0.2, 0.5],
                    # "sigma" : [0.001, 0, 0.5],
                    "alphaL" : [0.8, 0.1, 3],
                    "alphaR" : [2, 0.1, 10],
                    "nL" : [2, -10, 10],
                    "nR" : [2.3, -10, 10],
                },
                "par1" : {
                    "mean" : [1, -0.5, 2],
                    "sigma" : [0.016, 0.005, 0.08],
                    "alphaL" : [-0.05, -2, 2],
                    "alphaR" : [-0.07, -2, 2],
                    "nL" : [0.24, -0.5, 1],
                    "nR" : [0.02, -0.5, 1],
                }
            }

            self.param_manager.create_variable(par0_name, param_ranges["par0"].get(var, [0, -1, 1]))
            self.param_manager.create_variable(par1_name, param_ranges["par1"].get(var, [0, -1, 1]))
            self.param_manager.create_parametric_variable(
                param_name,
                "@0 + @1 * @2",
                [par0_name, par1_name, str(mass_value)],
            )

        model_name = f"sim_signal_{sample.label}{category.label}_{self.era}"
        param_names = [
            f"{var}_{component_tag}_{category.label}_{self.era}"
            for var in self.param_manager.dcb_vars
        ]
        
        # Get the mass observable and all parameter objects
        mass_obs = self.workspace_manager.workspace.var("mass")
        if _is_nil_root_obj(mass_obs):
            raise RuntimeError("Mass observable not found in workspace")
        
        param_map = {}
        for param_name in param_names:
            param_obj = self.workspace_manager.workspace.obj(param_name)
            if _is_nil_root_obj(param_obj):
                param_obj = self.workspace_manager.workspace.var(param_name)
            if _is_nil_root_obj(param_obj):
                raise RuntimeError(f"Parameter {param_name} not found in workspace")
            base_name = param_name.split(f"_{component_tag}", 1)[0]
            param_map[base_name] = param_obj

        # Create CrystalBall directly and import it (match original constructor signature)
        if all(name in param_map for name in ["mean", "sigma", "alphaL", "nL", "alphaR", "nR"]):
            component_pdf = ROOT.RooCrystalBall(
                model_name,
                model_name,
                mass_obs,
                param_map["mean"],
                param_map["sigma"],
                param_map["alphaL"],
                param_map["nL"],
                param_map["alphaR"],
                param_map["nR"],
            )
        elif all(name in param_map for name in ["mean", "sigma", "alphaL", "nL"]):
            component_pdf = ROOT.RooCrystalBall(
                model_name,
                model_name,
                mass_obs,
                param_map["mean"],
                param_map["sigma"],
                param_map["alphaL"],
                param_map["nL"],
                False,
            )
        else:
            raise RuntimeError(
                f"Unsupported DCB parameter set for {model_name}: {sorted(param_map.keys())}"
            )
        self.workspace_manager.workspace.Import(component_pdf, ROOT.RooCmdArg())
        
        # Retrieve it from workspace to verify
        component_pdf = self.workspace_manager.workspace.pdf(model_name)
        if _is_nil_root_obj(component_pdf):
            raise RuntimeError(f"Failed to create component PDF {model_name}")
        return component_pdf

    def _build_simultaneous_signal_dataset(self, category: CategoryConfig, samples: Dict[str, SampleConfig]) -> ROOT.RooDataSet:
        """Build a combined weighted dataset with a RooCategory selecting the mass point.
        
        First creates per-sample mass observables, then loads datasets, then combines them.
        """
        dataset_name = f"sim_signal_data_{category.label}_{self.era}"
        existing_data = self.workspace_manager.workspace.data(dataset_name)
        if not _is_nil_root_obj(existing_data):
            return existing_data

        main_samples = list(samples.items())
        if not main_samples:
            raise ValueError("No signal samples available for the simultaneous fit")

        # # Step 1: Create per-sample mass observables based on their ranges
        # for sample_name, sample in main_samples:
        #     obs_name = f"mass_{sample.label}"
        #     existing_obs = self.workspace_manager.workspace.var(obs_name)
        #     if _is_nil_root_obj(existing_obs):
        #         mass_mid, mass_min, mass_max = sample.mass_range[0], sample.mass_range[1], sample.mass_range[2]
        #         obs_var = ROOT.RooRealVar(obs_name, obs_name, float(mass_mid), float(mass_min), float(mass_max))
        #         self.workspace_manager.workspace.Import(obs_var, ROOT.RooCmdArg())

        # # Step 1: Create per-sample mass observables based on their ranges
        # for sample_name, sample in main_samples:
        #     obs_name = f"mass_{sample.label}"
        #     existing_obs = self.workspace_manager.workspace.var(obs_name)
        #     if _is_nil_root_obj(existing_obs):
        #         mass_mid, mass_min, mass_max = sample.mass_range[0], sample.mass_range[1], sample.mass_range[2]
        #         obs_var = ROOT.RooRealVar(obs_name, obs_name, float(mass_mid), float(mass_min), float(mass_max))
        #         self.workspace_manager.workspace.Import(obs_var, ROOT.RooCmdArg())

        # Step 1: Get shared mass range and create shared observable
        mass_min = min(sample.mass_range[1] for _, sample in main_samples)
        mass_max = max(sample.mass_range[2] for _, sample in main_samples)
        mass_var = self._ensure_mass_observable(mass_min, mass_max)
        sample_category = self._ensure_sample_category(category, [name for name, _ in main_samples])

        # Step 2: Create per-sample mass ranges
        for sample_name, sample in main_samples:
            mass_mid, mass_min, mass_max = sample.mass_range[0], sample.mass_range[1], sample.mass_range[2]
            mass_var.setRange(sample_name, float(mass_min), float(mass_max))
            print("DEBUG: set range ", sample_name, ": ", mass_var.getRange(sample_name))

        # Step 3: Create weight variable
        weight_name = f"sim_weight_{category.name or 'inclusive'}_{self.era}"
        weight_var = self.workspace_manager.workspace.var(weight_name)
        if _is_nil_root_obj(weight_var):
            weight_var = ROOT.RooRealVar(weight_name, weight_name, 1.0)
            self.workspace_manager.workspace.Import(weight_var, ROOT.RooCmdArg())
            weight_var = self.workspace_manager.workspace.var(weight_name)
            if _is_nil_root_obj(weight_var):
                raise RuntimeError(f"Failed to create weight variable {weight_name} in workspace")

        # Step 4: Load each sample's dataset and create map to sample name for import
        dataset_map = {}
        for sample_name, sample in main_samples:
            # obs_name = f"mass_{sample.label}"
            obs_name = f"mass"
            
            # Now load_dataset will find the observable that we created in Step 1
            source_dataset = self.dataset_loader.load_dataset(
                sample,
                category,
                obs_name,
                dataset_type="signal",
                use_reco_mass=False,
            )

            dataset_map[sample_name] = source_dataset

        # Step 5: Create combined dataset with list of variables
        # var_list = [mass_var, sample_category, weight_var]
        # data = ROOT.RooDataSet(
        #     dataset_name,
        #     dataset_name,
        #     ROOT.RooArgSet(var_list),
        #     ROOT.RooFit.WeightVar(weight_var.GetName()),
        # )
        data = ROOT.RooDataSet(
            dataset_name,
            dataset_name,
            mass_var, 
            ROOT.RooFit.Index(sample_category),
            ROOT.RooFit.Import(dataset_map)
        )

        self.workspace_manager.workspace.Import(data, ROOT.RooCmdArg())
        return self.workspace_manager.workspace.data(dataset_name)

    def build_simultaneous_signal_models(self, fit_models: bool = True):
        """Build a simultaneous RooSimultaneous signal model over all non-J/psi samples.
        
        The RooCategory index values and the RooSimultaneous PDF component order are matched
        by iterating over main_samples in the same order in both dataset and model building.
        """
        self.logger.log_analysis_step("Building Simultaneous Signal Models")

        main_samples = self._get_main_signal_samples()
        if not main_samples:
            raise ValueError("No signal samples available after excluding J/psi")

        for category_label, category in self.categories.items():
            self.logger.log_info(f"Building simultaneous signal model for category: {category_label}")
            # Dataset creation uses the same sample iteration order as PDF component addition below
            dataset = self._build_simultaneous_signal_dataset(category, main_samples)
            sample_category = self.workspace_manager.workspace.cat(f"signal_sample_{category.name or 'inclusive'}_{self.era}")

            model_name = f"simultaneous_signal_model_{category.label}_{self.era}"
            simultaneous_pdf = self.workspace_manager.workspace.pdf(model_name)
            if _is_nil_root_obj(simultaneous_pdf):
                simultaneous_pdf = ROOT.RooSimultaneous(model_name, model_name, sample_category)
                # Components must be added in the same order as category types are defined in _build_simultaneous_signal_dataset
                for sample_name, sample in main_samples.items():
                    component = self._build_simultaneous_signal_component(sample, category)
                    simultaneous_pdf.addPdf(component, sample_name)
                self.workspace_manager.workspace.Import(simultaneous_pdf, ROOT.RooCmdArg())
                simultaneous_pdf = self.workspace_manager.workspace.pdf(model_name)
                if _is_nil_root_obj(simultaneous_pdf):
                    raise RuntimeError(f"Failed to save RooSimultaneous {model_name} to workspace")

            if fit_models:
                self.fit_manager.fit_model(
                    simultaneous_pdf,
                    dataset,
                    sample_name="simultaneous",
                    category_name=category.name,
                    fit_type="signal",
                )

        self.workspace_manager.save()
        self.logger.log_info("Simultaneous signal models built successfully!")
    
    def build_signal_models(self, use_reco_mass: bool = False, fit_models: bool = False, max_workers: int = 4):
        """Build parametric signal models using simultaneous RooSimultaneous fit
        
        Args:
            use_reco_mass: Whether to use reconstructed mass (not supported in simultaneous mode)
            fit_models: Whether to fit the models
            max_workers: Unused (kept for backwards compatibility)
        """
        if self.gaussian_signal or self.param_manager.double_gaussian or self.model_builder.envelope:
            raise NotImplementedError(
                "gaussian_signal, double_gaussian, and envelope modes are not supported in the simultaneous fit path. "
                "Please use the per-sample approach by setting use_simultaneous_signal_fit=False."
            )
        
        self.build_simultaneous_signal_models(fit_models=fit_models)
    
    def _create_model_variables(self, label: str, category: CategoryConfig, 
                                mass: float, width: float, use_reco_mass: bool, tag: str):
        """Create variables for signal model (unified for both parametric and test models)
        
        Args:
            label: Label for the sample/mass point (e.g., sample.label or "M3p1")
            category: Category configuration
            mass: Mass value to use for parametric variables and BW mean
            width: Width value to use for BW width
            use_reco_mass: Whether to use reconstructed mass
            tag: Tag to append to variable names (e.g., "_param" or "_test_M3p1")
            create_variations: Whether to create systematic variation versions
        """
        all_vars = self.param_manager.dcb_vars if use_reco_mass else (
            self.param_manager.bw_vars + self.param_manager.dcb_vars
        )
        const_vars = set(self.param_manager.dcb_vars) - set(self.parametrized_vars)
                
        # Create variables for nominal and all variations
        for var in all_vars:
            # All parameters have era suffix (nuisance parameters are shared separately)
            var_name = f"{var}{tag}_{label}{category.label}_{self.era}"
            variations = self.param_manager.nuisanced_vars.get(var, [])
            use_stat_nuisance = var in self.nuisanced_vars_stat
                
            if var in self.parametrized_vars:
                # Base dependence is on mass for all DCB parameters in this model block.
                formula = "@0 + @1 * @2"
                dependencies = [
                    f"{var}{category.label}_fit_par0_{self.era}",
                    f"{var}{category.label}_fit_par1_{self.era}",
                    str(mass),
                ]

                # Add systematic-shift nuisance terms built from average up/down differences.
                for variation in variations:
                    # Keep historical mean/electronScaleVariation naming for backward compatibility.
                    if var == "mean" and "electronScaleVariation" in variation:
                        nuisance = f"{var}{category.label}_nuisance_{variation}"
                    else:
                        nuisance = f"{var}{category.label}_nuisance_{variation}_{self.era}"
                    self.param_manager.create_variable(nuisance, [0, -5, 5])

                    par0_diff = f"{var}{category.label}_fit_par0_{variation}_avgdiff_{self.era}"
                    par1_diff = f"{var}{category.label}_fit_par1_{variation}_avgdiff_{self.era}"

                    dependencies.extend([par0_diff, par1_diff, nuisance])
                    idx = len(dependencies)
                    # last three dependencies are [par0_diff, par1_diff, nuisance]
                    formula += f" + @{idx-1} * (@{idx-3} + @{idx-2} * @2)"

                # Add one statistical-band nuisance term using nominal linear-fit uncertainties.
                if use_stat_nuisance:
                    nuisance_stat = f"{var}{category.label}_nuisance_stat_{self.era}"
                    self.param_manager.create_variable(nuisance_stat, [0, -5, 5])

                    par0_err = f"{var}{category.label}_fit_par0_err_{self.era}"
                    par1_err = f"{var}{category.label}_fit_par1_err_{self.era}"
                    par01_cov = f"{var}{category.label}_fit_par01_cov_{self.era}"

                    dependencies.extend([par0_err, par1_err, par01_cov, nuisance_stat])
                    idx = len(dependencies)
                    # last four dependencies are [par0_err, par1_err, par01_cov, nuisance_stat]
                    formula += f" + @{idx-1} * sqrt((@{idx-4})**2 + (@{idx-3} * @2)**2 + 2 * @2 * @{idx-2})"

                if var in ["sigma", "sigma1", "sigma2"] and not use_reco_mass:
                    formula = f"({formula}) * @2"

                self.param_manager.create_parametric_variable(var_name, formula, dependencies)
                
            elif var in const_vars:
                # Create and set constant variable
                self.param_manager.create_variable(var_name, [0, -100, 100])
                const_val = self.workspace_manager.workspace.obj(f"{var}{category.label}_const_{self.era}").getVal()
                const_err = self.workspace_manager.workspace.obj(f"{var}{category.label}_const_{self.era}").getError()
                self.param_manager.set_constant_parameter(var_name, const_val, const_err)
            
            elif var in self.param_manager.bw_vars:
                # Create and set BW parameters
                self.param_manager.create_variable(var_name, [0, -100, 100])
                if var == "mean_BW":
                    self.param_manager.set_constant_parameter(var_name, mass)
                elif var == "width_BW":
                    self.param_manager.set_constant_parameter(var_name, width)
    
    def test_model_for_masses(self, mass_points: List[float], use_reco_mass: bool = False):
        """Test signal model for different mass points"""
        self.logger.log_analysis_step("Testing Model for Various Mass Points")
        
        # Create common mass variable
        mass_var = ROOT.RooRealVar("mass", "mass", 0, 11)
        self.workspace_manager.workspace.Import(mass_var, ROOT.RooCmdArg())
        
        for mass in mass_points:
            self.logger.log_info(f"Testing mass: {mass:.1f} GeV")
            name = f"M{mass:.1f}".replace(".", "p")
            
            for category_label, category in self.categories.items():
                # Create variables for this mass point
                self._create_model_variables(name, category, mass, 1e-10, use_reco_mass, "_test")

                # Build model
                model = self.model_builder.build_signal_model(
                    self._create_test_sample_config(mass), category, 
                    self.parametrized_vars, "test", use_reco_mass, use_shared_mass=True,
                    build_variations=self.use_syst
                )
        
        self.workspace_manager.save()
        self.logger.log_info("Mass testing completed!")
    
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
        self.logger.log_analysis_step("Full Analysis Pipeline")

        # Step 1: Build and fit the simultaneous signal model
        self.build_simultaneous_signal_models(fit_models=True)

        # Step 2: Test with different masses (optional)
        if test_mass_points:
            self.test_model_for_masses(test_mass_points, use_reco_mass)
        
        # Finalize log
        self.logger.finalize_log()
        self.logger.log_info("Full analysis completed successfully!")
