"""
Manual tuning script for Chebyshev polynomial background function

This script allows manual parameter tuning for the Chebyshev polynomial (4th degree)
background function using ROOT's RooFit framework.

Chebyshev polynomial formula:
    f(x) = sum of Chebyshev polynomials with coefficients a0, a1, a2, a3, a4

Parameters:
    - a0, a1, a2, a3, a4: Chebyshev polynomial coefficients (5 parameters)

Usage:
    Edit the hardcoded parameters at the top of main() function, then run:
    python manual_tuning_chebyshev.py
"""

import ROOT
import numpy as np
import datetime

# Turn on batch mode
ROOT.gROOT.SetBatch(True)

def create_chebyshev_function(workspace, mass_var, a_inits=None, a_limits=None):
    """
    Create Chebyshev polynomial function with given initial parameters
    
    Args:
        workspace: ROOT.RooWorkspace to store parameters
        mass_var: RooRealVar for the mass variable
        a_inits: Initial values for a0-a4 (Chebyshev coefficients)
        a_limits: Limits for a0-a4 parameters [(min, max), ...]
    """
    # Default values from background_config.py (inclusive, region1)
    if a_inits is None:
        a_inits = [0, 0, 0, 0, 0, 0]
    if a_limits is None:
        a_limits = [(-5, 5) for _ in range(6)]
    
    print(f"Creating Chebyshev polynomial (4th degree) with parameters:")
    print(f"  a_inits: {a_inits}")
    print(f"  a_limits: {a_limits}")
    
    # Create parameters
    params = ROOT.RooArgList()
    
    # Create Chebyshev coefficient parameters (a0-a4)
    for i in range(6):
        param_name = f"test_a{i}"
        param = ROOT.RooRealVar(param_name, param_name, 
                                a_inits[i], a_limits[i][0], a_limits[i][1])
        workspace.Import(param, ROOT.RooCmdArg())
        params.add(workspace.obj(param_name))
    
    # Create Chebyshev polynomial
    cheby = ROOT.RooChebychev("cheby_bkg", "cheby_bkg", mass_var, params)
    
    workspace.Import(cheby, ROOT.RooCmdArg())
    return workspace.obj("cheby_bkg")

def main():
    # ==================== HARDCODED PARAMETERS - EDIT HERE ====================
    region = "region1"
    dataset_path = "../datasets/dataset_data_{region}_data_full.root"
    do_fit = True  # Set to True to fit, False to just plot with initial values
    output_file = "bkg_chebyshev_tuning.png"
    use_logy = True  # Log scale on y-axis
    
    # Initial parameter values - EDIT THESE TO TUNE
    # a_inits = [-0.8, -0.1, 0.3, -0.1, -0.1]  # Chebyshev coefficients (a0, a1, a2, a3, a4)
    a_inits = [-0.8, -0.115, 0.25, 0.02, -0.076, 0.1]  # Chebyshev coefficients (a0, a1, a2, a3, a4)

    # a_inits = [-0.5, -0.1, 0.1, -0.1, -0.1]  # Chebyshev coefficients (a0, a1, a2, a3, a4)
    # a_inits = [0.05 for _ in range(5)]  # Chebyshev coefficients (a0, a1, a2, a3, a4)

    # ==========================================================================
    
    # Expand dataset path with region
    dataset_path = dataset_path.format(region=region)
    
    print("START TIME: ", datetime.datetime.now())

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
    
    # Create Chebyshev polynomial function
    cheby = create_chebyshev_function(w, mass, a_inits=a_inits)

    # create total model
    jpsi = w.obj("jpsi")
    psi2s = w.obj("psi2s")
    ndy = w.obj("ndy")
    njpsi = w.obj("njpsi")
    npsi2s = w.obj("npsi2s")
    total_model = ROOT.RooAddPdf("total_model", "total_model", ROOT.RooArgList(cheby, jpsi, psi2s), ROOT.RooArgList(ndy, njpsi, npsi2s))

    # Perform fit if requested
    if do_fit:
        print("\nFitting Chebyshev polynomial to data...")
        fit_result = total_model.fitTo(data,
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
    
    # params = total_model.getParameters(data)
    # print("\nFinal parameters:")
    # for param in params:
    #     if param.GetName() == ("test_a0"):
    #         param.setVal(-0.8)
    #     if param.GetName() == ("test_a1"):
    #         param.setVal(-0.115)
    #     if param.GetName() == ("test_a2"):
    #         param.setVal(0.25)
    #     if param.GetName() == ("test_a3"):
    #         param.setVal(0.02)
    #     if param.GetName() == ("test_a4"):
    #         param.setVal(-0.076)
    #     if param.GetName() == ("ndy"):
    #         param.setVal(817133)
    #     if param.GetName() == ("njpsi"):
    #         param.setVal(1207466)
    #     if param.GetName() == ("npsi2s"):
    #         param.setVal(60628)
    #     if not param.isConstant():
    #         print(f"  {param.GetName()} = {param.getVal():.6f} +/- {param.getError():.6f}")

    # plot total model
    total_model.plotOn(frame, ROOT.RooFit.LineColor(ROOT.kRed), 
                        ROOT.RooFit.LineWidth(2), ROOT.RooFit.Name("total_model"))

    # # Plot fitted function
    # cheby.plotOn(frame, ROOT.RooFit.LineColor(ROOT.kBlue), 
    #             ROOT.RooFit.LineWidth(2), ROOT.RooFit.Name("cheby"))
        
    # Draw frame
    frame.SetTitle(f"Chebyshev Polynomial (4th deg) - {region}")
    frame.Draw()
    
    # Add legend
    legend = ROOT.TLegend(0.65, 0.55, 0.89, 0.89)
    legend.SetBorderSize(0)
    legend.SetFillStyle(0)
    # legend.AddEntry("data", "Data", "lep")
    # legend.AddEntry("cheby", "Chebyshev", "l")
    # legend.Draw()
    
    # Set log scale if requested
    if use_logy:
        canvas.SetLogy()
    
    canvas.SaveAs(output_file)
    print(f"\nPlot saved to: {output_file}")

    # Print parameter values
    params = total_model.getParameters(data)
    print("\nFinal parameters:")
    for param in params:
        if not param.isConstant():
            print(f"  {param.GetName()} = {param.getVal():.6f} +/- {param.getError():.6f}")
    
    print("FINISH TIME: ", datetime.datetime.now())

    # # Print ready-to-copy line for config
    # print("\n# Copy to background_config.py:")
    # print(f'"region1" : [{", ".join([f"{w.obj(f"a{i}").getVal():.6f}" for i in range(5)])}],')
    
    return 0

if __name__ == "__main__":
    exit(main())
