import ROOT
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('-i', '--input', type=str, default='fitDiagnosticsTest.root', help='Input file containing B-only fit results')
args = parser.parse_args()

f_input = ROOT.TFile.Open(args.input, "READ")
fit_res = f_input.Get("fit_b").floatParsFinal()
# save all vars to dictionary
fit_vars = {var.GetName(): var.getValV() for var in fit_res if var != "r"}

print(','.join([f'{name}={val}' for name, val in fit_vars.items()]))

f_input.Close()