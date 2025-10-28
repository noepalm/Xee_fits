"""
Updated signal modeling configuration to use shared configuration system

This module shows how to integrate the signal modeling with the shared configuration.
"""
from typing import Dict, List, Optional
from pathlib import Path

from shared_config import SharedAnalysisConfig, CategoryConfig, SampleConfig, get_shared_config


class SignalAnalysisConfig:
    """Signal analysis configuration that uses shared categories"""
    
    def __init__(self):
        # Get shared configuration
        self.shared_config = get_shared_config()
        
        # Signal-specific settings
        self.wsfile = "signal_model.root"
        self.eos_folder = "/eos/home-n/npalmeri/www/DiElectron/signal_model/use_reco_mass"
        
        # Analysis parameters
        self.vars = ["mean", "sigma", "alphaL", "alphaR", "nL", "nR"]
        self.parametrized_vars = ["mean", "sigma", "alphaL", "alphaR", "nL", "nR"]
        
        # Use shared samples and categories
        self.samples = self.shared_config.signal_samples
        self.categories = self.shared_config.categories
        
        # Signal-specific parameter ranges
        self._apply_common_ranges()
        
    def _apply_common_ranges(self):
        """Apply common parameter ranges to all samples"""
        common_ranges = {
            "mean": [0, -2, 15],
            "sigma": [0.05, 0, 1],
            "alphaL": [1.5, 0.5, 5],
            "alphaR": [1.5, 0.5, 5], 
            "nL": [2, 0.1, 50],
            "nR": [2, 0.1, 50],
            "mean_BW": [0, 0, 15],
            "sigma_BW": [0.02, 0.001, 1],
            "n_signal": [1000, 0, 1e6]
        }
        
        for sample in self.samples.values():
            for param, range_vals in common_ranges.items():
                setattr(sample, f"{param}_range", range_vals.copy())
                
    def update_for_reco_mass(self):
        """Update configuration for reco mass analysis"""
        # Adjust mass ranges for reco mass
        for sample in self.samples.values():
            # Expand ranges slightly for reco mass
            reco_factor = 1.2
            sample.mass_range[1] *= reco_factor  # min
            sample.mass_range[2] *= reco_factor  # max
            
    def apply_tag(self, tag: str):
        """Apply tag to output files"""
        if tag:
            self.wsfile = f"signal_model_{tag}.root"
            
    def get_categories(self) -> Dict[str, CategoryConfig]:
        """Get available analysis categories"""
        return self.categories
        
    def get_category(self, name: str) -> Optional[CategoryConfig]:
        """Get specific category configuration"""
        return self.shared_config.get_category_by_name(name)
        
    def get_samples(self) -> Dict[str, SampleConfig]:
        """Get available signal samples"""
        return self.samples
        
    def get_sample(self, name: str) -> Optional[SampleConfig]:
        """Get specific sample configuration"""
        return self.samples.get(name)
