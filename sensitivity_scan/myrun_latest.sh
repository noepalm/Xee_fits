# --------------------------------------- #
# ------------- WORKSPACES -------------- #
# --------------------------------------- #

# reweighted (standard)
echo "Producing workspace for eta with reweighting"
python3 make_combine_workspace.py --cat="eta" &> logs/workspace_eta_log
tail -n 5 logs/workspace_eta_log
echo "Producing workspace for dR with reweighting"
python3 make_combine_workspace.py --cat="dR" &> logs/workspace_dR_log
tail -n 5 logs/workspace_dR_log
echo "Producing workspace for inclusive with reweighting"
python3 make_combine_workspace.py --cat="inclusive" &> logs/workspace_inclusive_log
tail -n 5 logs/workspace_inclusive_log

# reweighted (x1/100)
echo "Producing workspace for eta with reweighting"
python3 make_combine_workspace.py --cat="eta" --bkg_div100 --tag="div100wgt" &> logs/workspace_eta_div100wgt_log
tail -n 5 logs/workspace_eta_div100wgt_log
echo "Producing workspace for dR with reweighting"
python3 make_combine_workspace.py --cat="dR" --bkg_div100 --tag="div100wgt" &> logs/workspace_dR_div100wgt_log
tail -n 5 logs/workspace_dR_div100wgt_log
echo "Producing workspace for inclusive with reweighting"
python3 make_combine_workspace.py --cat="inclusive" --bkg_div100 --tag="div100wgt" &> logs/workspace_inclusive_div100wgt_log
tail -n 5 logs/workspace_inclusive_div100wgt_log

# no reweight, standard weights
echo "Producing workspace for inclusive with no reweighting"
python3 make_combine_workspace.py --cat="inclusive" --no_reweight &> logs/workspace_inclusive_noReweight_log
echo "Producing workspace for eta with no reweighting"
python3 make_combine_workspace.py --cat="eta" --no_reweight &> logs/workspace_eta_noReweight_log
echo "Producing workspace for dR with no reweighting"
python3 make_combine_workspace.py --cat="dR" --no_reweight &> logs/workspace_dR_noReweight_log
tail -n 5 logs/workspace_inclusive_noReweight_log

# no reweight, standard weights, BINNED
echo "Producing workspace for inclusive with no reweighting"
python3 make_combine_workspace.py --cat="inclusive" --no_reweight --binned &> logs/workspace_inclusive_binned_noReweight_log
# TODO: complete

# no reweight, x2 weights
echo "Producing workspace for inclusive with no reweighting"
python3 make_combine_workspace.py --cat="inclusive" --no_reweight --bkg_x2 --tag="x2wgt" &> logs/workspace_inclusive_noReweight_x2wgt_log
echo "Producing workspace for eta with no reweighting"
python3 make_combine_workspace.py --cat="eta" --no_reweight --bkg_x2 --tag="x2wgt" &> logs/workspace_eta_noReweight_x2wgt_log
echo "Producing workspace for dR with no reweighting"
python3 make_combine_workspace.py --cat="dR" --no_reweight --bkg_x2 --tag="x2wgt" &> logs/workspace_dR_noReweight_x2wgt_log

# no reweight, x1/100 weights
echo "Producing workspace for inclusive with no reweighting"
python3 make_combine_workspace.py --cat="inclusive" --no_reweight --bkg_div100 --tag="div100wgt" &> logs/workspace_inclusive_noReweight_div100wgt_log
echo "Producing workspace for eta with no reweighting"
python3 make_combine_workspace.py --cat="eta" --no_reweight --bkg_div100 --tag="div100wgt" &> logs/workspace_eta_noReweight_div100wgt_log
echo "Producing workspace for dR with no reweighting"
python3 make_combine_workspace.py --cat="dR" --no_reweight --bkg_div100 --tag="div100wgt" &> logs/workspace_dR_noReweight_div100wgt_log

# no reweight, x1/100 weights, x1/100 signal
echo "Producing workspace for inclusive with no reweighting"
python3 make_combine_workspace.py --cat="inclusive" --no_reweight --bkg_div100 --signal_multiplier=0.01 --tag="div100wgt_div100sgn" &> logs/workspace_inclusive_noReweight_div100wgt_div100sgn_log
echo "Producing workspace for eta with no reweighting"
python3 make_combine_workspace.py --cat="eta" --no_reweight --bkg_div100 --signal_multiplier=0.01 --tag="div100wgt_div100sgn" &> logs/workspace_eta_noReweight_div100wgt_div100sgn_log
echo "Producing workspace for dR with no reweighting"
python3 make_combine_workspace.py --cat="dR" --no_reweight --bkg_div100 --signal_multiplier=0.01 --tag="div100wgt_div100sgn" &> logs/workspace_dR_noReweight_div100wgt_div100sgn_log

