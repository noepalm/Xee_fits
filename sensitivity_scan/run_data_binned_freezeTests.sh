################################
####          DATA          ####
################################

# python3 make_combine_workspace.py --cat="inclusive" --region region1 --data \
#                                   --withSyst \
#                                   --input_tag altbkg_chebyshev_minbiasFreeze --tag altbkg_chebyshev_minbiasFreeze \
#                                   --folder_tag 260205 \
#                                   --binned &> logs/workspace_inclusive_region1_data_altbkg_chebyshev_minbiasFreeze_binned_log
# source scripts/run_limits_parallel.sh --cat inclusive \
#                                       --tag altbkg_chebyshev_minbiasFreeze_binned \
#                                       --folder_tag 260205 \
#                                       --region region1 \
#                                       --data &> logs/limits_inclusive_region1_data_altbkg_chebyshev_minbiasFreeze_binned_log &
# source scripts/run_diagnostics_parallel.sh --cat inclusive --folder_tag 260205 \
#                                            --region region1 \
#                                            --data --binned \
#                                            --tag altbkg_chebyshev_minbiasFreeze_binned &> logs/diagnostics_inclusive_region1_data_altbkg_chebyshev_minbiasFreeze_binned_log &

# wait

# python3 make_combine_workspace.py --cat="inclusive" --region region1 --data \
#                                   --withSyst \
#                                   --input_tag altbkg_chebyshev_promptMCFreeze --tag altbkg_chebyshev_promptMCFreeze \
#                                   --folder_tag 260205 \
#                                   --binned &> logs/workspace_inclusive_region1_data_altbkg_chebyshev_promptMCFreeze_binned_log
# source scripts/run_limits_parallel.sh --cat inclusive \
#                                       --tag altbkg_chebyshev_promptMCFreeze_binned \
#                                       --folder_tag 260205 \
#                                       --region region1 \
#                                       --data &> logs/limits_inclusive_region1_data_altbkg_chebyshev_promptMCFreeze_binned_log &
# source scripts/run_diagnostics_parallel.sh --cat inclusive --folder_tag 260205 \
#                                            --region region1 \
#                                            --data --binned \
#                                            --tag altbkg_chebyshev_promptMCFreeze_binned &> logs/diagnostics_inclusive_region1_data_altbkg_chebyshev_promptMCFreeze_binned_log &

# wait

python3 make_combine_workspace.py --cat="inclusive" --region region1 --data \
                                  --withSyst \
                                  --input_tag altbkg_chebyshev_dataFreeze --tag altbkg_chebyshev_dataFreeze \
                                  --folder_tag 260205 \
                                  --binned &> logs/workspace_inclusive_region1_data_altbkg_chebyshev_dataFreeze_binned_log
source scripts/run_limits_parallel.sh --cat inclusive \
                                      --tag altbkg_chebyshev_dataFreeze_binned \
                                      --folder_tag 260205 \
                                      --region region1 \
                                      --data &> logs/limits_inclusive_region1_data_altbkg_chebyshev_dataFreeze_binned_log &
source scripts/run_diagnostics_parallel.sh --cat inclusive --folder_tag 260205 \
                                           --region region1 \
                                           --data --binned \
                                           --tag altbkg_chebyshev_dataFreeze_binned &> logs/diagnostics_inclusive_region1_data_altbkg_chebyshev_dataFreeze_binned_log &