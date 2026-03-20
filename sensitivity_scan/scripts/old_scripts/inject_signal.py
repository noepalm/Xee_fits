# python3 &BASEDIR/scripts/inject_signal.py -i Xee_ee_0_2023.root -m $mass -o Xee_ee_0_2023_injected.root

import ROOT
import argparse

parser = argparse.ArgumentParser(description="Inject a signal into a RooWorkspace")
parser.add_argument('-i', '--input', type=str, required=True, help='Input RooWorkspace file')
parser.add_argument('-m', '--mass', type=float, required=True, help='Mass of the signal to inject')
parser.add_argument('-o', '--output', type=str, required=True, help='Output file name for the modified RooWorkspace')
parser.add_argument('--mu', type=float, default=1, help='Signal strength for injection')

args = parser.parse_args()

# Open the input file
input_file = ROOT.TFile.Open(args.input, "READ")

# Get the workspace
w = input_file.Get("w")

# retrieve dataset
data = w.data("data_obs")

# retrieve signal model 
# model_s = w.pdf("model_s")
model_s = w.pdf("shapeSig_Zd_Xee_ee_0_2023")
# retrieve signal normalization
sig_exp = w.function("n_exp_binXee_ee_0_2023_proc_Zd").getVal()
print(f"Injecting {args.mu} * {sig_exp} expected events at mass {args.mass} GeV")

# generate a binned dataset with the signal model
mass = w.var("mass")
signal_dataset = model_s.generate(ROOT.RooArgSet(mass), ROOT.RooFit.NumEvents(int(sig_exp * args.mu)))
data.append(signal_dataset)
# # now add points to data, but reweight by 100 (can get same expected events while generating 1/100 the events)
# for i in range(signal_dataset.numEntries()):
#     mass.setVal(signal_dataset.get(i).getRealValue("mass"))
#     data.add(mass, 100)

# # add the signal dataset to the workspace
# for i in range(signal_dataset.numEntries()):
#     mass.setVal(signal_dataset.get(i).getRealValue("mass"))
#     wgt = signal_dataset.weight(i) * 58.9 / 7.98  # rescale to match the expected number of events
#     data.add(mass, wgt)

w.Import(data, True)

# Save the modified workspace to a new file
output_file = ROOT.TFile.Open(args.output, "RECREATE")
w.Write()
output_file.Close()