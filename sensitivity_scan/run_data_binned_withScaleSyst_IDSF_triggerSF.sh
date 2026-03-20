# ################################
# ####          DATA          ####
# ################################

# python3 make_combine_workspace.py --cat="inclusive" --region region1 --data \
#                                   --withSyst \
#                                   --input_tag altbkg_chebyshev_withScaleSyst_IDSF_triggerSF --tag altbkg_chebyshev_withScaleSyst_IDSF_triggerSF \
#                                   --folder_tag 260226 \
#                                   --binned &> logs/workspace_inclusive_region1_data_altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_binned_log
# source scripts/run_limits_parallel.sh --cat inclusive \
#                                       --tag altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_binned \
#                                       --folder_tag 260226 \
#                                       --region region1 \
#                                       --data &> logs/limits_inclusive_region1_data_altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_withSigmaNuisance_binned_log &
# source scripts/run_diagnostics_parallel.sh --cat inclusive --folder_tag 260226 \
#                                            --region region1 \
#                                            --data --binned \
#                                            --tag altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_binned &> logs/diagnostics_inclusive_region1_data_altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_binned_log &

# wait 

# python3 make_combine_workspace.py --cat="inclusive" --region region0 --data \
#                                   --withSyst \
#                                   --input_tag altbkg_chebyshev_withScaleSyst_IDSF_triggerSF --tag altbkg_chebyshev_withScaleSyst_IDSF_triggerSF \
#                                   --folder_tag 260226 \
#                                   --binned &> logs/workspace_inclusive_region0_data_altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_binned_log
# source scripts/run_limits_parallel.sh --cat inclusive \
#                                       --tag altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_binned \
#                                       --folder_tag 260226 \
#                                       --region region0 \
#                                       --data &> logs/limits_inclusive_region0_data_altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_binned_log &
# source scripts/run_diagnostics_parallel.sh --cat inclusive --folder_tag 260226 \
#                                            --region region0 \
#                                            --data --binned \
#                                            --tag altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_binned &> logs/diagnostics_inclusive_region0_data_altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_binned_log &

# wait 

# python3 make_combine_workspace.py --cat="inclusive" --region region2 --data \
#                                   --withSyst \
#                                   --input_tag altbkg_chebyshev_withScaleSyst_IDSF_triggerSF --tag altbkg_chebyshev_withScaleSyst_IDSF_triggerSF \
#                                   --folder_tag 260226 \
#                                   --binned &> logs/workspace_inclusive_region2_data_altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_binned_log
# source scripts/run_limits_parallel.sh --cat inclusive \
#                                       --tag altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_binned \
#                                       --folder_tag 260226 \
#                                       --region region2 \
#                                       --no_caching \
#                                       --data &> logs/limits_inclusive_region2_data_altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_binned_log &
# source scripts/run_diagnostics_parallel.sh --cat inclusive --folder_tag 260226 \
#                                            --region region2 \
#                                            --data --binned \
#                                            --tag altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_binned &> logs/diagnostics_inclusive_region2_data_altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_binned_log &

# wait 

# python3 scripts/plot_limits_result.py -i cards/260226/cards_region0_data_altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_binned cards/260226/cards_region1_data_altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_binned cards/260226/cards_region2_data_altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_binned \
#                                       -c inclusive -r region0 region1 region2 \
#                                       -o /eos/home-n/npalmeri/www/DiElectron/sensitivity/260226/fitDiagnostics_grid_data_altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_binned/mu0/inclusive &> /eos/home-n/npalmeri/www/DiElectron/sensitivity/260226/fitDiagnostics_grid_data_altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_binned/mu0/inclusive/limits_summary_region0_region1_region2.log

############################
#### WITH MEAN NUISANCE ####
############################

python3 make_combine_workspace.py --cat="inclusive" --region region1 --data \
                                  --withSyst \
                                  --input_tag altbkg_chebyshev_withScaleSyst_IDSF_triggerSF --tag altbkg_chebyshev_withScaleSyst_withMeanNuisance_IDSF_triggerSF \
                                  --folder_tag 260226 \
                                  --binned &> logs/workspace_inclusive_region1_data_altbkg_chebyshev_withScaleSyst_withMeanNuisance_IDSF_triggerSF_binned_log
