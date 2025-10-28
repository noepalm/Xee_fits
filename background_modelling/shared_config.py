"""
Shared configuration system for signal and background modeling

This module provides a centralized way to define categories and analysis configurations
that can be used by both signal and background modeling frameworks.
"""
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass, field
import os


@dataclass
class CategoryConfig:
    """Configuration for a single category"""
    name: str
    cuts: Dict[str, List[List[float]]]
    display_name: str = ""  # The key used in the categories dictionary

    def __post_init__(self):
        self.label = f"_cat_{self.name}" if self.name != "" else ""
        # If display_name not provided, use name as default
        if not self.display_name:
            self.display_name = self.name
    
    def is_object_in_category(self, obj_name: str) -> bool:
        """Check if an object name matches this category's label"""
        if self.label == "":
            return "cat" not in obj_name
        else:
            return obj_name.endswith(self.label)

@dataclass 
class SampleConfig:
    """Configuration for a single sample"""
    name: str
    filename: str
    nominal_mass: float
    nominal_width: float = 0.02
    file: str = ""
    file_GEN: str = ""
    
    # Mass ranges - format: [nominal, min, max]
    mass_range: List[float] = field(default_factory=lambda: [0, 0, 10])
    mass_GEN_range: List[float] = field(default_factory=lambda: [0, 0, 10]) 
    mean_BW_range: List[float] = field(default_factory=lambda: [0, 0, 10])
    
    # Parameter ranges - will be set by _apply_common_ranges
    def __post_init__(self):
        """Set default ranges based on nominal mass if not provided"""
        if self.mass_range == [0, 0, 10]:
            self.mass_range = [self.nominal_mass, self.nominal_mass * 0.5, self.nominal_mass * 1.5]
        if self.mass_GEN_range == [0, 0, 10]:
            self.mass_GEN_range = [self.nominal_mass, self.nominal_mass * 0.9, self.nominal_mass * 1.1]
        if self.mean_BW_range == [0, 0, 10]:
            self.mean_BW_range = [self.nominal_mass, self.nominal_mass * 0.8, self.nominal_mass * 1.2]


class SharedAnalysisConfig:
    """Shared configuration class for both signal and background modeling"""
    
    def __init__(self):
        # Common paths
        self.base_data_path = "/eos/home-n/npalmeri/www/DiElectron"
        self.signal_base_path = f"{self.base_data_path}/signal_model/fw_output/signal_model_reweighted/zsnap/era2023/"
        self.background_base_path = f"{self.base_data_path}/background_model/data/"
        
        # Create category configurations
        self.categories = self._create_category_configs()
        
        # Create sample configurations for both signal and background
        self.signal_samples = self._create_signal_sample_configs()
        
    def _create_category_configs(self) -> Dict[str, CategoryConfig]:
        """Create shared category configurations"""
        categories = {
            "inclusive": CategoryConfig(
                name="",
                cuts={},
                display_name="inclusive"
            ),
            "dRlow": CategoryConfig(
                name="dRm0p3", 
                cuts={
                    "DiElectron_lep_deltaR": [[-1000, 0.3]]
                },
                display_name="dRlow"
            ),
            "dRhigh": CategoryConfig(
                name="dRp0p3",
                cuts={
                    "DiElectron_lep_deltaR": [[0.3, 1000]]
                },
                display_name="dRhigh"
            ),
            "etaLow": CategoryConfig(
                name="etam0p6",
                cuts={
                    "DiElectron_eta": [[-0.6, 0.6]]
                },
                display_name="etaLow"
            ),
            "etaHigh": CategoryConfig(
                name="etap0p6", 
                cuts={
                    "DiElectron_eta": [[-1000, -0.6], [0.6, 1000]]
                },
                display_name="etaHigh"
            ),
        }
        
        return categories
    
    def _create_signal_sample_configs(self) -> Dict[str, SampleConfig]:
        """Create signal sample configurations"""
        samples_data = {
            "Zd_M1": {
                "filename": "HAHM_13p6TeV_M1.root",
                "nominal_mass": 1,
                "mass_range": [1, 0.4, 1.4],
                "mass_GEN_range": [1, 0.8, 1.2],
                "mean_BW_range": [1, 0.7, 1.2],
            },
            "Zd_M3p1": {
                "filename": "HAHM_13p6TeV_M3p1.root", 
                "nominal_mass": 3.1,
                "mass_range": [3.1, 2, 3.6],
                "mass_GEN_range": [3.1, 2.9, 3.3],
                "mean_BW_range": [3.1, 2.9, 3.2],
            },
            "Zd_M5": {
                "filename": "HAHM_13p6TeV_M5.root",
                "nominal_mass": 5,
                "mass_range": [5, 3.5, 6],
                "mass_GEN_range": [5, 4.75, 5.25],
                "mean_BW_range": [5, 4, 6],
            },
            "Zd_M5p5": {
                "filename": "HAHM_13p6TeV_M5p5.root",
                "nominal_mass": 5.5,
                "mass_range": [5.5, 4, 6.5], 
                "mass_GEN_range": [5.5, 5.25, 5.75],
                "mean_BW_range": [5.5, 4.5, 6.5],
            },
            "Zd_M6": {
                "filename": "HAHM_13p6TeV_M6.root",
                "nominal_mass": 6,
                "mass_range": [6, 4.5, 7],
                "mass_GEN_range": [6, 5.75, 6.25],
                "mean_BW_range": [6, 5, 7],
            },
            "Zd_M6p5": {
                "filename": "HAHM_13p6TeV_M6p5.root",
                "nominal_mass": 6.5,
                "mass_range": [6.5, 5, 7.5],
                "mass_GEN_range": [6.5, 6.25, 6.75],
                "mean_BW_range": [6.5, 5.5, 7.5],
            },
            "UpsilonToEE": {
                "filename": "UpsilonToEE.root",
                "nominal_mass": 9.460,
                "mass_range": [9, 6, 12],
                "mass_GEN_range": [9, 9.2, 9.7],
                "mean_BW_range": [9.460, 9, 10],
            },
            "JPsiToEE": {
                "filename": "JPsiToEE.root",
                "nominal_mass": 3.097,
                "mass_range": [3.1, 2, 3.6],
                "mass_GEN_range": [3.1, 2.9, 3.3],
                "mean_BW_range": [3.1, 2.9, 3.2],
            },
        }
        
        samples = {}
        for name, data in samples_data.items():
            samples[name] = SampleConfig(name, **data)
            # Set file paths
            samples[name].file = os.path.join(
                self.signal_base_path, "base_9_GenMatching", data["filename"]
            )
            samples[name].file_GEN = os.path.join(
                self.signal_base_path, "base_8_GenSelection", data["filename"]
            )
        
        return samples
    
    def get_category_by_name(self, name: str) -> Optional[CategoryConfig]:
        """Get category by internal name"""
        for cat in self.categories.values():
            if cat.name == name:
                return cat
        return None
    
    def get_category_from_workspace_name(self, workspace_name: str) -> Optional[CategoryConfig]:
        """Extract category from workspace name"""
        for cat in self.categories.values():
            if cat.matches_workspace_name(workspace_name):
                return cat
        return None
    
    def get_available_categories(self) -> List[str]:
        """Get list of available category names"""
        return list(self.categories.keys())
    
    def get_category_display_names(self) -> Dict[str, str]:
        """Get mapping of internal names to display names"""
        return {key: cat.name.replace('_', ' ').title() if cat.name else 'Inclusive' for key, cat in self.categories.items()}