# no reweight, x2 bkg weights, x2 sgn
echo "Producing workspace for inclusive with no reweighting"
python3 make_combine_workspace.py --cat="inclusive" --no_reweight --bkg_x2 --signal_multiplier=2 --tag="x2wgt_x2sgn" &> logs/workspace_inclusive_noReweight_x2wgt_x2sgn_log
echo "Producing workspace for eta with no reweighting"
python3 make_combine_workspace.py --cat="eta" --no_reweight --bkg_x2 --signal_multiplier=2 --tag="x2wgt_x2sgn" &> logs/workspace_eta_noReweight_x2wgt_x2sgn_log
echo "Producing workspace for dR with no reweighting"
python3 make_combine_workspace.py --cat="dR" --no_reweight --bkg_x2 --signal_multiplier=2 --tag="x2wgt_x2sgn" &> logs/workspace_dR_noReweight_x2wgt_x2sgn_log

# no reweight, x100 sgn
echo "Producing workspace for inclusive with no reweighting"
python3 make_combine_workspace.py --cat="inclusive" --no_reweight --signal_multiplier=100 --tag="x100sgn" &> logs/workspace_inclusive_noReweight_x100sgn_log
echo "Producing workspace for eta with no reweighting"
python3 make_combine_workspace.py --cat="eta" --no_reweight --signal_multiplier=100 --tag="x100sgn" &> logs/workspace_eta_noReweight_x100sgn_log
echo "Producing workspace for dR with no reweighting"
python3 make_combine_workspace.py --cat="dR" --no_reweight --signal_multiplier=100 --tag="x100sgn" &> logs/workspace_dR_noReweight_x100sgn_log

# no reweight, 1/100 sgn
echo "Producing workspace for inclusive with no reweighting"
python3 make_combine_workspace.py --cat="inclusive" --no_reweight --signal_multiplier=0.01 --tag="div100sgn" &> logs/workspace_inclusive_noReweight_div100sgn_log
echo "Producing workspace for eta with no reweighting"
python3 make_combine_workspace.py --cat="eta" --no_reweight --signal_multiplier=0.01 --tag="div100sgn" &> logs/workspace_eta_noReweight_div100sgn_log
echo "Producing workspace for dR with no reweighting"
python3 make_combine_workspace.py --cat="dR" --no_reweight --signal_multiplier=0.01 --tag="div100sgn" &> logs/workspace_dR_noReweight_div100sgn_log

# -------------------------------- #
# --------- DIAGNOSTICS ---------- #
# -------------------------------- #

# reweighted
echo "NOW RUNNING: inclusive diagnostics; reweight"
source scripts/run_diagnostics_parallel.sh --cat inclusive &> logs/diagnostics_inclusive_log
echo "NOW RUNNING: eta diagnostics; reweight"
source scripts/run_diagnostics_parallel.sh --cat eta &> logs/diagnostics_eta_log
echo "NOW RUNNING: dR diagnostics; reweight"
source scripts/run_diagnostics_parallel.sh --cat dR &> logs/diagnostics_dR_log

# reweighted, 1/100
echo "NOW RUNNING: eta diagnostics; reweight, 1/100 bkg weight"
source scripts/run_diagnostics_parallel.sh --cat inclusive --tag div100wgt &> logs/diagnostics_inclusive_div100wgt_log
echo "NOW RUNNING: dR diagnostics; reweight, 1/100 bkg weight"
source scripts/run_diagnostics_parallel.sh --cat eta --tag div100wgt &> logs/diagnostics_eta_div100wgt_log
echo "NOW RUNNING: dR diagnostics; reweight, 1/100 bkg weight"
source scripts/run_diagnostics_parallel.sh --cat dR --tag div100wgt &> logs/diagnostics_dR_div100wgt_log

# no reweight
echo "NOW RUNNING: inclusive diagnostics; no reweight"
source scripts/run_diagnostics_parallel.sh --cat inclusive --no_reweight &> logs/diagnostics_inclusive_noReweight_log
echo "NOW RUNNING: eta diagnostics; no reweight"
source scripts/run_diagnostics_parallel.sh --cat eta --no_reweight &> logs/diagnostics_eta_noReweight_log
echo "NOW RUNNING: dR diagnostics; no reweight"
source scripts/run_diagnostics_parallel.sh --cat dR --no_reweight &> logs/diagnostics_dR_noReweight_log

# no reweight, binned
echo "NOW RUNNING: inclusive diagnostics; no reweight"
source scripts/run_diagnostics_parallel.sh --cat inclusive --no_reweight --tag binned &> logs/diagnostics_inclusive_noReweight_binned_log

