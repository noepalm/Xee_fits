# # ################################
# # ####          DATA          ####
# # ################################

# for era in 2022 2022EE 2023 2023BPix; do
#     python3 make_combine_workspace.py --cat="inclusive" --region region1 --data \
#                                     --withSyst \
#                                     --input_tag altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_isoCut \
#                                     --tag altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_isoCut_bySubera \
#                                     --era ${era} \
#                                     --folder_tag 260312 \
#                                     --binned &> logs/260312/workspace_inclusive_region1_data_altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_isoCut_bySubera_${era}_binned_log
    
#     source scripts/run_limits_parallel.sh --cat inclusive \
#                                         --tag altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_isoCut_bySubera_binned \
#                                         --folder_tag 260312 \
#                                         --era ${era} \
#                                         --region region1 \
#                                         --no_caching \
#                                         --data &> logs/260312/limits_inclusive_region1_data_altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_isoCut_bySubera_${era}_binned_log

#     source scripts/run_diagnostics_parallel.sh --cat inclusive \
#                                             --folder_tag 260312 \
#                                             --region region1 \
#                                             --data --binned \
#                                             --era ${era} \
#                                             --tag altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_isoCut_bySubera_binned &> logs/diagnostics_inclusive_region1_data_altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_isoCut_bySubera_${era}_binned_log &
# done

# source scripts/run_limits_parallel.sh --cat inclusive \
#                                       --tag altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_isoCut_bySubera_binned \
#                                       --folder_tag 260312 \
#                                       --era allYears \
#                                       --no_caching \
#                                       --region region1 \
#                                       --data &> logs/260312/limits_inclusive_region1_data_altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_isoCut_bySubera_allYears_binned_log

# for era in 2022 2022EE 2023 2023BPix; do
#     python3 make_combine_workspace.py --cat="inclusive" --region region2 --data \
#                                     --withSyst \
#                                     --input_tag altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_isoCut \
#                                     --tag altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_isoCut_bySubera \
#                                     --era ${era} \
#                                     --folder_tag 260312 \
#                                     --binned &> logs/260312/workspace_inclusive_region2_data_altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_isoCut_bySubera_${era}_binned_log
    
#     source scripts/run_limits_parallel.sh --cat inclusive \
#                                         --tag altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_isoCut_bySubera_binned \
#                                         --folder_tag 260312 \
#                                         --era ${era} \
#                                         --no_caching \
#                                         --region region2 \
#                                         --data &> logs/260312/limits_inclusive_region2_data_altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_isoCut_bySubera_${era}_binned_log

#     source scripts/run_diagnostics_parallel.sh --cat inclusive \
#                                             --folder_tag 260312 \
#                                             --region region2 \
#                                             --data --binned \
#                                             --era ${era} \
#                                             --tag altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_isoCut_bySubera_binned &> logs/diagnostics_inclusive_region2_data_altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_isoCut_bySubera_${era}_binned_log &

# done

# source scripts/run_limits_parallel.sh --cat inclusive \
#                                       --tag altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_isoCut_bySubera_binned \
#                                       --folder_tag 260312 \
#                                       --no_caching \
#                                       --era allYears \
#                                       --region region2 \
#                                       --data &> logs/260312/limits_inclusive_region2_data_altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_isoCut_bySubera_allYears_binned_log
# wait

# for era in 2022 2022EE 2023 2023BPix; do
#     python3 make_combine_workspace.py --cat="inclusive" --region region0 --data \
#                                     --withSyst \
#                                     --input_tag altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_isoCut \
#                                     --tag altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_isoCut_bySubera \
#                                     --era ${era} \
#                                     --folder_tag 260312 \
#                                     --binned &> logs/260312/workspace_inclusive_region0_data_altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_isoCut_bySubera_${era}_binned_log
    
#     source scripts/run_limits_parallel.sh --cat inclusive \
#                                         --tag altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_isoCut_bySubera_binned \
#                                         --folder_tag 260312 \
#                                         --era ${era} \
#                                         --region region0 \
#                                         --no_caching \
#                                         --data &> logs/260312/limits_inclusive_region0_data_altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_isoCut_bySubera_${era}_binned_log

#     source scripts/run_diagnostics_parallel.sh --cat inclusive \
#                                             --folder_tag 260312 \
#                                             --region region0 \
#                                             --data --binned \
#                                             --era ${era} \
#                                             --tag altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_isoCut_bySubera_binned &> logs/260312/diagnostics_inclusive_region0_data_altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_isoCut_bySubera_${era}_binned_log &

# done

# source scripts/run_limits_parallel.sh --cat inclusive \
#                                       --tag altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_isoCut_bySubera_binned \
#                                       --folder_tag 260312 \
#                                       --no_caching \
#                                       --era allYears \
#                                       --region region0 \
#                                       --data &> logs/260312/limits_inclusive_region0_data_altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_isoCut_bySubera_allYears_binned_log

