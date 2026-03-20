################################
####          DATA          ####
################################

# python3 make_combine_workspace.py --cat="inclusive" --region region1 --data --input_tag altbkg_chebyshev --tag altbkg_chebyshev --binned &> logs/workspace_inclusive_region1_data_altbkg_chebyshev_binned_log
# source scripts/run_limits_parallel.sh --cat inclusive --region region1 --tag altbkg_chebyshev_binned --data &> logs/limits_inclusive_region1_data_altbkg_chebyshev_binned_log &
# source scripts/run_diagnostics_parallel.sh --cat inclusive --region region1 --data --binned --tag altbkg_chebyshev_binned &> logs/diagnostics_inclusive_region1_data_altbkg_chebyshev_binned_log &


# python3 make_combine_workspace.py --cat="inclusive" --region region1 --data \
#                                   --withSyst \
#                                   --input_tag altbkg_chebyshev_withSyst --tag altbkg_chebyshev_withSyst \
#                                   --folder_tag 260122 \
#                                   --binned &> logs/workspace_inclusive_region1_data_altbkg_chebyshev_withSyst_binned_log
# source scripts/run_limits_parallel.sh --cat inclusive \
#                                       --tag altbkg_chebyshev_withSyst_binned \
#                                       --folder_tag 260122 \
#                                       --region region1 \
#                                       --no_caching \
#                                       --data &> logs/limits_inclusive_region1_data_altbkg_chebyshev_withSyst_withSigmaNuisance_binned_log &
# source scripts/run_diagnostics_parallel.sh --cat inclusive --folder_tag 260122 \
#                                            --region region1 \
#                                            --plot_only \
#                                            --data --binned \
#                                            --tag altbkg_chebyshev_withSyst_binned &> logs/diagnostics_inclusive_region1_data_altbkg_chebyshev_withSyst_binned_log &

# python3 make_combine_workspace.py --cat="inclusive" --region region0 --data \
#                                   --withSyst \
#                                   --input_tag altbkg_chebyshev_withSyst --tag altbkg_chebyshev_withSyst \
#                                   --folder_tag 260122 \
#                                   --binned &> logs/workspace_inclusive_region0_data_altbkg_chebyshev_withSyst_binned_log
# source scripts/run_limits_parallel.sh --cat inclusive \
#                                       --tag altbkg_chebyshev_withSyst_binned \
#                                       --folder_tag 260122 \
#                                       --region region0 \
#                                       --no_caching \
#                                       --data &> logs/limits_inclusive_region0_data_altbkg_chebyshev_withSyst_binned_log &
# source scripts/run_diagnostics_parallel.sh --cat inclusive --folder_tag 260122 \
#                                            --region region0 \
#                                            --data --binned \
#                                            --tag altbkg_chebyshev_withSyst_binned &> logs/diagnostics_inclusive_region0_data_altbkg_chebyshev_withSyst_binned_log &

# python3 make_combine_workspace.py --cat="inclusive" --region region2 --data \
#                                   --withSyst \
#                                   --input_tag altbkg_chebyshev_withSyst --tag altbkg_chebyshev_withSyst \
#                                   --folder_tag 260122 \
#                                   --binned &> logs/workspace_inclusive_region2_data_altbkg_chebyshev_withSyst_binned_log
# source scripts/run_limits_parallel.sh --cat inclusive \
#                                       --tag altbkg_chebyshev_withSyst_binned \
#                                       --folder_tag 260122 \
#                                       --region region2 \
#                                       --no_caching \
#                                       --data &> logs/limits_inclusive_region2_data_altbkg_chebyshev_withSyst_binned_log &
# source scripts/run_diagnostics_parallel.sh --cat inclusive --folder_tag 260122 \
#                                            --region region2 \
#                                            --data --binned \
#                                            --tag altbkg_chebyshev_withSyst_binned &> logs/diagnostics_inclusive_region2_data_altbkg_chebyshev_withSyst_binned_log &

python3 scripts/plot_limits_result.py -i cards/260122/cards_region0_data_altbkg_chebyshev_withSyst_binned cards/260122/cards_region1_data_altbkg_chebyshev_withSyst_binned cards/260122/cards_region2_data_altbkg_chebyshev_withSyst_binned \
                                      -c inclusive -r region0 region1 region2 \
                                      -o /eos/home-n/npalmeri/www/DiElectron/sensitivity/260122/fitDiagnostics_grid_data_altbkg_chebyshev_withSyst_binned/mu0/inclusive &> /eos/home-n/npalmeri/www/DiElectron/sensitivity/260122/fitDiagnostics_grid_data_altbkg_chebyshev_withSyst_binned/mu0/inclusive/limits_summary_region0_region1_region2.log