# no reweight, 1/100 wgt
echo "NOW RUNNING: inclusive diagnostics, no reweight, div100wgt"
source scripts/run_diagnostics_parallel.sh --cat inclusive --no_reweight --tag div100wgt &> logs/diagnostics_inclusive_noReweight_div100wgt_log
echo "NOW RUNNING: eta diagnostics, no reweight, div100wgt"
source scripts/run_diagnostics_parallel.sh --cat eta --no_reweight --tag div100wgt &> logs/diagnostics_eta_noReweight_div100wgt_log
echo "NOW RUNNING: dR diagnostics, no reweight, div100wgt"
source scripts/run_diagnostics_parallel.sh --cat dR --no_reweight --tag div100wgt &> logs/diagnostics_dR_noReweight_div100wgt_log

# no reweight, 1/100 wgt, 1/100 sgn
echo "NOW RUNNING: inclusive diagnostics, no reweight, div100wgt_div100sgn"
source scripts/run_diagnostics_parallel.sh --cat inclusive --no_reweight --tag div100wgt_div100sgn &> logs/diagnostics_inclusive_noReweight_div100wgt_div100sgn_log
echo "NOW RUNNING: eta diagnostics, no reweight, div100wgt_div100sgn"
source scripts/run_diagnostics_parallel.sh --cat eta --no_reweight --tag div100wgt_div100sgn &> logs/diagnostics_eta_noReweight_div100wgt_div100sgn_log
echo "NOW RUNNING: dR diagnostics, no reweight, div100wgt_div100sgn"
source scripts/run_diagnostics_parallel.sh --cat dR --no_reweight --tag div100wgt_div100sgn &> logs/diagnostics_dR_noReweight_div100wgt_div100sgn_log

# no reweight, x2 wgt
echo "NOW RUNNING: inclusive diagnostics, no reweight, x2wgt"
source scripts/run_diagnostics_parallel.sh --cat inclusive --no_reweight --tag x2wgt &> logs/diagnostics_inclusive_noReweight_x2wgt_log
echo "NOW RUNNING: eta diagnostics, no reweight, x2wgt"
source scripts/run_diagnostics_parallel.sh --cat eta --no_reweight --tag x2wgt &> logs/diagnostics_eta_noReweight_x2wgt_log
echo "NOW RUNNING: dR diagnostics, no reweight, x2wgt"
source scripts/run_diagnostics_parallel.sh --cat dR --no_reweight --tag x2wgt &> logs/diagnostics_dR_noReweight_x2wgt_log

# no reweight, x2 wgt x2 signal
echo "NOW RUNNING: inclusive diagnostics, no reweight, x2wgt_x2sgn"
source scripts/run_diagnostics_parallel.sh --cat inclusive --no_reweight --tag x2wgt_x2sgn &> logs/diagnostics_inclusive_noReweight_x2wgt_x2sgn_log
echo "NOW RUNNING: eta diagnostics, no reweight, x2wgt_x2sgn"
source scripts/run_diagnostics_parallel.sh --cat eta --no_reweight --tag x2wgt_x2sgn &> logs/diagnostics_eta_noReweight_x2wgt_x2sgn_log
echo "NOW RUNNING: dR diagnostics, no reweight, x2wgt_x2sgn"
source scripts/run_diagnostics_parallel.sh --cat dR --no_reweight --tag x2wgt_x2sgn &> logs/diagnostics_dR_noReweight_x2wgt_x2sgn_log

# no reweight, x100 signal
echo "NOW RUNNING: inclusive diagnostics, no reweight, x100sgn"
source scripts/run_diagnostics_parallel.sh --cat inclusive --no_reweight --tag x100sgn &> logs/diagnostics_inclusive_noReweight_x100sgn_log
echo "NOW RUNNING: eta diagnostics, no reweight, x100sgn"
source scripts/run_diagnostics_parallel.sh --cat eta --no_reweight --tag x100sgn &> logs/diagnostics_eta_noReweight_x100sgn_log
echo "NOW RUNNING: dR diagnostics, no reweight, x100sgn"
source scripts/run_diagnostics_parallel.sh --cat dR --no_reweight --tag x100sgn &> logs/diagnostics_dR_noReweight_x100sgn_log

# no reweight, 1/100 signal
echo "NOW RUNNING: inclusive diagnostics, no reweight, div100sgn"
source scripts/run_diagnostics_parallel.sh --cat inclusive --no_reweight --tag div100sgn &> logs/diagnostics_inclusive_noReweight_div100sgn_log
echo "NOW RUNNING: eta diagnostics, no reweight, div100sgn"
source scripts/run_diagnostics_parallel.sh --cat eta --no_reweight --tag div100sgn &> logs/diagnostics_eta_noReweight_div100sgn_log
echo "NOW RUNNING: dR diagnostics, no reweight, div100sgn"
source scripts/run_diagnostics_parallel.sh --cat dR --no_reweight --tag div100sgn &> logs/diagnostics_dR_noReweight_div100sgn_log

