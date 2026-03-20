source scripts/run_diagnostics_parallel.sh --cat "dR" &> logs/diagnostics_dR_log &
source scripts/run_diagnostics_parallel.sh --cat "eta" &> logs/diagnostics_eta_log &

source scripts/run_limits_parallel.sh --freeze_jpsi --tag "freezeJpsi" --cat "inclusive" &> logs/limits_inclusive_freezeJpsi_log &
source scripts/run_limits_parallel.sh --freeze_jpsi --tag "freezeJpsi" --cat "dR" &> logs/limits_dR_freezeJpsi_log &
source scripts/run_limits_parallel.sh --freeze_jpsi --tag "freezeJpsi" --cat "eta" &> logs/limits_eta_freezeJpsi_log &
source scripts/run_limits_combination_parallel.sh --tag "freezeJpsi" --cat "dR" &> logs/limits_dR_combination_freezeJpsi_log &
source scripts/run_limits_combination_parallel.sh --tag "freezeJpsi" --cat "eta" &> logs/limits_eta_combination_freezeJpsi_log &

source scripts/run_limits_parallel.sh --tag "freezeBoth" --cat "inclusive" &> logs/limits_inclusive_freezeBoth_log &
source scripts/run_limits_parallel.sh --tag "freezeBoth" --cat "dR" &> logs/limits_dR_freezeBoth_log &
source scripts/run_limits_parallel.sh --tag "freezeBoth" --cat "eta" &> logs/limits_eta_freezeBoth_log &
source scripts/run_limits_combination_parallel.sh --tag "freezeBoth" --cat "dR" &> logs/limits_dR_combination_freezeBoth_log &
source scripts/run_limits_combination_parallel.sh --tag "freezeBoth" --cat "eta" &> logs/limits_eta_combination_freezeBoth_log &

source scripts/run_limits_parallel.sh --tag "freezeNone" --cat "inclusive" &> logs/limits_inclusive_freezeNone_log &
source scripts/run_limits_parallel.sh --tag "freezeNone" --cat "dR" &> logs/limits_dR_freezeNone_log &
source scripts/run_limits_parallel.sh --tag "freezeNone" --cat "eta" &> logs/limits_eta_freezeNone_log &
source scripts/run_limits_combination_parallel.sh --tag "freezeNone" --cat "dR" &> logs/limits_dR_combination_freezeNone_log &
source scripts/run_limits_combination_parallel.sh --tag "freezeNone" --cat "eta" &> logs/limits_eta_combination_freezeNone_log &

# ---- no reweight ----
python3 make_combine_workspace.py --cat="eta" --no_reweight &> logs/workspace_eta_noReweight_log
python3 make_combine_workspace.py --cat="dR" --no_reweight &> logs/workspace_dR_noReweight_log
python3 make_combine_workspace.py --cat="inclusive" --no_reweight &> logs/workspace_inclusive_noReweight_log

source scripts/run_diagnostics_parallel.sh --cat eta --no_reweight --freeze_jpsi --fit_tag freezeJpsi &> logs/diagnostics_eta_noReweight_freezeJpsi_log
source scripts/run_limits_parallel.sh --cat eta --no_reweight --freeze_jpsi --fit_tag freezeJpsi &> logs/limits_eta_noReweight_freezeJpsi_log

source scripts/run_diagnostics_parallel.sh --cat dR --no_reweight --freeze_jpsi --fit_tag freezeJpsi &> logs/diagnostics_dR_noReweight_freezeJpsi_og
source scripts/run_limits_parallel.sh --cat dR --no_reweight --freeze_jpsi --fit_tag freezeJpsi &> logs/limits_dR_noReweight_freezeJpsi_log

source scripts/run_diagnostics_parallel.sh --cat inclusive --no_reweight --freeze_jpsi --fit_tag freezeJpsi &> logs/diagnostics_inclusive_noReweight_freezeJpsi_log
source scripts/run_limits_parallel.sh --cat inclusive --no_reweight --freeze_jpsi --fit_tag freezeJpsi &> logs/limits_inclusive_noReweight_freezeJpsi_log

