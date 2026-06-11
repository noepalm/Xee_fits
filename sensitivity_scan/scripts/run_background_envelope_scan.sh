#!/usr/bin/env bash

region_dirs=(
    "/eos/home-n/npalmeri/DiEleAnalyzer/Xee_fits/sensitivity_scan/cards/260404/cards_region0_data_envelope_withScaleSyst_withMeanNuisance_IDSF_triggerSF_finerBinning_tighterCuts_PUreweight_signalEnvelope_bySubera_binned/ee/1.8"
    "/eos/home-n/npalmeri/DiEleAnalyzer/Xee_fits/sensitivity_scan/cards/260404/cards_region1_data_envelope_withScaleSyst_withMeanNuisance_IDSF_triggerSF_finerBinning_tighterCuts_PUreweight_signalEnvelope_bySubera_binned/ee/3.3"
    "/eos/home-n/npalmeri/DiEleAnalyzer/Xee_fits/sensitivity_scan/cards/260404/cards_region2_data_envelope_withScaleSyst_withMeanNuisance_IDSF_triggerSF_finerBinning_tighterCuts_PUreweight_signalEnvelope_bySubera_binned/ee/5.8"
)

ranges=(
    "-30,10"
    "-10,4"
    "-5,5"
)

# for running trigger10percent test: 
# - process Xee_ee_4_allYears_triggerSF10percent.root
# - add _triggerSF10percent suffix to -n (after bkgEnvelope)
# - add --tag triggerSF10percent argument to plot_nll_scan.py

plot_dir="/eos/home-n/npalmeri/www/DiElectron/sensitivity/260404/fitDiagnostics_grid_data_envelope_withScaleSyst_withMeanNuisance_IDSF_triggerSF_finerBinning_tighterCuts_PUreweight_signalEnvelope_bySubera_binned/nll_scans/bkg_envelope/triggerSF_50percent"
WORKDIR="$(pwd)"

# for region in 1; do
for region in 0 1 2; do
    cd "${region_dirs[$region]}" || exit 1
    range="${ranges[$region]}"

    # full envelope
    combine -M MultiDimFit Xee_ee_4_allYears.root --algo grid --setParameterRanges r=${range} --points 30 \
            --setParameters signal_model_index_2022=0,signal_model_index_2022EE=0,signal_model_index_2023=0,signal_model_index_2023BPix=0 \
            --freezeParameters signal_model_index_2022,signal_model_index_2022EE,signal_model_index_2023,signal_model_index_2023BPix \
            --cminDefaultMinimizerStrategy 0 --saveNLL \
            -n .nll_scan_bkgEnvelope \
            --X-rtd MINIMIZER_freezeDisassociatedParams \
            --X-rtd REMOVE_CONSTANT_ZERO_POINT=1 -v 0

    for i in {0..1}; do
        combine -M MultiDimFit Xee_ee_4_allYears.root --algo grid --setParameterRanges r=${range} --points 30 \
                --setParameters signal_model_index_2022=0,signal_model_index_2022EE=0,signal_model_index_2023=0,signal_model_index_2023BPix=0,pdf_index_2022_envelope=$i,pdf_index_2022EE_envelope=$i,pdf_index_2023_envelope=$i,pdf_index_2023BPix_envelope=$i \
                --freezeParameters signal_model_index_2022,signal_model_index_2022EE,signal_model_index_2023,signal_model_index_2023BPix,pdf_index_2022_envelope,pdf_index_2022EE_envelope,pdf_index_2023_envelope,pdf_index_2023BPix_envelope \
                --cminDefaultMinimizerStrategy 0 --saveNLL \
                -n .nll_scan_bkgEnvelope_idx${i} \
                --X-rtd MINIMIZER_freezeDisassociatedParams \
                --X-rtd REMOVE_CONSTANT_ZERO_POINT=1 -v 0
    done

    python3 /eos/home-n/npalmeri/DiEleAnalyzer/Xee_fits/sensitivity_scan/scripts/utilities/plot_nll_scan.py \
            -o "${plot_dir}/nll_scan_bkg_region${region}.png"
done

cd "${WORKDIR}" || exit 1