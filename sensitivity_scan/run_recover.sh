# source scripts/run_limits_combination_parallel.sh --plot_only --freeze_jpsi --fit_tag "freezeJpsi" --cat "dR" &
# source scripts/run_limits_combination_parallel.sh --plot_only --freeze_jpsi --fit_tag "freezeJpsi" --cat "eta" &
# source scripts/run_limits_combination_parallel.sh --plot_only --cat eta --no_reweight --freeze_jpsi --fit_tag freezeJpsi &
# source scripts/run_limits_combination_parallel.sh --plot_only --cat dR --no_reweight --freeze_jpsi --fit_tag freezeJpsi &
# wait
# source scripts/run_limits_combination_parallel.sh --plot_only --cat eta --freeze_jpsi --no_reweight --fit_tag freezeJpsi --tag x2wgt &
# source scripts/run_limits_combination_parallel.sh --plot_only --cat dR --freeze_jpsi --no_reweight --fit_tag freezeJpsi --tag x2wgt &
# source scripts/run_limits_combination_parallel.sh --plot_only --cat eta --no_reweight --freeze_jpsi --fit_tag freezeJpsi --tag div100wgt &
# source scripts/run_limits_combination_parallel.sh --plot_only --cat dR --no_reweight --freeze_jpsi --fit_tag freezeJpsi --tag div100wgt &
# wait
# source scripts/run_limits_combination_parallel.sh --plot_only --cat eta --no_reweight --fit_tag freezeNone &
# source scripts/run_limits_combination_parallel.sh --plot_only --cat dR --no_reweight --fit_tag freezeNone &
# source scripts/run_limits_combination_parallel.sh --plot_only --cat eta --no_reweight &
# source scripts/run_limits_combination_parallel.sh --plot_only --cat dR --no_reweight &
# wait
# source scripts/run_limits_combination_parallel.sh --plot_only --cat eta --no_reweight --tag div100wgt &
# source scripts/run_limits_combination_parallel.sh --plot_only --cat dR --no_reweight --tag div100wgt &
# source scripts/run_limits_combination_parallel.sh --plot_only --cat eta --no_reweight --tag x2wgt &
# source scripts/run_limits_combination_parallel.sh --plot_only --cat dR --no_reweight --tag x2wgt &
# wait

# # ------------

# echo "NOW RUNNING: eta diagnostics, no reweight, freezeJpsi, div100wgt"
# source scripts/run_diagnostics_parallel.sh --cat eta --no_reweight --tag div100wgt &> logs/diagnostics_eta_noReweight_div100wgt_log
# echo "NOW RUNNING: dR diagnostics, no reweight, freezeJpsi, div100wgt"
# source scripts/run_diagnostics_parallel.sh --cat dR --no_reweight --tag div100wgt &> logs/diagnostics_dR_noReweight_div100wgt_log

# # ----------

# OG, no reweight
echo "NOW RUNNING: inclusive, eta, dR limits; no reweight, NO FREEZE"
source scripts/run_limits_parallel.sh --cat inclusive --no_reweight &> logs/limits_eta_noReweight_log &
source scripts/run_limits_parallel.sh --cat eta --no_reweight &> logs/limits_eta_noReweight_log &
source scripts/run_limits_parallel.sh --cat dR --no_reweight &> logs/limits_dR_noReweight_log &
wait
tail -n 5 logs/limits_eta_noReweight_log
tail -n 5 logs/limits_eta_noReweight_log
tail -n 5 logs/limits_dR_noReweight_log

echo "NOW RUNNING: eta and dR combination; no reweight, NO FREEZE"
source scripts/run_limits_combination_parallel.sh --cat eta --no_reweight &> logs/limits_eta_combination_noReweight_log &
source scripts/run_limits_combination_parallel.sh --cat dR --no_reweight &> logs/limits_dR_combination_noReweight_log &
wait
tail -n 5 logs/limits_eta_combination_noReweight_log
tail -n 5 logs/limits_dR_combination_noReweight_log

