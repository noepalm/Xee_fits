# fitDiagnostics_reweight_categories_div100wgt/mu0/inclusive/
# fitDiagnostics_reweight_categories_div100wgt/mu0/dRCombination/
# fitDiagnostics_reweight_categories_div100wgt/mu0/etaCombination/

# # Comparing INCLUSIVE vs. CATEGORY COMBINATION for reweighted dataset, 1/100 weights
# python3 plot_limits_comparison.py --input_folders "fitDiagnostics_reweight_categories_div100wgt/mu0/inclusive/" \
#                                                   "fitDiagnostics_reweight_categories_div100wgt/mu0/dRCombination/" \
#                                                   "fitDiagnostics_reweight_categories_div100wgt/mu0/etaCombination/" \
#                                   --tag "div100wgt"


# # Comparing reweighted VS no reweight dataset, inclusive category only
# python3 plot_limits_comparison.py --input_folders "fitDiagnostics_reweight_categories/mu0/inclusive/" \
#                                                   "fitDiagnostics_noReweight/mu0/inclusive/" \
#                                   --fit_tags "freezeNone" "" \
#                                   --labels "W/ trigger reweight" "No trigger reweight" \
#                                   --tag "reweight_vs_noReweight_inclusive"

# python3 plot_limits_comparison.py --input_folders "fitDiagnostics_reweight_categories_div100wgt/mu0/inclusive/" \
#                                                   "fitDiagnostics_noReweight_div100wgt/mu0/inclusive/" \
#                                   --labels "W/ trigger reweight" "No trigger reweight" \
#                                   --tag "reweight_vs_noReweight_inclusive_div100wgt"

# Comparing INCLUSIVE vs. CATEGORY COMBINATION for reweighted dataset, nominal weights
# region1
python3 plot_limits_comparison.py --input_folders "fitDiagnostics_grid_reweight_categories/mu0/inclusive/" \
                                                  "fitDiagnostics_grid_reweight_categories/mu0/dRCombination/" \
                                                  "fitDiagnostics_grid_reweight_categories/mu0/etaCombination/" \
                                  --region "region1"

# region 2 (excluding dR categories bc of low stats in low dR region)
python3 plot_limits_comparison.py --input_folders "fitDiagnostics_grid_reweight_categories/mu0/inclusive/" \
                                                  "fitDiagnostics_grid_reweight_categories/mu0/etaCombination/" \
                                  --region "region2"

