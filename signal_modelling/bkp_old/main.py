import ROOT
from plotting import *
from make_signal_model_workspace import *
from fit_parameters import *
import argparse
import os

# ------- NOTE ------ #
### There's some HARDCODED stuff here and there out of laziness. These are:
### - whether to fit and parametrize BW parameters, too
###   (uncomment relevant block in make_signal_model_workspace.py ('Use nominal values'/'Use fitted values'))
### - fixing BW width to 1e-10 or to nominal/fitted value
###   (same code block as above, comment out the assignment to width_BW)
# ------- I/O ------- #

wsfile = "signal_model.root"
# path = "../signal_model_cuts_fixed/snap/"
# path = "../signal_model_cuts_test/snap/"
path = "/eos/home-n/npalmeri/DiEleAnalyzer/CMGRDF_test/dp-ee-main/signal_model/zsnap/era2023/"

# ------ SAMPLES ------ #

# individual params
samples = {
    "Zd_M1" : {
        "filename" : "HAHM_13p6TeV_M1.root",
        "nominal_mass" : 1,                 # GeV
        "nominal_width" : 0.02,             # GeV
        "mass_range" : [1, 0.4, 1.4],       # GeV
        "mass_GEN_range" : [1, 0.8, 1.2],   # GeV
        "mean_BW_range" : [1, 0.7, 1.2],    # GeV
    },
    "Zd_M3p1" : {
        "filename" : "HAHM_13p6TeV_M3p1.root",
        "nominal_mass" : 3.1,
        "nominal_width" : 0.02,
        "mass_range" : [3.1, 2, 3.6],
        "mass_GEN_range" : [3.1, 2.9, 3.3],
        "mean_BW_range" : [3.1, 2.9, 3.2],
    },
    "Zd_M5" : {
        "filename" : "HAHM_13p6TeV_M5.root",
        "file_GEN" : path + "HAHM_13p6TeV_M5_2023_0common_0_GenSelection.root",
        "nominal_mass" : 5,
        "nominal_width" : 0.02,
        "mass_range" : [5, 3.5, 6],
        "mass_GEN_range" : [5, 4.75, 5.25],
        "mean_BW_range" : [5, 4, 6],
    },
    "Zd_M5p5" : {
        "filename" : "HAHM_13p6TeV_M5p5.root",
        "file_GEN" : path + "HAHM_13p6TeV_M5p5_2023_0common_0_GenSelection.root",
        "nominal_mass" : 5.5,
        "nominal_width" : 0.02,
        "mass_range" : [5.5, 4, 6.5],
        "mass_GEN_range" : [5.5, 5.25, 5.75],
        "mean_BW_range" : [5.5, 4.5, 6.5],
    },
    "Zd_M6" : {
        "filename" : "HAHM_13p6TeV_M6.root",
        "file_GEN" : path + "HAHM_13p6TeV_M6_2023_0common_0_GenSelection.root",
        "nominal_mass" : 6,
        "nominal_width" : 0.02,
        "mass_range" : [6, 4.5, 7],
        "mass_GEN_range" : [6, 5.75, 6.25],
        "mean_BW_range" : [6, 5, 7],
    },
    "Zd_M6p5" : {
        "filename" : "HAHM_13p6TeV_M6p5.root",
        "file_GEN" : path + "HAHM_13p6TeV_M6p5_2023_0common_0_GenSelection.root",
        "nominal_mass" : 6.5,
        "nominal_width" : 0.02,
        "mass_range" : [6.5, 5, 7.5],
        "mass_GEN_range" : [6.5, 6.25, 6.75],
        "mean_BW_range" : [6.5, 5.5, 7.5],
    },
    "UpsilonToEE" : {
        "filename" : "UpsilonToEE.root",
        "file_GEN" : path + "PromptUpsilon_2023_0common_0_GenSelection.root",
        "nominal_mass" : 9.460,
        "nominal_width" : 0.02, #PDG: 54 kev
        "mass_range" : [9, 6, 12],
        "mass_GEN_range" : [9, 9.2, 9.7],
        "mean_BW_range" : [9.460, 9, 10],
    },
    "JPsiToEE" : {
        "filename" : "JPsiToEE.root",
        "file_GEN" : path + "BuToKJpsi_2023_0common_0_GenSelection.root",
        "nominal_mass" : 3.097,
        "nominal_width" : 0.02, #54 kevfile_GEN
        "mass_range" : [3.1, 2, 3.6],
        "mass_GEN_range" : [3.1, 2.9, 3.3],
        "mean_BW_range" : [3.1, 2.9, 3.2],
    },

}

