"""
Main script for signal modeling analysis - Object-oriented approach

This script provides the main interface for running the signal modeling analysis
using the new object-oriented framework.
"""

import ROOT
import numpy as np
import argparse
import os
from pathlib import Path
from typing import Dict, List

from signal_model_analyzer import SignalModelAnalyzer, SampleConfig, CategoryConfig
from plotting_oo import SignalModelPlotter


class AnalysisConfig:
    """Configuration class for the analysis"""
    
    def __init__(self):
        # I/O settings
        self.wsfile = "signal_model.root"
        self.base_path = "/eos/home-n/npalmeri/www/DiElectron/signal_model/fw_output/signal_model_reweighted/zsnap/era2023/"
        self.eos_folder = "/eos/home-n/npalmeri/www/DiElectron/signal_model/use_reco_mass"
        
        # Analysis parameters
        self.vars = ["mean", "sigma", "alphaL", "alphaR", "nL", "nR"]
        self.parametrized_vars = ["mean", "sigma", "alphaL", "alphaR", "nL", "nR"]
        
        # Sample configurations
        self.samples = self._create_sample_configs()
        
        # Category configurations  
        self.categories = self._create_category_configs()
        
        # Common parameter ranges
        self._apply_common_ranges()
    
    def _create_sample_configs(self) -> Dict[str, SampleConfig]:
        """Create sample configurations"""
        samples_data = {
            "Zd_M1": {
                "filename": "HAHM_13p6TeV_M1.root",
                "nominal_mass": 1,
                "nominal_width": 0.02,
                "mass_range": [1, 0.4, 1.4],
                "mass_GEN_range": [1, 0.8, 1.2],
                "mean_BW_range": [1, 0.7, 1.2],
            },
            "Zd_M3p1": {
                "filename": "HAHM_13p6TeV_M3p1.root",
                "nominal_mass": 3.1,
                "nominal_width": 0.02,
                "mass_range": [3.1, 2, 3.6],
                "mass_GEN_range": [3.1, 2.9, 3.3],
                "mean_BW_range": [3.1, 2.9, 3.2],
            },
            "Zd_M5": {
                "filename": "HAHM_13p6TeV_M5.root",
                "nominal_mass": 5,
                "nominal_width": 0.02,
                "mass_range": [5, 3.5, 6],
                "mass_GEN_range": [5, 4.75, 5.25],
                "mean_BW_range": [5, 4, 6],
            },
            "Zd_M5p5": {
                "filename": "HAHM_13p6TeV_M5p5.root",
                "nominal_mass": 5.5,
                "nominal_width": 0.02,
                "mass_range": [5.5, 4, 6.5],
                "mass_GEN_range": [5.5, 5.25, 5.75],
                "mean_BW_range": [5.5, 4.5, 6.5],
            },
            "Zd_M6": {
                "filename": "HAHM_13p6TeV_M6.root",
                "nominal_mass": 6,
                "nominal_width": 0.02,
                "mass_range": [6, 4.5, 7],
                "mass_GEN_range": [6, 5.75, 6.25],
                "mean_BW_range": [6, 5, 7],
            },
            "Zd_M6p5": {
                "filename": "HAHM_13p6TeV_M6p5.root",
                "nominal_mass": 6.5,
                "nominal_width": 0.02,
                "mass_range": [6.5, 5, 7.5],
                "mass_GEN_range": [6.5, 6.25, 6.75],
                "mean_BW_range": [6.5, 5.5, 7.5],
            },
            "UpsilonToEE": {
                "filename": "UpsilonToEE.root",
                "nominal_mass": 9.460,
                "nominal_width": 0.02,
                "mass_range": [9, 6, 12],
                "mass_GEN_range": [9, 9.2, 9.7],
                "mean_BW_range": [9.460, 9, 10],
            },
            "JPsiToEE": {
                "filename": "JPsiToEE.root",
                "nominal_mass": 3.097,
                "nominal_width": 0.02,
                "mass_range": [3.1, 2, 3.6],
                "mass_GEN_range": [3.1, 2.9, 3.3],
                "mean_BW_range": [3.1, 2.9, 3.2],
            },
        }
        
        samples = {}
        for name, data in samples_data.items():
            samples[name] = SampleConfig(name, **data)
            # Set file paths
            samples[name].file = os.path.join(self.base_path, "base_9_GenMatching", data["filename"])
            samples[name].file_GEN = os.path.join(self.base_path, "base_8_GenSelection", data["filename"])
        
        return samples
    
    def _create_category_configs(self) -> Dict[str, CategoryConfig]:
        """Create category configurations"""
        categories_data = {
            "inclusive": {
                "name": "",
                "cuts": {}
            },
            "dR<0.3": {
                "name": "dRm0p3",
                "cuts": {
                    "SelectedDiEle_lep_deltaR": [[-1, 0.3]],
                }
            },
            "dR>0.3": {
                "name": "dRp0p3",
                "cuts": {
                    "SelectedDiEle_lep_deltaR": [[0.3, 1000]],
                }
            },
            "|eta|<0.6": {
                "name": "etam0p6",
                "cuts": {
                    "DiElectron_eta": [[-0.6, 0.6]],
                }
            },
            "|eta|>0.6": {
                "name": "etap0p6",
                "cuts": {
                    "DiElectron_eta": [[-1000, -0.6], [0.6, 1000]],
                }
            }
        }
        
        return {name: CategoryConfig(**data) for name, data in categories_data.items()}
    
    def _apply_common_ranges(self):
        """Apply common parameter ranges to all samples"""
        common_ranges = {
            # Response function parameters
            "reduced_mass_range": [0, -0.6, 0.6],
            "response_mean_range": [0, -0.2, 0.2],
            "response_sigma_range": [0.02, 0, 1],
            "response_alphaL_range": [0.4, 0.1, 10],
            "response_alphaR_range": [5, 0.1, 10],
            "response_nL_range": [1, 0, 10],
            "response_nR_range": [1, 0, 10],
            "response_nsgn_range": [100, 0, 1000],

            # "reduced_mass_range" : [0, -0.6, 0.6],
            # "response_mean_range" : [0, -0.2, 0.2],
            # "response_sigma_range" : [0.02, 0, 1],
            # "response_alphaL_range" : [0.7, 0.1, 10],
            # "response_alphaR_range" : [1.4, 0.1, 10],
            # "response_nL_range" : [2.3, 0, 10],
            # "response_nR_range" : [8, 0, 10],
            # "response_nsgn_range" : [100, 0, 1000],

            # Signal model parameters
            "mean_range": [0, -0.6, 0.6],
            "sigma_range": [0.1, 0, 1],
            "alphaL_range": [1, 0.2, 10],
            "alphaR_range": [5, 0.2, 10],
            "nL_range": [1, 0, 10],
            "nR_range": [1, 0, 10],
            "width_BW_range": [0.001, 0, 0.1],
            "nsgn_range": [100, 0, 1000],
        }
        
        for name, sample in self.samples.items():
            for param, param_range in common_ranges.items():
                if not hasattr(sample, param):
                    setattr(sample, param, param_range)
    
    def update_for_reco_mass(self):
        """Update sample configurations for reco mass analysis"""
        for name, sample in self.samples.items():
            # Update mean ranges by adding nominal mass
            for attr_name in dir(sample):
                if "mean_range" in attr_name:
                    current_range = getattr(sample, attr_name)
                    updated_range = [val + sample.nominal_mass for val in current_range]
                    setattr(sample, attr_name, updated_range)
                
                # Update sigma ranges by multiplying by nominal mass
                if "sigma_range" in attr_name:
                    current_range = getattr(sample, attr_name)
                    updated_range = [val * sample.nominal_mass for val in current_range]
                    setattr(sample, attr_name, updated_range)
    
    def apply_tag(self, tag: str):
        """Apply tag to output files"""
        if tag:
            self.wsfile = self.wsfile.replace(".root", f"_{tag}.root")
            self.eos_folder = f"{self.eos_folder}_{tag}"


