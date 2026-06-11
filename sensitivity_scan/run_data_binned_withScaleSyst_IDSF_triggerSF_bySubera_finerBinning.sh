#############################
#### CHEBYSHEV BKG (n.0) ####
#############################

# mkdir -p logs/260316

# # for era in 2022 2022EE 2023 2023BPix; do
# #     for region in region0 region1 region2; do
# #         python3 make_combine_workspace.py --cat="inclusive" --region ${region} --data \
# #                                         --withSyst \
# #                                         --input_tag altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_finerBinning \
# #                                         --tag altbkg_chebyshev_withScaleSyst_withMeanNuisance_IDSF_triggerSF_finerBinning_bySubera \
# #                                         --era ${era} \
# #                                         --folder_tag 260316 \
# #                                         --binned &> logs/260316/workspace_inclusive_${region}_data_altbkg_chebyshev_withScaleSyst_withMeanNuisance_IDSF_triggerSF_finerBinning_bySubera_${era}_binned_log
# #     done
# # done

# python3 scripts/run_limits_parallel.py --cat inclusive \
#                                       --tag altbkg_chebyshev_withScaleSyst_withMeanNuisance_IDSF_triggerSF_finerBinning_bySubera_binned \
#                                       --folder_tag 260316 \
#                                       --eras allYears \
#                                       --regions region0 region1 region2 \
#                                       --data

# python3 scripts/plot_limits_result.py -i cards/260316/cards_region0_data_altbkg_chebyshev_withScaleSyst_withMeanNuisance_IDSF_triggerSF_finerBinning_bySubera_binned cards/260316/cards_region1_data_altbkg_chebyshev_withScaleSyst_withMeanNuisance_IDSF_triggerSF_finerBinning_bySubera_binned cards/260316/cards_region2_data_altbkg_chebyshev_withScaleSyst_withMeanNuisance_IDSF_triggerSF_finerBinning_bySubera_binned \
#                                       -c inclusive -r region0 region1 region2 \
#                                       --era allYears \
#                                       -o /eos/home-n/npalmeri/www/DiElectron/sensitivity/260316/fitDiagnostics_grid_data_altbkg_chebyshev_withScaleSyst_withMeanNuisance_IDSF_triggerSF_finerBinning_bySubera_binned/mu0/inclusive_allYears &> /eos/home-n/npalmeri/www/DiElectron/sensitivity/260316/fitDiagnostics_grid_data_altbkg_chebyshev_withScaleSyst_withMeanNuisance_IDSF_triggerSF_finerBinning_bySubera_binned/mu0/inclusive_allYears/limits_summary_region0_region1_region2.log

# python3 scripts/run_diagnostics_parallel.py --cat inclusive \
#                                             --folder_tag 260316 \
#                                             --tag altbkg_chebyshev_withScaleSyst_withMeanNuisance_IDSF_triggerSF_finerBinning_bySubera_binned \
#                                             --regions region0 region1 region2 \
#                                             --data --binned \
#                                             --eras 2022 2022EE 2023 2023BPix

###########################
### POLYEXP BKG (n.2) ####
###########################

# for era in 2022 2022EE 2023 2023BPix; do
#     for region in region0 region1 region2; do
#         python3 make_combine_workspace.py --cat="inclusive" --region ${region} --data \
#                                         --withSyst \
#                                         --input_tag altbkg_polyexp_withScaleSyst_IDSF_triggerSF_finerBinning \
#                                         --tag altbkg_polyexp_withScaleSyst_withMeanNuisance_IDSF_triggerSF_finerBinning_bySubera \
#                                         --era ${era} \
#                                         --folder_tag 260316 \
#                                         --binned &> logs/260316/workspace_inclusive_${region}_data_altbkg_polyexp_withScaleSyst_withMeanNuisance_IDSF_triggerSF_finerBinning_bySubera_${era}_binned_log
#     done
# done

