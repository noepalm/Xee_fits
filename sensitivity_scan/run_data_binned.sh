################################
####          DATA          ####
################################

python3 make_combine_workspace.py --cat="inclusive" --region region0 --data --binned &> logs/workspace_inclusive_region0_data_binned_log &
source scripts/run_diagnostics_parallel.sh --cat inclusive --region region0 --data --binned --tag binned &> logs/diagnostics_inclusive_region0_data_binned_log &
source scripts/run_limits_parallel.sh --cat inclusive --region region0 --data --tag binned &> logs/limits_inclusive_region0_data_binned_log &

python3 make_combine_workspace.py --cat="inclusive" --region region1 --data --binned &> logs/workspace_inclusive_region1_data_binned_log
source scripts/run_diagnostics_parallel.sh --cat inclusive --region region1 --data --binned --tag binned &> logs/diagnostics_inclusive_region1_data_binned_log &
source scripts/run_limits_parallel.sh --cat inclusive --region region1 --data --tag binned &> logs/limits_inclusive_region1_data_binned_log &

python3 make_combine_workspace.py --cat="inclusive" --region region2 --data --binned &> logs/workspace_inclusive_region2_data_binned_log
source scripts/run_limits_parallel.sh --cat inclusive --region region2 --data --tag binned &> logs/limits_inclusive_region2_data_binned_log &
source scripts/run_diagnostics_parallel.sh --cat inclusive --region region2 --data --binned --tag binned &> logs/diagnostics_inclusive_region2_data_binned_log &

### ENVELOPE 
python3 make_combine_workspace.py --cat="inclusive" --region region0 --envelope --data --binned --tag envelope &> logs/workspace_inclusive_region0_data_binned_envelope_log &
source scripts/run_limits_parallel.sh --cat inclusive --region region0 --data --tag envelope_binned &> logs/limits_inclusive_region0_data_binned_envelope_log &
source scripts/run_diagnostics_parallel.sh --cat inclusive --region region0 --data --binned --tag envelope_binned &> logs/diagnostics_inclusive_region0_data_binned_envelope_log &

python3 make_combine_workspace.py --cat="inclusive" --region region1 --envelope --data --binned --tag envelope &> logs/workspace_inclusive_region1_data_binned_envelope_log &
source scripts/run_limits_parallel.sh --cat inclusive --region region1 --data --tag envelope_binned &> logs/limits_inclusive_region1_data_binned_envelope_log
source scripts/run_diagnostics_parallel.sh --cat inclusive --region region1 --data --binned --tag envelope_binned &> logs/diagnostics_inclusive_region1_data_binned_envelope_log &

python3 make_combine_workspace.py --cat="inclusive" --region region2 --envelope --data --binned --tag envelope &> logs/workspace_inclusive_region2_data_binned_envelope_log &
source scripts/run_limits_parallel.sh --cat inclusive --region region2 --data --tag envelope_binned &> logs/limits_inclusive_region2_data_binned_envelope_log &
source scripts/run_diagnostics_parallel.sh --cat inclusive --region region2 --data --binned --tag envelope_binned &> logs/diagnostics_inclusive_region2_data_binned_envelope_log &

### ALT BKGs (input to above)

# Chebyshev
python3 make_combine_workspace.py --cat="inclusive" --region region0 --data --input_tag altbkg_chebyshev --tag altbkg_chebyshev --binned &> logs/workspace_inclusive_region0_data_altbkg_chebyshev_binned_log
source scripts/run_limits_parallel.sh --cat inclusive --region region0 --tag altbkg_chebyshev_binned --data &> logs/limits_inclusive_region0_data_altbkg_chebyshev_binned_log &
source scripts/run_diagnostics_parallel.sh --cat inclusive --region region0 --data --binned --tag altbkg_chebyshev_binned &> logs/diagnostics_inclusive_region0_data_altbkg_chebyshev_binned_log &

python3 make_combine_workspace.py --cat="inclusive" --region region1 --data --input_tag altbkg_chebyshev --tag altbkg_chebyshev --binned &> logs/workspace_inclusive_region1_data_altbkg_chebyshev_binned_log
source scripts/run_limits_parallel.sh --cat inclusive --region region1 --tag altbkg_chebyshev_binned --data &> logs/limits_inclusive_region1_data_altbkg_chebyshev_binned_log &
source scripts/run_diagnostics_parallel.sh --cat inclusive --region region1 --data --binned --tag altbkg_chebyshev_binned &> logs/diagnostics_inclusive_region1_data_altbkg_chebyshev_binned_log &

