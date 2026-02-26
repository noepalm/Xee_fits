time python3 main_oo.py --full --delete_ws --use_reco_mass \
                   --no_categories --syst \
                   --no_plots \
                   --nuisanced_vars mean:electronScaleVariation \
                   --copy_eos --tag="nanov15_withScaleSyst_IDSF_triggerSF" &> logs/log_reco_nanov15_withScaleSyst_IDSF_triggerSF.log
time python3 main_oo.py --plots --use_reco_mass \
                   --no_categories --syst \
                   --nuisanced_vars mean:electronScaleVariation \
                   --copy_eos --tag="nanov15_withScaleSyst_IDSF_triggerSF" &> logs/log_reco_nanov15_withScaleSyst_IDSF_triggerSF_plotting.log


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