# -------------------------------------- #
# --------- LIMITS, OG METHOD ---------- #
# -------------------------------------- #

# OG, reweight
echo "NOW RUNNING: inclusive, eta, dR limits; reweight, NO FREEZE"
source scripts/run_limits_parallel.sh --cat inclusive --fit_tag freezeNone &> logs/limits_inclusive_freezeNone_log &
source scripts/run_limits_parallel.sh --cat eta --fit_tag freezeNone &> logs/limits_eta_freezeNone_log &
source scripts/run_limits_parallel.sh --cat dR --fit_tag freezeNone &> logs/limits_dR_freezeNone_log &
wait
tail -n 5 logs/limits_eta_noReweight_log
tail -n 5 logs/limits_eta_noReweight_log
tail -n 5 logs/limits_dR_noReweight_log

echo "NOW RUNNING: eta and dR combination; reweight, NO FREEZE"
source scripts/run_limits_combination_parallel.sh --cat eta --fit_tag freezeNone &> logs/limits_eta_combination_freezeNone_log &
source scripts/run_limits_combination_parallel.sh --cat dR --fit_tag freezeNone &> logs/limits_dR_combination_freezeNone_log &
wait
tail -n 5 logs/limits_eta_combination_noReweight_freezeNone_log
tail -n 5 logs/limits_dR_combination_noReweight_freezeNone_log

# OG, reweight, 1/100 wgt
echo "NOW RUNNING: inclusive, eta, dR limits; no reweight, NO FREEZE, 1/100 bkg weight"
source scripts/run_limits_parallel.sh --cat inclusive --tag div100wgt &> logs/limits_inclusive_div100wgt_log &
source scripts/run_limits_parallel.sh --cat eta --tag div100wgt &> logs/limits_eta_div100wgt_log &
source scripts/run_limits_parallel.sh --cat dR --tag div100wgt &> logs/limits_dR_div100wgt_log &
wait
tail -n 5 logs/limits_inclusive_div100wgt_log
tail -n 5 logs/limits_eta_div100wgt_log
tail -n 5 logs/limits_dR_div100wgt_log

echo "NOW RUNNING: eta and dR combination; no reweight, NO FREEZE, 1/100 bkg weight"
source scripts/run_limits_combination_parallel.sh --cat eta --tag div100wgt &> logs/limits_eta_combination_div100wgt_log &
source scripts/run_limits_combination_parallel.sh --cat dR --tag div100wgt &> logs/limits_dR_combination_div100wgt_log &
wait
tail -n 5 logs/limits_eta_combination_div100wgt_log
tail -n 5 logs/limits_dR_combination_div100wgt_log

# OG, no reweight
echo "NOW RUNNING: inclusive, eta, dR limits; no reweight, NO FREEZE"
source scripts/run_limits_parallel.sh --cat inclusive --no_reweight &> logs/limits_inclusive_noReweight_log &
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

# OG, no reweight, binned
echo "NOW RUNNING: inclusive, eta, dR limits; no reweight, NO FREEZE"
source scripts/run_limits_parallel.sh --cat inclusive --no_reweight --tag binned &> logs/limits_inclusive_noReweight_binned_log

# OG, x1/100 wgt
echo "NOW RUNNING: inclusive, eta, dR limits; no reweight, NO FREEZE, div100wgt"
source scripts/run_limits_parallel.sh --cat inclusive --no_reweight --tag div100wgt &> logs/limits_inclusive_noReweight_div100wgt_log &
source scripts/run_limits_parallel.sh --cat eta --no_reweight --tag div100wgt &> logs/limits_eta_noReweight_div100wgt_log &
source scripts/run_limits_parallel.sh --cat dR --no_reweight --tag div100wgt &> logs/limits_dR_noReweight_div100wgt_log &
wait
tail -n 5 logs/limits_inclusive_noReweight_div100wgt_log
tail -n 5 logs/limits_eta_noReweight_div100wgt_log
tail -n 5 logs/limits_dR_noReweight_div100wgt_log

echo "NOW RUNNING: eta and dR combination; no reweight, NO FREEZE, div100wgt"
source scripts/run_limits_combination_parallel.sh --cat eta --no_reweight --tag div100wgt &> logs/limits_eta_combination_noReweight_div100wgt_log &
source scripts/run_limits_combination_parallel.sh --cat dR --no_reweight --tag div100wgt &> logs/limits_dR_combination_noReweight_div100wgt_log &
wait
tail -n 5 logs/limits_eta_combination_noReweight_div100wgt_log
tail -n 5 logs/limits_dR_combination_noReweight_div100wgt_log