# ---- no reweight, x2 wgt test ----
python3 make_combine_workspace.py --cat="eta" --no_reweight --tag="x2wgt" &> logs/workspace_eta_noReweight_x2wgt_log
python3 make_combine_workspace.py --cat="dR" --no_reweight --tag="x2wgt" &> logs/workspace_dR_noReweight_x2wgt_log
python3 make_combine_workspace.py --cat="inclusive" --no_reweight --tag="x2wgt" &> logs/workspace_inclusive_noReweight_x2wgt_log

source scripts/run_diagnostics_parallel.sh --cat eta --no_reweight --tag x2wgt &> logs/diagnostics_eta_noReweight_x2wgt_log
source scripts/run_limits_parallel.sh --cat eta --no_reweight --tag x2wgt &> logs/limits_eta_noReweight_x2wgt_log

source scripts/run_diagnostics_parallel.sh --cat dR --no_reweight --tag x2wgt &> logs/diagnostics_dR_noReweight_x2wgt_og
source scripts/run_limits_parallel.sh --cat dR --no_reweight --tag x2wgt &> logs/limits_dR_noReweight_x2wgt_log

source scripts/run_diagnostics_parallel.sh --cat inclusive --no_reweight --tag x2wgt &> logs/diagnostics_inclusive_noReweight_x2wgt_log
source scripts/run_limits_parallel.sh --cat inclusive --no_reweight --tag x2wgt &> logs/limits_inclusive_noReweight_x2wgt_log

source scripts/run_limits_parallel.sh --cat inclusive --no_reweight --tag x2wgt &> logs/limits_inclusive_noReweight_x2wgt_log
source scripts/run_limits_parallel.sh --cat eta --no_reweight --tag x2wgt &> logs/limits_eta_noReweight_x2wgt_log
source scripts/run_limits_parallel.sh --cat dR --no_reweight --tag x2wgt &> logs/limits_dR_noReweight_x2wgt_log

source scripts/run_diagnostics_parallel.sh --cat inclusive --no_reweight --tag x2wgt &> logs/diagnostics_inclusive_noReweight_x2wgt_log

# ---- no reweight, x2 wgt test, freeze Jpsi ----
source scripts/run_limits_parallel.sh --cat inclusive --no_reweight --freeze_jpsi --fit_tag freezeJpsi --tag x2wgt &> logs/limits_inclusive_noReweight_x2wgt_freezeJpsi_log
source scripts/run_limits_parallel.sh --cat eta --no_reweight --freeze_jpsi --fit_tag freezeJpsi --tag x2wgt &> logs/limits_eta_noReweight_x2wgt_freezeJpsi_log
source scripts/run_limits_parallel.sh --cat dR --no_reweight --freeze_jpsi --fit_tag freezeJpsi --tag x2wgt &> logs/limits_dR_noReweight_x2wgt_freezeJpsi_log

# ---- no reweight, 1/100 wgt test ----
python3 make_combine_workspace.py --cat="eta" --no_reweight --tag="div100wgt" &> logs/workspace_eta_noReweight_div100wgt_log
python3 make_combine_workspace.py --cat="dR" --no_reweight --tag="div100wgt" &> logs/workspace_dR_noReweight_div100wgt_log
python3 make_combine_workspace.py --cat="inclusive" --no_reweight --tag="div100wgt" &> logs/workspace_inclusive_noReweight_div100wgt_log

source scripts/run_diagnostics_parallel.sh --cat eta --no_reweight --tag div100wgt &> logs/diagnostics_eta_noReweight_div100wgt_log
source scripts/run_limits_parallel.sh --cat eta --no_reweight --tag div100wgt &> logs/limits_eta_noReweight_div100wgt_log

source scripts/run_diagnostics_parallel.sh --cat dR --no_reweight --tag div100wgt &> logs/diagnostics_dR_noReweight_div100wgt_og
source scripts/run_limits_parallel.sh --cat dR --no_reweight --tag div100wgt &> logs/limits_dR_noReweight_div100wgt_log

