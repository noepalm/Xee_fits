### tighter cuts, new signal, PU reweight
mkdir -p logs/260430
# for era in 2022; do
for era in 2022; do
    time python3 main_oo.py --full --delete_ws --use_reco_mass \
                    --no_categories --syst \
                    --no_plots \
                    --era "$era" \
                    --folder_tag "260430" \
                    --copy_eos --tag="allCorrections_simultaneousFit" &> logs/260430/log_reco_allCorrections_simultaneousFit_era${era}.log
    time python3 main_oo.py --plots --use_reco_mass \
                    --no_categories --syst \
                    --era "$era" \
                    --folder_tag "260430" \
                    --copy_eos --tag="allCorrections_simultaneousFit" &> logs/260430/log_reco_allCorrections_simultaneousFit_era${era}_plotting.log
done
                    # --nuisanced_vars_stat sigma nL nR alphaL alphaR \
                    # --weight_nuisanced_vars mean:pileupReweight,electronID,triggerSF1DCorrection sigma:pileupReweight,electronID,triggerSF1DCorrection alphaL:pileupReweight,electronID,triggerSF1DCorrection alphaR:pileupReweight,electronID,triggerSF1DCorrection nR:pileupReweight,electronID,triggerSF1DCorrection nL:pileupReweight,electronID,triggerSF1DCorrection \

                    # --nuisanced_vars mean:electronScaleVariation \
                    # --nuisanced_vars_stat sigma \