# Freezing Jpsi, no reweight
echo "NOW RUNNING: inclusive diagnostics; no reweight, freezeJpsi"
source scripts/run_diagnostics_parallel.sh --cat inclusive --no_reweight &> logs/diagnostics_inclusive_noReweight_log
echo "NOW RUNNING: eta diagnostics; no reweight, freezeJpsi"
source scripts/run_diagnostics_parallel.sh --cat eta --no_reweight &> logs/diagnostics_eta_noReweight_log
echo "NOW RUNNING: dR diagnostics; no reweight, freezeJpsi"
source scripts/run_diagnostics_parallel.sh --cat dR --no_reweight &> logs/diagnostics_dR_noReweight_log

echo "NOW RUNNING: inclusive, dR, and eta limits; NO reweight, freezeJpsi"
source scripts/run_limits_parallel.sh --cat inclusive --no_reweight --freeze_jpsi --fit_tag freezeJpsi &> logs/limits_inclusive_noReweight_freezeJpsi_log &
source scripts/run_limits_parallel.sh --cat eta --no_reweight --freeze_jpsi --fit_tag freezeJpsi &> logs/limits_eta_noReweight_freezeJpsi_log &
source scripts/run_limits_parallel.sh --cat dR --no_reweight --freeze_jpsi --fit_tag freezeJpsi &> logs/limits_dR_noReweight_freezeJpsi_log &
wait 
tail -n 5 logs/limits_inclusive_noReweight_freezeJpsi_log
tail -n 5 logs/limits_eta_noReweight_freezeJpsi_log
tail -n 5 logs/limits_dR_noReweight_freezeJpsi_log

echo "NOW RUNNING: eta and dR combination; NO reweight, freezeJpsi"
source scripts/run_limits_combination_parallel.sh --cat eta --no_reweight --freeze_jpsi --fit_tag freezeJpsi &> logs/limits_eta_combination_noReweight_freezeJpsi_log &
source scripts/run_limits_combination_parallel.sh --cat dR --no_reweight --freeze_jpsi --fit_tag freezeJpsi &> logs/limits_dR_combination_noReweight_freezeJpsi_log &
wait
tail -n 5 logs/limits_eta_combination_noReweight_freezeJpsi_log
tail -n 5 logs/limits_dR_combination_noReweight_freezeJpsi_log

# # ----------------

# OG, x2 wgt x2 sgn
echo "NOW RUNNING: inclusive, eta, dR limits, no reweight, NO FREEZE, x2wgt_x2sgn"
source scripts/run_limits_parallel.sh --cat inclusive --no_reweight --tag x2wgt_x2sgn &> logs/limits_inclusive_noReweight_x2wgt_x2sgn_log &
source scripts/run_limits_parallel.sh --cat eta --no_reweight --tag x2wgt_x2sgn &> logs/limits_eta_noReweight_x2wgt_x2sgn_log &
source scripts/run_limits_parallel.sh --cat dR --no_reweight --tag x2wgt_x2sgn &> logs/limits_dR_noReweight_x2wgt_x2sgn_log &
wait
tail -n 5 logs/limits_inclusive_noReweight_x2wgt_x2sgn_log
tail -n 5 logs/limits_eta_noReweight_x2wgt_x2sgn_log
tail -n 5 logs/limits_dR_noReweight_x2wgt_x2sgn_log

# echo "NOW RUNNING: eta and dR combination, no reweight, NO FREEZE, x2wgt"
# source scripts/run_limits_combination_parallel.sh --cat eta --no_reweight --tag x2wgt_x2sgn &> logs/limits_eta_combination_noReweight_x2wgt_x2sgn_log &
# source scripts/run_limits_combination_parallel.sh --cat dR --no_reweight --tag x2wgt_x2sgn &> logs/limits_dR_combination_noReweight_x2wgt_x2sgn_log &
# wait
# tail -n 5 logs/limits_eta_combination_noReweight_x2wgt_x2sgn_log
# tail -n 5 logs/limits_dR_combination_noReweight_x2wgt_x2sgn_log

