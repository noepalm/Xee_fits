python3 make_combine_workspace.py --cat="inclusive" -r="region2" &> logs/workspace_inclusive_region2_log

source scripts/run_diagnostics_parallel.sh --cat inclusive --tag test \
                                           --fit_tag region2 \
                                           --region region2 &> logs/diagnostics_inclusive_region2_log

source scripts/run_limits_parallel.sh --cat inclusive --fit_tag region2 --tag test \
                                      --region region2 &> logs/limits_inclusive_region2_log