# Global shared configuration instance
SHARED_CONFIG = SharedAnalysisConfig()


def get_shared_config() -> SharedAnalysisConfig:
    """Get the global shared configuration instance"""
    return SHARED_CONFIG


def update_shared_config(**kwargs):
    """Update the global shared configuration"""
    global SHARED_CONFIG
    for key, value in kwargs.items():
        if hasattr(SHARED_CONFIG, key):
            setattr(SHARED_CONFIG, key, value)


def parse_category_args(category_args: List[str]) -> Dict[str, CategoryConfig]:
    """Parse command line category arguments into CategoryConfig objects
    
    Args:
        category_args: List of strings in format 'name=cuts' where cuts is a ROOT cut string
        
    Returns:
        Dictionary mapping category names to CategoryConfig objects
    """
    categories = {}
    
    for arg in category_args:
        if '=' in arg:
            name, cut_string = arg.split('=', 1)
            name = name.strip()
            cut_string = cut_string.strip().strip('"\'')
            
            # For command line args, we create a simple CategoryConfig with the cut string
            # This is a simplified version - for full parsing of cuts into ranges,
            # additional logic would be needed
            categories[name] = CategoryConfig(
                name=name,
                cuts={'cut_string': cut_string},  # Store as simple string for now
                display_name=name
            )
        else:
            # If no cuts specified, use default (inclusive)
            name = arg.strip()
            categories[name] = CategoryConfig(
                name=name,
                cuts={},
                display_name=name
            )
    
    return categories


def get_default_categories() -> Dict[str, CategoryConfig]:
    """Get the default category configuration"""
    return SHARED_CONFIG.categories


def check_category_conditions(event_vars: Dict[str, float], category_config: CategoryConfig) -> bool:
    """Check if an event satisfies the conditions for a given category
    
    Args:
        event_vars: Dictionary mapping variable names to values
        category_config: CategoryConfig object defining the cuts
        
    Returns:
        True if event passes all cuts for this category
    """
    for var_name, ranges in category_config.cuts.items():
        if var_name == 'cut_string':
            # For command line defined categories with cut strings, we can't evaluate here
            # This would need ROOT evaluation - for now, return True
            continue
            
        if var_name not in event_vars:
            # If variable not available, skip this cut
            continue
            
        value = event_vars[var_name]
        
        # Check if value falls within any of the defined ranges
        passes_any_range = False
        for min_val, max_val in ranges:
            if min_val <= value <= max_val:
                passes_any_range = True
                break
                
        if not passes_any_range:
            return False
            
    return True
