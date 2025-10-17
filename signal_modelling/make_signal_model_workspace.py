import ROOT

def make_response_function_workspace(samples, categories, wsfile, use_reco_mass = False):

    # ------ STEP 1: INDIVIDUAL FITS ------ #

    # Create a workspace
    w = ROOT.RooWorkspace("w")
    
    for name, sample in samples.items():
        print(name)

        # open input tree
        f = ROOT.TFile.Open(sample['file'])
        t = f.Get("Events")
    
        # create corresponding obs and variables
        observables = ["mass" if use_reco_mass else "reduced_mass"]
        vars = ["response_mean", "response_sigma", "response_alphaL", "response_nL", "response_alphaR", "response_nR"] #NB: order must match function parameters later 
        normalizations = ["response_nsgn"]

        for category_label, category in categories.items():
            print(f"\t{category_label}")
            cat_name = f"_{category['name']}" if category["name"] != "" else category["name"]
            
            for var in observables + vars + normalizations:
                w.factory(f"""{var}_{name}{cat_name}[{','.join([str(v) for v in sample[f'{var}_range']])}]""") #horrid but compact syntax

            # create and fill dataset
            print("Filling reduced mass dataset")
            weightVar = ROOT.RooRealVar(f"weightVar_{name}{cat_name}", f"weightVar_{name}{cat_name}", 1.0) # create a weight variable
            w.Import(weightVar, ROOT.RooCmdArg())
            data = ROOT.RooDataSet(f"response_data_{name}{cat_name}", f"response_data_{name}{cat_name}", ROOT.RooArgSet(w.var(f"{observables[0]}_{name}")), ROOT.RooFit.WeightVar(f"weightVar_{name}{cat_name}"))
            min_val = sample[f'{observables[0]}_range'][1]
            max_val = sample[f'{observables[0]}_range'][2]
            for i in range(t.GetEntries()):
                t.GetEntry(i)
                weight = t.weight if hasattr(t, 'weight') else 1.0
                cat_vars = {var : t.__getattr__(var) for var in category["cuts"].keys()}
                cat_ranges = {var : category["cuts"][var] for var in category["cuts"].keys()}
                for j, val in enumerate(t.SelectedDiEle_fitted_mass):
                    # CATEGORY CHECK
                    is_in_cat = True
                    for var, ranges in cat_ranges.items():
                        cat_var_value = cat_vars[var][j]
                        # consider OR of specified ranges
                        range_check = False
                        for r in ranges: 
                            if cat_var_value > r[0] and cat_var_value <= r[1]:
                                range_check = True
                        if not range_check:
                            is_in_cat = False
                            break

                    if not is_in_cat:
                        continue

                    # FILL DATASET
                    gen_mass = t.GenZd_invMass
                    fill_value = val if use_reco_mass else val/gen_mass - 1 #val/sample["nominal_mass"] - 1

                    # only fill values within specified mass range
                    if fill_value < min_val or fill_value > max_val:
                        continue

                    w.var(f"{observables[0]}_{name}{cat_name}").setVal(fill_value)
                    data.add(ROOT.RooArgSet(w.var(f"{observables[0]}_{name}{cat_name}")), weight)
            
            # import dataset in workspace
            w.Import(data)

            # create model
            # w.factory(f"""CrystalBall::crystalBall_response_{name}({','.join([f"{var}_{name}" for var in observables + vars])})""")
            # w.factory(f"""ExtendPdf::response_function_{name}(crystalBall_response_{name}, response_nsgn_{name})""")
            w.factory(f"""CrystalBall::response_function_{name}{cat_name}({','.join([f"{var}_{name}" for var in observables + vars])})""")
            # w.factory(f"""ExtendPdf::response_function_{name}(crystalBall_response_{name}, response_nsgn_{name})""")

            # fit the model to the data
            model = w.pdf(f"response_function_{name}{cat_name}")
            fitResult = model.fitTo(data, ROOT.RooFit.Save(), ROOT.RooFit.NumCPU(8), ROOT.RooFit.SumW2Error(True))

            # import model in workspace
            w.Import(model)
            w.writeToFile(wsfile)

        # close the file
        f.Close()

