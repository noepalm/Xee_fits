import argparse
import ROOT
import tarfile
import os

parser = argparse.ArgumentParser(description="Extract nanoprod efficiency from tar file")
parser.add_argument(
    "-f", 
    "--folder",
    type=str,
    required=True,
    help="Path to the folder to look for tar files",
    default = "/eos/cms/store/cmst3/group/xee/backgroundSamples/allnanoColl/InclusiveDileptonMinBias_TuneCP5Plus_13p6TeV_pythia8/crab_InclusiveDileptonMinBias/250415_163927/0000/log"
)

args = parser.parse_args()

total = 0
passed = 0

log = open("nanoprod_efficiency.log", "w")

print("Probing ", args.folder)

for file in os.listdir(args.folder):
    if file.endswith(".tar.gz"):
        tar_path = os.path.join(args.folder, file)
        with tarfile.open(tar_path, "r") as tar:
            for member in tar.getmembers():
                if member.name.startswith("cmsRun-stdout"):
                    # read file content
                    f = tar.extractfile(member)
                    if f is None:
                        print(f"Could not extract {member.name} from {file}")
                        continue
                    content = f.readlines()[::-1]
                    # find line "Event   Summary"
                    for line in content:
                        if b"TrigReport Events total" in line:
                            total_number = int(line.decode("utf-8").split("total = ")[1].split()[0].strip())
                            passed_number = int(line.decode("utf-8").split("passed = ")[1].split()[0].strip())

                            total += total_number
                            passed += passed_number

                            log.write(f"{file} {member.name} total: {total_number}, passed: {passed_number}\n")

                            break

# compute efficiency with ROOT
if total > 0:
    eff = passed / total
    low_boundary = ROOT.TEfficiency.ClopperPearson(total, passed, 0.683, False)
    high_boundary = ROOT.TEfficiency.ClopperPearson(total, passed, 0.683, True)
else:
    raise ValueError("Total number of events is zero, cannot compute efficiency.")

print(f"Total events: {total}, Passed events: {passed}\n")
print(f"Efficiency: {eff:.3g} + {high_boundary - eff:.3g} - {low_boundary - eff:.3g}\n")

# save final efficiency to file
log.write("-------------------------------\n")
log.write(f"Total events: {total}, Passed events: {passed}\n")
log.write(f"Efficiency: {eff:.3g} + {high_boundary - eff:.3g} - {low_boundary - eff:.3g}\n")
log.close()