# for era in 2022 2022EE 2023 2023BPix; do
#     for region in region0 region1 region2; do
#         python3 make_combine_workspace.py --cat="inclusive" --region ${region} --data \
#                                         --withSyst \
#                                         --input_tag altbkg_bernstein_withScaleSyst_IDSF_triggerSF_finerBinning \
#                                         --tag altbkg_bernstein_withScaleSyst_withMeanNuisance_IDSF_triggerSF_finerBinning_bySubera \
#                                         --era ${era} \
#                                         --folder_tag 260316 \
#                                         --binned &> logs/260316/workspace_inclusive_${region}_data_altbkg_bernstein_withScaleSyst_withMeanNuisance_IDSF_triggerSF_finerBinning_bySubera_${era}_binned_log
#     done
# done

# python3 scripts/run_limits_parallel.py --cat inclusive \
#                                       --tag altbkg_polyexp_withScaleSyst_withMeanNuisance_IDSF_triggerSF_finerBinning_bySubera_binned \
#                                       --folder_tag 260316 \
#                                       --eras allYears \
#                                       --regions region0 region1 region2 \
#                                       --data

# python3 scripts/plot_limits_result.py -i cards/260316/cards_region0_data_altbkg_polyexp_withScaleSyst_withMeanNuisance_IDSF_triggerSF_finerBinning_bySubera_binned cards/260316/cards_region1_data_altbkg_polyexp_withScaleSyst_withMeanNuisance_IDSF_triggerSF_finerBinning_bySubera_binned cards/260316/cards_region2_data_altbkg_polyexp_withScaleSyst_withMeanNuisance_IDSF_triggerSF_finerBinning_bySubera_binned \
#                                       -c inclusive -r region0 region1 region2 \
#                                       --era allYears \
#                                       -o /eos/home-n/npalmeri/www/DiElectron/sensitivity/260316/fitDiagnostics_grid_data_altbkg_polyexp_withScaleSyst_withMeanNuisance_IDSF_triggerSF_finerBinning_bySubera_binned/mu0/inclusive_allYears &> /eos/home-n/npalmeri/www/DiElectron/sensitivity/260316/fitDiagnostics_grid_data_altbkg_polyexp_withScaleSyst_withMeanNuisance_IDSF_triggerSF_finerBinning_bySubera_binned/mu0/inclusive_allYears/limits_summary_region0_region1_region2.log

# python3 scripts/run_diagnostics_parallel.py --cat inclusive \
#                                             --folder_tag 260316 \
#                                             --tag altbkg_polyexp_withScaleSyst_withMeanNuisance_IDSF_triggerSF_finerBinning_bySubera_binned \
#                                             --regions region0 region1 region2 \
#                                             --data --binned \
#                                             --eras 2022 2022EE 2023 2023BPix

############################
###### WITH ENVELOPE #######
############################
# for era in 2022 2022EE 2023 2023BPix; do
#     for region in region0 region1 region2; do
#         python3 make_combine_workspace.py --cat="inclusive" --region ${region} --data \
#                                         --withSyst \
#                                         --input_tag envelope_withScaleSyst_IDSF_triggerSF_finerBinning \
#                                         --tag envelope_withScaleSyst_withMeanNuisance_IDSF_triggerSF_finerBinning_bySubera \
#                                         --era ${era} \
#                                         --envelope \
#                                         --folder_tag 260316 \
#                                         --binned &> logs/260316/workspace_inclusive_${region}_data_envelope_withScaleSyst_withMeanNuisance_IDSF_triggerSF_finerBinning_bySubera_${era}_binned_log
#     done
# done

# python3 scripts/run_limits_parallel.py --cat inclusive \
#                                       --tag envelope_withScaleSyst_withMeanNuisance_IDSF_triggerSF_finerBinning_bySubera_binned \
#                                       --folder_tag 260316 \
#                                       --eras allYears \
#                                       --regions region0 region1 region2 \
#                                       --data