def make_signal_model(samples, categories, wsfile, parametrized_vars, isParametrized = False, fit = False, use_reco_mass = False):

    for name, sample in samples.items():
        ### WORKSPACE 
        f = ROOT.TFile.Open(wsfile)
        w = f.Get("w")

        ### VARIABLES AND OBSERVABLES
        observables = ["mass"]
        vars_BW = ["mean_BW", "width_BW"]
        vars_dCB = ["mean", "sigma", "alphaL", "nL", "alphaR", "nR"] #NB: order must match function parameters later 
        const_vars = list(set(vars_dCB) - set(parametrized_vars))

        tag = "param" if isParametrized else "nonParam"
        if fit:
            tag = tag + "_fit"
        all_vars = vars_dCB if use_reco_mass else vars_BW + vars_dCB

        w.factory(f"mass_{name}[{','.join([str(v) for v in sample['mass_range']])}]")

        for category_label, category in categories.items():
            cat_name = f"_{category['name']}" if category["name"] != "" else category["name"]

            for var in all_vars:
                if var in parametrized_vars and isParametrized: # vars to be parametrized
                    ### Parametric fit sigma
                    ## Factory syntax
                    # # NB: doesn't work when w.Import(obj) is called, saved as TObject instead of RooAbsReal. Not really clear
                    # w.factory(f"""expr::sigma_param_{name}(sigma_fit_par0 + sigma_fit_par1 * mean_param_{name}, sigma_fit_par0, sigma_fit_par1, mean_param_{name})""")
                    ## Object syntax
                    formula = "@0 + @1 * @2"
                    if var == "sigma" and not use_reco_mass:
                        formula = "(@0 + @1 * @2) * @2"
                    # if var == "mean":
                    #     formula = "((@0 + @1 * @2) + 1) * @2"
                    obj = ROOT.RooFormulaVar(
                        f"{var}_{tag}_{name}{cat_name}",
                        f"{var}_{tag}_{name}{cat_name}",
                        # f"{var}_fit_par0 + {var}_fit_par1 * nominal_mass",
                        formula,
                        ROOT.RooArgList([w.obj(f"{var}{cat_name}_fit_par0"), w.obj(f"{var}{cat_name}_fit_par1"), sample["nominal_mass"]])
                        )
                    w.Import(obj)
                else:
                    w.factory(f"""{var}_{tag}_{name}{cat_name}[{','.join([str(v) for v in sample[f'{var}_range']])}]""") #horrid but compact syntax
                    if var in const_vars:
                        obj = w.obj(f'{var}_{tag}_{name}{cat_name}')
                        obj.setVal(w.obj(f'{var}{cat_name}_const').getVal())
                        obj.setError(w.obj(f'{var}{cat_name}_const').getError())
                        obj.setConstant(True)
                    if var in vars_BW:
                        # # Use nominal values
                        # ref_var = "nominal_mass" if var == "mean_BW" else "nominal_width"
                        # ref_var = sample[ref_var]
                        # val = ref_var
                        # Use fitted values
                        ref_var = w.var(f"{var}_GEN_fit_{name}{cat_name}").getVal()
                        w.var(f"{var}_{tag}_{name}{cat_name}").setVal(ref_var)
                        w.var(f"{var}_{tag}_{name}{cat_name}").setConstant(True)
                        val = sample["nominal_mass"] * w.obj(f"{var}{cat_name}_fit_par1").getVal() + w.obj(f"{var}{cat_name}_fit_par0").getVal()
                        # if var == "width_BW":
                        #     val = 10e-10
                        w.obj(f"{var}_{tag}_{name}{cat_name}").setVal(val)
                        w.var(f"{var}_{tag}_{name}{cat_name}").setConstant(True)
                        print(f"Setting {var}_{tag}_{name}{cat_name} to {val}")
                        # formula = "@0 + @1 * @2"
                        # obj = ROOT.RooFormulaVar(
                        #     f"{var}_{tag}_{name}",
                        #     f"{var}_{tag}_{name}",
                        #     "@0 + @1 * @2",
                        #     ROOT.RooArgList([w.obj(f"{var}_fit_par0"), w.obj(f"{var}_fit_par1"), sample["nominal_mass"]])
                        # )
                        # print(f"Setting {var}_{tag}_{name} to {obj.getVal()}")
                        # w.Import(obj)

            # print all variables
            for var in all_vars:
                print(f"{var}_{tag}_{name}{cat_name}: {w.obj(f'{var}_{tag}_{name}').getVal()}")

            ### DATASET
            # first check if data already in workspace
            data = w.data(f"data_{name}{cat_name}")
            if not data:
                print(f"Data for {name}{cat_name} not found in workspace. Reloading samples")

                f = ROOT.TFile.Open(sample['file'])
                t = f.Get("Events")

                weightVar = ROOT.RooRealVar(f"weightVar_{name}{cat_name}", f"weightVar_{name}{cat_name}", 1.0) # create a weight variable
                w.Import(weightVar, ROOT.RooCmdArg())
                data = ROOT.RooDataSet(f"data_{name}{cat_name}", f"data_{name}{cat_name}", ROOT.RooArgSet(w.var(f"mass_{name}")), ROOT.RooFit.WeightVar(f"weightVar_{name}{cat_name}"))
                # retrieve min, max values of the mass range
                min_val = sample['mass_range'][1]
                max_val = sample['mass_range'][2]

                for i in range(t.GetEntries()):                    
                    t.GetEntry(i)
                    weight = t.weight if hasattr(t, 'weight') else 1.0
                    cat_vars = {var : t.__getattr__(var) for var in category["cuts"].keys()}
                    cat_ranges = {var : category["cuts"][var] for var in category["cuts"].keys()}
                    for j, val in enumerate(t.SelectedDiEle_fitted_mass):
                        # CATEGORY CHECK
                        is_in_cat = True
                        for var, ranges in cat_ranges.items():
                            cat_var_value = cat_vars[var][j]
                            # consider OR of specified ranges
                            range_check = False
                            for r in ranges: 
                                if cat_var_value > r[0] and cat_var_value <= r[1]:
                                    range_check = True
                            if not range_check:
                                is_in_cat = False
                                break

                        if not is_in_cat:
                            continue

                        if val < min_val or val > max_val:
                            continue
                        w.var(f"mass_{name}").setVal(val)
                        data.add(ROOT.RooArgSet(w.var(f"mass_{name}")), weight)

                print(f"Data for {name}{cat_name} reloaded")

                w.Import(data, True)

            ### MODEL
            ## TODO: fix implementation with correct variable instead of rescaling sigma
            # dCB_var = ROOT.RooFormulaVar(
            #     f"reduced_mass_sgn_{name}",
            #     f"reduced_mass_sgn_{name}",
            #     f"@0/@1 - 1",
            #     ROOT.RooArgList([w.var(f"mass_{name}"), sample["nominal_mass"]])
            # )
            # w.Import(dCB_var)
            # var_string_dCB = f"reduced_mass_sgn_{name}, {','.join([f'{var}_{tag}_{name}' for var in vars_dCB])}"
            var_string_dCB = f"mass_{name}, {','.join([f'{var}_{tag}_{name}{cat_name}' for var in vars_dCB])}"
            w.factory(f"CrystalBall::crystalBall_{tag}_{name}{cat_name}({var_string_dCB})")
            # var_string_BW = f"mass_{name}, {','.join([f'{var}_{tag}_{name}' for var in vars_BW])}"
            # w.factory(f"BreitWigner::BW_{tag}_{name}({var_string_BW})")

            if use_reco_mass:
                model = w.pdf(f"crystalBall_{tag}_{name}{cat_name}").Clone(f"model_{tag}_{name}{cat_name}")
            else:
                # create BW -- final model given by convolution of dCB and BW

                var_list_BW = [w.obj(f"{var}_{tag}_{name}{cat_name}") for var in vars_BW]
                var_list_BW.insert(0, w.var(f"mass_{name}"))
                var_string_BW = ",".join([v.GetName() for v in var_list_BW])

                print(var_string_BW)

                # for var in var_list_BW:
                #     print(var.GetName())
                #     print(var.getVal())
                # print(ROOT.TMath.BreitWignerRelativistic)
                # relBW = ROOT.RooFit.bindPdf(f"relBW_{tag}_{name}", ROOT.TMath.BreitWignerRelativistic, *var_list_BW)
                # w.Import(relBW)

                # # NOTE: function pointers seem to act up? Maybe some python issue, try with C interface
                # ROOT.gSystem.Load("libRooFit")
                # ROOT.gInterpreter.ProcessLine(f"""
                #     RooAbsPdf* relBW = RooFit::bindPdf("relBW", TMath::BreitWignerRelativistic, {var_string_BW});
                #     w.Import(*relBW);
                # """)

                # Double_t mm = median*median;
                # Double_t gg = gamma*gamma;
                # Double_t mg = median*gamma;
                # Double_t xxMinusmm = x*x - mm;
                
                # Double_t y = sqrt(mm * (mm + gg));
                # Double_t k = (0.90031631615710606*mg*y)/(sqrt(mm+y)); //2*sqrt(2)/pi = 0.90031631615710606
                
                # Double_t bw = k/(xxMinusmm*xxMinusmm + mg*mg);
                # return bw;
                
                # relBW_formula = f"TMath::BreitWignerRelativistic({var_string_BW})"
                # @0 = x, @1 = median, @2 = gamma
                relBW_formula = "2*sqrt(2)/pi * @1**2 * @2*sqrt(@1**2 + @2**2) / ((@0**2 - @1**2)*(@0**2 - @1**2) + @1**2 * @2**2) / (sqrt(@1**2 + @1*sqrt(@2**2 + @1**2)))"
                # w.factory(f"GenericPdf::relBW_{tag}_{name}({relBW_formula}, {var_string_BW})")
                relBW = ROOT.RooGenericPdf(f"relBW_{tag}_{name}{cat_name}", relBW_formula, var_list_BW )        
                w.Import(relBW)

                # define convolution
                mass = w.var(f"mass_{name}")
                mass.setBins(10000, "cache")
                mass.setMin("cache", -20)
                mass.setMax("cache", 20)

                w.factory(f"FFTConvPdf::model_{tag}_{name}{cat_name}(mass_{name}, crystalBall_{tag}_{name}{cat_name}, relBW_{tag}_{name}{cat_name})")
                model = w.pdf(f"model_{tag}_{name}{cat_name}")

            ### FIT TO SAMPLES
            if fit:
                fitResult = model.fitTo(data, ROOT.RooFit.Save(), ROOT.RooFit.NumCPU(8), ROOT.RooFit.SumW2Error(True))

                fitResult.Print()
                w.Import(fitResult, True)

            # Print post-parametrization fit parameters
            if isParametrized and fit:
                print(f"Post-parametrization fit parameters for {name}{cat_name}:")
                for var in all_vars:
                    obj = w.obj(f'{var}_{tag}_{name}{cat_name}')
                    val = obj.getVal()

                    if var in parametrized_vars:
                        err = obj.getPropagatedError(fitResult)
                    else:
                        err = obj.getError()

                    print(f"{var}: {val:.3g} +/- {err:.3g}")

            # import model in workspace
            w.Import(model, ROOT.RooCmdArg())

            # close the file
            f.Close()
            w.writeToFile(wsfile)


