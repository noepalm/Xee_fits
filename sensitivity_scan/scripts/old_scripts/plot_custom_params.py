import ROOT
import argparse
import os

# argparse
parser = argparse.ArgumentParser()
parser.add_argument('-d', '--datacard', type=str, default='Xee_ee_0_2023.root', help='Name of the combine workspace; output of text2workspace')
parser.add_argument('-f', '--fit_result', type=str, default=None, help='Fit result file (fitDiagnostics.root, multidimfit.root, or higgsCombine*.root)')
parser.add_argument('--fit_type', type=str, default='s', choices=['s', 'b'], help='Use signal+background (s) or background-only (b) fit')
parser.add_argument('-o', '--output_folder', type=str, default='plots', help='Output folder')
parser.add_argument('-m', '--mass', type=float, default=1.8, help='Mass value to plot')
parser.add_argument('-c', '--cat_id', type=int, default=0, help='Category ID to plot')
parser.add_argument('-r', '--region', type=str, default='region0', choices=["region0", "region1", "region2"])
parser.add_argument('--tag', type=str, default='', help='Tag to append to output folder name')

# Parameters to override (if not loading from fit result)
parser.add_argument('--mu', type=float, default=None, help='Override mu value')
parser.add_argument('--a0', type=float, default=None, help='Override a0 parameter')
parser.add_argument('--a1', type=float, default=None, help='Override a1 parameter')
parser.add_argument('--a2', type=float, default=None, help='Override a2 parameter')
parser.add_argument('--a3', type=float, default=None, help='Override a3 parameter')
parser.add_argument('--a4', type=float, default=None, help='Override a4 parameter')

args = parser.parse_args()
cat_id = args.cat_id
tag_label = f"_{args.tag}" if args.tag else ""

# print all arguments
print("Arguments:")
for arg in vars(args):
    print(f"{arg}: {getattr(args, arg)}")

# Create output directory if it doesn't exist
os.makedirs(args.output_folder, exist_ok=True)

# Region-specific configurations
region_config = {
    "region0": {
        "resonant_bkgs": ["phi", "omega", "eta"],
        "bkg_labels": ["DY", "phi", "omega", "eta"],
        "all_labels": ["phi", "omega", "eta", "DY", "Signal", "Total S+B"],
        "mass_range": (0.17, 2.0),
        "y_min": 1e1,
        "y_max": 1e6
    },
    "region1": {
        "resonant_bkgs": ["jpsi", "psi2s"],
        "bkg_labels": ["DY", "J/#psi", "#psi(2S)"],
        "all_labels": ["J/#psi", "#psi(2S)", "DY", "Signal", "Total S+B"],
        "mass_range": (2.0, 4.2),
        "y_min": 0.1,
        "y_max": 1e5
    },
    "region2": {
        "resonant_bkgs": ["upsilon1s"],
        "bkg_labels": ["DY", "#Upsilon(1S)"],
        "all_labels": ["#Upsilon(1S)", "DY", "Signal", "Total S+B"],
        "mass_range": (4.2, 12.0),
        "y_min": 10,
        "y_max": 1e5
    }
}

resonant_bkgs = region_config[args.region]["resonant_bkgs"]
bkg_labels = region_config[args.region]["bkg_labels"]
all_labels = region_config[args.region]["all_labels"]
mass_range = region_config[args.region]["mass_range"]

# Open datacard workspace
f_datacard = ROOT.TFile.Open(args.datacard, "READ")
if not f_datacard or f_datacard.IsZombie():
    print(f"ERROR: Cannot open datacard file {args.datacard}")
    exit(1)

w = f_datacard.Get("w")
if not w:
    print("ERROR: Workspace 'w' not found in datacard")
    exit(1)

# Get data and mass variable
dataset = w.data("data_obs")
m = w.var("mass")

if not dataset or not m:
    print("ERROR: Could not find data_obs or mass variable in workspace")
    exit(1)