python3 make_combine_workspace.py --cat="inclusive" --region region2 --data --input_tag altbkg_chebyshev --tag altbkg_chebyshev --binned &> logs/workspace_inclusive_region2_data_altbkg_chebyshev_binned_log
source scripts/run_limits_parallel.sh --cat inclusive --region region2 --tag altbkg_chebyshev_binned --data &> logs/limits_inclusive_region2_data_altbkg_chebyshev_binned_log &
source scripts/run_diagnostics_parallel.sh --cat inclusive --region region2 --data --binned --tag altbkg_chebyshev_binned &> logs/diagnostics_inclusive_region2_data_altbkg_chebyshev_binned_log &

# Poly * exp
python3 make_combine_workspace.py --cat="inclusive" --region region0 --data --input_tag altbkg_poly --tag altbkg_poly --binned &> logs/workspace_inclusive_region0_data_altbkg_poly_binned_log &
source scripts/run_limits_parallel.sh --cat inclusive --region region0 --tag altbkg_poly_binned --data &> logs/limits_inclusive_region0_data_altbkg_poly_binned_log &
source scripts/run_diagnostics_parallel.sh --cat inclusive --region region0 --data --binned --tag altbkg_poly_binned &> logs/diagnostics_inclusive_region0_data_altbkg_poly_binned_log &

python3 make_combine_workspace.py --cat="inclusive" --region region1 --data --input_tag altbkg_poly --tag altbkg_poly --binned &> logs/workspace_inclusive_region1_data_altbkg_poly_binned_log
source scripts/run_limits_parallel.sh --cat inclusive --region region1 --tag altbkg_poly_binned --data &> logs/limits_inclusive_region1_data_altbkg_poly_binned_log &
source scripts/run_diagnostics_parallel.sh --cat inclusive --region region1 --data --binned --tag altbkg_poly_binned &> logs/diagnostics_inclusive_region1_data_altbkg_poly_binned_log &

python3 make_combine_workspace.py --cat="inclusive" --region region2 --data --input_tag altbkg_poly --tag altbkg_poly --binned &> logs/workspace_inclusive_region2_data_altbkg_poly_binned_log &
source scripts/run_limits_parallel.sh --cat inclusive --region region2 --tag altbkg_poly_binned --data &> logs/limits_inclusive_region2_data_altbkg_poly_binned_log &
source scripts/run_diagnostics_parallel.sh --cat inclusive --region region2 --data --binned --tag altbkg_poly_binned &> logs/diagnostics_inclusive_region2_data_altbkg_poly_binned_log &


### TESTING UPDATED SIGNAL MODEL
python3 make_combine_workspace.py --cat="inclusive" --region region0 --data \
                                  --input_tag altbkg_chebyshev_newsignal --tag altbkg_chebyshev_newsignal \
                                  --folder_tag 251208 \
                                  --binned &> logs/workspace_inclusive_region0_data_altbkg_chebyshev_newsignal_binned_log &
source scripts/run_limits_parallel.sh --cat inclusive \
                                      --tag altbkg_chebyshev_newsignal_binned \
                                      --folder_tag 251208 \
                                      --region region0 \
                                      --no_caching \
                                      --data &> logs/limits_inclusive_region0_data_altbkg_chebyshev_newsignal_binned_log &
source scripts/run_diagnostics_parallel.sh --cat inclusive --folder_tag 251208 \
                                           --region region0 \
                                           --data --binned \
                                           --tag altbkg_chebyshev_newsignal_binned &> logs/diagnostics_inclusive_region0_data_altbkg_chebyshev_newsignal_binned_log &

python3 make_combine_workspace.py --cat="inclusive" --region region1 --data \
                                  --input_tag altbkg_chebyshev_newsignal --tag altbkg_chebyshev_newsignal \
                                  --folder_tag 251208 \
                                  --binned &> logs/workspace_inclusive_region1_data_altbkg_chebyshev_newsignal_binned_log &
source scripts/run_limits_parallel.sh --cat inclusive \
                                      --tag altbkg_chebyshev_newsignal_binned \
                                      --folder_tag 251208 \
                                      --region region1 \
                                      --no_caching \
                                      --data &> logs/limits_inclusive_region1_data_altbkg_chebyshev_newsignal_binned_log &