class AnalysisRunner:
    """Main class for running the analysis"""
    
    def __init__(self, config: AnalysisConfig):
        self.config = config
        self.analyzer = None
        self.plotter = None
    
    def setup_analyzer(self):
        """Setup the signal model analyzer"""
        wsfile = os.path.join("workspaces", self.config.wsfile)
        self.analyzer = SignalModelAnalyzer(
            self.config.samples,
            self.config.categories,
            wsfile,
            self.config.parametrized_vars,
            eos_folder=self.config.eos_folder
        )
        
        # Setup plotter
        self.plotter = SignalModelPlotter(self.analyzer)
    
    def run_response_analysis(self, use_reco_mass: bool = False):
        """Run response function analysis"""
        print("=== Running Response Function Analysis ===")
        self.analyzer.build_response_functions(use_reco_mass)
        self.analyzer.fit_parameters()
    
    def run_gen_analysis(self):
        """Run generator-level analysis"""
        print("=== Running Generator-Level Analysis ===")
        # Note: This would require implementation of GEN analysis in the analyzer
        # For now, we'll skip this part as it requires additional method implementation
        pass
    
    def run_signal_model_analysis(self, use_reco_mass: bool = False):
        """Run signal model analysis"""
        print("=== Running Signal Model Analysis ===")
        self.analyzer.build_signal_models(use_reco_mass)
    
    def run_mass_testing(self, use_reco_mass: bool = False):
        """Run mass point testing"""
        print("=== Running Mass Point Testing ===")
        mass_points = np.concatenate([np.arange(0.5, 10.5, 0.1), [3.1, 3.7]])
        self.analyzer.test_model_for_masses(mass_points.tolist(), use_reco_mass)
    
    def generate_plots(self, args):
        """Generate all plots"""
        print("=== Generating Plots ===")
        
        if not (args.gen or args.test_signal_model):
            self.plotter.plot_all_response_fits(args.use_reco_mass)
            self.plotter.plot_all_parametrizations(self.config.vars, gen=False)
            self.plotter.plot_all_sample_fits(gen=False)
        
        if not args.no_test_signal_model and not args.gen:
            self.plotter.plot_parametric_models()
        
        # if not args.no_gen and not args.test_signal_model:
        #     self.plotter.plot_all_parametrizations(["mean_BW", "width_BW"], gen=True)
        #     self.plotter.plot_all_sample_fits(gen=True)
    
    def run_full_analysis(self, args):
        """Run complete analysis pipeline"""
        print("=== Starting Full Signal Modeling Analysis ===")
        
        # Setup
        self.setup_analyzer()
        
        # Delete existing workspace if requested
        if args.delete_ws:
            self.analyzer.delete_workspace()
        
        # Response function analysis
        if args.response or (args.full and not args.no_response):
            self.run_response_analysis(args.use_reco_mass)
        
        # Generator-level analysis
        if args.gen or (args.full and not args.no_gen):
            self.run_gen_analysis()
        
        # Signal model analysis
        if args.signal_model or (args.full and not args.no_signal_model):
            self.run_signal_model_analysis(args.use_reco_mass)
        
        # Mass testing
        if args.test_signal_model or (args.full and not args.no_test_signal_model):
            self.run_mass_testing(args.use_reco_mass)
        
        # Generate plots
        if args.plots or (args.full and not args.no_plots):
            self.generate_plots(args)
        
        # Copy to EOS
        if args.copy_eos:
            print("=== Copying Plots to EOS ===")
            self.plotter.copy_plots_to_eos(self.config.eos_folder)
        
        # Finalize log and copy to EOS if needed
        self.analyzer.logger.finalize_log()
        
        print("=== Analysis Complete! ===")


