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
        params = model.getParameters(ROOT.RooArgSet())
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
                    if abs(param.getVal() - min_val)/(min_val + 1e-6) < 1e-2 or abs(param.getVal() - max_val)/(max_val + 1e-6) < 1e-2:
                        const_str += " (WARNING: bounded)"
                
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
            print(f"DEBUG: shape variations set to {self.shape_variations}")
            print(f"DEBUG: weight variations set to {self.weight_variations}")
            print(f"DEBUG: merged variations set to {self.variations}")
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
        if existing_data:
            return existing_data
        
        ### Creating datasets
        f = ROOT.TFile.Open(sample.file)
        print(f"DEBUG: opened file {sample.file} for sample {sample.label}")
        t = f.Get("Events")
        
        weight_var = ROOT.RooRealVar(f"weightVar_{sample.label}{category.label}_{self.era}", 
                                   f"weightVar_{sample.label}{category.label}_{self.era}", 1.0)
        self.workspace.Import(weight_var, ROOT.RooCmdArg())
        
        obs_var = self.workspace.var(observable_name)
        data = ROOT.RooDataSet(data_name, data_name, 
                             ROOT.RooArgSet(obs_var),
                             ROOT.RooFit.WeightVar(weight_var.GetName()))

        # Create systematic variation dataset (if requested)
        data_vars = {}
        if self.use_syst:
            for variation in self.variations:
                for direction in self.directions:
                    syst_data_name = f"{prefix}_{sample.label}{category.label}_{variation}_{direction}_{self.era}"
                    dataset = ROOT.RooDataSet(syst_data_name, syst_data_name,
                                         ROOT.RooArgSet(obs_var), 
                                         ROOT.RooFit.WeightVar(weight_var.GetName()))
                    print(f"DEBUG: saving systematic dataset {syst_data_name} to {variation}_{direction}")
                    data_vars[f"{variation}_{direction}"] = dataset
        
        # Determine branch to read and range to use
        # Use corrected mass only when shape variations are enabled.
        mass_var = "DiElectron_fitted_mass_corrected" if (self.use_syst and self.shape_variations) else "SelectedDiEle_fitted_mass"

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
                data.add(ROOT.RooArgSet(obs_var), weight)
                
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
                            data_vars[f"{variation}_{direction}"].add(ROOT.RooArgSet(obs_var), syst_weight)
        
        f.Close()
        self.workspace.Import(data)
        if self.use_syst:
            for dataset in data_vars.values():
                self.workspace.Import(dataset)
        
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
                # if "mean" in var and "electronScaleVariation" in variation_tag:
                #     var_range[0] = var_range[0] * 0.99 if "down" in variation_tag else var_range[0] * 1.01
                #     # var_range = [new_init, var_range[1], var_range[2]]
                # if ("nL" in var or "nR" in var) and "electronScaleVariation" in variation_tag:
                #     var_range[0] = 5
                # print("building var", var_name, "with range", var_range)
                self.workspace.factory(f"{var_name}[{','.join(map(str, var_range))}]")
                # # DEBUG: retrieve variable from workspace and check min/max
                # created_var = self.workspace.var(var_name)
                # print(f"DEBUG:    var {var_name} has range {created_var.getMin()}, {created_var.getMax()} (range string = [{','.join(map(str, var_range))}])")
    
    def create_variable(self, var_name: str, var_range: List[float]):
        """Create a single RooRealVar with specified range
        
        Args:
            var_name: Name of the variable
            var_range: Range as [initial, min, max]
        """
        self.workspace.factory(f"{var_name}[{','.join(map(str, var_range))}]")
    
    def create_parametric_variable(self, var_name: str, formula: str, 
                                 dependencies: List[str]) -> ROOT.RooFormulaVar:
        """Create parametric variable using formula"""
        dep_objects = []
        for dep in dependencies:
            # Check if dependency is a numeric constant
            if dep.replace(".", "").replace("-", "").isdigit():
                # Convert numeric string to RooConstVar
                const_val = float(dep)
                const_var = ROOT.RooFit.RooConst(const_val)
                dep_objects.append(const_var)
            else:
                # Get from workspace
                dep_obj = self.workspace.obj(dep)
                if dep_obj is None:
                    raise ValueError(f"Dependency '{dep}' for parametric variable '{var_name}' not found in workspace.")
                dep_objects.append(dep_obj)
        
        param_var = ROOT.RooFormulaVar(var_name, var_name, formula, 
                                     ROOT.RooArgList(*dep_objects))
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

        if self.param_manager.double_gaussian:
            mean1 = f"response_mean1_{sample.label}{category.label}{variation_tag}_{self.era}"
            sigma1 = f"response_sigma1_{sample.label}{category.label}{variation_tag}_{self.era}"
            mean2 = f"response_mean2_{sample.label}{category.label}{variation_tag}_{self.era}"
            sigma2 = f"response_sigma2_{sample.label}{category.label}{variation_tag}_{self.era}"
            frac = f"response_sig1frac_{sample.label}{category.label}{variation_tag}_{self.era}"

            g1_name = f"response_gauss1_{sample.label}{category.label}{variation_tag}_{self.era}"
            g2_name = f"response_gauss2_{sample.label}{category.label}{variation_tag}_{self.era}"

            self.workspace.factory(f"Gaussian::{g1_name}({observable_name},{mean1},{sigma1})")
            self.workspace.factory(f"Gaussian::{g2_name}({observable_name},{mean2},{sigma2})")
            self.workspace.factory(f"SUM::{model_name}({frac}*{g1_name},{g2_name})")
            return self.workspace.pdf(model_name)
        
        # Build variable list for Crystal Ball (all parameters have era suffix)
        var_names = [observable_name]
        for var in self.param_manager.response_vars:
            var_names.append(f"{var}_{sample.label}{category.label}{variation_tag}_{self.era}")
        var_string = ",".join(var_names)
        
        self.workspace.factory(f"CrystalBall::{model_name}({var_string})")
        return self.workspace.pdf(model_name)

    def _get_signal_model_index(self) -> ROOT.RooCategory:
        """Get or create the era-specific signal-model index used by RooMultiPdf."""
        index_name = f"signal_model_index_{self.era}"
        index = self.workspace.cat(index_name)
        if index:
            return index

        index = ROOT.RooCategory(index_name, index_name)
        index.defineType("dcb")
        index.defineType("gaussian")
        self.workspace.Import(index, ROOT.RooCmdArg())
        stored_index = self.workspace.cat(index_name)
        return stored_index if stored_index else index

    def _build_signal_core_pdf(self, sample: SampleConfig, category: CategoryConfig,
                               tag: str, use_shared_mass: bool, core_type: str) -> str:
        """Build the signal-core PDF used by the full signal model."""
        mass_obs = "mass" if use_shared_mass else f"mass_{sample.label}"

        if core_type == "gaussian":
            mean = f"mean_{tag}_{sample.label}{category.label}_{self.era}"
            sigma = f"sigma_{tag}_{sample.label}{category.label}_{self.era}"
            gauss_name = f"gaussian_{tag}_{sample.label}{category.label}_{self.era}"
            self.workspace.factory(f"Gaussian::{gauss_name}({mass_obs},{mean},{sigma})")
            return gauss_name

        if core_type == "dcb":
            dcb_vars = []
            for dcb_var in self.param_manager.dcb_vars:
                dcb_vars.append(f"{dcb_var}_{tag}_{sample.label}{category.label}_{self.era}")
            dcb_var_string = f"{mass_obs}," + ",".join(dcb_vars)
            dcb_name = f"crystalBall_{tag}_{sample.label}{category.label}_{self.era}"
            self.workspace.factory(f"CrystalBall::{dcb_name}({dcb_var_string})")
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
            self.workspace.factory(f"Gaussian::{g1_name}({mass_obs},{mean1},{sigma1})")
            self.workspace.factory(f"Gaussian::{g2_name}({mass_obs},{mean2},{sigma2})")
            self.workspace.factory(f"SUM::{core_name}({frac}*{g1_name},{g2_name})")
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
        self.workspace.Import(relBW)
        
        # Setup convolution
        mass_var.setBins(10000, "cache")
        mass_var.setMin("cache", -20)
        mass_var.setMax("cache", 20)
        
        # Build convolution
        conv_name = f"model_{tag}_{sample.label}{category.label}{model_suffix}_{self.era}"
        self.workspace.factory(f"FFTConvPdf::{conv_name}(mass_{sample.label}, {dcb_name}, {relBW_name})")
        
        return self.workspace.pdf(conv_name)