# Hard-coded parameter values to test
hardcoded_params = {
    "a0": 0.00336728,
    "a1": 0.0492368,
    "a2": 0.00465092,
    "a3": 0.743905,
    "a4": 0.840506,
    "alphaL_fit_par0": 0.717792,
    "alphaL_fit_par1": -0.0257102,
    "alphaR_fit_par0": 1.31732,
    "alphaR_fit_par1": 0.0175667,
    "eta_alphaL": 1.0806,
    "eta_alphaR": 1.0,
    "eta_mean": 0.376564,
    "eta_nL": 10.0,
    "eta_nR": 40.0,
    "eta_sigma": 0.0371016,
    "mean_fit_par0": 0.000393618,
    "mean_fit_par1": 0.998374,
    "nL_fit_par0": 2.92605,
    "nL_fit_par1": 0.0391294,
    "nR_fit_par0": 3.64544,
    "nR_fit_par1": -0.141911,
    "omega_alphaL": 0.852757,
    "omega_alphaR": 1.24513,
    "omega_mean": 0.781672,
    "omega_nL": 6.04529,
    "omega_nR": 2.42697,
    "omega_sigma": 0.0165227,
    "phi_alphaL": 0.883423,
    "phi_alphaR": 1.53324,
    "phi_mean": 1.01784,
    "phi_nL": 2.92206,
    "phi_nR": 3.12502,
    "phi_sigma": 0.013752,
    "r": 1.30046,
    "scale_dy_inclusive": 0.987433,
    "scale_eta_inclusive": 1.02599,
    "scale_omega_inclusive": 0.971992,
    "scale_phi_inclusive": 0.98441,
    "sigma_fit_par0": -0.00490639,
    "sigma_fit_par1": 0.0187522
}

print("\nApplying hard-coded parameter values...")
for param_name, param_value in hardcoded_params.items():
    # Try with category suffix first
    param_var = w.var(f"{param_name}_Xee_ee_{cat_id}_2023")
    if not param_var:
        # Try without suffix
        param_var = w.var(param_name)
    
    if param_var:
        param_var.setVal(param_value)
        print(f"  Set {param_name} = {param_value}")
    else:
        print(f"  Warning: Could not find parameter {param_name}")

# Get PDFs for each component
all_funcs = resonant_bkgs + ["dy", "Zd"]

# Get normalization variables
norm_vars = {}
for bkg in resonant_bkgs:
    # Try different naming conventions
    norm_name_variants = [
        f"n_exp_binXee_ee_{cat_id}_2023_proc_{bkg}",  # ProcessNormalization format
        f"n{bkg}_Xee_ee_{cat_id}_2023",                # Old format
        f"n{bkg}",                                      # Simple format
    ]
    
    norm_var = None
    for norm_name in norm_name_variants:
        norm_var = w.function(norm_name)  # Try as function first (ProcessNormalization)
        if not norm_var:
            norm_var = w.var(norm_name)    # Then as variable
        if norm_var:
            print(f"Found normalization for {bkg}: {norm_name} = {norm_var.getVal():.1f}")
            break
    
    if norm_var:
        norm_vars[bkg] = norm_var
    else:
        print(f"Warning: Could not find normalization variable for {bkg}")

# Get DY normalization
dy_norm_variants = [
    f"n_exp_binXee_ee_{cat_id}_2023_proc_dy",
    f"ndy_Xee_ee_{cat_id}_2023",
    "ndy",
]

ndy = None
for norm_name in dy_norm_variants:
    ndy = w.function(norm_name)
    if not ndy:
        ndy = w.var(norm_name)
    if ndy:
        print(f"Found DY normalization: {norm_name} = {ndy.getVal():.1f}")
        break

if ndy:
    norm_vars["dy"] = ndy

# Get signal normalization (r parameter)
r = w.var("r")
if not r:
    print("Warning: Could not find r parameter, creating it")
    r = ROOT.RooRealVar("r", "signal strength", 1.0, -10, 10)
    
# r should already be set from hardcoded_params, but confirm
print(f"\nSignal strength r = {r.getVal():.6f}")

# Get PDFs
pdfs = {}
for func_name in all_funcs:
    # Try different naming conventions
    pdf_name_variants = []
    
    if func_name == "Zd":
        # Signal PDF
        pdf_name_variants = [
            f"shapeSig_Zd_Xee_ee_{cat_id}_2023",
            f"Zd_Xee_ee_{cat_id}_2023",
            "Zd",
        ]
    elif func_name == "dy":
        # DY background PDF
        pdf_name_variants = [
            f"shapeBkg_dy_Xee_ee_{cat_id}_2023",
            f"dy_Xee_ee_{cat_id}_2023",
            f"bkg_f1_Xee_ee_{cat_id}_2023",  # Bernstein polynomial
            "dy",
        ]
    else:
        # Resonant backgrounds (phi, omega, eta, jpsi, psi2s, upsilon1s)
        pdf_name_variants = [
            f"shapeBkg_{func_name}_Xee_ee_{cat_id}_2023",
            f"{func_name}_Xee_ee_{cat_id}_2023",
            func_name,
        ]
    
    pdf = None
    for pdf_name in pdf_name_variants:
        pdf = w.pdf(pdf_name)
        if pdf:
            print(f"Found PDF for {func_name}: {pdf_name}")
            break
    
    if pdf:
        pdfs[func_name] = pdf
    else:
        print(f"Warning: Could not find PDF for {func_name}")