source scripts/run_diagnostics_parallel.sh --cat inclusive --folder_tag 251208 \
                                           --region region1 \
                                           --data --binned \
                                           --tag altbkg_chebyshev_newsignal_binned &> logs/diagnostics_inclusive_region1_data_altbkg_chebyshev_newsignal_binned_log &

python3 make_combine_workspace.py --cat="inclusive" --region region2 --data \
                                  --input_tag altbkg_chebyshev_newsignal --tag altbkg_chebyshev_newsignal \
                                  --folder_tag 251208 \
                                  --binned &> logs/workspace_inclusive_region2_data_altbkg_chebyshev_newsignal_binned_log &
source scripts/run_limits_parallel.sh --cat inclusive \
                                      --tag altbkg_chebyshev_newsignal_binned \
                                      --folder_tag 251208 \
                                      --region region2 \
                                      --no_caching \
                                      --data &> logs/limits_inclusive_region2_data_altbkg_chebyshev_newsignal_binned_log &
source scripts/run_diagnostics_parallel.sh --cat inclusive --folder_tag 251208 \
                                           --region region2 \
                                           --data --binned \
                                           --tag altbkg_chebyshev_newsignal_binned &> logs/diagnostics_inclusive_region2_data_altbkg_chebyshev_newsignal_binned_log &

# ================================================

# ALL REGIONS COMBINED

# REGION 0 + 1 + 2 PLOTS
python3 scripts/plot_limits_result.py -i cards/251208/cards_region0_data_altbkg_chebyshev_newsignal_binned cards/251208/cards_region1_data_altbkg_chebyshev_newsignal_binned cards/251208/cards_region2_data_altbkg_chebyshev_newsignal_binned \
                                      -c inclusive -r region0 region1 region2 \
                                      -o /eos/home-n/npalmeri/www/DiElectron/sensitivity/251208/fitDiagnostics_grid_data_altbkg_chebyshev_newsignal_binned/mu0/inclusive &> /eos/home-n/npalmeri/www/DiElectron/sensitivity/251208/fitDiagnostics_grid_data_altbkg_chebyshev_newsignal_binned/mu0/inclusive/limits_summary_region0_region1_region2.log
                                      
python3 plot_limits_comparison.py -i "251208/fitDiagnostics_grid_data_altbkg_chebyshev_newsignal_binned/mu0/inclusive/" \
                                  -o "/eos/home-n/npalmeri/www/DiElectron/sensitivity/251208/fitDiagnostics_grid_data_altbkg_chebyshev_newsignal_binned/mu0/inclusive" \
                                  -r region0 region1 region2 \
                                  --tag "data_chebyshev_overlap"

# Comparison for new signal model

python3 scripts/plot_limits_result.py -i cards/cards_region0_data_altbkg_chebyshev_binned cards/cards_region1_data_altbkg_chebyshev_binned cards/cards_region2_data_altbkg_chebyshev_binned \
                                      -c inclusive -r region0 region1 region2 \
                                      -o /eos/home-n/npalmeri/www/DiElectron/sensitivity/fitDiagnostics_grid_data_altbkg_chebyshev_binned/mu0/inclusive &> /eos/home-n/npalmeri/www/DiElectron/sensitivity/fitDiagnostics_grid_data_altbkg_chebyshev_binned/mu0/inclusive/limits_summary_region0_region1_region2.log

python3 plot_limits_comparison.py -i "251208/fitDiagnostics_grid_data_altbkg_chebyshev_newsignal_binned/mu0/inclusive/" "fitDiagnostics_grid_data_altbkg_chebyshev_binned/mu0/inclusive/" \
                                  -l "new signal" "old" \
                                  -o "/eos/home-n/npalmeri/www/DiElectron/sensitivity/251208/fitDiagnostics_grid_data_altbkg_chebyshev_newsignal_binned/mu0/inclusive" \
                                  -r region0 region1 region2 \
                                  --overlap \
                                  --tag "data_chebyshev_newsignal"

python3 plot_limits_comparison.py -i "251208/fitDiagnostics_grid_data_altbkg_chebyshev_newsignal_binned/mu0/inclusive/" "fitDiagnostics_grid_data_altbkg_chebyshev_binned/mu0/inclusive/" \
                                  -l "new signal" "old" \
                                  -o "/eos/home-n/npalmeri/www/DiElectron/sensitivity/251208/fitDiagnostics_grid_data_altbkg_chebyshev_newsignal_binned/mu0/inclusive" \
                                  -r region0 region1 region2 \
                                  --overlap --mu \
                                  --tag "mu_data_chebyshev_newsignal"