# OG, x1/100 wgt x1/100 sgn
echo "NOW RUNNING: inclusive, eta, dR limits; no reweight, NO FREEZE, div100wgt_div100sgn"
source scripts/run_limits_parallel.sh --cat inclusive --no_reweight --tag div100wgt_div100sgn &> logs/limits_inclusive_noReweight_div100wgt_div100sgn_log &
source scripts/run_limits_parallel.sh --cat eta --no_reweight --tag div100wgt_div100sgn &> logs/limits_eta_noReweight_div100wgt_div100sgn_log &
source scripts/run_limits_parallel.sh --cat dR --no_reweight --tag div100wgt_div100sgn &> logs/limits_dR_noReweight_div100wgt_div100sgn_log &
wait
tail -n 5 logs/limits_inclusive_noReweight_div100wgt_div100sgn_log
tail -n 5 logs/limits_eta_noReweight_div100wgt_div100sgn_log
tail -n 5 logs/limits_dR_noReweight_div100wgt_div100sgn_log
echo "NOW RUNNING: eta and dR combination, no reweight, NO FREEZE, div100wgt_div100sgn"
source scripts/run_limits_combination_parallel.sh --cat eta --no_reweight --tag div100wgt_div100sgn &> logs/limits_eta_combination_noReweight_div100wgt_div100sgn_log &
source scripts/run_limits_combination_parallel.sh --cat dR --no_reweight --tag div100wgt_div100sgn &> logs/limits_dR_combination_noReweight_div100wgt_div100sgn_log &
wait
tail -n 5 logs/limits_eta_combination_noReweight_div100wgt_div100sgn_log
tail -n 5 logs/limits_dR_combination_noReweight_div100wgt_div100sgn_log

# OG, x2 wgt
echo "NOW RUNNING: inclusive, eta, dR limits; no reweight, NO FREEZE, x2wgt"
source scripts/run_limits_parallel.sh --cat inclusive --no_reweight --tag x2wgt &> logs/limits_inclusive_noReweight_x2wgt_log &
source scripts/run_limits_parallel.sh --cat eta --no_reweight --tag x2wgt &> logs/limits_eta_noReweight_x2wgt_log &
source scripts/run_limits_parallel.sh --cat dR --no_reweight --tag x2wgt &> logs/limits_dR_noReweight_x2wgt_log &
wait
tail -n 5 logs/limits_inclusive_noReweight_x2wgt_log
tail -n 5 logs/limits_eta_noReweight_x2wgt_log
tail -n 5 logs/limits_dR_noReweight_x2wgt_log

echo "NOW RUNNING: eta and dR combination, no reweight, NO FREEZE, x2wgt"
source scripts/run_limits_combination_parallel.sh --cat eta --no_reweight --tag x2wgt &> logs/limits_eta_combination_noReweight_x2wgt_log &
source scripts/run_limits_combination_parallel.sh --cat dR --no_reweight --tag x2wgt &> logs/limits_dR_combination_noReweight_x2wgt_log &
wait
tail -n 5 logs/limits_eta_combination_noReweight_x2wgt_log
tail -n 5 logs/limits_dR_combination_noReweight_x2wgt_log

# OG, x2 wgt x2 sgn
echo "NOW RUNNING: inclusive, eta, dR limits, no reweight, NO FREEZE, x2wgt_x2sgn"
source scripts/run_limits_parallel.sh --cat inclusive --no_reweight --tag x2wgt_x2sgn &> logs/limits_inclusive_noReweight_x2wgt_x2sgn_log &
source scripts/run_limits_parallel.sh --cat eta --no_reweight --tag x2wgt_x2sgn &> logs/limits_eta_noReweight_x2wgt_x2sgn_log &
source scripts/run_limits_parallel.sh --cat dR --no_reweight --tag x2wgt_x2sgn &> logs/limits_dR_noReweight_x2wgt_x2sgn_log &
wait
tail -n 5 logs/limits_inclusive_noReweight_x2wgt_x2sgn_log
tail -n 5 logs/limits_eta_noReweight_x2wgt_x2sgn_log
tail -n 5 logs/limits_dR_noReweight_x2wgt_x2sgn_log

echo "NOW RUNNING: eta and dR combination, no reweight, NO FREEZE, x2wgt"
source scripts/run_limits_combination_parallel.sh --cat eta --no_reweight --tag x2wgt_x2sgn &> logs/limits_eta_combination_noReweight_x2wgt_x2sgn_log &
source scripts/run_limits_combination_parallel.sh --cat dR --no_reweight --tag x2wgt_x2sgn &> logs/limits_dR_combination_noReweight_x2wgt_x2sgn_log &
wait
tail -n 5 logs/limits_eta_combination_noReweight_x2wgt_x2sgn_log
tail -n 5 logs/limits_dR_combination_noReweight_x2wgt_x2sgn_log

