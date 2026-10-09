#!/usr/bin/env python3
import argparse
import sys
import ROOT

def extract_toy(input_file, output_file, toy_index):
    # Prevent ROOT auto-garbage collection issues
    ROOT.TH1.AddDirectory(False)
    
    f_in = ROOT.TFile.Open(input_file, "READ")
    if not f_in or f_in.IsZombie():
        print(f"Error: Could not open input file '{input_file}'")
        sys.exit(1)

    dir_name = "toys"
    d_in = f_in.Get(dir_name)
    if not d_in:
        print(f"Error: Directory '{dir_name}' not found in '{input_file}'")
        f_in.Close()
        sys.exit(1)

    source_toy_name = f"toy_{toy_index}"
    target_toy_name = "toy_1"
    
    # Read specifically the target object key
    toy_key = d_in.GetKey(source_toy_name)
    if not toy_key:
        print(f"Error: Key '{source_toy_name}' not found in '{dir_name}/' of '{input_file}'")
        f_in.Close()
        sys.exit(1)

    # Read target RooDataSet into memory
    toy = toy_key.ReadObj()
    if not toy or not toy.InheritsFrom("RooAbsData"):
        print(f"Error: Object '{source_toy_name}' is not a RooDataSet/RooAbsData")
        f_in.Close()
        sys.exit(1)

    # Set external object name AND clone with target_toy_name ('toy_1')
    # Both are set to make sure RooDataSet internal attributes match the TKey name
    toy.SetName(target_toy_name)
    toy_clone = toy.Clone(target_toy_name)

    # Open target output file
    f_out = ROOT.TFile.Open(output_file, "RECREATE")
    if not f_out or f_out.IsZombie():
        print(f"Error: Could not create output file '{output_file}'")
        f_in.Close()
        sys.exit(1)

    # Recreate the exact 'toys' subfolder
    d_out = f_out.mkdir(dir_name)
    d_out.cd()

    # Write the renamed cloned dataset as 'toy_1'
    toy_clone.Write(target_toy_name, ROOT.TObject.kOverwrite)

    # Clean up and close
    f_out.Close()
    f_in.Close()
    
    print(f"Success: '{source_toy_name}' extracted, renamed to '{target_toy_name}', and saved to '{output_file}/{dir_name}/{target_toy_name}'")

if __name__ == "__main__":
    ROOT.PyConfig.IgnoreCommandLineOptions = True
    ROOT.gROOT.SetBatch(True)

    parser = argparse.ArgumentParser(description="Extract a single Combine toy and rename it to 'toy_1' for Combine compatibility.")
    parser.add_argument("-i", "--input", required=True, help="Path to input ROOT file")
    parser.add_argument("-o", "--output", required=True, help="Path to output ROOT file")
    parser.add_argument("-t", "--toy", required=True, type=int, help="Toy index number to extract (e.g. 5 for 'toy_5')")

    args = parser.parse_args()

    extract_toy(args.input, args.output, args.toy)