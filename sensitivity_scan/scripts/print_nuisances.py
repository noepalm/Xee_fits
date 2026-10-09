import ROOT
import argparse

parser = argparse.ArgumentParser(description="Print constrained nuisances from a combine workspace")
parser.add_argument("-i", "--input", required=True, help="Input workspace ROOT file")
parser.add_argument("-w", "--workspace", default="w", help="Name of the workspace object (default: 'w')")
args = parser.parse_args()

ROOT.gROOT.SetBatch(True)
# Suppress RooFit info messages
ROOT.RooMsgService.instance().setGlobalKillBelow(ROOT.RooFit.WARNING)

f = ROOT.TFile(args.input)
if not f or f.IsZombie():
    raise RuntimeError(f"Could not open {args.input}")

w = f.Get(args.workspace)
if not w:
    raise RuntimeError(f"Could not find workspace '{args.workspace}' in {args.input}")

mc = w.obj("ModelConfig")
if not mc:
    raise RuntimeError("Could not find ModelConfig in workspace")

nuisances = mc.GetNuisanceParameters()

if not nuisances or nuisances.getSize() == 0:
    print("No constrained nuisance parameters found in the ModelConfig.")
else:
    print(f"Found {nuisances.getSize()} constrained nuisance parameters:")
    
    # Iterate through the RooArgSet and print the names
    iterator = nuisances.createIterator()
    var = iterator.Next()
    while var:
        print(f"  - {var.GetName()}")
        var = iterator.Next()