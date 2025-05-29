import ROOT

f = ROOT.TFile.Open(f"workspaces/workspace_background.root")
w_bkg = f.Get("w_bkg")

### Define MULTIPDF
for region in ["Region2", "Region3"]:
    cat = ROOT.RooCategory(f"pdfindex_{region}", f"Index of Pdf which is active for {region}")
    
    models = ROOT.RooArgList()
    models.add(w_bkg.obj(f"bkg_f0_{region}"))
    models.add(w_bkg.obj(f"bkg_f1_{region}"))
    models.add(w_bkg.obj(f"bkg_f2_{region}"))
    models.add(w_bkg.obj(f"bkg_f3_{region}"))

    multipdf = ROOT.RooMultiPdf(f"multipdf_{region}", f"MultiPdf for {region}", cat, models)
    w_bkg.Import(multipdf)

# Retrive signal model from dataset_minbias.root
signal_ws_file = '../signal_modelling/workspaces/signal_model.root'
w = ROOT.TFile.Open(signal_ws_file).Get('w')
signal_model = w.obj("model_test_M6p0")
# convert to pdf (pyroot does not do this automatically)

w_bkg.Import(signal_model, ROOT.RooFit.Rename(signal_model.GetName()))

w_bkg.writeToFile("workspaces/workspace_bkg_multipdf.root")