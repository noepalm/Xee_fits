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

**NB**: The mass values to scan for the S+B fit are specified here. If you want to do a coarser/finer scan, make sure to change the range here.

### What it does
 - Fits (depending on configuration) the reduced mass OR reconstructed mass distribution for all signal model peaks + Y(1S) with a double Crystal Ball;
 - (Optional) convolutes the above distribution with a Breit-Wigner (which can be fit to the GEN mass distribution or kept fixed to nominal mass/width values);
 - performs a linear fit in the dCB parameters to interpolate/extrapolate for any mass value;
 - **[MAIN OUTPUT]** constructs and saves parametric signal models for a given set of mass values -- to be used in next steps;
 - plots the predicted parametric model vs. the reconstructed mass distribution for all of the available samples;
 - (for debugging purposes) plot the reduced and reconstructed mass distribution for the $Z_D$ @ $M=3.1 \text{GeV}$ sample and for the $J/\psi$ one to visualize shape difference. 


# Background modelling
Uses output from `cmgrdf-cli` for inclusive minimum bias dilepton sample (currently, will eventually be replaced by data) and prompt $J/\psi$ sample; also uses file produced by signal modelling step.

The two main files are:
 - `create_dataset.py`: to be run twice, once with `--use_jpsi` (JPsiToEE) and once without (MinBias). It creates a single RooWorkspace containing:
    - a (weighted) RooDataSet out of the snapshot saved by CMGRDF. **NB**: currently there is a hard-coded weight rescaling to normalize the min bias dataset to expected number of events for $58.9\,\text{fb}^{-1}$. Remove it to keep the normalization as the one set in CMGRDF.
    - all signal models produced in the previous step;
    - signal efficiency and production cross-section for signal models, as interpolated from values measured on available MC samples. Efficiencies are retrieved from the .csv file produced by CMGRDF (assumes no skimming done for producing the NANOAODs); cross-sections are hard-coded and fixed to the values reported on the analysis wiki.
 - `bkg_test.py`: 
    - actually performs the background-only fit. In its final version, it will be able to perform background-only fit for the 3 intended mass regions, including a non-resonant background component (to be fit with 3 different function families, for later inclusion in an envelope) and a resonant component for each SM resonance included in the range. For now, it only works in the central region ([2.6, 4.2] GeV) and only fits a 4-th degree Bernstein function as non-resonant component.
    - The current fit is performed in the following steps:
        - Fit the $J/\psi$, $\psi(2S)$ peaks by themselves on the `JPsiToEE` sample with double Crystal Ball functions. The shape is frozen to the parameters obtained here.
        - Fit $J/\psi$, $\psi(2S)$ sidebands with the non-resonant function by itself, with parameters obtained from this step used as initialization for the last one.
        - Fit $J/\psi + \psi(2S)$ + non-resonant background in the whole central region.
    - While this fit step is not strictly necessary, it serves as a useful initialization for the full S+B fit.

Several fit debug options are included.

# Sensitivity scan
Uses as input the RooWorkspace produced by the background modelling step. It performs the actual FitDiagonistics and AsymptoticLimit estimations. 

You first need to setup the Combine environment to run it -- follow the [instructions for Combine v10](https://cms-analysis.github.io/HiggsAnalysis-CombinedLimit/latest/#combine-v10-recommended-version).

After you have `cmsenv`'d there, you can run the rest of the code here. A convenience `setup.sh` is included once you have changed the folder location to your Combine CMSSW installation.

The datacards and final RooWorkspace for Combine are crated by running:
```bash
python3 make_combine_workspace.py
```

All main scans are then performed by scripts, including:
- `run_diagostics_parallel.sh`: runs FitDiagnostics, hence fitting S+B for all given mass points. It runs one fit per mass value. It also produces the corresponding plots for the fit and a summary plot with the best fit value for $\mu$ for each mass point. Analogous versions of the script are available that also perform a S+B fit after injecting signal at $\mu = 1$ (`run_diagnostics_mu1_parallel.sh`) and $\mu=10$ (`run_diagnostics_mu10_parallel.sh`).
- `run_limits_parallel.sh`: estimates upper limits on $\mu$. It also produces the limits plot on $\mu$ and its corresponding model-independent version (limited converted to $\sigma \cdot \mathcal(B) \cdot \epsilon$). 