# OG, x100 sgn
echo "NOW RUNNING: inclusive, eta, dR limits, no reweight, NO FREEZE, x100sgn"
source scripts/run_limits_parallel.sh --cat inclusive --no_reweight --tag x100sgn &> logs/limits_inclusive_noReweight_x100sgn_log &
source scripts/run_limits_parallel.sh --cat eta --no_reweight --tag x100sgn &> logs/limits_eta_noReweight_x100sgn_log &
source scripts/run_limits_parallel.sh --cat dR --no_reweight --tag x100sgn &> logs/limits_dR_noReweight_x100sgn_log &
wait
tail -n 5 logs/limits_inclusive_noReweight_x100sgn_log
tail -n 5 logs/limits_eta_noReweight_x100sgn_log
tail -n 5 logs/limits_dR_noReweight_x100sgn_log
echo "NOW RUNNING: eta and dR combination, no reweight, NO FREEZE, x100sgn"
source scripts/run_limits_combination_parallel.sh --cat eta --no_reweight --tag x100sgn &> logs/limits_eta_combination_noReweight_x100sgn_log &
source scripts/run_limits_combination_parallel.sh --cat dR --no_reweight --tag x100sgn &> logs/limits_dR_combination_noReweight_x100sgn_log &
wait
tail -n 5 logs/limits_eta_combination_noReweight_x100sgn_log
tail -n 5 logs/limits_dR_combination_noReweight_x100sgn_log

# OG, x100 sgn
echo "NOW RUNNING: inclusive, eta, dR limits, no reweight, NO FREEZE, div100sgn"
source scripts/run_limits_parallel.sh --cat inclusive --no_reweight --tag div100sgn &> logs/limits_inclusive_noReweight_div100sgn_log &
source scripts/run_limits_parallel.sh --cat eta --no_reweight --tag div100sgn &> logs/limits_eta_noReweight_div100sgn_log &
source scripts/run_limits_parallel.sh --cat dR --no_reweight --tag div100sgn &> logs/limits_dR_noReweight_div100sgn_log &
wait
tail -n 5 logs/limits_inclusive_noReweight_div100sgn_log
tail -n 5 logs/limits_eta_noReweight_div100sgn_log
tail -n 5 logs/limits_dR_noReweight_div100sgn_log
echo "NOW RUNNING: eta and dR combination, no reweight, NO FREEZE, div100sgn"
source scripts/run_limits_combination_parallel.sh --cat eta --no_reweight --tag div100sgn &> logs/limits_eta_combination_noReweight_div100sgn_log &
source scripts/run_limits_combination_parallel.sh --cat dR --no_reweight --tag div100sgn &> logs/limits_dR_combination_noReweight_div100sgn_log &
wait
tail -n 5 logs/limits_eta_combination_noReweight_div100sgn_log
tail -n 5 logs/limits_dR_combination_noReweight_div100sgn_log

# ---------------------------------------- #
# --------- LIMITS, JPSI FREEZE ---------- #
# ---------------------------------------- #

# Freezing Jpsi, reweighted
echo "NOW RUNNING: inclusive, dR, and eta limits; reweight, freezeJpsi"
source scripts/run_limits_parallel.sh --freeze_jpsi --fit_tag "freezeJpsi" --cat "inclusive" &> logs/limits_inclusive_freezeJpsi_log &
source scripts/run_limits_parallel.sh --freeze_jpsi --fit_tag "freezeJpsi" --cat "dR" &> logs/limits_dR_freezeJpsi_log &
source scripts/run_limits_parallel.sh --freeze_jpsi --fit_tag "freezeJpsi" --cat "eta" &> logs/limits_eta_freezeJpsi_log &
wait
tail -n 5 logs/limits_inclusive_freezeJpsi_log
tail -n 5 logs/limits_dR_freezeJpsi_log
tail -n 5 logs/limits_eta_freezeJpsi_log

echo "NOW RUNNING: eta and dR combination, reweight, freezeJpsi"
source scripts/run_limits_combination_parallel.sh --freeze_jpsi --fit_tag "freezeJpsi" --cat "dR" &> logs/limits_dR_combination_freezeJpsi_log &
source scripts/run_limits_combination_parallel.sh --freeze_jpsi --fit_tag "freezeJpsi" --cat "eta" &> logs/limits_eta_combination_freezeJpsi_log &
wait 
tail -n 5 logs/limits_dR_combination_freezeJpsi_log
tail -n 5 logs/limits_eta_combination_freezeJpsi_log

# Freezing Jpsi, no reweight
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