# python3 scripts/plot_limits_result.py -i cards/260316/cards_region0_data_envelope_withScaleSyst_withMeanNuisance_IDSF_triggerSF_finerBinning_bySubera_binned cards/260316/cards_region1_data_envelope_withScaleSyst_withMeanNuisance_IDSF_triggerSF_finerBinning_bySubera_binned cards/260316/cards_region2_data_envelope_withScaleSyst_withMeanNuisance_IDSF_triggerSF_finerBinning_bySubera_binned \
#                                       -c inclusive -r region0 region1 region2 \
#                                       --era allYears \
#                                       -o /eos/home-n/npalmeri/www/DiElectron/sensitivity/260316/fitDiagnostics_grid_data_envelope_withScaleSyst_withMeanNuisance_IDSF_triggerSF_finerBinning_bySubera_binned/mu0/inclusive_allYears &> /eos/home-n/npalmeri/www/DiElectron/sensitivity/260316/fitDiagnostics_grid_data_envelope_withScaleSyst_withMeanNuisance_IDSF_triggerSF_finerBinning_bySubera_binned/mu0/inclusive_allYears/limits_summary_region0_region1_region2.log

# python3 scripts/run_diagnostics_parallel.py --cat inclusive \
#                                             --folder_tag 260316 \
#                                             --tag envelope_withScaleSyst_withMeanNuisance_IDSF_triggerSF_finerBinning_bySubera_binned \
#                                             --regions region0 region1 region2 \
#                                             --data --binned \
#                                             --eras 2022 2022EE 2023 2023BPix

# ######################################
# ##### WITH ENVELOPE (FOR REAL) #######
# ######################################
# for era in 2022 2022EE 2023 2023BPix; do
#     for region in region0 region1 region2; do
#         python3 make_combine_workspace.py --cat="inclusive" --region ${region} --data \
#                                         --withSyst \
#                                         --input_tag envelope_withScaleSyst_IDSF_triggerSF_finerBinning \
#                                         --tag envelope_noFreeze_withScaleSyst_withMeanNuisance_IDSF_triggerSF_finerBinning_bySubera \
#                                         --era ${era} \
#                                         --envelope \
#                                         --folder_tag 260316 \
#                                         --binned &> logs/260316/workspace_inclusive_${region}_data_envelope_noFreeze_withScaleSyst_withMeanNuisance_IDSF_triggerSF_finerBinning_bySubera_${era}_binned_log
#     done
# done

# python3 scripts/run_limits_parallel.py --cat inclusive \
#                                       --tag envelope_noFreeze_withScaleSyst_withMeanNuisance_IDSF_triggerSF_finerBinning_bySubera_binned \
#                                       --folder_tag 260316 \
#                                       --eras allYears \
#                                       --no_caching \
#                                       --regions region0 region1 region2 \
#                                       --data

# python3 scripts/plot_limits_result.py -i cards/260316/cards_region0_data_envelope_noFreeze_withScaleSyst_withMeanNuisance_IDSF_triggerSF_finerBinning_bySubera_binned cards/260316/cards_region1_data_envelope_noFreeze_withScaleSyst_withMeanNuisance_IDSF_triggerSF_finerBinning_bySubera_binned cards/260316/cards_region2_data_envelope_noFreeze_withScaleSyst_withMeanNuisance_IDSF_triggerSF_finerBinning_bySubera_binned \
#                                       -c inclusive -r region0 region1 region2 \
#                                       --era allYears \
#                                       -o /eos/home-n/npalmeri/www/DiElectron/sensitivity/260316/fitDiagnostics_grid_data_envelope_noFreeze_withScaleSyst_withMeanNuisance_IDSF_triggerSF_finerBinning_bySubera_binned/mu0/inclusive_allYears &> /eos/home-n/npalmeri/www/DiElectron/sensitivity/260316/fitDiagnostics_grid_data_envelope_noFreeze_withScaleSyst_withMeanNuisance_IDSF_triggerSF_finerBinning_bySubera_binned/mu0/inclusive_allYears/limits_summary_region0_region1_region2.log