#############################
#### WITH SIGMA NUISANCE ####
#############################

# python3 make_combine_workspace.py --cat="inclusive" --region region1 --data \
#                                   --withSyst \
#                                   --input_tag altbkg_chebyshev_withSyst --tag altbkg_chebyshev_withSyst_withSigmaNuisance \
#                                   --folder_tag 260122 \
#                                   --binned &> logs/workspace_inclusive_region1_data_altbkg_chebyshev_withSyst_withSigmaNuisance_binned_log &
# source scripts/run_limits_parallel.sh --cat inclusive \
#                                       --tag altbkg_chebyshev_withSyst_withSigmaNuisance_binned \
#                                       --folder_tag 260122 \
#                                       --region region1 \
#                                       --no_caching \
#                                       --data &> logs/limits_inclusive_region1_data_altbkg_chebyshev_withSyst_withSigmaNuisance_binned_log &
# source scripts/run_diagnostics_parallel.sh --cat inclusive --folder_tag 260122 \
#                                            --region region1 \
#                                            --data --binned \
#                                            --tag altbkg_chebyshev_withSyst_withSigmaNuisance_binned &> logs/diagnostics_inclusive_region1_data_altbkg_chebyshev_withSyst_withSigmaNuisance_binned_log &

# python3 make_combine_workspace.py --cat="inclusive" --region region0 --data \
#                                   --withSyst \
#                                   --input_tag altbkg_chebyshev_withSyst --tag altbkg_chebyshev_withSyst_withSigmaNuisance \
#                                   --folder_tag 260122 \
#                                   --binned &> logs/workspace_inclusive_region0_data_altbkg_chebyshev_withSyst_withSigmaNuisance_binned_log &
# source scripts/run_limits_parallel.sh --cat inclusive \
#                                       --tag altbkg_chebyshev_withSyst_withSigmaNuisance_binned \
#                                       --folder_tag 260122 \
#                                       --region region0 \
#                                       --no_caching \
#                                       --data &> logs/limits_inclusive_region0_data_altbkg_chebyshev_withSyst_withSigmaNuisance_binned_log &
# source scripts/run_diagnostics_parallel.sh --cat inclusive --folder_tag 260122 \
#                                            --region region0 \
#                                            --data --binned \
#                                            --tag altbkg_chebyshev_withSyst_withSigmaNuisance_binned &> logs/diagnostics_inclusive_region0_data_altbkg_chebyshev_withSyst_withSigmaNuisance_binned_log &

# python3 make_combine_workspace.py --cat="inclusive" --region region2 --data \
#                                   --withSyst \
#                                   --input_tag altbkg_chebyshev_withSyst --tag altbkg_chebyshev_withSyst_withSigmaNuisance \
#                                   --folder_tag 260122 \
#                                   --binned &> logs/workspace_inclusive_region2_data_altbkg_chebyshev_withSyst_withSigmaNuisance_binned_log &
# source scripts/run_limits_parallel.sh --cat inclusive \
#                                       --tag altbkg_chebyshev_withSyst_withSigmaNuisance_binned \
#                                       --folder_tag 260122 \
#                                       --region region2 \
#                                       --no_caching \
#                                       --data &> logs/limits_inclusive_region2_data_altbkg_chebyshev_withSyst_withSigmaNuisance_binned_log &
# source scripts/run_diagnostics_parallel.sh --cat inclusive --folder_tag 260122 \
#                                            --region region2 \
#                                            --data --binned \
#                                            --tag altbkg_chebyshev_withSyst_withSigmaNuisance_binned &> logs/diagnostics_inclusive_region2_data_altbkg_chebyshev_withSyst_withSigmaNuisance_binned_log &

# python3 scripts/plot_limits_result.py -i cards/260122/cards_region0_data_altbkg_chebyshev_withSyst_withSigmaNuisance_binned cards/260122/cards_region1_data_altbkg_chebyshev_withSyst_withSigmaNuisance_binned cards/260122/cards_region2_data_altbkg_chebyshev_withSyst_withSigmaNuisance_binned \
#                                       -c inclusive -r region0 region1 region2 \
#                                       -o /eos/home-n/npalmeri/www/DiElectron/sensitivity/260122/fitDiagnostics_grid_data_altbkg_chebyshev_withSyst_withSigmaNuisance_binned/mu0/inclusive &> /eos/home-n/npalmeri/www/DiElectron/sensitivity/260122/fitDiagnostics_grid_data_altbkg_chebyshev_withSyst_withSigmaNuisance_binned/mu0/inclusive/limits_summary_region0_region1_region2.log
