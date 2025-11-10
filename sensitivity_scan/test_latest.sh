### REGION 1

# NOMINAL WEIGHTS
python3 make_combine_workspace.py --cat="eta" --region region1 &> logs/workspace_eta_region1_log
python3 make_combine_workspace.py --cat="dR" --region region1 &> logs/workspace_dR_region1_log
python3 make_combine_workspace.py --cat="inclusive" --region region1 &> logs/workspace_inclusive_region1_log

python3 make_combine_workspace.py --cat="eta" --region region1 --tag nanov15 &> logs/workspace_eta_region1_nanov15_log
python3 make_combine_workspace.py --cat="dR" --region region1 --tag nanov15 &> logs/workspace_dR_region1_nanov15_log
python3 make_combine_workspace.py --cat="inclusive" --region region1 --tag nanov15 &> logs/workspace_inclusive_region1_nanov15_log

source scripts/run_diagnostics_parallel.sh --cat eta --region region1  &> logs/diagnostics_eta_region1_log &
source scripts/run_diagnostics_parallel.sh --cat dR --region region1 &> logs/diagnostics_dR_region1_log &
source scripts/run_diagnostics_parallel.sh --cat inclusive --region region1 &> logs/diagnostics_inclusive_region1_log &

source scripts/run_limits_parallel.sh --cat eta --region region1 &> logs/limits_eta_region1_log &
source scripts/run_limits_parallel.sh --cat dR --region region1 &> logs/limits_dR_region1_log &
wait
source scripts/run_limits_parallel.sh --cat eta --region region1 --combination &> logs/limits_etaCombination_region1_log &
source scripts/run_limits_parallel.sh --cat dR --region region1 --combination &> logs/limits_dRCombination_region1_log &
wait
source scripts/run_limits_parallel.sh --cat inclusive --region region1 &> logs/limits_inclusive_region1_log &

source scripts/run_limits_parallel.sh --cat eta --region region1 --tag nanov15 &> logs/limits_eta_region1_nanov15_log &
source scripts/run_limits_parallel.sh --cat dR --region region1 --tag nanov15 &> logs/limits_dR_region1_nanov15_log &
source scripts/run_limits_parallel.sh --cat eta --region region1 --tag nanov15 --combination &> logs/limits_etaCombination_region1_nanov15_log &
source scripts/run_limits_parallel.sh --cat dR --region region1 --tag nanov15 --combination &> logs/limits_dRCombination_region1_nanov15_log &
source scripts/run_limits_parallel.sh --cat inclusive --region region1 --tag nanov15 &> logs/limits_inclusive_region1_nanov15_log &

# # 1/100 WEIGHTS
# python3 make_combine_workspace.py --cat="eta" --bkg_div100 --tag="div100wgt" &> logs/workspace_eta_div100wgt_log
# python3 make_combine_workspace.py --cat="dR" --bkg_div100 --tag="div100wgt" &> logs/workspace_dR_div100wgt_log
# python3 make_combine_workspace.py --cat="inclusive" --bkg_div100 --tag="div100wgt" &> logs/workspace_inclusive_div100wgt_log

# source scripts/run_limits_parallel.sh --cat inclusive --region region1 --tag div100wgt &> logs/limits_inclusive_div100wgt_region1_log &
# source scripts/run_limits_parallel.sh --cat eta --region region1 --tag div100wgt &> logs/limits_eta_div100wgt_region1_log &
# source scripts/run_limits_parallel.sh --cat dR --region region1 --tag div100wgt &> logs/limits_dR_div100wgt_region1_log &

### REGION 2

# NOMINAL WEIGHTS
python3 make_combine_workspace.py --cat="eta" --region region2 &> logs/workspace_eta_region2_log
python3 make_combine_workspace.py --cat="dR" --region region2 &> logs/workspace_dR_region2_log
python3 make_combine_workspace.py --cat="inclusive" --region region2 &> logs/workspace_inclusive_region2_log

python3 make_combine_workspace.py --cat="eta" --region region2 --tag nanov15 &> logs/workspace_eta_region2_nanov15_log
python3 make_combine_workspace.py --cat="dR" --region region2 --tag nanov15 &> logs/workspace_dR_region2_nanov15_log
python3 make_combine_workspace.py --cat="inclusive" --region region2 --tag nanov15 &> logs/workspace_inclusive_region2_nanov15_log

source scripts/run_diagnostics_parallel.sh --cat eta --region region2 &> logs/diagnostics_eta_region2_log &
source scripts/run_diagnostics_parallel.sh --cat dR --region region2 &> logs/diagnostics_dR_region2_log &
source scripts/run_diagnostics_parallel.sh --cat inclusive --region region2 &> logs/diagnostics_inclusive_region2_log

