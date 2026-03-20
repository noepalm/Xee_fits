echo "Producing workspace for eta with reweighting"
python3 make_combine_workspace.py --cat="eta" &> logs/workspace_eta_log
tail -n 5 logs/workspace_eta_log
echo "Producing workspace for dR with reweighting"
python3 make_combine_workspace.py --cat="dR" &> logs/workspace_dR_log
tail -n 5 logs/workspace_dR_log
echo "Producing workspace for inclusive with reweighting"
python3 make_combine_workspace.py --cat="inclusive" &> logs/workspace_inclusive_log
tail -n 5 logs/workspace_inclusive_log

# echo "NOW RUNNING: inclusive diagnostics; reweight"
# source scripts/run_diagnostics_parallel.sh --cat inclusive &> logs/diagnostics_inclusive_log
# echo "NOW RUNNING: eta diagnostics; reweight"
# source scripts/run_diagnostics_parallel.sh --cat eta &> logs/diagnostics_eta_log
# echo "NOW RUNNING: dR diagnostics; reweight"
# source scripts/run_diagnostics_parallel.sh --cat dR &> logs/diagnostics_dR_log

# TEST 0: standard
source scripts/run_limits_parallel.sh --cat inclusive --region region1 &> logs/limits_inclusive_region1_log &
source scripts/run_limits_parallel.sh --cat eta --region region1 &> logs/limits_eta_region1_log &
source scripts/run_limits_parallel.sh --cat dR --region region1 &> logs/limits_dR_region1_log &
wait
tail -n 10 logs/limits_inclusive_region1_log
tail -n 10 logs/limits_eta_region1_log
tail -n 10 logs/limits_dR_region1_log

# TEST 1: run Asymptotic with rMin = 4
source scripts/run_limits_parallel.sh --cat inclusive --fit_tag Grid &> logs/limits_inclusive_Grid_log &
source scripts/run_limits_parallel.sh --cat eta --fit_tag Grid &> logs/limits_eta_Grid_log &
source scripts/run_limits_parallel.sh --cat dR --fit_tag Grid &> logs/limits_dR_Grid_log &
wait
tail -n 10 logs/limits_inclusive_Grid_log
tail -n 10 logs/limits_eta_Grid_log
tail -n 10 logs/limits_dR_Grid_log

source scripts/run_limits_parallel.sh --cat inclusive --fit_tag debug &> logs/limits_inclusive_debug_log &
source scripts/run_limits_parallel.sh --cat eta --fit_tag debug &> logs/limits_eta_debug_log &
source scripts/run_limits_parallel.sh --cat dR --fit_tag debug &> logs/limits_dR_debug_log &
wait
tail -n 5 logs/limits_inclusive_debug_log
tail -n 5 logs/limits_eta_debug_log
tail -n 5 logs/limits_dR_debug_log

echo "NOW RUNNING: inclusive, eta, dR limits; reweight, NO FREEZE"
source scripts/run_limits_parallel.sh --cat inclusive --fit_tag rMin4 &> logs/limits_inclusive_rMin4_log &
source scripts/run_limits_parallel.sh --cat eta --fit_tag rMin4 &> logs/limits_eta_rMin4_log &
source scripts/run_limits_parallel.sh --cat dR --fit_tag rMin4 &> logs/limits_dR_rMin4_log &
wait
tail -n 5 logs/limits_inclusive_rMin4_log
tail -n 5 logs/limits_eta_rMin4_log
tail -n 5 logs/limits_dR_rMin4_log

# TEST 2: run Asymptotic with rMin = 2
echo "NOW RUNNING: inclusive, eta, dR limits; reweight, NO FREEZE"
source scripts/run_limits_parallel.sh --cat inclusive --fit_tag rMin2 &> logs/limits_inclusive_rMin2_log &
source scripts/run_limits_parallel.sh --cat eta --fit_tag rMin2 &> logs/limits_eta_rMin2_log &
source scripts/run_limits_parallel.sh --cat dR --fit_tag rMin2 &> logs/limits_dR_rMin2_log &
wait
tail -n 5 logs/limits_inclusive_rMin2_log
tail -n 5 logs/limits_eta_rMin2_log
tail -n 5 logs/limits_dR_rMin2_log

# TEST 1: run Asymptotic with grid
echo "NOW RUNNING: inclusive, eta, dR limits; reweight, NO FREEZE"
source scripts/run_limits_parallel.sh --cat inclusive --fit_tag grid &> logs/limits_inclusive_grid_log &
source scripts/run_limits_parallel.sh --cat eta --fit_tag grid &> logs/limits_eta_grid_log &
source scripts/run_limits_parallel.sh --cat dR --fit_tag grid &> logs/limits_dR_grid_log &
wait
tail -n 5 logs/limits_inclusive_grid_log
tail -n 5 logs/limits_eta_grid_log
tail -n 5 logs/limits_dR_grid_log

# # Freezing Jpsi, reweighted
# echo "NOW RUNNING: inclusive, dR, and eta limits; reweight, freezeJpsi"
# source scripts/run_limits_parallel.sh --freeze_jpsi --fit_tag "freezeJpsi" --cat "inclusive" &> logs/limits_inclusive_freezeJpsi_log &
# source scripts/run_limits_parallel.sh --freeze_jpsi --fit_tag "freezeJpsi" --cat "dR" &> logs/limits_dR_freezeJpsi_log &
# source scripts/run_limits_parallel.sh --freeze_jpsi --fit_tag "freezeJpsi" --cat "eta" &> logs/limits_eta_freezeJpsi_log &
# wait
# tail -n 5 logs/limits_inclusive_freezeJpsi_log
# tail -n 5 logs/limits_dR_freezeJpsi_log
# tail -n 5 logs/limits_eta_freezeJpsi_log
