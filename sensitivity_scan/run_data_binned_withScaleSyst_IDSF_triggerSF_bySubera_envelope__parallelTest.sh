# # ################################
# # ####          DATA          ####
# # ################################

# for era in 2022 2022EE 2023 2023BPix; do
#     python3 make_combine_workspace.py --cat="inclusive" --region region1 --data \
#                                     --withSyst \
#                                     --input_tag altbkg_chebyshev_withScaleSyst_IDSF_triggerSF \
#                                     --tag altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_bySubera \
#                                     --era ${era} \
#                                     --folder_tag 260226 \
#                                     --binned &> logs/260226/workspace_inclusive_region1_data_altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_bySubera_${era}_binned_log
    
#     source scripts/run_limits_parallel.sh --cat inclusive \
#                                         --tag altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_bySubera_binned \
#                                         --folder_tag 260226 \
#                                         --era ${era} \
#                                         --region region1 \
#                                         --no_caching \
#                                         --data &> logs/260226/limits_inclusive_region1_data_altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_bySubera_${era}_binned_log

#     source scripts/run_diagnostics_parallel.sh --cat inclusive \
#                                             --folder_tag 260226 \
#                                             --region region1 \
#                                             --data --binned \
#                                             --era ${era} \
#                                             --tag altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_bySubera_binned &> logs/diagnostics_inclusive_region1_data_altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_bySubera_${era}_binned_log &
# done

# source scripts/run_limits_parallel.sh --cat inclusive \
#                                       --tag altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_bySubera_binned \
#                                       --folder_tag 260226 \
#                                       --era allYears \
#                                       --no_caching \
#                                       --region region1 \
#                                       --data &> logs/260226/limits_inclusive_region1_data_altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_bySubera_allYears_binned_log

# for era in 2022 2022EE 2023 2023BPix; do
#     python3 make_combine_workspace.py --cat="inclusive" --region region2 --data \
#                                     --withSyst \
#                                     --input_tag altbkg_chebyshev_withScaleSyst_IDSF_triggerSF \
#                                     --tag altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_bySubera \
#                                     --era ${era} \
#                                     --folder_tag 260226 \
#                                     --binned &> logs/260226/workspace_inclusive_region2_data_altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_bySubera_${era}_binned_log
    
#     source scripts/run_limits_parallel.sh --cat inclusive \
#                                         --tag altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_bySubera_binned \
#                                         --folder_tag 260226 \
#                                         --era ${era} \
#                                         --no_caching \
#                                         --region region2 \
#                                         --data &> logs/260226/limits_inclusive_region2_data_altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_bySubera_${era}_binned_log

#     source scripts/run_diagnostics_parallel.sh --cat inclusive \
#                                             --folder_tag 260226 \
#                                             --region region2 \
#                                             --data --binned \
#                                             --era ${era} \
#                                             --tag altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_bySubera_binned &> logs/diagnostics_inclusive_region2_data_altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_bySubera_${era}_binned_log &

# done

# source scripts/run_limits_parallel.sh --cat inclusive \
#                                       --tag altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_bySubera_binned \
#                                       --folder_tag 260226 \
#                                       --no_caching \
#                                       --era allYears \
#                                       --region region2 \
#                                       --data &> logs/260226/limits_inclusive_region2_data_altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_bySubera_allYears_binned_log
# wait

# for era in 2022 2022EE 2023 2023BPix; do
#     python3 make_combine_workspace.py --cat="inclusive" --region region0 --data \
#                                     --withSyst \
#                                     --input_tag altbkg_chebyshev_withScaleSyst_IDSF_triggerSF \
#                                     --tag altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_bySubera \
#                                     --era ${era} \
#                                     --folder_tag 260226 \
#                                     --binned &> logs/260226/workspace_inclusive_region0_data_altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_bySubera_${era}_binned_log
    
#     source scripts/run_limits_parallel.sh --cat inclusive \
#                                         --tag altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_bySubera_binned \
#                                         --folder_tag 260226 \
#                                         --era ${era} \
#                                         --region region0 \
#                                         --no_caching \
#                                         --data &> logs/260226/limits_inclusive_region0_data_altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_bySubera_${era}_binned_log

#     source scripts/run_diagnostics_parallel.sh --cat inclusive \
#                                             --folder_tag 260226 \
#                                             --region region0 \
#                                             --data --binned \
#                                             --era ${era} \
#                                             --tag altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_bySubera_binned &> logs/260226/diagnostics_inclusive_region0_data_altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_bySubera_${era}_binned_log &

# done

# source scripts/run_limits_parallel.sh --cat inclusive \
#                                       --tag altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_bySubera_binned \
#                                       --folder_tag 260226 \
#                                       --no_caching \
#                                       --era allYears \
#                                       --region region0 \
#                                       --data &> logs/260226/limits_inclusive_region0_data_altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_bySubera_allYears_binned_log

