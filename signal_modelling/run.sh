### tighter cuts, new signal, PU reweight
mkdir -p logs/260403
# for era in 2022; do
for era in 2022 2022EE 2023 2023BPix; do
    # time python3 main_oo.py --full --delete_ws --use_reco_mass \
    #                 --no_categories --syst \
    #                 --no_plots \
    #                 --era "$era" \
    #                 --envelope \
    #                 --nuisanced_vars mean:electronScaleVariation \
    #                 --nuisanced_vars_stat sigma \
    #                 --folder_tag "260403" \
    #                 --copy_eos --tag="nanov15_withScaleSyst_IDSF_triggerSF_tighterCuts_newSignal_PUreweight_envelope" &> logs/260403/log_reco_nanov15_withScaleSyst_IDSF_triggerSF_tighterCuts_newSignal_PUreweight_envelope_era${era}.log
    time python3 main_oo.py --plots --use_reco_mass \
                    --no_categories --syst \
                    --era "$era" \
                    --envelope \
                    --folder_tag "260403" \
                    --nuisanced_vars mean:electronScaleVariation \
                    --nuisanced_vars_stat sigma \
                    --copy_eos --tag="nanov15_withScaleSyst_IDSF_triggerSF_tighterCuts_newSignal_PUreweight_envelope" &> logs/260403/log_reco_nanov15_withScaleSyst_IDSF_triggerSF_tighterCuts_newSignal_PUreweight_envelope_era${era}_plotting.log
done
                    # --nuisanced_vars_stat sigma nL nR alphaL alphaR \
                    # --weight_nuisanced_vars mean:pileupReweight,electronID,triggerSF1DCorrection sigma:pileupReweight,electronID,triggerSF1DCorrection alphaL:pileupReweight,electronID,triggerSF1DCorrection alphaR:pileupReweight,electronID,triggerSF1DCorrection nR:pileupReweight,electronID,triggerSF1DCorrection nL:pileupReweight,electronID,triggerSF1DCorrection \

# ### tighter cuts, 6p5 trigger only
# for era in 2022 2022EE 2023 2023BPix; do
#     time python3 main_oo.py --full --delete_ws --use_reco_mass \
#                     --no_categories --syst \
#                     --no_plots \
#                     --era "$era" \
#                     --folder_tag "260324" \
#                     --nuisanced_vars mean:electronScaleVariation \
#                     --copy_eos --tag="nanov15_withScaleSyst_IDSF_triggerSF_tighterCuts_6p5triggerOnly" &> logs/260324/log_reco_nanov15_withScaleSyst_IDSF_triggerSF_tighterCuts_6p5triggerOnly_era${era}.log
#     time python3 main_oo.py --plots --use_reco_mass \
#                     --no_categories --syst \
#                     --era "$era" \
#                     --folder_tag "260324" \
#                     --nuisanced_vars mean:electronScaleVariation \
#                     --copy_eos --tag="nanov15_withScaleSyst_IDSF_triggerSF_tighterCuts_6p5triggerOnly" &> logs/260324/log_reco_nanov15_withScaleSyst_IDSF_triggerSF_tighterCuts_6p5triggerOnly_era${era}_plotting.log
# done

# ### tighter cuts
# for era in 2022 2022EE 2023 2023BPix; do
#     time python3 main_oo.py --full --delete_ws --use_reco_mass \
#                     --no_categories --syst \
#                     --no_plots \
#                     --era "$era" \
#                     --folder_tag "260324" \
#                     --nuisanced_vars mean:electronScaleVariation \
#                     --copy_eos --tag="nanov15_withScaleSyst_IDSF_triggerSF_tighterCuts" &> logs/260324/log_reco_nanov15_withScaleSyst_IDSF_triggerSF_tighterCuts_era${era}.log
#     time python3 main_oo.py --plots --use_reco_mass \
#                     --no_categories --syst \
#                     --era "$era" \
#                     --folder_tag "260324" \
#                     --nuisanced_vars mean:electronScaleVariation \
#                     --copy_eos --tag="nanov15_withScaleSyst_IDSF_triggerSF_tighterCuts" &> logs/260324/log_reco_nanov15_withScaleSyst_IDSF_triggerSF_tighterCuts_era${era}_plotting.log
# done

