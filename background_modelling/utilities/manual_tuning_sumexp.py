"""
Manual tuning script for sum of exponentials background function

This script allows manual parameter tuning for the sum of exponentials (bkg_f2)
background function using ROOT's RooFit framework.

Sum of exponentials formula:
    f(x) = cc0*exp(c0*x) + cc1*exp(c1*x) + cc2*exp(c2*x) + (1-cc0-cc1-cc2)*exp(c3*x)

Parameters:
    - c0, c1, c2, c3: exponential slopes (4 parameters)
    - cc0, cc1, cc2: coefficients for first 3 exponentials (3 parameters)
    - 4th exponential coefficient is constrained: (1 - cc0 - cc1 - cc2)

Usage:
    Edit the hardcoded parameters at the top of main() function, then run:
    python manual_tuning_sumexp.py
"""

import ROOT
import numpy as np

# Turn on batch mode
ROOT.gROOT.SetBatch(True)

def create_sum_exp_function(workspace, mass_var,
                             c_inits=None, cc_inits=None,
                             c_limits=None, cc_limits=None):
    """
    Create sum of exponentials function with given initial parameters
    
    Args:
        workspace: ROOT.RooWorkspace to store parameters
        mass_var: RooRealVar for the mass variable
        c_inits: Initial values for c0-c3 (exponential slopes)
        cc_inits: Initial values for cc0-cc2 (coefficients)
        c_limits: Limits for c0-c3 parameters [(min, max), ...]
        cc_limits: Limits for cc0-cc2 parameters [(min, max), ...]
    """
    # Default values from background_config.py (inclusive, region1)
    if c_inits is None:
        c_inits = [4.3, 0.2, -0.1, 0]
    if cc_inits is None:
        cc_inits = [-3, 3, -0.3]
    if c_limits is None:
        c_limits = [(-10, 10) for _ in range(4)]
    if cc_limits is None:
        cc_limits = [(-10, 10) for _ in range(3)]
    
    print(f"Creating sum of exponentials with parameters:")
    print(f"  c_inits: {c_inits}")
    print(f"  cc_inits: {cc_inits}")
    print(f"  c_limits: {c_limits}")
    print(f"  cc_limits: {cc_limits}")
    
    # Create parameters
    params = ROOT.RooArgList()
    
    # Create exponential slope parameters (c0-c3)
    for i in range(4):
        param_name = f"test_c{i}"
        param = ROOT.RooRealVar(param_name, param_name, 
                                c_inits[i], c_limits[i][0], c_limits[i][1])
        workspace.Import(param, ROOT.RooCmdArg())
        params.add(workspace.obj(param_name))
    
    # Create exponential functions
    exp_funcs = []
    for i in range(4):
        param_name = f"test_c{i}"
        param = workspace.obj(param_name)
        exp_func = ROOT.RooExponential(f"test_bkg_f2_exp{i}",
                                       f"test_bkg_f2_exp{i}", 
                                       mass_var, param)
        exp_funcs.append(exp_func)
        workspace.Import(exp_func, ROOT.RooCmdArg())
    
    # Create coefficient parameters (cc0-cc2)
    coeff_list = ROOT.RooArgList()
    for i in range(3):
        param_name = f"test_cc{i}"
        param = ROOT.RooRealVar(param_name, param_name,
                                cc_inits[i], cc_limits[i][0], cc_limits[i][1])
        workspace.Import(param, ROOT.RooCmdArg())
        coeff_list.add(workspace.obj(param_name))
    
    # Create sum with coefficients
    # Note: RooAddPdf automatically constrains the 4th coefficient to be (1 - sum of others)
    exp_funcs_list = ROOT.RooArgList()
    for exp_func in exp_funcs:
        exp_funcs_list.add(workspace.obj(exp_func.GetName()))
    
    print("EXP FUNCTIONS")
    for func in exp_funcs_list:
        print(func)
        for param in func.getParameters(mass_var):
            print(f"  {param.GetName()} = {param.getVal():.6f} +/- {param.getError():.6f}")
    print("COEFFICIENTS")
    for coeff in coeff_list:
        print(coeff)

    sum_exp = ROOT.RooAddPdf(f"test_bkg_f2", 
                             f"test_sum_exp", 
                             exp_funcs_list, coeff_list)
    
    workspace.Import(sum_exp, ROOT.RooCmdArg())
    return workspace.obj(f"test_bkg_f2")

