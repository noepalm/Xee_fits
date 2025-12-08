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

# region 0 (excluding dR categories bc of low stats in low dR region)
python3 plot_limits_comparison.py --input_folders "fitDiagnostics_grid_reweight_categories/mu0/inclusive/" \
                                                  "fitDiagnostics_grid_reweight_categories/mu0/etaCombination/" \
                                  --region "region0"


# ====================================================================

# Comparing limits with Bernstein vs. Chebyshev background functions

python3 plot_limits_comparison.py --input_folders "fitDiagnostics_grid_reweight_categories_nanov15_altbkg_chebyshev/mu0/inclusive/" \
                                                  "fitDiagnostics_grid_reweight_categories_nanov15_altbkg_poly/mu0/inclusive/" \
                                                  "fitDiagnostics_grid_reweight_categories_nanov15_overlap/mu0/inclusive/" \
                                  --region "region0" \
                                  --labels "Chebyshev" "Polynomial" "Bernstein" \
                                  --tag "altbkg"

python3 plot_limits_comparison.py --input_folders "fitDiagnostics_grid_reweight_categories_nanov15_altbkg_chebyshev/mu0/inclusive/" \
                                                  "fitDiagnostics_grid_reweight_categories_nanov15_altbkg_poly/mu0/inclusive/" \
                                                  "fitDiagnostics_grid_reweight_categories_nanov15_overlap/mu0/inclusive/" \
                                  --region "region1" \
                                  --labels "Chebyshev" "Polynomial" "Bernstein" \
                                  --tag "altbkg"

python3 plot_limits_comparison.py --input_folders "fitDiagnostics_grid_reweight_categories_nanov15_altbkg_chebyshev/mu0/inclusive/" \
                                                  "fitDiagnostics_grid_reweight_categories_nanov15_altbkg_poly/mu0/inclusive/" \
                                                  "fitDiagnostics_grid_reweight_categories_nanov15_overlap/mu0/inclusive/" \
                                  --region "region2" \
                                  --labels "Chebyshev" "Polynomial" "Bernstein" \
                                  --tag "altbkg"

# ====================================================================

# Comparing binned vs unbinned

python3 plot_limits_comparison.py --input_folders "fitDiagnostics_grid_data_condor/mu0/inclusive/" \
                                                  "fitDiagnostics_grid_data_binned/mu0/inclusive/" \
                                  --region "region0" \
                                  --labels "Unbinned" "Binned" \
                                  --mu \
                                  --tag "data_binned_vs_unbinned"

python3 plot_limits_comparison.py --input_folders "fitDiagnostics_grid_data_condor/mu0/inclusive/" \
                                                  "fitDiagnostics_grid_data_binned/mu0/inclusive/" \
                                  --region "region1" \
                                  --mu \
                                  --labels "Unbinned" "Binned" \
                                  --tag "data_binned_vs_unbinned"

python3 plot_limits_comparison.py --input_folders "fitDiagnostics_grid_data_condor/mu0/inclusive/" \
                                                  "fitDiagnostics_grid_data_binned/mu0/inclusive/" \
                                  --region "region2" \
                                  --mu \
                                  --labels "Unbinned" "Binned" \
                                  --tag "data_binned_vs_unbinned"

# ====================================================================

# Comparing envelope limits w/ individual bkgs


python3 plot_limits_comparison.py --input_folders "fitDiagnostics_grid_data_altbkg_chebyshev_binned/mu0/inclusive/" \
                                                  "fitDiagnostics_grid_data_altbkg_poly_binned/mu0/inclusive/" \
                                                  "fitDiagnostics_grid_data_binned/mu0/inclusive/" \
                                                  "fitDiagnostics_grid_data_envelope_binned/mu0/inclusive/" \
                                  --region "region0" \
                                  --labels "Chebyshev" "Polynomial" "Bernstein" "Envelope" \
                                  --tag "data_envelope"

python3 plot_limits_comparison.py --input_folders "fitDiagnostics_grid_data_altbkg_chebyshev_binned/mu0/inclusive/" \
                                                  "fitDiagnostics_grid_data_altbkg_poly_binned/mu0/inclusive/" \
                                                  "fitDiagnostics_grid_data_binned/mu0/inclusive/" \
                                                  "fitDiagnostics_grid_data_envelope_binned/mu0/inclusive/" \
                                  --region "region1" \
                                  --labels "Chebyshev" "Polynomial" "Bernstein" "Envelope" \
                                  --tag "data_envelope"

python3 plot_limits_comparison.py --input_folders "fitDiagnostics_grid_data_altbkg_chebyshev_binned/mu0/inclusive/" \
                                                  "fitDiagnostics_grid_data_altbkg_poly_binned/mu0/inclusive/" \
                                                  "fitDiagnostics_grid_data_binned/mu0/inclusive/" \
                                                  "fitDiagnostics_grid_data_envelope_binned/mu0/inclusive/" \
                                  --region "region1" \
                                  --labels "Chebyshev" "Polynomial" "Bernstein" "Envelope" \
                                  --tag "data_envelope_97p5"


python3 plot_limits_comparison.py --input_folders "fitDiagnostics_grid_data_altbkg_chebyshev_binned/mu0/inclusive/" \
                                                  "fitDiagnostics_grid_data_altbkg_poly_binned/mu0/inclusive/" \
                                                  "fitDiagnostics_grid_data_binned/mu0/inclusive/" \
                                                  "fitDiagnostics_grid_data_envelope_binned/mu0/inclusive/" \
                                  --region "region2" \
                                  --labels "Chebyshev" "Polynomial" "Bernstein" "Envelope" \
                                  --tag "data_envelope"