# ### new signal tests, 6p5trigger only
# for era in 2022 2022EE 2023 2023BPix; do
#     time python3 main_oo.py --full --delete_ws --use_reco_mass \
#                     --no_categories --syst \
#                     --no_plots \
#                     --era "$era" \
#                     --folder_tag "260324" \
#                     --nuisanced_vars mean:electronScaleVariation \
#                     --copy_eos --tag="nanov15_withScaleSyst_IDSF_triggerSF_tighterCuts_6p5triggerOnly_newSignal" &> logs/260324/log_reco_nanov15_withScaleSyst_IDSF_triggerSF_tighterCuts_6p5triggerOnly_newSignal_era${era}.log
#     time python3 main_oo.py --plots --use_reco_mass \
#                     --no_categories --syst \
#                     --era "$era" \
#                     --folder_tag "260324" \
#                     --nuisanced_vars mean:electronScaleVariation \
#                     --copy_eos --tag="nanov15_withScaleSyst_IDSF_triggerSF_tighterCuts_6p5triggerOnly_newSignal" &> logs/260324/log_reco_nanov15_withScaleSyst_IDSF_triggerSF_tighterCuts_6p5triggerOnly_newSignal_era${era}_plotting.log
# done

### new signal tests
# for era in 2022 2022EE 2023 2023BPix; do
#     time python3 main_oo.py --full --delete_ws --use_reco_mass \
#                     --no_categories --syst \
#                     --no_plots \
#                     --era "$era" \
#                     --folder_tag "260324" \
#                     --nuisanced_vars mean:electronScaleVariation \
#                     --copy_eos --tag="nanov15_withScaleSyst_IDSF_triggerSF_tighterCuts_newSignal" &> logs/260324/log_reco_nanov15_withScaleSyst_IDSF_triggerSF_tighterCuts_newSignal_era${era}.log
#     time python3 main_oo.py --plots --use_reco_mass \
#                     --no_categories --syst \
#                     --era "$era" \
#                     --folder_tag "260324" \
#                     --nuisanced_vars mean:electronScaleVariation \
#                     --copy_eos --tag="nanov15_withScaleSyst_IDSF_triggerSF_tighterCuts_newSignal" &> logs/260324/log_reco_nanov15_withScaleSyst_IDSF_triggerSF_tighterCuts_newSignal_era${era}_plotting.log
# done


# ### Efficiency test for AN commentes (=> what abt pT=6.5 GeV trigger only?)
# for era in 2022 2023 2022EE 2023BPix; do
#     time python3 main_oo.py --full --delete_ws --use_reco_mass \
#                     --no_categories --syst \
#                     --no_plots \
#                     --era "$era" \
#                     --folder_tag "260320" \
#                     --nuisanced_vars mean:electronScaleVariation \
#                     --copy_eos --tag="nanov15_withScaleSyst_IDSF_triggerSF_6p5triggerOnly" &> logs/260320/log_reco_nanov15_withScaleSyst_IDSF_triggerSF_6p5triggerOnly_era${era}.log
#     time python3 main_oo.py --plots --use_reco_mass \
#                     --no_categories --syst \
#                     --era "$era" \
#                     --folder_tag "260320" \
#                     --nuisanced_vars mean:electronScaleVariation \
#                     --copy_eos --tag="nanov15_withScaleSyst_IDSF_triggerSF_6p5triggerOnly" &> logs/260320/log_reco_nanov15_withScaleSyst_IDSF_triggerSF_6p5triggerOnly_era${era}_plotting.log
# done

# ### Added cut on isolation
# for era in 2022; do
#     time python3 main_oo.py --full --delete_ws --use_reco_mass \
#                     --no_categories --syst \
#                     --no_plots \
#                     --era "$era" \
#                     --folder_tag "260312" \
#                     --nuisanced_vars mean:electronScaleVariation \
#                     --copy_eos --tag="nanov15_withScaleSyst_IDSF_triggerSF_isoCut" &> logs/260312/log_reco_nanov15_withScaleSyst_IDSF_triggerSF_isoCut_era${era}.log
#     time python3 main_oo.py --plots --use_reco_mass \
#                     --no_categories --syst \
#                     --era "$era" \
#                     --folder_tag "260312" \
#                     --nuisanced_vars mean:electronScaleVariation \
#                     --copy_eos --tag="nanov15_withScaleSyst_IDSF_triggerSF_isoCut" &> logs/260312/log_reco_nanov15_withScaleSyst_IDSF_triggerSF_isoCut_era${era}_plotting.log
# done

# ### TRIGGER SFs IMPLEMENTED, new mass points with new GEN filters
# for era in 2023; do
#     time python3 main_oo.py --full --delete_ws --use_reco_mass \
#                     --no_categories --syst \
#                     --no_plots \
#                     --era "$era" \
#                     --folder_tag "260309" \
#                     --nuisanced_vars mean:electronScaleVariation \
#                     --copy_eos --tag="nanov15_withScaleSyst_IDSF_triggerSF" &> logs/260309/log_reco_nanov15_withScaleSyst_IDSF_triggerSF_era${era}.log
#     time python3 main_oo.py --plots --use_reco_mass \
#                     --no_categories --syst \
#                     --era "$era" \
#                     --folder_tag "260309" \
#                     --nuisanced_vars mean:electronScaleVariation \
#                     --copy_eos --tag="nanov15_withScaleSyst_IDSF_triggerSF" &> logs/260309/log_reco_nanov15_withScaleSyst_IDSF_triggerSF_era${era}_plotting.log
# done