# for era in 2022 2022EE 2023 2023BPix; do
#     python3 scripts/plot_limits_result.py -i cards/260226/cards_region0_data_altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_bySubera_binned cards/260226/cards_region1_data_altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_bySubera_binned cards/260226/cards_region2_data_altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_bySubera_binned \
#                                         -c inclusive -r region0 region1 region2 \
#                                         --era $era \
#                                         -o /eos/home-n/npalmeri/www/DiElectron/sensitivity/260226/fitDiagnostics_grid_data_altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_bySubera_binned/mu0/inclusive_$era &> /eos/home-n/npalmeri/www/DiElectron/sensitivity/260226/fitDiagnostics_grid_data_altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_bySubera_binned/mu0/inclusive_${era}/limits_summary_region0_region1_region2.log
# done
# python3 scripts/plot_limits_result.py -i cards/260226/cards_region0_data_altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_bySubera_binned cards/260226/cards_region1_data_altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_bySubera_binned cards/260226/cards_region2_data_altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_bySubera_binned \
#                                       -c inclusive -r region0 region1 region2 \
#                                       --era allYears \
#                                       -o /eos/home-n/npalmeri/www/DiElectron/sensitivity/260226/fitDiagnostics_grid_data_altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_bySubera_binned/mu0/inclusive_allYears &> /eos/home-n/npalmeri/www/DiElectron/sensitivity/260226/fitDiagnostics_grid_data_altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_bySubera_binned/mu0/inclusive_allYears/limits_summary_region0_region1_region2.log


############################
#### WITH MEAN NUISANCE ####
############################
# for era in 2022 2022EE 2023 2023BPix; do
# for era in 2022 2022EE 2023 2023BPix; do
#     for region in region0 region1 region2; do
#         time python3 make_combine_workspace.py --cat="inclusive" --region $region --data \
#                                         --withSyst \
#                                         --envelope \
#                                         --input_tag envelope_withScaleSyst_IDSF_triggerSF \
#                                         --tag envelope_withScaleSyst_withMeanNuisance_IDSF_triggerSF_bySubera__parallelTest \
#                                         --era ${era} \
#                                         --folder_tag 260226 \
#                                         --binned &> logs/260311/workspace_inclusive_${region}_data_envelope_withScaleSyst_withMeanNuisance_IDSF_triggerSF_bySubera__parallelTest_${era}_binned_log
#     done
# done

# time python3 scripts/run_limits_parallel.py --cat inclusive \
#                                       --tag envelope_withScaleSyst_withMeanNuisance_IDSF_triggerSF_bySubera__parallelTest_binned \
#                                       --folder_tag 260311 \
#                                       --eras 2022 2022EE 2023 2023BPix allYears \
#                                       --regions region0 region1 region2 \
#                                       --data

# for era in 2022 2022EE 2023 2023BPix; do
#     python3 make_combine_workspace.py --cat="inclusive" --region region2 --data \
#                                     --withSyst \
#                                     --envelope \
#                                     --input_tag envelope_withScaleSyst_IDSF_triggerSF \
#                                     --tag envelope_withScaleSyst_withMeanNuisance_IDSF_triggerSF_bySubera \
#                                     --era ${era} \
#                                     --folder_tag 260226 \
#                                     --binned &> logs/260226/workspace_inclusive_region2_data_envelope_withScaleSyst_withMeanNuisance_IDSF_triggerSF_bySubera_${era}_binned_log
    
#     source scripts/run_limits_parallel.sh --cat inclusive \
#                                         --tag envelope_withScaleSyst_withMeanNuisance_IDSF_triggerSF_bySubera_binned \
#                                         --folder_tag 260226 \
#                                         --era ${era} \
#                                         --region region2 \
#                                         --data &> logs/260226/limits_inclusive_region2_data_envelope_withScaleSyst_withMeanNuisance_IDSF_triggerSF_bySubera_${era}_binned_log

#     source scripts/run_diagnostics_parallel.sh --cat inclusive \
#                                             --folder_tag 260226 \
#                                             --region region2 \
#                                             --data --binned \
#                                             --era ${era} \
#                                             --tag envelope_withScaleSyst_withMeanNuisance_IDSF_triggerSF_bySubera_binned &> logs/260226/diagnostics_inclusive_region2_data_envelope_withScaleSyst_withMeanNuisance_IDSF_triggerSF_bySubera_${era}_binned_log &

# done