def main():
    # ==================== HARDCODED PARAMETERS - EDIT HERE ====================
    region = "region1"
    dataset_path = "../datasets/dataset_data_{region}_data_full.root"
    do_fit = False  # Set to True to fit, False to just plot with initial values
    output_file = "bkg_sumexp_tuning.png"
    use_logy = True  # Log scale on y-axis
    
    # Initial parameter values - EDIT THESE TO TUNE
    c_inits = [0.6, 0.2, -0.1, 0]  # Exponential slopes (c0, c1, c2, c3)
    cc_inits = [-0.3, 3, -0.3]  # Coefficients (cc0, cc1, cc2)

    # ==========================================================================
    
    # Expand dataset path with region
    dataset_path = dataset_path.format(region=region)
    
    print(f"Loading dataset from: {dataset_path}")
    
    # Open file and get workspace
    f = ROOT.TFile.Open(dataset_path)
    if not f or f.IsZombie():
        print(f"Error: Cannot open file {dataset_path}")
        return 1
    
    w = f.Get("w")
    if not w:
        print("Error: Workspace 'w' not found in file")
        return 1
            
    # Retrieve data and mass variable
    data = w.obj(f"data_obs")
    mass = w.obj("mass")
    
    if not data or not mass:
        print(f"Error: Required objects not found in workspace")
        print(f"  Looking for: data_obs, mass")
        return 1
    
    print(f"Loaded dataset '{data.GetName()}' with {data.numEntries()} entries")
    print(f"Mass variable range: [{mass.getMin():.2f}, {mass.getMax():.2f}] GeV")
    
    # Create sum of exponentials function
    sum_exp = create_sum_exp_function(w, mass, c_inits=c_inits, cc_inits=cc_inits)
    
    # Perform fit if requested
    if do_fit:
        print("\nFitting sum of exponentials to data...")
        fit_result = sum_exp.fitTo(data,
                                ROOT.RooFit.Range(region),
                                ROOT.RooFit.Save(),
                                ROOT.RooFit.NumCPU(8),
                                ROOT.RooFit.SumW2Error(True))
        
        print("\nFit results:")
        print(f"  Status: {fit_result.status()}")
        print(f"  Covariance quality: {fit_result.covQual()}")
    else:
        print("\nSkipping fit - plotting with initial parameter values")
            
    # Create plot
    canvas = ROOT.TCanvas("canvas", "canvas", 800, 600)
    frame = mass.frame(ROOT.RooFit.Range(region))
    
    # Plot data
    data.plotOn(frame, ROOT.RooFit.Name("data"), ROOT.RooFit.MarkerSize(0.8))
    
    # Plot fitted function
    sum_exp.plotOn(frame, ROOT.RooFit.LineColor(ROOT.kBlue), 
                   ROOT.RooFit.LineWidth(2), ROOT.RooFit.Name("sum_exp"))
    
    # Draw frame
    frame.SetTitle(f"Sum of Exponentials - {region}")
    frame.Draw()
    
    # Add legend
    legend = ROOT.TLegend(0.65, 0.55, 0.89, 0.89)
    legend.SetBorderSize(0)
    legend.SetFillStyle(0)
    legend.AddEntry("data", "Data", "lep")
    legend.AddEntry("sum_exp", "Sum of exp.", "l")
    legend.Draw()
    
    # Set log scale if requested
    if use_logy:
        canvas.SetLogy()
    
    canvas.SaveAs(output_file)
    print(f"\nPlot saved to: {output_file}")

    # Print parameter values
    params = sum_exp.getParameters(data)
    print("\nFinal parameters:")
    for param in params:
        if not param.isConstant():
            print(f"  {param.GetName()} = {param.getVal():.6f} +/- {param.getError():.6f}")
    
    # # Print ready-to-copy line for config
    # print("\n# Copy to background_config.py:")
    # print(f'"region1" : [{", ".join([f"{w.obj(f"c{i}").getVal():.6f}" for i in range(4)])}] + [{", ".join([f"{w.obj(f"cc{i}").getVal():.6f}" for i in range(3)])}],')
    
    return 0

if __name__ == "__main__":
    exit(main())