source scripts/run_diagnostics_parallel.sh --cat inclusive --no_reweight --tag div100wgt &> logs/diagnostics_inclusive_noReweight_div100wgt_log
source scripts/run_limits_parallel.sh --cat inclusive --no_reweight --tag div100wgt &> logs/limits_inclusive_noReweight_div100wgt_log

source scripts/run_limits_parallel.sh --cat inclusive --no_reweight --tag div100wgt &> logs/limits_inclusive_noReweight_div100wgt_log
source scripts/run_limits_parallel.sh --cat eta --no_reweight --tag div100wgt &> logs/limits_eta_noReweight_div100wgt_log
source scripts/run_limits_parallel.sh --cat dR --no_reweight --tag div100wgt &> logs/limits_dR_noReweight_div100wgt_log

# ---- no reweight, 1/100 wgt, freezeJpsi test ----

source scripts/run_limits_parallel.sh --cat inclusive --freeze_jpsi --fit_tag freezeJpsi --no_reweight --tag div100wgt &> logs/limits_inclusive_noReweight_div100wgt_freezeJpsi_log
source scripts/run_limits_parallel.sh --cat eta --freeze_jpsi --fit_tag freezeJpsi --no_reweight --tag div100wgt &> logs/limits_eta_noReweight_div100wgt_freezeJpsi_log
source scripts/run_limits_parallel.sh --cat dR --freeze_jpsi --fit_tag freezeJpsi --no_reweight --tag div100wgt &> logs/limits_dR_noReweight_div100wgt_freezeJpsi_log



# ---- no reweight, 1/100 wgt, 1/100 signal yield test ----
python3 make_combine_workspace.py --cat="eta" --no_reweight --tag="div100wgt_div100sgn" &> logs/workspace_eta_noReweight_div100wgt_div100sgn_log
python3 make_combine_workspace.py --cat="dR" --no_reweight --tag="div100wgt_div100sgn" &> logs/workspace_dR_noReweight_div100wgt_div100sgn_log
python3 make_combine_workspace.py --cat="inclusive" --no_reweight --tag="div100wgt_div100sgn" &> logs/workspace_inclusive_noReweight_div100wgt_div100sgn_log

source scripts/run_diagnostics_parallel.sh --cat eta --no_reweight --tag div100wgt_div100sgn &> logs/diagnostics_eta_noReweight_div100wgt_div100sgn_log
source scripts/run_limits_parallel.sh --cat eta --no_reweight --tag div100wgt_div100sgn &> logs/limits_eta_noReweight_div100wgt_div100sgn_log

source scripts/run_diagnostics_parallel.sh --cat dR --no_reweight --tag div100wgt_div100sgn &> logs/diagnostics_dR_noReweight_div100wgt_div100sgn_og
source scripts/run_limits_parallel.sh --cat dR --no_reweight --tag div100wgt_div100sgn &> logs/limits_dR_noReweight_div100wgt_div100sgn_log

source scripts/run_diagnostics_parallel.sh --cat inclusive --no_reweight --tag div100wgt_div100sgn &> logs/diagnostics_inclusive_noReweight_div100wgt_div100sgn_log
source scripts/run_limits_parallel.sh --cat inclusive --no_reweight --tag div100wgt_div100sgn &> logs/limits_inclusive_noReweight_div100wgt_div100sgn_log

source scripts/run_limits_parallel.sh --cat inclusive --no_reweight --tag div100wgt_div100sgn &> logs/limits_inclusive_noReweight_div100wgt_div100sgn_log
source scripts/run_limits_parallel.sh --cat eta --no_reweight --tag div100wgt_div100sgn &> logs/limits_eta_noReweight_div100wgt_div100sgn_log
source scripts/run_limits_parallel.sh --cat dR --no_reweight --tag div100wgt_div100sgn &> logs/limits_dR_noReweight_div100wgt_div100sgn_log

source scripts/run_limits_parallel.sh --cat inclusive --no_reweight --tag div100wgt_div100sgn --plots_only &> logs/limits_inclusive_noReweight_div100wgt_div100sgn_log