def create_argument_parser():
    """Create command line argument parser"""
    parser = argparse.ArgumentParser(description="Signal Model Analysis - Object-oriented version")
    
    # File options
    parser.add_argument("--wsfile", help="Workspace file name", default="signal_model.root")
    parser.add_argument("--delete_ws", help="Delete workspace file", action="store_true", default=False)
    parser.add_argument("--copy_eos", help="Copy all output plots to EOS directory", action="store_true", default=False)
    parser.add_argument("--tag", help="Tag for output files", default="")
    
    # Analysis options
    parser.add_argument("--full", help="Run all steps", action="store_true", default=False)
    parser.add_argument("--parametrized_vars", help="Parametrized variables", nargs="+", 
                       default=["mean", "sigma", "alphaL", "alphaR", "nL", "nR"])
    parser.add_argument("--use_reco_mass", help="Derive signal model from reco mass rather than reduced", 
                       action="store_true", default=False)
    
    # Individual step options
    parser.add_argument("--response", help="Build response function workspace + fit parameters", 
                       action="store_true", default=False)
    parser.add_argument("--signal_model", help="Test signal model workspace", action="store_true", default=False)
    parser.add_argument("--test_signal_model", help="Create signal model for a sequence of mass points", 
                       action="store_true", default=False)
    parser.add_argument("--gen", help="Test GEN distribution", action="store_true", default=False)
    parser.add_argument("--plots", help="Produce all plots", action="store_true", default=False)
    parser.add_argument("--compare_response", help="Compare response function workspace + fit parameters for M = 3.1 GeV (Zd vs Jpsi)", 
                       action="store_true", default=False)
    
    # Skip options
    parser.add_argument("--no_response", help="Skip building response function workspace + fit parameters [works with --full]", 
                       action="store_true", default=False)
    parser.add_argument("--no_signal_model", help="Skip testing signal model workspace [works with --full]", 
                       action="store_true", default=False)
    parser.add_argument("--no_test_signal_model", help="Skip creating signal model for a sequence of mass points", 
                       action="store_true", default=False)
    parser.add_argument("--no_gen", help="Skip testing GEN distribution [works with --full]", 
                       action="store_true", default=False)
    parser.add_argument("--no_plots", help="Skip producing all plots [works with --full]", 
                       action="store_true", default=False)
    parser.add_argument("--no_compare_response", help="Skip comparing response function workspace + fit parameters for M = 3.1 GeV (Zd vs Jpsi)", 
                       action="store_true", default=False)
    
    return parser


def main():
    """Main function"""
    # Parse arguments
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # Create configuration
    config = AnalysisConfig()
    
    # Apply configuration updates
    if args.wsfile != "signal_model.root":
        config.wsfile = args.wsfile
    
    if args.tag:
        config.apply_tag(args.tag)
    
    if args.use_reco_mass:
        config.update_for_reco_mass()
    
    # Validate parametrized variables
    if not set(args.parametrized_vars).issubset(set(config.vars)):
        raise ValueError(f"parametrized_vars must be a subset of vars ({config.vars}), got {args.parametrized_vars}")
    config.parametrized_vars = args.parametrized_vars
    
    # Create and run analysis
    runner = AnalysisRunner(config)
    runner.run_full_analysis(args)


if __name__ == "__main__":
    main()
