import os
import csv
import unicodedata

# iterate over samples in the folder (one .csv file per sample)
input_folder = "/eos/home-n/npalmeri/www/DiElectron/signal_model/fw_output/signal_model_reweighted/ztables/era2023/base_9_GenMatching/csv"

def clean_string(s):
    # Convert subscript/superscript characters to normal characters
    cleaned = unicodedata.normalize("NFKC", s.strip("%")).replace("−", "-").replace(" ̇", ".").strip() #that minus...
    # split central value, minus error and plus error
    central = float(cleaned.split("-")[0])
    lower_err = float(cleaned.split("-")[1].split("+")[0])
    upper_err = float(cleaned.split("-")[1].split("+")[1])

    return (central, lower_err, upper_err)

def retrieve_efficiencies(input_folder):
    ID_efficiencies = {}
    reweight_efficiencies = {}
    for filename in os.listdir(input_folder):
        if filename.endswith(".csv"):
            with open(os.path.join(input_folder, filename), 'r') as csvfile:
                reader = csv.reader(csvfile, delimiter=",")
                header = next(reader)

                # scan rows until we find the ID one (second entry)
                for row in reader:
                    if row[1] == "ID":
                        # retrieve cumulative selection efficiency at that step
                        ID_efficiencies[filename.replace('.csv', '')] = clean_string(row[5])
                    elif row[1] == "TriggerPSReweight":
                        # retrieve cumulative selection efficiency at that step
                        reweight_efficiencies[filename.replace('.csv', '')] = clean_string(row[5])
    
    return {"ID_efficiencies": ID_efficiencies, "reweight_efficiencies": reweight_efficiencies}

if __name__ == "__main__":
    efficiencies = retrieve_efficiencies(input_folder)
    print("ID Efficiencies:", efficiencies["ID_efficiencies"])
    print("Reweight Efficiencies:", efficiencies["reweight_efficiencies"])