# Create combined background model
bkg_pdfs = ROOT.RooArgList()
bkg_norms = ROOT.RooArgList()
for bkg in resonant_bkgs + ["dy"]:
    if bkg in pdfs and bkg in norm_vars:
        bkg_pdfs.add(pdfs[bkg])
        bkg_norms.add(norm_vars[bkg])

full_bkg_model = ROOT.RooAddPdf("full_bkg_model", "Full Background", bkg_pdfs, bkg_norms)

# Create signal+background model
if "Zd" in pdfs:
    # Get expected signal yield
    sig_norm_variants = [
        f"n_exp_binXee_ee_{cat_id}_2023_proc_Zd",
        f"nZd_Xee_ee_{cat_id}_2023",
        "nZd",
    ]
    
    sig_norm = None
    for norm_name in sig_norm_variants:
        sig_norm = w.function(norm_name)
        if not sig_norm:
            sig_norm = w.var(norm_name)
        if sig_norm:
            print(f"Found signal normalization: {norm_name} = {sig_norm.getVal():.1f}")
            break
    
    if sig_norm:
        # Scale signal by r parameter
        scaled_sig_norm = ROOT.RooProduct("scaled_sig_norm", "r * nZd", ROOT.RooArgList(r, sig_norm))
        
        # Create S+B model
        sb_pdfs = ROOT.RooArgList(full_bkg_model, pdfs["Zd"])
        sb_norms = ROOT.RooArgList(bkg_norms.at(0), scaled_sig_norm)  # Use first bkg norm as reference
        
        # For extended model, sum all background norms
        total_bkg_norm = None
        if bkg_norms.getSize() > 0:
            norm_list = [bkg_norms.at(i) for i in range(bkg_norms.getSize())]
            total_bkg_norm = ROOT.RooAddition("total_bkg_norm", "Total Background Norm", ROOT.RooArgList(*norm_list))
        
        full_sb_model = ROOT.RooAddPdf("full_sb_model", "Signal + Background", 
                                       ROOT.RooArgList(pdfs["Zd"], full_bkg_model),
                                       ROOT.RooArgList(scaled_sig_norm, total_bkg_norm))
    else:
        print("Warning: Could not find signal normalization, using background only")
        full_sb_model = full_bkg_model
else:
    print("Warning: Could not find signal PDF, using background only")
    full_sb_model = full_bkg_model

# Draw
ROOT.gROOT.SetBatch()

colors = [
    "#3f90da",
    "#ffa90e",
    "#bd1f01",
    "#94a4a2",
    "#832db6",
    "#a96b59",
    "#e76300",
]

c = ROOT.TCanvas("c", "c", 800, 800)

# Split canvas between 70% for plot and 30% for pulls
c.Divide(1, 2)
c.cd(1)
ROOT.gPad.SetPad(0, 0.3, 1, 1)
ROOT.gPad.SetBottomMargin(0.001)
ROOT.gPad.SetGrid()
c.cd(2)
ROOT.gPad.SetPad(0, 0, 1, 0.3)
ROOT.gPad.SetGrid()

c.cd(1)

frame = m.frame(mass_range[0], mass_range[1])
frame.SetTitle("")
frame.GetXaxis().SetTitle("m(ee) [GeV]")

# Plot data
dataset.plotOn(frame, ROOT.RooFit.DataError(ROOT.RooAbsData.SumW2), ROOT.RooFit.MarkerSize(0.5))

# Plot models
# Plot background components
for idx, bkg in enumerate(resonant_bkgs + ["dy"]):
    if bkg in pdfs and bkg in norm_vars:
        pdfs[bkg].plotOn(frame, 
                        ROOT.RooFit.LineColor(ROOT.TColor.GetColor(colors[idx])),
                        ROOT.RooFit.Normalization(norm_vars[bkg].getVal(), ROOT.RooAbsReal.NumEvent))

# Plot signal
if "Zd" in pdfs and sig_norm:
    sig_events = r.getVal() * sig_norm.getVal()
    pdfs["Zd"].plotOn(frame,
                     ROOT.RooFit.LineColor(ROOT.kBlack),
                     ROOT.RooFit.LineWidth(2),
                     ROOT.RooFit.Normalization(sig_events, ROOT.RooAbsReal.NumEvent))

# Plot total S+B
full_sb_model.plotOn(frame, 
                    ROOT.RooFit.LineColor(ROOT.kRed),
                    ROOT.RooFit.LineWidth(2),
                    ROOT.RooFit.LineStyle(ROOT.kDashed))

frame.Draw()
ROOT.gPad.SetLogy()

