import ROOT
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# infolder = Path("/eos/home-n/npalmeri/DiEleAnalyzer/combine/CMSSW_14_1_0_pre4/src/my_analysis/cards/ee/3.1")
# infolder = Path("/eos/home-n/npalmeri/DiEleAnalyzer/Xee_fits/sensitivity_scan/cards_noReweight_x100sgn/ee/2.5")
infolder = Path("/eos/home-n/npalmeri/DiEleAnalyzer/Xee_fits/sensitivity_scan/cards_noReweight_x2wgt/ee/3.5")
# infolder = Path("/eos/home-n/npalmeri/DiEleAnalyzer/Xee_fits/sensitivity_scan/cards_noReweight_div100wgt/ee/2.4")


# asimov_file = infolder / "higgsCombine_etaHigh.AsymptoticLimits.mH120.123456.root" # should be exactly the one used by asymptotic limit
# asimov_file = infolder / "higgsCombine_etaHigh_bonly_asimov.GenerateOnly.mH120.123456.root" # GENERATED, uses results of b-only MultiDimFit
# asimov_file = infolder / "higgsCombine_test.AsymptoticLimits.mH120.123456.root" # GENERATED, uses results of b-only MultiDimFit
asimov_file = infolder / "higgsCombine_inclusive_Bonly_asimov.GenerateOnly.mH120.123456.root" # GENERATED, uses results of b-only MultiDimFit
dataset_file = infolder / "Xee_ee_4_2023.root"
# dataset_file = infolder / "../common/Xee_ee.input.root" #same as above

asimov_dataset = ROOT.TFile.Open(str(asimov_file)).Get("toys/toy_asimov")
dataset = ROOT.TFile.Open(str(dataset_file)).Get("w").data("data_obs")
# dataset = ROOT.TFile.Open(str(dataset_file)).Get("w").data("data_obs_cat_etap0p6")

# get mass variable
m = dataset.get()[0]

asimov_dataset.Print()
dataset.Print()

# print("Asimov dataset points:")
# for i in range(asimov_dataset.numEntries()):
#     entry = asimov_dataset.get(i)
#     mass = entry.getRealValue(m.GetName())
#     value = asimov_dataset.weight()
#     print(f"Entry {i}: mass = {mass}, value = {value}")

# print("\nObserved dataset points:")
# for i in range(dataset.numEntries()):
#     entry = dataset.get(i)
#     mass = entry.getRealValue(m.GetName())
#     value = dataset.weight()
#     print(f"Entry {i}: mass = {mass}, value = {value}")

# create frame
frame = m.frame(ROOT.RooFit.Title("Asimov Dataset"))

# first, normalize the two datasets to the same number of events
# asimov_dataset_sum = asimov_dataset.sumEntries()
# dataset_sum = dataset.sumEntries()

asimov_dataset_sum = 1
dataset_sum = 1

asimov_dataset.plotOn(frame, ROOT.RooFit.Name("asimov"), 
                             ROOT.RooFit.LineColor(ROOT.kRed), 
                             ROOT.RooFit.MarkerColor(ROOT.kRed),
                             ROOT.RooFit.DataError(ROOT.RooAbsData.SumW2),
                             ROOT.RooFit.Rescale(1.0 / asimov_dataset_sum))
dataset.plotOn(frame, ROOT.RooFit.Name("data"),
                      ROOT.RooFit.LineColor(ROOT.kBlue), 
                      ROOT.RooFit.MarkerColor(ROOT.kBlue),
                      ROOT.RooFit.DataError(ROOT.RooAbsData.SumW2),
                      ROOT.RooFit.Rescale(1.0 / dataset_sum),)

# create canvas and plot
canvas = ROOT.TCanvas("canvas", "Asimov Dataset Comparison", 800, 600)
frame.Draw()

# change minimum
frame.SetMinimum(1e-4)

# draw legend
legend = ROOT.TLegend(0.6, 0.7, 0.9, 0.9)
legend.AddEntry(frame.findObject("asimov"), "Asimov Dataset", "l")
legend.AddEntry(frame.findObject("data"), "Observed Data", "l")
legend.SetBorderSize(0)
legend.SetFillColor(0)
legend.Draw()

# set log y scale
canvas.SetLogy()

# save the plot
output_file = infolder / "asimov_dataset_comparison.png"
canvas.SaveAs(str(output_file))
print(f"Plot saved to {output_file}")