source scripts/run_limits_parallel.sh --cat eta --region region2 &> logs/limits_eta_region2_log &
source scripts/run_limits_parallel.sh --cat dR --region region2 &> logs/limits_dR_region2_log &
source scripts/run_limits_parallel.sh --cat eta --region region2 --combination &> logs/limits_etaCombination_region2_log &
source scripts/run_limits_parallel.sh --cat dR --region region2 --combination &> logs/limits_dRCombination_region2_log &
source scripts/run_limits_parallel.sh --cat inclusive --region region2 &> logs/limits_inclusive_region2_log &

# source scripts/run_limits_parallel.sh --cat inclusive --region region2 --plot_only
# source scripts/run_limits_parallel.sh --cat eta --region region2 --plot_only
# source scripts/run_limits_parallel.sh --cat dR --region region2 --plot_only

# # 1/100 WEIGHTS
# python3 make_combine_workspace.py --cat="eta" --bkg_div100 --tag="div100wgt" &> logs/workspace_eta_div100wgt_log
# python3 make_combine_workspace.py --cat="dR" --bkg_div100 --tag="div100wgt" &> logs/workspace_dR_div100wgt_log
# python3 make_combine_workspace.py --cat="inclusive" --bkg_div100 --tag="div100wgt" &> logs/workspace_inclusive_div100wgt_log

# source scripts/run_limits_parallel.sh --cat inclusive --region region2 --tag div100wgt &> logs/limits_inclusive_div100wgt_region2_log &
# source scripts/run_limits_parallel.sh --cat eta --region region2 --tag div100wgt &> logs/limits_eta_div100wgt_region2_log &
# source scripts/run_limits_parallel.sh --cat dR --region region2 --tag div100wgt &> logs/limits_dR_div100wgt_region2_log &


### REGION 1
python3 make_combine_workspace.py --cat="inclusive" --region region0 &> logs/workspace_inclusive_region0_log
source scripts/run_diagnostics_parallel.sh --cat inclusive --region region0 &> logs/diagnostics_inclusive_region0_log &
source scripts/run_limits_parallel.sh --cat inclusive --region region0 &> logs/limits_inclusive_region0_log &

python3 make_combine_workspace.py --cat="eta" --region region0 &> logs/workspace_eta_region0_log
source scripts/run_diagnostics_parallel.sh --cat eta --region region0 &> logs/diagnostics_eta_region0_log &
source scripts/run_limits_parallel.sh --cat eta --region region0 &> logs/limits_eta_region0_log &
source scripts/run_limits_parallel.sh --cat eta --region region0 --combination &> logs/limits_etaCombination_region0_log &


### REGION1+2 PLOTS

python3 scripts/plot_limits_result.py -i cards_region1 cards_region2 \
                                      -c inclusive -r region1 region2 \
                                      -o /eos/home-n/npalmeri/www/DiElectron/sensitivity/fitDiagnostics_grid_reweight_categories/mu0/inclusive &> /eos/home-n/npalmeri/www/DiElectron/sensitivity/fitDiagnostics_grid_reweight_categories/mu0/inclusive/limits_summary_region1_region2.log

python3 scripts/plot_limits_result.py -i cards_region1 cards_region2 \
                                      -c etaCombination -r region1 region2 \
                                      -o /eos/home-n/npalmeri/www/DiElectron/sensitivity/fitDiagnostics_grid_reweight_categories/mu0/etaCombination &> /eos/home-n/npalmeri/www/DiElectron/sensitivity/fitDiagnostics_grid_reweight_categories/mu0/etaCombination/limits_summary_region1_region2.log

python3 scripts/plot_limits_result.py -i cards_region1 cards_region2 \
                                      -c etaHigh -r region1 region2 \
                                      -o /eos/home-n/npalmeri/www/DiElectron/sensitivity/fitDiagnostics_grid_reweight_categories/mu0/etaHigh &> /eos/home-n/npalmeri/www/DiElectron/sensitivity/fitDiagnostics_grid_reweight_categories/mu0/etaHigh/limits_summary_region1_region2.log

python3 scripts/plot_limits_result.py -i cards_region1 cards_region2 \
                                      -c etaLow -r region1 region2 \
                                      -o /eos/home-n/npalmeri/www/DiElectron/sensitivity/fitDiagnostics_grid_reweight_categories/mu0/etaLow &> /eos/home-n/npalmeri/www/DiElectron/sensitivity/fitDiagnostics_grid_reweight_categories/mu0/etaLow/limits_summary_region1_region2.log

python3 scripts/plot_limits_result.py -i cards_region1 cards_region2 \
                                      -c dRCombination -r region1 region2 \
                                      -o /eos/home-n/npalmeri/www/DiElectron/sensitivity/fitDiagnostics_grid_reweight_categories/mu0/dRCombination &> /eos/home-n/npalmeri/www/DiElectron/sensitivity/fitDiagnostics_grid_reweight_categories/mu0/dRCombination/limits_summary_region1_region2.log