# common params
common_ranges = {
    # response function parameters
    "reduced_mass_range" : [0, -0.6, 0.6],
    "response_mean_range" : [0, -0.2, 0.2],
    "response_sigma_range" : [0.02, 0, 1],
    "response_alphaL_range" : [0.4, 0.1, 10],
    "response_alphaR_range" : [2, 0.1, 10],
    "response_nL_range" : [5, 0, 10],
    "response_nR_range" : [2, 0, 10],
    "response_nsgn_range" : [100, 0, 1000],
    # signal model parameters
    # dCB (non-parametrized, all free)
    "mean_range" : [0, -0.6, 0.6],
    "sigma_range" : [0.1, 0, 1],
    "alphaL_range" : [1, 0.2, 10],
    "alphaR_range" : [5, 0.2, 10],
    "nL_range" : [1, 0, 10],
    "nR_range" : [1, 0, 10],
    # BW
    "width_BW_range" : [0.001, 0, 0.1],
    "nsgn_range" : [100, 0, 1000],
}

for name, sample in samples.items():
    sample["file"] = os.path.join(path, "main_2_Final", sample["filename"])
    sample["file_GEN"] = os.path.join(path, "main_0_GenSelection", sample["filename"])

for name, sample in samples.items():
    # only overwrite params which are not already in dict
    for param, param_range in common_ranges.items():
        if param not in sample:
            sample[param] = param_range

vars = ["mean", "sigma", "alphaL", "alphaR", "nL", "nR"]
# parametrized_vars = ["sigma", "alphaL", "nL"]
parametrized_vars = ["mean", "sigma", "alphaL", "alphaR", "nL", "nR"]
# parametrized_vars = []