# source scripts/run_limits_parallel.sh --cat inclusive \
#                                       --tag envelope_withScaleSyst_withMeanNuisance_IDSF_triggerSF_bySubera_binned \
#                                       --folder_tag 260226 \
#                                       --era allYears \
#                                       --region region2 \
#                                       --data &> logs/260226/limits_inclusive_region2_data_envelope_withScaleSyst_withMeanNuisance_IDSF_triggerSF_bySubera_allYears_binned_log

# wait

# for era in 2022 2022EE 2023 2023BPix; do
#     python3 make_combine_workspace.py --cat="inclusive" --region region0 --data \
#                                     --withSyst \
#                                     --input_tag envelope_withScaleSyst_IDSF_triggerSF \
#                                     --tag envelope_withScaleSyst_withMeanNuisance_IDSF_triggerSF_bySubera \
#                                     --envelope \
#                                     --era ${era} \
#                                     --folder_tag 260226 \
#                                     --binned &> logs/260226/workspace_inclusive_region0_data_envelope_withScaleSyst_withMeanNuisance_IDSF_triggerSF_bySubera_${era}_binned_log
    
#     source scripts/run_limits_parallel.sh --cat inclusive \
#                                         --tag envelope_withScaleSyst_withMeanNuisance_IDSF_triggerSF_bySubera_binned \
#                                         --folder_tag 260226 \
#                                         --era ${era} \
#                                         --region region0 \
#                                         --data &> logs/260226/limits_inclusive_region0_data_envelope_withScaleSyst_withMeanNuisance_IDSF_triggerSF_bySubera_${era}_binned_log

#     source scripts/run_diagnostics_parallel.sh --cat inclusive \
#                                             --folder_tag 260226 \
#                                             --region region0 \
#                                             --data --binned \
#                                             --era ${era} \
#                                             --tag envelope_withScaleSyst_withMeanNuisance_IDSF_triggerSF_bySubera_binned &> logs/260226/diagnostics_inclusive_region0_data_envelope_withScaleSyst_withMeanNuisance_IDSF_triggerSF_bySubera_${era}_binned_log &
# done

# source scripts/run_limits_parallel.sh --cat inclusive \
#                                       --tag envelope_withScaleSyst_withMeanNuisance_IDSF_triggerSF_bySubera_binned \
#                                       --folder_tag 260226 \
#                                       --era allYears \
#                                       --no_caching \
#                                       --region region0 \
#                                       --data &> logs/260226/limits_inclusive_region0_data_envelope_withScaleSyst_withMeanNuisance_IDSF_triggerSF_bySubera_allYears_binned_log

# region-combined limits
for era in 2022 2022EE 2023 2023BPix; do
    python3 scripts/plot_limits_result.py -i cards/260311/cards_region0_data_envelope_withScaleSyst_withMeanNuisance_IDSF_triggerSF_bySubera__parallelTest_binned cards/260311/cards_region1_data_envelope_withScaleSyst_withMeanNuisance_IDSF_triggerSF_bySubera__parallelTest_binned cards/260311/cards_region2_data_envelope_withScaleSyst_withMeanNuisance_IDSF_triggerSF_bySubera__parallelTest_binned \
                                        -c inclusive -r region0 region1 region2 \
                                        --era $era \
                                        -o /eos/home-n/npalmeri/www/DiElectron/sensitivity/260311/fitDiagnostics_grid_data_envelope_withScaleSyst_withMeanNuisance_IDSF_triggerSF_bySubera__parallelTest_binned/mu0/inclusive_$era &> /eos/home-n/npalmeri/www/DiElectron/sensitivity/260311/fitDiagnostics_grid_data_envelope_withScaleSyst_withMeanNuisance_IDSF_triggerSF_bySubera__parallelTest_binned/mu0/inclusive_${era}/limits_summary_region0_region1_region2.log
done
python3 scripts/plot_limits_result.py -i cards/260311/cards_region0_data_envelope_withScaleSyst_withMeanNuisance_IDSF_triggerSF_bySubera__parallelTest_binned cards/260311/cards_region1_data_envelope_withScaleSyst_withMeanNuisance_IDSF_triggerSF_bySubera__parallelTest_binned cards/260311/cards_region2_data_envelope_withScaleSyst_withMeanNuisance_IDSF_triggerSF_bySubera__parallelTest_binned \
                                      -c inclusive -r region0 region1 region2 \
                                      --era allYears \
                                      -o /eos/home-n/npalmeri/www/DiElectron/sensitivity/260311/fitDiagnostics_grid_data_envelope_withScaleSyst_withMeanNuisance_IDSF_triggerSF_bySubera__parallelTest_binned/mu0/inclusive_allYears &> /eos/home-n/npalmeri/www/DiElectron/sensitivity/260311/fitDiagnostics_grid_data_envelope_withScaleSyst_withMeanNuisance_IDSF_triggerSF_bySubera__parallelTest_binned/mu0/inclusive_allYears/limits_summary_region0_region1_region2.log