# Calculate chi2
data_h = dataset.createHistogram("data_hist", m, ROOT.RooFit.Binning(100))
data_h.Sumw2()

# Create histogram from full model for chi2 calculation
full_sb_hist = full_sb_model.createHistogram("full_sb_hist", m, ROOT.RooFit.Binning(100))
# Scale by data integral
total_events = dataset.sumEntries()
full_sb_hist.Scale(total_events / full_sb_hist.Integral())

chi2 = full_sb_hist.Chi2Test(data_h, "UU CHI2")
n_free_params = 6  # Approximate: r + 5 background params
reduced_chi2 = chi2 / (100 - 1 - n_free_params)

# Make legend
legend = ROOT.TLegend(0.55, 0.5, 0.88, 0.88)
legend.SetFillStyle(0)
legend.SetBorderSize(0)
legend.SetTextSize(0.03)
legend.AddEntry(dataset, "Data", "p")
legend.AddEntry(full_sb_hist, f"Total S+B (#mu={r.getVal():.2f})", "l")

# Add signal
if "Zd" in pdfs:
    legend.AddEntry("", f"Signal = {sig_events:.1f}", "")

# Add backgrounds
for bkg, label in zip(resonant_bkgs + ["dy"], bkg_labels):
    if bkg in norm_vars:
        legend.AddEntry("", f"{label} = {norm_vars[bkg].getVal():.0f}", "")

legend.AddEntry("", f"#chi^{{2}}/ndf = {reduced_chi2:.2f}", "")
legend.Draw()

frame.SetMinimum(region_config[args.region]["y_min"])
frame.SetMaximum(region_config[args.region]["y_max"])

c.cd(2)
# Compute pulls
pulls = ROOT.TGraphAsymmErrors()

for i in range(100):
    x = data_h.GetBinCenter(i + 1)
    y = full_sb_hist.GetBinContent(i + 1)
    data_y = data_h.GetBinContent(i + 1)
    data_y_err = data_h.GetBinError(i + 1)

    pull_value = 0
    if data_y_err > 0:
        pull_value = (data_y - y) / data_y_err
    else:
        print(f"WARNING: data_y_err is zero at bin {i+1}, setting pull to 0", flush=True)
    
    pulls.SetPoint(i, x, pull_value)
    pulls.SetPointError(i, 0, 0, 1, 1)

pulls.SetMarkerStyle(20)
pulls.SetMarkerSize(0.5)

# Change x-axis range to match the frame
pulls.GetXaxis().SetLimits(frame.GetXaxis().GetXmin(), frame.GetXaxis().GetXmax())
pulls.GetXaxis().SetTitle("m(ee) [GeV]")
pulls.GetXaxis().SetLabelSize(0.07)
pulls.GetXaxis().SetTitleSize(0.1)
pulls.GetYaxis().SetTitle("Pulls")
pulls.GetYaxis().SetLabelSize(0.07)
pulls.GetYaxis().SetTitleSize(0.1)
pulls.GetYaxis().SetTitleOffset(0.3)

# Change bottom padding
ROOT.gPad.SetBottomMargin(0.25)
pulls.Draw("AP E1")

# Draw horizontal line at 0
line = ROOT.TLine(frame.GetXaxis().GetXmin(), 0, frame.GetXaxis().GetXmax(), 0)
line.SetLineColor(ROOT.kGray)
line.SetLineStyle(2)
line.Draw("same")

# Save plots
for ext in ['png', 'pdf']:
    output_path = os.path.join(args.output_folder, f"custom_params_M{args.mass:.1f}_mu{r.getVal():.2f}{tag_label}.{ext}")
    c.SaveAs(output_path)
    print(f"Saved plot: {output_path}")

# Print parameter values
print("\nFinal parameter values used:")
print(f"  mu (r) = {r.getVal():.6f}")
dy_params = ["a0", "a1", "a2", "a3", "a4"]
for param_name in dy_params:
    param_var = w.var(f"{param_name}_Xee_ee_{cat_id}_2023")
    if not param_var:
        param_var = w.var(param_name)
    if param_var:
        print(f"  {param_name} = {param_var.getVal():.6f}")
        
# Print resonant background parameters
for res in resonant_bkgs:
    print(f"\n  {res} parameters:")
    for par_type in ["mean", "sigma", "alphaL", "alphaR", "nL", "nR"]:
        param_var = w.var(f"{res}_{par_type}")
        if param_var:
            print(f"    {par_type} = {param_var.getVal():.6f}")
            
for bkg in resonant_bkgs + ["dy"]:
    if bkg in norm_vars:
        print(f"  n{bkg} = {norm_vars[bkg].getVal():.1f}")

# Close files
f_datacard.Close()