def build_signal_model_for_mass(samples, categories, wsfile, parametrized_vars, mass, use_reco_mass = False):
    ### WORKSPACE 
    f = ROOT.TFile.Open(wsfile)
    w = f.Get("w")

    vars_BW = ["mean_BW", "width_BW"]
    vars_dCB = ["mean", "sigma", "alphaL", "nL", "alphaR", "nR"] #NB: order must match function parameters later 
    const_vars = list(set(vars_dCB) - set(parametrized_vars))

    tag = "test"

    # create one observable for all mass points
    m = ROOT.RooRealVar(f"mass_{tag}", f"mass_{tag}", 0, 11)
    w.Import(m)

    print(f"Mass: {mass}")
    name = f"M{mass:.1f}"
    name = name.replace(".", "p")

    all_vars = vars_dCB if use_reco_mass else vars_BW + vars_dCB

    for category_label, category in categories.items():
        cat_name = f"_{category['name']}" if category["name"] != "" else category["name"]

        for var in all_vars:
            if var in parametrized_vars: # vars to be parametrized
                formula = "@0 + @1 * @2"
                if var == "sigma" and not use_reco_mass:
                    formula = "(@0 + @1 * @2) * @2"
                obj = ROOT.RooFormulaVar(
                    f"{var}_{tag}_{name}{cat_name}",
                    f"{var}_{tag}_{name}{cat_name}",
                    formula,
                    ROOT.RooArgList([w.obj(f"{var}{cat_name}_fit_par0"), w.obj(f"{var}{cat_name}_fit_par1"), mass])
                    )
                w.Import(obj)
            else:
                w.factory(f"{var}{cat_name}_{tag}_{name}[0, -100, 100]")
                if var in const_vars:
                    obj = w.obj(f'{var}{cat_name}_{tag}_{name}')
                    obj.setVal(w.obj(f'{var}{cat_name}_const').getVal())
                    obj.setError(w.obj(f'{var}{cat_name}_const').getError())
                    obj.setConstant(True)
                if var in vars_BW:
                    # # Use fitted value
                    # val = mass * w.obj(f"{var}_fit_par1").getVal() + w.obj(f"{var}_fit_par0").getVal()
                    if var == "width_BW":
                        val = 10e-10
                    elif var == "mean_BW":
                        val = mass
                    w.obj(f"{var}_{tag}_{name}{cat_name}").setVal(val)
                    w.var(f"{var}_{tag}_{name}{cat_name}").setConstant(True)
                    print(f"Setting {var}_{tag}_{name}{cat_name} to {val}")

        # print all variables
        for var in all_vars:
            print(f"{var}_{tag}_{name}{cat_name}: {w.obj(f'{var}_{tag}_{name}{cat_name}').getVal()}")

        var_string_dCB = f"mass_{tag}, {','.join([f'{var}_{tag}_{name}{cat_name}' for var in vars_dCB])}"
        w.factory(f"CrystalBall::crystalBall_{tag}_{name}{cat_name}({var_string_dCB})")

        if use_reco_mass:
            model = w.pdf(f"crystalBall_{tag}_{name}{cat_name}").Clone(f"model_{tag}_{name}{cat_name}")
        else:
            var_list_BW = [w.obj(f"{var}_{tag}_{name}{cat_name}") for var in vars_BW]
            var_list_BW.insert(0, w.obj(f"mass_{tag}"))
            var_string_BW = ",".join([v.GetName() for v in var_list_BW])

            relBW_formula = "2*sqrt(2)/pi * @1**2 * @2*sqrt(@1**2 + @2**2) / ((@0**2 - @1**2)*(@0**2 - @1**2) + @1**2 * @2**2) / (sqrt(@1**2 + @1*sqrt(@2**2 + @1**2)))"
            relBW = ROOT.RooGenericPdf(f"relBW_{tag}_{name}{cat_name}", relBW_formula, var_list_BW )        
            w.Import(relBW)

            # define convolution
            # mass = w.var(f"mass_{tag}")
            m.setBins(10000, "cache")
            m.setMin("cache", -20)
            m.setMax("cache", 20)

            w.factory(f"FFTConvPdf::model_{tag}_{name}{cat_name}(mass_{tag}, crystalBall_{tag}_{name}{cat_name}, relBW_{tag}_{name}{cat_name})")
            model = w.pdf(f"model_{tag}_{name}{cat_name}")

        # import model in workspace
        w.Import(model, True)

    # close the file
    f.Close()
    w.writeToFile(wsfile)