# Freezing Jpsi, x2 wgt
echo "NOW RUNNING: inclusive, eta, dR limits, no reweight, freezeJpsi, x2wgt"
source scripts/run_limits_parallel.sh --cat inclusive --no_reweight --freeze_jpsi --fit_tag freezeJpsi --tag x2wgt &> logs/limits_inclusive_noReweight_x2wgt_freezeJpsi_log &
source scripts/run_limits_parallel.sh --cat eta --no_reweight --freeze_jpsi --fit_tag freezeJpsi --tag x2wgt &> logs/limits_eta_noReweight_x2wgt_freezeJpsi_log &
source scripts/run_limits_parallel.sh --cat dR --no_reweight --freeze_jpsi --fit_tag freezeJpsi --tag x2wgt &> logs/limits_dR_noReweight_x2wgt_freezeJpsi_log &
wait
tail -n 5 logs/limits_inclusive_noReweight_x2wgt_freezeJpsi_log
tail -n 5 logs/limits_eta_noReweight_x2wgt_freezeJpsi_log
tail -n 5 logs/limits_dR_noReweight_x2wgt_freezeJpsi_log

echo "NOW RUNNING: eta and dR combination, no reweight, freezeJpsi, x2wgt"
source scripts/run_limits_combination_parallel.sh --cat eta --freeze_jpsi --no_reweight --fit_tag freezeJpsi --tag x2wgt &> logs/limits_eta_combination_noReweight_x2wgt_freezeJpsi_log &
source scripts/run_limits_combination_parallel.sh --cat dR --freeze_jpsi --no_reweight --fit_tag freezeJpsi --tag x2wgt &> logs/limits_dR_combination_noReweight_x2wgt_freezeJpsi_log &
wait
tail -n 5 logs/limits_eta_combination_noReweight_x2wgt_freezeJpsi_log
tail -n 5 logs/limits_dR_combination_noReweight_x2wgt_freezeJpsi_log

# Freezing Jpsi, x2 wgt x2 sgn
echo "NOW RUNNING: inclusive, eta, dR limits, no reweight, freezeJpsi, x2wgt_x2sgn"
source scripts/run_limits_parallel.sh --cat inclusive --no_reweight --freeze_jpsi --fit_tag freezeJpsi --tag x2wgt_x2sgn &> logs/limits_inclusive_noReweight_x2wgt_x2sgn_freezeJpsi_log &
source scripts/run_limits_parallel.sh --cat eta --no_reweight --freeze_jpsi --fit_tag freezeJpsi --tag x2wgt_x2sgn &> logs/limits_eta_noReweight_x2wgt_x2sgn_freezeJpsi_log &
source scripts/run_limits_parallel.sh --cat dR --no_reweight --freeze_jpsi --fit_tag freezeJpsi --tag x2wgt_x2sgn &> logs/limits_dR_noReweight_x2wgt_x2sgn_freezeJpsi_log &
wait
tail -n 5 logs/limits_inclusive_noReweight_x2wgt_x2sgn_freezeJpsi_log
tail -n 5 logs/limits_eta_noReweight_x2wgt_x2sgn_freezeJpsi_log
tail -n 5 logs/limits_dR_noReweight_x2wgt_x2sgn_freezeJpsi_log

echo "NOW RUNNING: eta and dR combination, no reweight, freezeJpsi, x2wgt_x2sgn"
source scripts/run_limits_combination_parallel.sh --cat eta --freeze_jpsi --no_reweight --fit_tag freezeJpsi --tag x2wgt_x2sgn &> logs/limits_eta_combination_noReweight_x2wgt_x2sgn_freezeJpsi_log &
source scripts/run_limits_combination_parallel.sh --cat dR --freeze_jpsi --no_reweight --fit_tag freezeJpsi --tag x2wgt_x2sgn &> logs/limits_dR_combination_noReweight_x2wgt_x2sgn_freezeJpsi_log &
wait
tail -n 5 logs/limits_eta_combination_noReweight_x2wgt_x2sgn_freezeJpsi_log
tail -n 5 logs/limits_dR_combination_noReweight_x2wgt_x2sgn_freezeJpsi_log

# Freezing Jpsi, x1/100 wgt
echo "NOW RUNNING: inclusive, eta, dR limits; no reweight, freezeJpsi, div100wgt"
source scripts/run_limits_parallel.sh --cat inclusive --freeze_jpsi --fit_tag freezeJpsi --no_reweight --tag div100wgt &> logs/limits_inclusive_noReweight_div100wgt_freezeJpsi_log &
source scripts/run_limits_parallel.sh --cat eta --freeze_jpsi --fit_tag freezeJpsi --no_reweight --tag div100wgt &> logs/limits_eta_noReweight_div100wgt_freezeJpsi_log &
source scripts/run_limits_parallel.sh --cat dR --freeze_jpsi --fit_tag freezeJpsi --no_reweight --tag div100wgt &> logs/limits_dR_noReweight_div100wgt_freezeJpsi_log &
wait
tail -n 5 logs/limits_inclusive_noReweight_div100wgt_freezeJpsi_log
tail -n 5 logs/limits_eta_noReweight_div100wgt_freezeJpsi_log
tail -n 5 logs/limits_dR_noReweight_div100wgt_freezeJpsi_log

