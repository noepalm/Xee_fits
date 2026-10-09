import ROOT
from pathlib import Path

resonances = {
    "region0" : ["omega", "phi"],
    "region1" : ["jpsi", "psi2s"],
    "region2" : ["upsilon1s", "upsilon2s"]
}

eras = ["2022", "2022EE", "2023", "2023BPix"]

true_mass_values = {
    "omega" : 0.78265,
    "phi" : 1.019461,
    "jpsi" : 3.0969,
    "psi2s" : 3.6861,
    "upsilon1s" : 9.46030,
    "upsilon2s" : 10.02326
}

mass_examples = {
    "region0" : "1.0",
    "region1" : "3.5",
    "region2" : "9.0"
}

BASE_DIR = Path("/eos/home-n/npalmeri/DiEleAnalyzer/Xee_fits/sensitivity_scan/cards/260828")

results = {}
for res_list in resonances.values():
    for res in res_list:
        results[res] = {}

for region, res_list in resonances.items():
    region_subfolder = BASE_DIR / f"cards_{region}_data_envelope_allCorrections_binned"    
    mass_subfolder = region_subfolder / f"ee/{mass_examples[region]}"
    f = ROOT.TFile.Open(str(mass_subfolder / "Xee_ee_4_allYears.root"))
    w = f.Get("w")
    for res in res_list:
        for era in eras:
            wvar = w.var(f"{res}_mean_{era}")
            results[res][era] = wvar.getVal()

# print results
for region, res_list in resonances.items():
    for res in res_list:
        print(f"  Resonance: {res}")
        for era in eras:
            print(f"    Era: {era}, Mean: {results[res][era]:.4f} (diff wrt nominal = {results[res][era] - true_mass_values[res]:.4f} = {100*(results[res][era] - true_mass_values[res])/true_mass_values[res]:.4f}%)")