# full envelope
combine -M MultiDimFit Xee_ee_4_allYears.root --algo grid --setParameterRanges r=-1.5,1 --points 15 \
        --setParameters signal_model_index_2022={$i},signal_model_index_2022EE={$i},signal_model_index_2023={$i},signal_model_index_2023BPix={$i} \
        --freezeParameters signal_model_index_2022,signal_model_index_2022EE,signal_model_index_2023,signal_model_index_2023BPix \
        --cminDefaultMinimizerStrategy 0 --saveNLL \
        -n .nll_scan_bkgEnvelope \
        --X-rtd MINIMIZER_freezeDisassociatedParams \
        --X-rtd REMOVE_CONSTANT_ZERO_POINT=1 -v 0

for i in {0..2}; do
    combine -M MultiDimFit Xee_ee_4_allYears.root --algo grid --setParameterRanges r=-1.5,1 --points 15 \
            --setParameters signal_model_index_2022=0,signal_model_index_2022EE=0,signal_model_index_2023=0,signal_model_index_2023BPix=0,pdf_index_2022_envelope=$i,pdf_index_2022EE_envelope=$i,pdf_index_2023_envelope=$i,pdf_index_2023BPix_envelope=$i \
            --freezeParameters signal_model_index_2022,signal_model_index_2022EE,signal_model_index_2023,signal_model_index_2023BPix,pdf_index_2022_envelope,pdf_index_2022EE_envelope,pdf_index_2023_envelope,pdf_index_2023BPix_envelope \
            --cminDefaultMinimizerStrategy 0 --saveNLL \
            -n .nll_scan_bkgEnvelope_idx$i \
		        --X-rtd MINIMIZER_freezeDisassociatedParams \
            --X-rtd REMOVE_CONSTANT_ZERO_POINT=1 -v 0
done
python3 /eos/home-n/npalmeri/DiEleAnalyzer/Xee_fits/sensitivity_scan/scripts/utilities/plot_nll_scan.py