# Freezing Jpsi, x2 wgt x2 sgn
echo "NOW RUNNING: inclusive diagnostics, no reweight, freezeJpsi, x2wgt_x2sgn"
source scripts/run_diagnostics_parallel.sh --cat inclusive --no_reweight --tag x2wgt_x2sgn &> logs/diagnostics_inclusive_noReweight_x2wgt_x2sgn_log
echo "NOW RUNNING: eta diagnostics, no reweight, freezeJpsi, x2wgt_x2sgn"
source scripts/run_diagnostics_parallel.sh --cat eta --no_reweight --tag x2wgt_x2sgn &> logs/diagnostics_eta_noReweight_x2wgt_x2sgn_log
echo "NOW RUNNING: dR diagnostics, no reweight, freezeJpsi, x2wgt_x2sgn"
source scripts/run_diagnostics_parallel.sh --cat dR --no_reweight --tag x2wgt_x2sgn &> logs/diagnostics_dR_noReweight_x2wgt_x2sgn_log

# echo "NOW RUNNING: inclusive, eta, dR limits, no reweight, freezeJpsi, x2wgt_x2sgn"
# source scripts/run_limits_parallel.sh --cat inclusive --no_reweight --freeze_jpsi --fit_tag freezeJpsi --tag x2wgt_x2sgn &> logs/limits_inclusive_noReweight_x2wgt_x2sgn_freezeJpsi_log &
# source scripts/run_limits_parallel.sh --cat eta --no_reweight --freeze_jpsi --fit_tag freezeJpsi --tag x2wgt_x2sgn &> logs/limits_eta_noReweight_x2wgt_x2sgn_freezeJpsi_log &
# source scripts/run_limits_parallel.sh --cat dR --no_reweight --freeze_jpsi --fit_tag freezeJpsi --tag x2wgt_x2sgn &> logs/limits_dR_noReweight_x2wgt_x2sgn_freezeJpsi_log &
# wait
# tail -n 5 logs/limits_inclusive_noReweight_x2wgt_x2sgn_freezeJpsi_log
# tail -n 5 logs/limits_eta_noReweight_x2wgt_x2sgn_freezeJpsi_log
# tail -n 5 logs/limits_dR_noReweight_x2wgt_x2sgn_freezeJpsi_log

# echo "NOW RUNNING: eta and dR combination, no reweight, freezeJpsi, x2wgt_x2sgn"
# source scripts/run_limits_combination_parallel.sh --cat eta --freeze_jpsi --no_reweight --fit_tag freezeJpsi --tag x2wgt_x2sgn &> logs/limits_eta_combination_noReweight_x2wgt_x2sgn_freezeJpsi_log &
# source scripts/run_limits_combination_parallel.sh --cat dR --freeze_jpsi --no_reweight --fit_tag freezeJpsi --tag x2wgt_x2sgn &> logs/limits_dR_combination_noReweight_x2wgt_x2sgn_freezeJpsi_log &
# wait
# tail -n 5 logs/limits_eta_combination_noReweight_x2wgt_x2sgn_freezeJpsi_log
# tail -n 5 logs/limits_dR_combination_noReweight_x2wgt_x2sgn_freezeJpsi_log

# --------------

source scripts/run_diagnostics_parallel.sh --cat inclusive --no_reweight --tag x2wgt &> logs/diagnostics_inclusive_noReweight_x2wgt_log &
source scripts/run_limits_parallel.sh --cat inclusive --no_reweight --tag x2wgt &> logs/limits_inclusive_noReweight_x2wgt_log &
wait

source scripts/run_diagnostics_parallel.sh --cat inclusive --no_reweight &> logs/diagnostics_inclusive_noReweight_log &
source scripts/run_limits_parallel.sh --cat inclusive --no_reweight &> logs/limits_eta_noReweight_log &
wait