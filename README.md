# Xee_fits
Code for signal modelling, background modelling and then perform fits for Xee analysis.


# Signal modelling
Uses output from `cmgrdf-cli`. With current configuration, it expects all signal models to have been processed + prompt Y(1S) sample (actually used) and $J/\psi$ sample (for comparison). 

### Usage
Typical command:
```bash
python3 main.py --full --no_compare_response --copy_eos
```
You can run the full chain (see below) with argument `--full` (note: this includes the debug Zd vs Jpsi plot above; it's recommended to exclude it with argument `--no_compare_response`). You can exclude ~any individual step with the appropriate arguments.

Make sure to change, in `main.py`:
 - input file location
 - EOS output folder for plots

### What it does
 - Fits (depending on configuration) the reduced mass OR reconstructed mass distribution for all signal model peaks + Y(1S) with a double Crystal Ball;
 - (Optional) convolutes the above distribution with a Breit-Wigner (which can be fit to the GEN mass distribution or kept fixed to nominal mass/width values);
 - performs a linear fit in the dCB parameters to interpolate/extrapolate for any mass value;
 - **[MAIN OUTPUT]** constructs and saves parametric signal models for a given set of mass values -- to be used in next steps;
 - plots the predicted parametric model vs. the reconstructed mass distribution for all of the available samples;
 - (for debugging purposes) plot the reduced and reconstructed mass distribution for the $Z_D$ @ $M=3.1 \text{GeV}$ sample and for the $J/\psi$ one to visualize shape difference. 


# Background modelling