echo "NOW RUNNING: eta and dR combination, no reweight, freezeJpsi, div100wgt"
source scripts/run_limits_combination_parallel.sh --cat eta --no_reweight --freeze_jpsi --fit_tag freezeJpsi --tag div100wgt &> logs/limits_eta_combination_noReweight_div100wgt_freezeJpsi_log &
source scripts/run_limits_combination_parallel.sh --cat dR --no_reweight --freeze_jpsi --fit_tag freezeJpsi --tag div100wgt &> logs/limits_dR_combination_noReweight_div100wgt_freezeJpsi_log &
wait
tail -n 5 logs/limits_eta_combination_noReweight_div100wgt_freezeJpsi_log
tail -n 5 logs/limits_dR_combination_noReweight_div100wgt_freezeJpsi_log

# Freezing Jpsi, x100 sgn
echo "NOW RUNNING: inclusive, eta, dR limits; no reweight, freezeJpsi, x100sgn"
source scripts/run_limits_parallel.sh --cat inclusive --freeze_jpsi --fit_tag freezeJpsi --no_reweight --tag x100sgn &> logs/limits_inclusive_noReweight_x100sgn_freezeJpsi_log &
source scripts/run_limits_parallel.sh --cat eta --freeze_jpsi --fit_tag freezeJpsi --no_reweight --tag x100sgn &> logs/limits_eta_noReweight_x100sgn_freezeJpsi_log &
source scripts/run_limits_parallel.sh --cat dR --freeze_jpsi --fit_tag freezeJpsi --no_reweight --tag x100sgn &> logs/limits_dR_noReweight_x100sgn_freezeJpsi_log &
wait
tail -n 5 logs/limits_inclusive_noReweight_x100sgn_freezeJpsi_log
tail -n 5 logs/limits_eta_noReweight_x100sgn_freezeJpsi_log
tail -n 5 logs/limits_dR_noReweight_x100sgn_freezeJpsi_log
echo "NOW RUNNING: eta and dR combination; no reweight, freezeJpsi, x100sgn"
source scripts/run_limits_combination_parallel.sh --cat eta --no_reweight --freeze_jpsi --fit_tag freezeJpsi --tag x100sgn &> logs/limits_eta_combination_noReweight_x100sgn_freezeJpsi_log &
source scripts/run_limits_combination_parallel.sh --cat dR --no_reweight --freeze_jpsi --fit_tag freezeJpsi --tag x100sgn &> logs/limits_dR_combination_noReweight_x100sgn_freezeJpsi_log &
wait
tail -n 5 logs/limits_eta_combination_noReweight_x100sgn_freezeJpsi_log
tail -n 5 logs/limits_dR_combination_noReweight_x100sgn_freezeJpsi_log

# Freezing Jpsi, x100 sgn
echo "NOW RUNNING: inclusive, eta, dR limits; no reweight, freezeJpsi, div100sgn"
source scripts/run_limits_parallel.sh --cat inclusive --freeze_jpsi --fit_tag freezeJpsi --no_reweight --tag div100sgn &> logs/limits_inclusive_noReweight_div100sgn_freezeJpsi_log &
source scripts/run_limits_parallel.sh --cat eta --freeze_jpsi --fit_tag freezeJpsi --no_reweight --tag div100sgn &> logs/limits_eta_noReweight_div100sgn_freezeJpsi_log &
source scripts/run_limits_parallel.sh --cat dR --freeze_jpsi --fit_tag freezeJpsi --no_reweight --tag div100sgn &> logs/limits_dR_noReweight_div100sgn_freezeJpsi_log &
wait
tail -n 5 logs/limits_inclusive_noReweight_div100sgn_freezeJpsi_log
tail -n 5 logs/limits_eta_noReweight_div100sgn_freezeJpsi_log
tail -n 5 logs/limits_dR_noReweight_div100sgn_freezeJpsi_log
echo "NOW RUNNING: eta and dR combination; no reweight, freezeJpsi, div100sgn"
source scripts/run_limits_combination_parallel.sh --cat eta --no_reweight --freeze_jpsi --fit_tag freezeJpsi --tag div100sgn &> logs/limits_eta_combination_noReweight_div100sgn_freezeJpsi_log &
source scripts/run_limits_combination_parallel.sh --cat dR --no_reweight --freeze_jpsi --fit_tag freezeJpsi --tag div100sgn &> logs/limits_dR_combination_noReweight_div100sgn_freezeJpsi_log &
wait
tail -n 5 logs/limits_eta_combination_noReweight_div100sgn_freezeJpsi_log
tail -n 5 logs/limits_dR_combination_noReweight_div100sgn_freezeJpsi_log