# # python3 scripts/run_diagnostics_parallel.py --cat inclusive \
# #                                             --folder_tag 260316 \
# #                                             --tag envelope_noFreeze_altpoly_withScaleSyst_withMeanNuisance_IDSF_triggerSF_finerBinning_bySubera_binned \
# #                                             --regions region0 region1 region2 \
# #                                             --data --binned \
# #                                             --eras 2022 2022EE 2023 2023BPix


# ---------------------------------------------
### BIAS TEST

# # no signal injection
# python3 scripts/run_bias_test.py --cat inclusive \
#                                  --folder_tag 260316 \
#                                  --tag envelope_noFreeze_withScaleSyst_withMeanNuisance_IDSF_triggerSF_finerBinning_bySubera_binned \
#                                  --regions region0 region1 region2 \
#                                  --ntoys 50 \
#                                  --jobs `nproc` \
#                                  --data --binned \
#                                  --eras 2022

# # signal injected (mu=1)
# python3 scripts/run_bias_test.py --cat inclusive \
#                                  --folder_tag 260316 \
#                                  --tag envelope_noFreeze_withScaleSyst_withMeanNuisance_IDSF_triggerSF_finerBinning_bySubera_binned \
#                                  --regions region0 region1 region2 \
#                                  --expectSignal 1 \
#                                  --ntoys 50 \
#                                  --jobs `nproc` \
#                                  --data --binned \
#                                  --eras 2022

# ### POLYEXP TUNING TESTS
# # mkdir -p logs/260316
# for era in 2022; do
#     for region in region1; do
#         python3 make_combine_workspace.py --cat="inclusive" --region ${region} --data \
#                                         --withSyst \
#                                         --input_tag altbkg_polyexp_withScaleSyst_IDSF_triggerSF_finerBinning \
#                                         --tag altbkg_polyexp_withScaleSyst_withMeanNuisance_IDSF_triggerSF_finerBinning_bySubera \
#                                         --era ${era} \
#                                         --folder_tag 260316 \
#                                         --binned &> logs/260316/workspace_inclusive_${region}_data_altbkg_polyexp_withScaleSyst_withMeanNuisance_IDSF_triggerSF_finerBinning_bySubera_${era}_binned_log
#     done
# done

# # no signal injection
# python3 scripts/run_bias_test.py --cat inclusive \
#                                  --folder_tag 260316 \
#                                  --tag envelope_withScaleSyst_withMeanNuisance_IDSF_triggerSF_finerBinning_bySubera_binned \
#                                  --regions region0 region1 region2 \
#                                  --plot_only \
#                                  --ntoys 50 \
#                                  --jobs `nproc` \
#                                  --data --binned \
#                                  --eras 2022

# # signal injected (mu=1)
# python3 scripts/run_bias_test.py --cat inclusive \
#                                  --folder_tag 260316 \
#                                  --tag envelope_withScaleSyst_withMeanNuisance_IDSF_triggerSF_finerBinning_bySubera_binned \
#                                  --regions region0 region1 region2 \
#                                  --expectSignal 1 \
#                                  --plot_only \
#                                  --ntoys 50 \
#                                  --jobs `nproc` \
#                                  --data --binned \
#                                  --eras 2022

# # signal injected (mu=0.1)
# python3 scripts/run_bias_test.py --cat inclusive \
#                                  --folder_tag 260316 \
#                                  --tag envelope_withScaleSyst_withMeanNuisance_IDSF_triggerSF_finerBinning_bySubera_binned \
#                                  --regions region0 region1 region2 \
#                                  --expectSignal 0.1 \
#                                  --ntoys 50 \
#                                  --jobs `nproc` \
#                                  --data --binned \
#                                  --eras 2022

# signal injected (mu=0.01)
python3 scripts/run_bias_test.py --cat inclusive \
                                 --folder_tag 260316 \
                                 --tag envelope_withScaleSyst_withMeanNuisance_IDSF_triggerSF_finerBinning_bySubera_binned \
                                 --regions region0 region1 region2 \
                                 --expectSignal 0.01 \
                                 --ntoys 50 \
                                 --jobs `nproc` \
                                 --data --binned \
                                 --eras 2022
