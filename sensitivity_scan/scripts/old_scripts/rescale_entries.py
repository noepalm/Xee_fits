import ROOT
import argparse

parser = argparse.ArgumentParser(description="Inject a signal into a RooWorkspace")
parser.add_argument('-i', '--input', type=str, required=True, help='Input RooWorkspace file')
parser.add_argument('-o', '--output', type=str, required=True, help='Output file name for the modified RooWorkspace')
parser.add_argument('-n', '--number', type=int, default=60000, help='Number of entries to rescale to')

args = parser.parse_args()

# Open the input file
input_file = ROOT.TFile.Open(args.input, "READ")
# Get the workspace
w = input_file.Get("w")
# Retrieve the datasetq
data = w.data("data_obs")

# Get the number of entries in the dataset
num_entries = data.numEntries()
# compute sum of weights
sum_weights = data.sumEntries()

# Calculate the scaling factor
scale = args.number / sum_weights if sum_weights > 0 else 0

# create new scaled dataset
data_scaled = ROOT.RooDataSet("data_obs", "data_obs", ROOT.RooArgSet(data.get()), ROOT.RooFit.WeightVar(data.weightVar()))

# Rescale the dataset
for i in range(num_entries):
    entry = data.get(i)
    weight = data.weight() * scale
    data_scaled.add(entry, weight)

print("New sum of entries = ", data_scaled.sumEntries())

# Import dataset into the workspace
# remove old dataset
w.RecursiveRemove(w.data("data_obs"))
w.Import(data_scaled)

# retrieve dataset again; check etriesthat sum of entries is now correct
print("Saved correctly?  Sum of  = ", w.data("data_obs").sumEntries())


### retrieve all ProcessNormalization vars, rescale them and re-import them
process_norms = [var for var in w.allVars() if "ProcessNormalization" in var.GetName()]
for norm in process_norms:
    # rescale the normalization variable
    print(norm)
    # norm.setVal(norm.getVal() * scale)
    # # re-import the variable into the workspace
    # w.Import(norm, True)

if w.data("data_obs").sumEntries() > 60001: 
    print("ERROR: dataset not imported correctly. Aborting.")
    exit()

# Save the modified workspace to a new file
w.writeToFile(args.output)