# REGION 0 + 1 + 2 PLOTS
python3 scripts/plot_limits_result.py -i cards_region0 cards_region1 cards_region2 \
                                      -c inclusive -r region0 region1 region2 \
                                      -o /eos/home-n/npalmeri/www/DiElectron/sensitivity/fitDiagnostics_grid_reweight_categories/mu0/inclusive &> /eos/home-n/npalmeri/www/DiElectron/sensitivity/fitDiagnostics_grid_reweight_categories/mu0/inclusive/limits_summary_region0_region1_region2.log


# ========================================
#           DEBUGGING FIT ISSUE
# ========================================

python3 make_combine_workspace.py --cat="inclusive" --region region0 --tag debug &> logs/workspace_inclusive_region0_debug_log
source scripts/run_limits_parallel.sh --cat inclusive --region region0 --tag debug &> logs/limits_inclusive_region0_debug_log &

python3 make_combine_workspace.py --cat="inclusive" --region region1 --tag debug &> logs/workspace_inclusive_region1_debug_log
source scripts/run_diagnostics_parallel.sh --cat inclusive --region region1 --tag debug &> logs/diagnostics_inclusive_region1_debug_log &
source scripts/run_limits_parallel.sh --cat inclusive --region region1 --tag debug &> logs/limits_inclusive_region1_debug_log &

python3 make_combine_workspace.py --cat="inclusive" --region region2 --tag debug &> logs/workspace_inclusive_region2_debug_log
source scripts/run_limits_parallel.sh --cat inclusive --region region2 --tag debug &> logs/limits_inclusive_region2_debug_log &
source scripts/run_limits_parallel.sh --cat inclusive --region region2 --tag debug &> logs/limits_inclusive_region2_debug_5p0_log &


source scripts/run_diagnostics_parallel.sh --cat inclusive --region region1 --tag debug --plot_only


source scripts/run_limits_parallel.sh --cat inclusive --region region0 --plot_only

# =======================================
#           NANOV15 FULL STATS
# =======================================

# region0
python3 make_combine_workspace.py --cat="inclusive" --region region0 --tag nanov15 &> logs/workspace_inclusive_region0_nanov15_log
source scripts/run_diagnostics_parallel.sh --cat inclusive --region region0 --tag nanov15 &> logs/diagnostics_inclusive_region0_nanov15_log &
source scripts/run_limits_parallel.sh --cat inclusive --region region0 --tag nanov15 &> logs/limits_inclusive_region0_nanov15_log &

# region1
python3 make_combine_workspace.py --cat="inclusive" --region region1 --tag nanov15 &> logs/workspace_inclusive_region1_nanov15_log &
source scripts/run_diagnostics_parallel.sh --cat inclusive --region region1 --tag nanov15 &> logs/diagnostics_inclusive_region1_nanov15_log &
source scripts/run_limits_parallel.sh --cat inclusive --region region1 --tag nanov15 &> logs/limits_inclusive_region1_nanov15_log &

python3 make_combine_workspace.py --cat="eta" --region region1 --tag nanov15 &> logs/workspace_eta_region1_nanov15_log &
source scripts/run_diagnostics_parallel.sh --cat eta --region region1 --tag nanov15 &> logs/diagnostics_eta_region1_nanov15_log &
source scripts/run_limits_parallel.sh --cat eta --region region1 --tag nanov15 &> logs/limits_eta_region1_nanov15_log &
source scripts/run_limits_parallel.sh --cat eta --region region1 --tag nanov15 --combination &> logs/limits_etaCombination_region1_nanov15_log &

python3 make_combine_workspace.py --cat="dR" --region region1 --tag nanov15 &> logs/workspace_dR_region1_nanov15_log &
source scripts/run_diagnostics_parallel.sh --cat dR --region region1 --tag nanov15 &> logs/diagnostics_dR_region1_nanov15_log &
source scripts/run_limits_parallel.sh --cat dR --region region1 --tag nanov15 &> logs/limits_dR_region1_nanov15_log &
source scripts/run_limits_parallel.sh --cat dR --region region1 --tag nanov15 --combination &> logs/limits_dRCombination_region1_nanov15_log &

# region2 
python3 make_combine_workspace.py --cat="inclusive" --region region2 --tag nanov15 &> logs/workspace_inclusive_region2_nanov15_log &
source scripts/run_diagnostics_parallel.sh --cat inclusive --region region2 --tag nanov15 &> logs/diagnostics_inclusive_region2_nanov15_log &
source scripts/run_limits_parallel.sh --cat inclusive --region region2 --tag nanov15 &> logs/limits_inclusive_region2_nanov15_log &

python3 scripts/plot_limits_result.py -i cards_region0_nanov15 cards_region1_nanov15 cards_region2_nanov15 \
                                      -c inclusive -r region0 region1 region2 \
                                      -o /eos/home-n/npalmeri/www/DiElectron/sensitivity/fitDiagnostics_grid_reweight_categories_nanov15/mu0/inclusive &> /eos/home-n/npalmeri/www/DiElectron/sensitivity/fitDiagnostics_grid_reweight_categories_nanov15/mu0/inclusive/limits_summary_region0_region1_region2.log