class FitManager:
    """Manages fitting operations"""
    
    def __init__(self, workspace: ROOT.RooWorkspace, logger: Optional['FitLogger'] = None, era : str = "2023"):
        self.workspace = workspace
        self.logger = logger
        self.era = era
    
    def compute_chi2(self, model: ROOT.RooAbsPdf, dataset: ROOT.RooDataSet, ndof: None) -> Optional[float]:
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
            params = model.getParameters(ROOT.RooArgSet(obs))
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
        
        # Compute Chi2
        chi2_ndf = self.compute_chi2(model, dataset)
        
        # Log fit result
        if self.logger:
            if fit_type == "response":
                self.logger.log_response_fit_result(sample_name, category_name, model, dataset, result, chi2_ndf)
            elif fit_type == "signal":
                model_type = "param"  # Could be extended to support different types
                self.logger.log_signal_fit_result(sample_name, category_name, model, dataset, result, model_type, chi2_ndf)
        
        return result
    
    def fit_parameters_vs_mass(self, samples: Dict[str, SampleConfig], 
                             category: CategoryConfig, vars_to_fit: List[str], 
                             parametrized_vars: List[str],
                             nuisanced_vars: Dict[str, List[str]] = None,
                             gen: bool = False,                             
                             min_entries: int = 10,
                             entry_counts: Optional[Dict[str, int]] = None,
                             logger: Optional['FitLogger'] = None) -> Dict[str, ROOT.TF1]:
        """Fit parameters as function of mass
        
        Args:
            samples: Dictionary of sample configurations
            category: Category configuration
            vars_to_fit: List of variables to fit
            parametrized_vars: List of variables to parametrize
            nuisanced_vars: Dictionary of nuisanced variables
            gen: Whether to use GEN variables
            min_entries: Minimum number of entries required to include a point
            entry_counts: Dictionary with keys like 'sample_name_category_label' containing entry counts
        """
        # Filter out JPsi samples for parameter fitting
        fit_samples = {name: sample for name, sample in samples.items() 
                      if "JPsi" not in name}
        # # Filter out JPsi and Upsilon samples for parameter fitting
        # fit_samples = {name: sample for name, sample in samples.items() 
        #               if "JPsi" not in name and "Upsilon" not in name}
        # # Include all samples
        # fit_samples = {name: sample for name, sample in samples.items()}
        print(f"DEBUG: fit_samples = {fit_samples.keys()}", flush = True)
                
        # Create graphs for each variable (nominal + variations)
        graphs = {var: ROOT.TGraphErrors() for var in vars_to_fit}
        
        # Create variation graphs if nuisanced variables are specified
        variation_graphs = {}
        if nuisanced_vars:
            for var in vars_to_fit:
                if var in nuisanced_vars:
                    for variation in nuisanced_vars[var]:
                        variation_graphs[f"{var}_{variation}_up"] = ROOT.TGraphErrors()
                        variation_graphs[f"{var}_{variation}_down"] = ROOT.TGraphErrors()
        
        # Fill graphs with data points
        for name, sample in fit_samples.items():
            # Check if we have enough entries for this sample-category combination
            if entry_counts is not None:
                entry_key = f"{name}{category.label}"
                if entry_key in entry_counts and entry_counts[entry_key] < min_entries:
                    print(f"Skipping {name} in category {category.name}: only {entry_counts[entry_key]} entries (< {min_entries})")
                    continue
            
            print(f"DEBUG: vars to fit = {vars_to_fit}", flush = True)
            for var in vars_to_fit:
                input_var = f"{var}_GEN_fit_{name}{category.label}_{self.era}" if gen else f"response_{var}_{name}{category.label}_{self.era}"
                workspace_var = self.workspace.var(input_var)
                if not workspace_var:
                    print(f"WARNING: Variable {input_var} not found in workspace, skipping {name}")
                    break  # Skip this entire sample
                val = workspace_var.getVal()
                err = workspace_var.getError()

                # Fill nominal graph with statistical error only
                print(f"Setting nominal point for {var} at mass {sample.nominal_mass}: value = {val}, error = {err}", flush = True)
                graphs[var].SetPoint(graphs[var].GetN(), sample.nominal_mass, val)
                graphs[var].SetPointError(graphs[var].GetN()-1, 0, err)

                # Fill variation graphs if applicable
                if nuisanced_vars and var in nuisanced_vars:
                    print(f"DEBUG: processing nuisanced variable {var} for sample {name}", flush = True)
                    for variation in nuisanced_vars[var]:
                        # All parameters have era suffix (nuisance parameters are shared separately)
                        var_up = f"{var}_GEN_fit_{name}{category.label}_{variation}_up_{self.era}" if gen else f"response_{var}_{name}{category.label}_{variation}_up_{self.era}"
                        var_down = f"{var}_GEN_fit_{name}{category.label}_{variation}_down_{self.era}" if gen else f"response_{var}_{name}{category.label}_{variation}_down_{self.era}"
                        
                        workspace_var_up = self.workspace.var(var_up)
                        workspace_var_down = self.workspace.var(var_down)
                        
                        if workspace_var_up and workspace_var_down:
                            val_up = workspace_var_up.getVal()
                            err_up = workspace_var_up.getError()
                            val_down = workspace_var_down.getVal()
                            err_down = workspace_var_down.getError()
                            
                            print(f"DEBUG: variation {variation}: val_up = {val_up} +- {err_up}, val_down = {val_down} +- {err_down}", flush = True)
                            
                            # Fill variation graphs
                            graph_up = variation_graphs[f"{var}_{variation}_up"]
                            graph_up.SetPoint(graph_up.GetN(), sample.nominal_mass, val_up)
                            graph_up.SetPointError(graph_up.GetN()-1, 0, err_up)
                            
                            graph_down = variation_graphs[f"{var}_{variation}_down"]
                            graph_down.SetPoint(graph_down.GetN(), sample.nominal_mass, val_down)
                            graph_down.SetPointError(graph_down.GetN()-1, 0, err_down)
                        else:
                            print(f"WARNING: Nuisanced variables {var_up} or {var_down} not found in workspace, skipping variation", flush = True)
        
        # Fit parametrized variables with linear functions
        fits = {}
        tag = "_GEN" if gen else ""
        
        # Fit nominal graphs
        for var in parametrized_vars:
            if var in vars_to_fit:
                print("Fitting nominal graph for var ", var, " category ", category.label)
                for i in range(graphs[var].GetN()):
                    print(f"\tPoint {i}: x = {graphs[var].GetX()[i]}, y = {graphs[var].GetY()[i]} +- {graphs[var].GetEY()[i]}")
                fit_func = ROOT.TF1(f"fit{tag}_{var}{category.label}", "[0] + [1]*x", 0, 12)
                fit_result = graphs[var].Fit(fit_func, "S")
                fit_result.Print()
                fits[var] = fit_func

                # Extract covariance matrix to retrieve parameter error and correlation
                cov_mat = fit_result.GetCovarianceMatrix()

                # Save nominal fit parameters to workspace
                for i in range(2):
                    par_err = np.sqrt(cov_mat(i, i))
                    param_name = f"{var}{category.label}_fit_par{i}_{self.era}"
                    param_obj = ROOT.RooRealVar(param_name, param_name, fit_func.GetParameter(i))
                    param_obj.setError(par_err)
                    param_obj.setConstant()
                    self.workspace.Import(param_obj, True)

                    param_err_name = f"{var}{category.label}_fit_par{i}_err_{self.era}"
                    param_err_obj = ROOT.RooRealVar(param_err_name, param_err_name, par_err)
                    param_err_obj.setConstant()
                    self.workspace.Import(param_err_obj, True)

                # Save covariance between linear fit parameters par0 and par1
                cov_name = f"{var}{category.label}_fit_par01_cov_{self.era}"
                cov_obj = ROOT.RooRealVar(cov_name, cov_name, cov_mat(0, 1))
                cov_obj.setConstant()
                self.workspace.Import(cov_obj, True)
                
                # Save residual between fit and points
                for i in range(graphs[var].GetN()):
                    x = graphs[var].GetX()[i]
                    y = graphs[var].GetY()[i]
                    y_fit = fit_func.Eval(x)
                    residual = y - y_fit
                    print(f"DEBUG: variables {var} residual for point ", i, ": x = ", x, ", y = ", y, ", y_fit = ", y_fit, ", residual = ", residual)
                    resid_name = f"{var}{category.label}_residual_point{i}_{self.era}"
                    resid_obj = ROOT.RooRealVar(resid_name, resid_name, residual)
                    resid_obj.setConstant()
                    self.workspace.Import(resid_obj, True)
                
                # Log parametrization result
                if logger:
                    logger.log_parametrization_result(
                        category.name, var, fit_func, is_constant=False
                    )
        
        # Fit variation graphs
        if nuisanced_vars:
            for var in parametrized_vars:
                if var in vars_to_fit and var in nuisanced_vars:

                    for variation in nuisanced_vars[var]:
                        # Store fit functions for up/down to compute differences
                        fit_funcs = {}
                        
                        for direction in ["up", "down"]:
                            graph_key = f"{var}_{variation}_{direction}"
                            if graph_key in variation_graphs:
                                print(f"Fitting variation graph for var {var}, variation {variation}_{direction}, category {category.label}")
                                variation_graph = variation_graphs[graph_key]
                                
                                for i in range(variation_graph.GetN()):
                                    print(f"\tPoint {i}: x = {variation_graph.GetX()[i]}, y = {variation_graph.GetY()[i]} +- {variation_graph.GetEY()[i]}")
                                
                                # Create and perform fit
                                fit_func_var = ROOT.TF1(f"fit{tag}_{var}{category.label}_{variation}_{direction}", "[0] + [1]*x", 0, 12)
                                fit_result_var = variation_graph.Fit(fit_func_var, "S")
                                fit_result_var.Print()
                                fit_funcs[direction] = fit_func_var

                                cov_mat_var = fit_result_var.GetCovarianceMatrix()
                                # Save variation fit parameters to workspace
                                for i in range(2):
                                    par_err = np.sqrt(cov_mat_var(i, i))
                                    param_name = f"{var}{category.label}_fit_par{i}_{variation}_{direction}_{self.era}"
                                    param_obj = ROOT.RooRealVar(param_name, param_name, fit_func_var.GetParameter(i))
                                    param_obj.setError(par_err)
                                    param_obj.setConstant()
                                    self.workspace.Import(param_obj, True)

                                    param_err_name = f"{var}{category.label}_fit_par{i}_err_{variation}_{direction}_{self.era}"
                                    param_err_obj = ROOT.RooRealVar(param_err_name, param_err_name, par_err)
                                    param_err_obj.setConstant()
                                    self.workspace.Import(param_err_obj, True)

                                # Save covariance between par0/par1 for the variation fit
                                cov_name_var = f"{var}{category.label}_fit_par01_cov_{variation}_{direction}_{self.era}"
                                cov_obj_var = ROOT.RooRealVar(cov_name_var, cov_name_var, cov_mat_var(0, 1))
                                cov_obj_var.setConstant()
                                self.workspace.Import(cov_obj_var, True)
                                
                                # Log variation parametrization result
                                if logger:
                                    logger.log_info(f"Fitted variation {variation}_{direction} for {var} in {category.name}")
                        
                        # Calculate and store average absolute difference between nominal and variations
                        if "up" in fit_funcs and "down" in fit_funcs:
                            nominal_fit = fits.get(var)
                            if nominal_fit:
                                for i in range(2):
                                    nominal_val = nominal_fit.GetParameter(i)
                                    up_val = fit_funcs["up"].GetParameter(i)
                                    down_val = fit_funcs["down"].GetParameter(i)
                                    
                                    # Average of absolute differences
                                    avg_diff = (abs(nominal_val - up_val) + abs(nominal_val - down_val)) / 2.0
                                    
                                    diff_name = f"{var}{category.label}_fit_par{i}_{variation}_avgdiff_{self.era}"
                                    diff_obj = ROOT.RooRealVar(diff_name, diff_name, avg_diff)
                                    diff_obj.setConstant()
                                    self.workspace.Import(diff_obj, True)

                                    print(f"Stored average difference for {var} par{i} {variation}: {avg_diff:.6f} (nominal={nominal_val:.6f}, up={up_val:.6f}, down={down_val:.6f})")
        
        # Handle constant variables
        const_vars = set(vars_to_fit) - set(parametrized_vars)
        for var in const_vars:
            y_values = np.array([graphs[var].GetY()[i] for i in range(graphs[var].GetN())])
            y_errors = np.array([graphs[var].GetEY()[i] for i in range(graphs[var].GetN())])
            
            # Weighted mean
            weights = 1.0 / y_errors**2
            mean = np.average(y_values, weights=weights)
            err = np.sqrt(1.0 / np.sum(weights))
            
            const_name = f"{var}{category.label}{tag}_const_{self.era}"
            const_obj = ROOT.RooRealVar(const_name, const_name, mean)
            const_obj.setError(err)
            const_obj.setConstant()
            self.workspace.Import(const_obj, True)
            
            # Log constant parametrization result
            if logger:
                logger.log_parametrization_result(
                    category.name, var, None, is_constant=True, 
                    const_value=mean, const_error=err
                )
        
        return fits


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
        
        # Analysis state
        self._response_functions_built = False
        self._parameters_fitted = False
    
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
    
    def _build_response_for_sample(self, name: str, sample: SampleConfig, use_reco_mass: bool, 
                                   observables: List[str], variation_tags: List[str]):
        """Helper method to build response functions for a single sample (parallelizable)"""
        self.logger.log_info(f"Processing sample: {name}")
        
        for category_label, category in self.categories.items():
            self.logger.log_info(f"Processing category: {category_label}")
            
            obs_name = f"{observables[0]}_{sample.label}_{self.era}"
            
            # Create observable variable first (needed to load dataset)
            self.param_manager.create_variables(sample, category, observables)
            
            # Load datasets (creates nominal and all variations if use_syst=True)
            self.dataset_loader.load_dataset(sample, category, obs_name, 
                                            dataset_type="response", use_reco_mass=use_reco_mass)
            
            for variation_tag in variation_tags:
                var_label = "nominal" if variation_tag == "" else variation_tag[1:]  # Remove leading underscore
                self.logger.log_info(f"Processing {var_label}")
                
                # Create response variables
                vars_to_create = self.param_manager.response_vars + ["response_nsgn"]
                self.param_manager.create_variables(sample, category, vars_to_create,
                                                  variation_tag=variation_tag)
                
                # Load dataset
                dataset_name = f"response_data_{sample.label}{category.label}{variation_tag}_{self.era}"
                dataset = self.workspace_manager.workspace.data(dataset_name)
                
                if not dataset:
                    self.logger.log_warning(f"Dataset {dataset_name} not found, skipping")
                    continue
                
                self.logger.log_info(f"Loaded dataset with {dataset.numEntries()} entries")
                
                # Build and fit model
                model = self.model_builder.build_response_function(sample, category, obs_name,
                                                                  variation_tag=variation_tag)
                self.fit_manager.fit_model(model, dataset, sample_name=sample.label,
                                         category_name=category.name, fit_type="response")
                
                self.logger.log_info(f"Fitted model: {model.GetName()}")
    
    def build_response_functions(self, use_reco_mass: bool = False, max_workers: int = 4):
        """Build response function workspace and fit parameters
        
        Args:
            use_reco_mass: Whether to use reconstructed mass
            max_workers: Maximum number of parallel workers for sample processing
        """
        self.logger.log_analysis_step("Building Response Functions")
        
        observables = ["mass" if use_reco_mass else "reduced_mass"]
        
        # Build list of variation tags to process
        variation_tags = [""]  # Start with nominal (empty tag)
        if self.use_syst:
            variation_tags.extend([f"_{var}_{dir}" for var in self.dataset_loader.variations 
                                  for dir in self.dataset_loader.directions])
        
        # Process samples in parallel
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self._build_response_for_sample, name, sample, 
                              use_reco_mass, observables, variation_tags): name
                for name, sample in self.samples.items()
            }
            
            for future in as_completed(futures):
                sample_name = futures[future]
                try:
                    future.result()
                    self.logger.log_info(f"Completed processing sample: {sample_name}")
                except Exception as e:
                    self.logger.log_error(f"Error processing sample {sample_name}: {e}")
        
        self.workspace_manager.save()
        self._response_functions_built = True
        self.logger.log_info("Response function workspace built successfully!")
    
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
        
        self.logger.log_analysis_step("Fitting Parameters vs Mass")
        
        if vars_list is None:
            vars_list = self.param_manager.dcb_vars if not gen else self.param_manager.bw_vars
        
        for category_label, category in self.categories.items():
            self.logger.log_info(f"Fitting parameters for category: {category_label}")
            
            # Get entry counts for this category
            dataset_type = "signal" if gen else "response"
            entry_counts = self.dataset_loader.get_entry_counts_for_category(
                self.samples, category, dataset_type
            )
            
            # Log entry counts
            self.logger.log_entry_counts(entry_counts, category.name, dataset_type)
            
            fits = self.fit_manager.fit_parameters_vs_mass(
                self.samples, category, vars_list, self.parametrized_vars, self.nuisanced_vars,
                gen, min_entries, entry_counts, self.logger
            )
        
        self.workspace_manager.save()
        self._parameters_fitted = True
        self.logger.log_info("Parameter fitting completed!")
    
    def _build_signal_model_for_sample(self, name: str, sample: SampleConfig, 
                                       use_reco_mass: bool, fit_models: bool):
        """Helper method to build signal model for a single sample (parallelizable)"""
        self.logger.log_info(f"Building signal model for: {name}")
        
        # Create mass observable
        mass_range = ",".join(map(str, sample.mass_range))
        self.workspace_manager.workspace.factory(f"mass_{sample.label}[{mass_range}]")
        
        for category_label, category in self.categories.items():

            self.logger.log_info(f"Processing category: {category_label}")
            # Create parametric variables (nominal + variations)
            self._create_model_variables(sample.label, category, sample.nominal_mass, 
                                        sample.nominal_width, use_reco_mass, "_param")
            
            print(f"DEBUG: created model variables, parametric", flush=True)

            # Load dataset
            obs_name = f"mass_{sample.label}"
            dataset = self.dataset_loader.load_dataset(sample, category, obs_name, 
                                                      dataset_type="signal", use_reco_mass=False)
            
            # Build model (nominal + variations)
            print(f"DEBUG: building signal models (param)", flush=True)
            model = self.model_builder.build_signal_model(
                sample, category, self.parametrized_vars, "param", use_reco_mass,
                use_shared_mass=False, build_variations=self.use_syst
            )
            
            # Optionally fit model
            if fit_models and not self.model_builder.envelope:
                self.fit_manager.fit_model(model, dataset, sample_name=sample.label,
                                         category_name=category.name, fit_type="signal")
            elif fit_models and self.model_builder.envelope:
                self.logger.log_warning("Skipping fit for envelope signal model; the RooMultiPdf is meant for downstream selection/plotting.")
    
    def build_signal_models(self, use_reco_mass: bool = False, fit_models: bool = False, max_workers: int = 4):
        """Build parametric signal models
        
        Args:
            use_reco_mass: Whether to use reconstructed mass
            fit_models: Whether to fit the models
            max_workers: Maximum number of parallel workers for sample processing
        """
        if not self._parameters_fitted:
            raise RuntimeError("Parameters must be fitted before building signal models")
        
        self.logger.log_analysis_step("Building Signal Models")
        
        # Process samples in parallel
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self._build_signal_model_for_sample, name, sample, 
                              use_reco_mass, fit_models): name
                for name, sample in self.samples.items()
            }
            
            for future in as_completed(futures):
                sample_name = futures[future]
                try:
                    future.result()
                    self.logger.log_info(f"Completed building signal model for: {sample_name}")
                except Exception as e:
                    self.logger.log_error(f"Error building signal model for {sample_name}: {e}")
        
        self.workspace_manager.save()
        self.logger.log_info("Signal models built successfully!")
    
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
                    print(f"DEBUG: Adding nuisance for systematic uncertainty on var {var}, era {self.era}: formula = {formula}, dependencies = {dependencies}", flush=True)

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
                    print(f"DEBUG: Adding nuisance for stat uncertainty on var {var}, era {self.era}: formula = {formula}, dependencies = {dependencies}", flush=True)

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
        self.workspace_manager.workspace.Import(mass_var)
        
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
        
        # Step 1: Build response functions
        self.build_response_functions(use_reco_mass)
        
        # Step 2: Fit parameters
        self.fit_parameters()
        
        # Step 3: Build signal models
        self.build_signal_models(use_reco_mass)
        
        # Step 4: Test with different masses (optional)
        if test_mass_points:
            self.test_model_for_masses(test_mass_points, use_reco_mass)
        
        # Finalize log
        self.logger.finalize_log()
        self.logger.log_info("Full analysis completed successfully!")
