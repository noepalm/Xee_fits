import ROOT
import uproot
import numpy as np

def fit_parameters(samples, wsfile, vars, parametrized_vars, gen = False):
    # DEBUGGING: do not consider Jpsi sample for parameter fit
    samples = {name : sample for name, sample in samples.items() if "JPsi" not in name}

    # Open workspace
    f = ROOT.TFile.Open(wsfile)
    w = f.Get("w")

    const_vars = list(set(vars) - set(parametrized_vars))

    
    # Create TGraph with mean, sigma vs mass
    graphs = {var : ROOT.TGraphErrors() for var in vars}

    # # Also create RooDataSet
    # m = ROOT.RooRealVar("mass", "mass", 0, 12)
    # w.Import(m, True)
    # for var in vars:
    #     w.factory(f"RooRealVar::{var}_fit_data(0, -5, 5)")
    # datas = {var : ROOT.RooDataSet(f"data_{var}", f"data_{var}", ROOT.RooArgSet(m, w.var(f"{var}_fit_data")), ROOT.RooFit.StoreError(ROOT.RooArgSet(m, w.var(f"{var}_fit_data")))) for var in vars}

    for name, sample in samples.items():
        for var in vars:
            input_var = f"{var}_GEN_fit_{name}" if gen else f"response_{var}_{name}"
            val = w.var(input_var).getVal()
            err = w.var(input_var).getError()
            graphs[var].SetPoint(graphs[var].GetN(), sample["nominal_mass"], val)
            graphs[var].SetPointError(graphs[var].GetN()-1, 0, err)

            # m.setVal(sample["nominal_mass"])
            ### TOFIX: setVal not working? setError does though
            # w.var(f"{var}_fit_data").setVal(val)
            # w.var(f"{var}_fit_data").setError(err)
            # datas[var].add(ROOT.RooArgSet(m, w.var(f"{var}_fit_data")))

    # # print all data points in datasets
    # for var in vars:
    #     print(f"{var} data points:")
    #     for i in range(datas[var].numEntries()):
    #         pt = datas[var].get(i)
            
    #         print(f"Point {i}: x = {pt['mass'].getVal()}, y = {pt[w.var(f'{var}_fit_data').GetName()].getVal()} +- {pt[w.var(f'{var}_fit_data').GetName()].getError()}")
    #         print(f"vs graph: x = {graphs[var].GetX()[i]}, y = {graphs[var].GetY()[i]} +- {graphs[var].GetEY()[i]}")

    # Fit both graphs with linear models
    tag = "_GEN" if gen else ""
    fits = {var : ROOT.TF1(f"fit{tag}_{var}", "[0] + [1]*x", 0, 12) for var in parametrized_vars}

    # for var in parametrized_vars:
    #     w.factory(f"RooPolynomial::fit{tag}_{var}(m, {var}_fit_par0[-1,1], {var}_fit_par1[-1,1])")
    # fits = {var : w.pdf(f"fit{tag}_{var}") for var in parametrized_vars}

    consts = {var : ROOT.RooRealVar(f"{var}{tag}_const", f"{var}{tag}_const", -1) for var in const_vars}

    for var in vars:
        if var in parametrized_vars:
            fitResult = graphs[var].Fit(fits[var], "S")
            # # print covariance matrix
            # cov = fitResult.GetCovarianceMatrix()
            # print(f"{var} fit parameters:")

            ### TOFIX: error in syntax
            # fitResult = fits[var].fitTo(datas[var], ROOT.RooFit.Save())
            # for i in range(2):
            #     print(f"{var} fit parameters:")
            #     print(f"{fits[var].getVal(i)} +- {fits[var].getError(i)}")
            
            # # save fit parameter correlations
            # w.Import(fitResult, True)

        else:
            # compute mean + uncertainty of Y values
            y_values = np.array([graphs[var].GetY()[i] for i in range(graphs[var].GetN())])
            y_errors = np.array([graphs[var].GetEY()[i] for i in range(graphs[var].GetN())])

            # weighted mean + error
            mean = np.average(y_values, weights = 1/y_errors**2)
            err = np.sqrt(1/sum(1/y_errors**2))

            consts[var].setVal(mean)
            consts[var].setError(err)
            consts[var].setConstant()

    for var in parametrized_vars:
        print(f"{var} fit parameters:")
        for i in range(2):
            print(f"{fits[var].GetParameter(i)} +- {fits[var].GetParError(i)}")
    for var in const_vars:
        print(f"{var} constant value: {consts[var].getVal()} +- {consts[var].getError()}")

    ## Define RooRealVar with fit parameters and save to workspace
    for i in range(2):
        for var, fit in fits.items():
            obj = ROOT.RooRealVar(f"{var}_fit_par{i}", f"{var}_fit_par{i}", fit.GetParameter(i))
            obj.setError(fit.GetParError(i))
            obj.setConstant()
            w.Import(obj, True)

    # ## Define RooRealVar with fit parameters and save to workspace
    # for i in range(2):
    #     for var in parametrized_vars:
    #         obj = w.var(f"{var}_fit_par{i}")
    #         obj.setConstant()

    for var, const in consts.items():
        w.Import(const, True)

    # Export workspace
    w.writeToFile(wsfile, True)

if __name__ == "__main__":
    from main import samples, wsfile
    
    # Fitting parameters
    fit_parameters(samples, wsfile)