if __name__ == "__main__":
    ### INPUT ARGUMENTS ###
    # retrieve arguments from command line using argparse
    parser = argparse.ArgumentParser()
    #action=argparse.BooleanOptionalAction
    parser.add_argument("--wsfile", help="Workspace file name", default="signal_model.root")
    parser.add_argument("--delete_ws", help="Delete workspace file", action="store_true", default=False)
    parser.add_argument("--copy_eos", help="Copy all output plots to EOS directory", action="store_true", default=False)
    parser.add_argument("--full", help="Run all steps", action="store_true", default=False)
    parser.add_argument("--parametrized_vars", help="Parametrized variables", nargs="+", default=parametrized_vars)
    parser.add_argument("--response", help="Build response function workspace + fit parameters", action="store_true", default=False)
    parser.add_argument("--compare_response", help="Compare response function workspace + fit parameters for M = 3.1 GeV (Zd vs Jpsi)", action="store_true", default=False)
    parser.add_argument("--signal_model", help="Test signal model workspace", action="store_true", default=False)
    parser.add_argument("--test_signal_model", help="Create signal model for a sequence of mass points", action="store_true", default=False)
    parser.add_argument("--gen", help="Test GEN distribution", action="store_true", default=False)
    parser.add_argument("--plots", help="Produce all plots", action="store_true", default=False)
    parser.add_argument("--no_response", help="Skip building response function workspace + fit parameters [works with --full]", action="store_true", default=False)
    parser.add_argument("--no_compare_response", help="Skip comparing response function workspace + fit parameters for M = 3.1 GeV (Zd vs Jpsi)", action="store_true", default=False)
    parser.add_argument("--no_signal_model", help="Skip testing signal model workspace [works with --full]", action="store_true", default=False)
    parser.add_argument("--no_test_signal_model", help="Skip creating signal model for a sequence of mass points", action="store_true", default=False)
    parser.add_argument("--no_gen", help="Skip testing GEN distribution [works with --full]", action="store_true", default=False)
    parser.add_argument("--no_plots", help="Skip producing all plots [works with --full]", action="store_true", default=False)
    parser.add_argument("--use_reco_mass", help="Derive signal model from reco mass rather than reduced", action="store_true", default=False)
    args = parser.parse_args()
    
    wsfile = args.wsfile

    # check if parametrized_vars is a strict subset of vars
    if not set(args.parametrized_vars).issubset(set(vars)):
        raise ValueError("parametrized_vars must be a subset of vars ({}), got {}".format(vars, args.parametrized_vars))
    parametrized_vars = args.parametrized_vars

    # delete previous workspace
    if args.delete_ws and os.path.exists(wsfile):
        print(f"Found previous workspace in {wsfile}; deleting file")
        os.remove(wsfile)

    if args.response or (args.full and not args.no_response):
        print("Making response function workspace")
        make_response_function_workspace(samples, wsfile)

        print("Fitting parameters")
        fit_parameters(samples, wsfile, vars, parametrized_vars)

    if args.gen or (args.full and not args.no_gen):
        print("Testing GEN distribution of signal")
        test_BW_GEN(samples, wsfile, parametrized_vars, fit = False)

        print("Fitting GEN distribution of signal")
        test_BW_GEN(samples, wsfile, parametrized_vars, fit = True)

    if (args.gen and args.response) or (args.full and not (args.no_gen or args.no_response)):
        print("Fitting GEN model parameters")
        fit_parameters(samples, wsfile, ["mean_BW", "width_BW"], ["mean_BW", "width_BW"], gen = True)

    if args.signal_model or (args.full and not args.no_signal_model):
        # ## DEBUGGING ONLY: fit signal model parameters to check best agreement
        # print("Testing full signal model (non-parametric)")
        # make_signal_model(samples, wsfile, parametrized_vars, fit = True)

        print("Testing full signal model (parametric)")
        make_signal_model(samples, wsfile, parametrized_vars, isParametrized = True) # no fit, just saving and displaying

    if args.compare_response or (args.full and not args.no_compare_response):
        print("Comparing response function workspace for M = 3.1 GeV (Zd vs Jpsi)")
        compare_zd_jpsi_shape(samples, wsfile, plot_fit = True)

    if args.test_signal_model or (args.full and not args.no_test_signal_model):
        print("Testing signal model workspace for several mass points")
        for mass in np.concatenate([np.arange(0.5, 10.5, 0.5), [3.1, 3.7]]):
            build_signal_model_for_mass(samples, wsfile, parametrized_vars, mass)

    if args.plots or (args.full and not args.no_plots):
        print("Plotting")
        if not (args.gen or args.test_signal_model):
            plot_response_fit(samples, wsfile)
            plot_parametrization(samples, wsfile, vars, parametrized_vars, plot_post_param = False)
            plot_sample_fit(samples, wsfile, plot_pre_param = False)
        if not args.no_test_signal_model and not args.gen:
            plot_model_only(samples, wsfile, parametrized_vars)
        if not args.no_gen and not args.test_signal_model:
            plot_parametrization(samples, wsfile, ["mean_BW", "width_BW"], ["mean_BW", "width_BW"], gen = True, plot_post_param = False)
            plot_sample_fit(samples, wsfile, plot_pre_param = True, gen = True, plot_post_param = True)
    
    if args.copy_eos:
        print("Copying plots to EOS")
        copy_plots_to_eos()