# for era in 2022 2022EE 2023 2023BPix; do
#     python3 scripts/plot_limits_result.py -i cards/260312/cards_region0_data_altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_isoCut_bySubera_binned cards/260312/cards_region1_data_altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_isoCut_bySubera_binned cards/260312/cards_region2_data_altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_isoCut_bySubera_binned \
#                                         -c inclusive -r region0 region1 region2 \
#                                         --era $era \
#                                         -o /eos/home-n/npalmeri/www/DiElectron/sensitivity/260312/fitDiagnostics_grid_data_altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_isoCut_bySubera_binned/mu0/inclusive_$era &> /eos/home-n/npalmeri/www/DiElectron/sensitivity/260312/fitDiagnostics_grid_data_altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_isoCut_bySubera_binned/mu0/inclusive_${era}/limits_summary_region0_region1_region2.log
# done
# python3 scripts/plot_limits_result.py -i cards/260312/cards_region0_data_altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_isoCut_bySubera_binned cards/260312/cards_region1_data_altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_isoCut_bySubera_binned cards/260312/cards_region2_data_altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_isoCut_bySubera_binned \
#                                       -c inclusive -r region0 region1 region2 \
#                                       --era allYears \
#                                       -o /eos/home-n/npalmeri/www/DiElectron/sensitivity/260312/fitDiagnostics_grid_data_altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_isoCut_bySubera_binned/mu0/inclusive_allYears &> /eos/home-n/npalmeri/www/DiElectron/sensitivity/260312/fitDiagnostics_grid_data_altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_isoCut_bySubera_binned/mu0/inclusive_allYears/limits_summary_region0_region1_region2.log


############################
#### WITH MEAN NUISANCE ####
############################
# for era in 2022; do

for era in 2022 2022EE 2023 2023BPix; do
    for region in region0 region1 region2; do
        python3 make_combine_workspace.py --cat="inclusive" --region ${region} --data \
                                        --withSyst \
                                        --input_tag altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_isoCut \
                                        --tag altbkg_chebyshev_withScaleSyst_withMeanNuisance_IDSF_triggerSF_isoCut_bySubera \
                                        --era ${era} \
                                        --folder_tag 260312 \
                                        --binned &> logs/260312/workspace_inclusive_${region}_data_altbkg_chebyshev_withScaleSyst_withMeanNuisance_IDSF_triggerSF_isoCut_bySubera_${era}_binned_log
    done
done

python3 scripts/run_limits_parallel.py --cat inclusive \
                                      --tag altbkg_chebyshev_withScaleSyst_withMeanNuisance_IDSF_triggerSF_isoCut_bySubera_binned \
                                      --folder_tag 260312 \
                                      --eras allYears \
                                      --no_caching \
                                      --regions region0 region1 region2 \
                                      --data

python3 scripts/run_diagnostics_parallel.py --cat inclusive \
                                            --folder_tag 260312 \
                                            --tag altbkg_chebyshev_withScaleSyst_withMeanNuisance_IDSF_triggerSF_isoCut_bySubera_binned \
                                            --regions region0 region1 region2 \
                                            --data --binned \
                                            --eras 2022 2022EE 2023 2023BPix

python3 scripts/plot_limits_result.py -i cards/260312/cards_region0_data_altbkg_chebyshev_withScaleSyst_withMeanNuisance_IDSF_triggerSF_isoCut_bySubera_binned cards/260312/cards_region1_data_altbkg_chebyshev_withScaleSyst_withMeanNuisance_IDSF_triggerSF_isoCut_bySubera_binned cards/260312/cards_region2_data_altbkg_chebyshev_withScaleSyst_withMeanNuisance_IDSF_triggerSF_isoCut_bySubera_binned \
                                      -c inclusive -r region0 region1 region2 \
                                      --era allYears \
                                      -o /eos/home-n/npalmeri/www/DiElectron/sensitivity/260312/fitDiagnostics_grid_data_altbkg_chebyshev_withScaleSyst_withMeanNuisance_IDSF_triggerSF_isoCut_bySubera_binned/mu0/inclusive_allYears &> /eos/home-n/npalmeri/www/DiElectron/sensitivity/260312/fitDiagnostics_grid_data_altbkg_chebyshev_withScaleSyst_withMeanNuisance_IDSF_triggerSF_isoCut_bySubera_binned/mu0/inclusive_allYears/limits_summary_region0_region1_region2.log

python3 scripts/plot_limits_comparison.py --input_folders "260312/fitDiagnostics_grid_data_altbkg_chebyshev_withScaleSyst_withMeanNuisance_IDSF_triggerSF_isoCut_bySubera_binned/mu0/inclusive_allYears" \
                                                          "260226/fitDiagnostics_grid_data_altbkg_chebyshev_withScaleSyst_withMeanNuisance_IDSF_triggerSF_bySubera_binned/mu0/inclusive_allYears" \
                                          -o "/eos/home-n/npalmeri/www/DiElectron/sensitivity/260312/fitDiagnostics_grid_data_altbkg_chebyshev_withScaleSyst_withMeanNuisance_IDSF_triggerSF_isoCut_bySubera_binned/mu0/inclusive_allYears" \
                                          --region region0 region1 region2 \
                                          --labels "With iso cut" "No iso cut"\
                                          --tag "data_isoCut"