# ### TRIGGER SFs IMPLEMENTED
# for era in 2022 2022EE 2023 2023BPix; do
#     # time python3 main_oo.py --full --delete_ws --use_reco_mass \
#     #                 --no_categories --syst \
#     #                 --no_plots \
#     #                 --era "$era" \
#     #                 --folder_tag "260226" \
#     #                 --nuisanced_vars mean:electronScaleVariation \
#     #                 --copy_eos --tag="nanov15_withScaleSyst_IDSF_triggerSF" &> logs/260226/log_reco_nanov15_withScaleSyst_IDSF_triggerSF_era${era}.log
#     time python3 main_oo.py --plots --use_reco_mass \
#                     --no_categories --syst \
#                     --era "$era" \
#                     --folder_tag "260226" \
#                     --nuisanced_vars mean:electronScaleVariation \
#                     --copy_eos --tag="nanov15_withScaleSyst_IDSF_triggerSF" &> logs/260226/log_reco_nanov15_withScaleSyst_IDSF_triggerSF_era${era}_plotting.log
# done


### ID SF IMPLEMENTED 
# time python3 main_oo.py --full --delete_ws --use_reco_mass \
#                    --no_categories --syst \
#                    --no_plots \
#                    --nuisanced_vars mean:electronScaleVariation \
#                    --copy_eos --tag="nanov15_withScaleSyst_IDSF" &> logs/log_reco_nanov15_withScaleSyst_IDSF.log
# time python3 main_oo.py --plots --use_reco_mass \
#                    --no_categories --syst \
#                    --nuisanced_vars mean:electronScaleVariation \
                #    --copy_eos --tag="nanov15_withScaleSyst_IDSF" &> logs/log_reco_nanov15_withScaleSyst_IDSF_plotting.log

# time python3 main_oo.py --full --delete_ws --use_reco_mass \
#                    --no_categories --syst \
#                    --no_plots \
#                    --nuisanced_vars mean:electronScaleVariation \
#                    --copy_eos --tag="nanov15_withSyst_scaleOnly_elenaSyst" &> logs/log_reco_nanov15_withSyst_scaleOnly_elenaSyst.log
# time python3 main_oo.py --plots --use_reco_mass \
#                    --no_categories --syst \
#                    --nuisanced_vars mean:electronScaleVariation \
#                    --copy_eos --tag="nanov15_withSyst_scaleOnly_elenaSyst" &> logs/log_reco_nanov15_withSyst_scaleOnly_elenaSyst_plotting.log

# ### SCALE ONLY SYSTEMATICS, old values, flat variation
# time python3 main_oo.py --full --delete_ws --use_reco_mass \
#                    --no_categories --syst \
#                    --no_plots \
#                    --nuisanced_vars mean:electronScaleVariation_flat \
#                    --copy_eos --tag="nanov15_withSyst_scaleOnly" &> logs/log_reco_nanov15_withSyst_scaleOnly.log
# time python3 main_oo.py --plots --use_reco_mass \
#                    --no_categories --syst \
#                    --nuisanced_vars mean:electronScaleVariation_flat \
#                    --copy_eos --tag="nanov15_withSyst_scaleOnly" &> logs/log_reco_nanov15_withSyst_scaleOnly_plotting.log

# ### FULL CORRECTIONS: both scale and smearing applied
# time python3 main_oo.py --full --delete_ws --use_reco_mass \
#                    --no_categories --syst \
#                    --no_plots \
#                    --nuisanced_vars sigma:electronSmearing alphaR:electronSmearing nL:electronSmearing nR:electronSmearing alphaL:electronSmearing \
#                    --copy_eos --tag="nanov15_withSyst" &> logs/log_reco_nanov15_withSyst.log
# time python3 main_oo.py --plots --use_reco_mass \
#                    --no_categories --syst \
#                    --nuisanced_vars sigma:electronSmearing alphaR:electronSmearing nL:electronSmearing nR:electronSmearing alphaL:electronSmearing \
#                    --copy_eos --tag="nanov15_withSyst" &> logs/log_reco_nanov15_withSyst_plotting.log

# # ------ OLD (no systematics) ------ #
# python3 main_oo.py --full --delete_ws --use_reco_mass \
#                    --copy_eos --tag="withReweight_Categories_nanov15" &> logs/log_reco_triggerReweight_Categories_nanov15.log

# python3 main_oo.py --plots --use_reco_mass \
#                    --copy_eos --tag="withReweight_Categories_nanov15"