def test_BW_GEN(samples, categories, wsfile, parametrized_vars, fit = False):

    for name, sample in samples.items():
        
        f = ROOT.TFile.Open(wsfile)
        w = f.Get("w")

        ### VARIABLES AND OBSERVABLES
        observables = ["mass_GEN"]
        vars_BW = ["mean_BW", "width_BW"]

        tag = "GEN"
        if fit:
            tag = tag + "_fit"

        w.factory(f"mass_GEN_{name}[{','.join([str(v) for v in sample['mass_GEN_range']])}]")

        for category_label, category in categories.items():
            cat_name = f"_{category['name']}" if category["name"] != "" else category["name"]

            for var in vars_BW:
                w.factory(f"""{var}_{tag}_{name}{cat_name}[{','.join([str(v) for v in sample[f'{var}_range']])}]""") #horrid but compact syntax
                if var in vars_BW:
                    # if width, set value to nominal_width; if mean, set to nominal_mass
                    ref_var = "nominal_mass" if var == "mean_BW" else "nominal_width"
                    w.var(f"{var}_{tag}_{name}{cat_name}").setVal(sample[ref_var])
                    if not fit:
                        w.var(f"{var}_{tag}_{name}{cat_name}").setConstant(True)

            ### DATASET
            # first check if data already in workspace
            data = w.data(f"data_GEN_{name}{cat_name}")
            if not data:
                print(f"Data for {name} not found in workspace. Reloading samples")

                f = ROOT.TFile.Open(sample['file'])
                t = f.Get("Events")

                data = ROOT.RooDataSet(f"data_GEN_{name}{cat_name}", f"data_GEN_{name}{cat_name}", ROOT.RooArgSet(w.var(f"mass_GEN_{name}")))
                min_val = sample['mass_GEN_range'][1]
                max_val = sample['mass_GEN_range'][2]
                for i in range(t.GetEntries()):
                    t.GetEntry(i)
                    # handle both case in which GenZd_mass is variable or array
                    vals = [t.GenZd_invMass] if not isinstance(t.GenZd_invMass, ROOT.RVec('float')) else t.GenZd_invMass
                    cat_vars = {var : t.__getattr__(var) for var in category["cuts"].keys()}
                    cat_ranges = {var : category["cuts"][var] for var in category["cuts"].keys()}
                    
                    for j, val in enumerate(vals):
                        # CATEGORY CHECK
                        is_in_cat = True
                        for var, ranges in cat_ranges.items():
                            cat_var_value = cat_vars[var][j]
                            # consider OR of specified ranges
                            range_check = False
                            for r in ranges: 
                                if cat_var_value > r[0] and cat_var_value <= r[1]:
                                    range_check = True
                            if not range_check:
                                is_in_cat = False
                                break
                                
                        if not is_in_cat:
                            continue

                        # MASS CHECK
                        if val < min_val or val > max_val:
                            continue

                        w.var(f"mass_GEN_{name}").setVal(val)
                        data.add(ROOT.RooArgSet(w.var(f"mass_GEN_{name}")))

                print(f"GEN data for {name}{cat_name} reloaded")

                w.Import(data, True)

            ### MODEL
            var_list_BW = [w.obj(f"{var}_{tag}_{name}{cat_name}") for var in vars_BW]
            var_list_BW.insert(0, w.var(f"mass_GEN_{name}"))
            var_string_BW = ",".join([v.GetName() for v in var_list_BW])

            # relBW_formula = f"TMath::BreitWignerRelativistic({var_string_BW})"
            relBW_formula = "2*sqrt(2)/pi * @1**2 * @2*sqrt(@1**2 + @2**2) / ((@0**2 - @1**2)*(@0**2 - @1**2) + @1**2 * @2**2) / (sqrt(@1**2 + @1*sqrt(@2**2 + @1**2)))"

            # NB: creating GenericPdf as model_XXX does not work for some reason. 
            relBW = ROOT.RooGenericPdf(f"relBW_{tag}_{name}{cat_name}", relBW_formula, var_list_BW)
            w.Import(relBW)
            model = relBW.Clone(f"model_{tag}_{name}{cat_name}")

            # w.factory(f"ExtendPdf::model_{tag}_{name}(relBW_{tag}_{name}, n[100,0,1000])")
            # model = w.pdf(f"model_{tag}_{name}")

            ### FIT TO SAMPLES
            if fit:
                print("Fitting BW")
                fitResult = model.fitTo(data, ROOT.RooFit.Save())

                fitResult.Print()
                w.Import(fitResult, True)

            # import model in workspace
            w.Import(model, True)

        # close the file
        f.Close()
        w.writeToFile(wsfile)
    
if __name__ == "__main__":
    from main import samples, categories, wsfile

    print("Making response function workspace")
    make_response_function_workspace(samples, categories, wsfile)