source scripts/run_limits_parallel.sh --cat inclusive \
                                      --tag altbkg_chebyshev_withScaleSyst_withMeanNuisance_IDSF_triggerSF_binned \
                                      --folder_tag 260226 \
                                      --region region1 \
                                      --data &> logs/limits_inclusive_region1_data_altbkg_chebyshev_withScaleSyst_withMeanNuisance_IDSF_triggerSF_binned_log &
source scripts/run_diagnostics_parallel.sh --cat inclusive --folder_tag 260226 \
                                           --region region1 \
                                           --data --binned \
                                           --tag altbkg_chebyshev_withScaleSyst_withMeanNuisance_IDSF_triggerSF_binned &> logs/diagnostics_inclusive_region1_data_altbkg_chebyshev_withScaleSyst_withMeanNuisance_IDSF_triggerSF_binned_log &

wait 

python3 make_combine_workspace.py --cat="inclusive" --region region0 --data \
                                  --withSyst \
                                  --input_tag altbkg_chebyshev_withScaleSyst_IDSF_triggerSF --tag altbkg_chebyshev_withScaleSyst_withMeanNuisance_IDSF_triggerSF \
                                  --folder_tag 260226 \
                                  --binned &> logs/workspace_inclusive_region0_data_altbkg_chebyshev_withScaleSyst_withMeanNuisance_IDSF_triggerSF_binned_log
source scripts/run_limits_parallel.sh --cat inclusive \
                                      --tag altbkg_chebyshev_withScaleSyst_withMeanNuisance_IDSF_triggerSF_binned \
                                      --folder_tag 260226 \
                                      --region region0 \
                                      --data &> logs/limits_inclusive_region0_data_altbkg_chebyshev_withScaleSyst_withMeanNuisance_IDSF_triggerSF_binned_log &
source scripts/run_diagnostics_parallel.sh --cat inclusive --folder_tag 260226 \
                                           --region region0 \
                                           --data --binned \
                                           --tag altbkg_chebyshev_withScaleSyst_withMeanNuisance_IDSF_triggerSF_binned &> logs/diagnostics_inclusive_region0_data_altbkg_chebyshev_withScaleSyst_withMeanNuisance_IDSF_triggerSF_binned_log &

wait 

python3 make_combine_workspace.py --cat="inclusive" --region region2 --data \
                                  --withSyst \
                                  --input_tag altbkg_chebyshev_withScaleSyst_IDSF_triggerSF --tag altbkg_chebyshev_withScaleSyst_withMeanNuisance_IDSF_triggerSF \
                                  --folder_tag 260226 \
                                  --binned &> logs/workspace_inclusive_region2_data_altbkg_chebyshev_withScaleSyst_withMeanNuisance_IDSF_triggerSF_binned_log
source scripts/run_limits_parallel.sh --cat inclusive \
                                      --tag altbkg_chebyshev_withScaleSyst_withMeanNuisance_IDSF_triggerSF_binned \
                                      --folder_tag 260226 \
                                      --region region2 \
                                      --data &> logs/limits_inclusive_region2_data_altbkg_chebyshev_withScaleSyst_withMeanNuisance_IDSF_triggerSF_binned_log &
source scripts/run_diagnostics_parallel.sh --cat inclusive --folder_tag 260226 \
                                           --region region2 \
                                           --data --binned \
                                           --tag altbkg_chebyshev_withScaleSyst_withMeanNuisance_IDSF_triggerSF_binned &> logs/diagnostics_inclusive_region2_data_altbkg_chebyshev_withScaleSyst_withMeanNuisance_IDSF_triggerSF_binned_log &

wait 

python3 scripts/plot_limits_result.py -i cards/260226/cards_region0_data_altbkg_chebyshev_withScaleSyst_withMeanNuisance_IDSF_triggerSF_binned cards/260226/cards_region1_data_altbkg_chebyshev_withScaleSyst_withMeanNuisance_IDSF_triggerSF_binned cards/260226/cards_region2_data_altbkg_chebyshev_withScaleSyst_withMeanNuisance_IDSF_triggerSF_binned \
                                      -c inclusive -r region0 region1 region2 \
                                      -o /eos/home-n/npalmeri/www/DiElectron/sensitivity/260226/fitDiagnostics_grid_data_altbkg_chebyshev_withScaleSyst_withMeanNuisance_IDSF_triggerSF_binned/mu0/inclusive &> /eos/home-n/npalmeri/www/DiElectron/sensitivity/260226/fitDiagnostics_grid_data_altbkg_chebyshev_withScaleSyst_withMeanNuisance_IDSF_triggerSF_binned/mu0/inclusive/limits_summary_region0_region1_region2.log
