import ROOT

def plot_macro():

    f = ROOT.TFile("datasets/260605/2022EE/dataset_data_region2_binned_data_altbkg_chebyshev_allCorrections_2022EE_full.root")
    w = f.Get("w")

    # 1. Workspace and Data Retrieval
    mass_var = w.var("mass")

    # Generate dummy data to mimic your data_obs
    data = w.data("data_obs")

    # 2. Chebyshev PDF Configuration
    t0 = ROOT.RooRealVar("t0_2022EE", "t0", -1.31262, -5.0, 5.0)
    t1 = ROOT.RooRealVar("t1_2022EE", "t1", 0.42791, -5.0, 5.0)
    t2 = ROOT.RooRealVar("t2_2022EE", "t2", 0.00310, -5.0, 5.0)
    t3 = ROOT.RooRealVar("t3_2022EE", "t3", -0.09039, -5.0, 5.0)
    t4 = ROOT.RooRealVar("t4_2022EE", "t4", 0.04920, -5.0, 5.0)

    chebyshev_params = ROOT.RooArgList(t0, t1, t2, t3, t4)
    cheb_func = ROOT.RooChebychev("bkg_cheb_2022EE", "Chebyshev", mass_var, chebyshev_params)

    # 3. Fermi PDF Configuration
    # Indices strictly map to: @0 = mass, @1 = threshold, @2 = steepness
    fermi_p1 = ROOT.RooRealVar("fermi_p1", "threshold", 6.0)
    fermi_p2 = ROOT.RooRealVar("fermi_p2", "steepness", 0.2)
    fermi_params = [fermi_p1, fermi_p2]
    
    fermi_func = ROOT.RooGenericPdf(
        "bkg_fermi_2022EE", 
        "Fermi Function", 
        "1/(1 + exp(@2*(@0 - @1)))", 
        ROOT.RooArgList(mass_var, *fermi_params)
    )

    # 4. Product Combination
    # RooProdPdf calculates PDF1(x) * PDF2(x) and correctly renormalizes the integral over mass
    prod_func = ROOT.RooProdPdf(
        "bkg_cheb_fermi_2022EE", 
        "Chebyshev * Fermi", 
        ROOT.RooArgSet(cheb_func, fermi_func)
    )

    # 5. Visualization
    c = ROOT.TCanvas("c", "Model Visualization", 800, 600)
    frame = mass_var.frame(ROOT.RooFit.Title("Background Model Overlay"))

    # Plot data
    data.plotOn(frame, ROOT.RooFit.Name("Data"), ROOT.RooFit.MarkerSize(0.8))

    # Plot base Chebyshev
    cheb_func.plotOn(frame, ROOT.RooFit.LineColor(ROOT.kRed), ROOT.RooFit.LineWidth(2), ROOT.RooFit.Name("Chebyshev"))

    # Plot multiplied function
    prod_func.plotOn(frame, ROOT.RooFit.LineColor(ROOT.kBlue), ROOT.RooFit.LineStyle(ROOT.kDashed), ROOT.RooFit.LineWidth(2), ROOT.RooFit.Name("ChebFermi"))

    frame.Draw()

    # Construct legend
    leg = ROOT.TLegend(0.60, 0.70, 0.88, 0.88)
    leg.SetBorderSize(0)
    leg.AddEntry(frame.findObject("Data"), "data_obs", "pe")
    leg.AddEntry(frame.findObject("Chebyshev"), "Standard Chebyshev", "l")
    leg.AddEntry(frame.findObject("ChebFermi"), "Chebyshev #times Fermi", "l")
    leg.Draw()

    c.Draw()
    c.SaveAs("chebyshev_fermi_test.png")
    
    # Prevent the canvas from being garbage collected if running interactively
    ROOT.SetOwnership(c, False)

if __name__ == "__main__":
    plot_macro()