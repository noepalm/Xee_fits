# python main_background_analysis.py --full_analysis --bkg_function 0 \
#                                    --fit_jpsi_prompt --floating_resonant \
#                                    --data --tag="data" \
#                                    --category="inclusive" \
#                                    --fit_region="region0" &> logs/reweight_data_region0_log &

# python main_background_analysis.py --full_analysis --bkg_function 0 \
#                                    --fit_jpsi_prompt --floating_resonant \
#                                    --data --tag="data" \
#                                    --category="inclusive" \
#                                    --fit_region="region1" &> logs/reweight_data_region1_log &

# python main_background_analysis.py --full_analysis --bkg_function 0 \
#                                    --fit_jpsi_prompt --floating_resonant \
#                                    --data --tag="data" \
#                                    --category="inclusive" \
#                                    --fit_region="region2" &> logs/reweight_data_region2_log &

# binned
python main_background_analysis.py --full_analysis --bkg_function 0 \
                                   --fit_jpsi_prompt --floating_resonant \
                                   --data --tag="data" \
                                   --category="inclusive" \
                                   --binned \
                                   --fit_region="region0" &> logs/reweight_data_region0_binned_log &
python main_background_analysis.py --full_analysis --bkg_function 0 \
                                   --fit_jpsi_prompt --floating_resonant \
                                   --data --tag="data" \
                                   --category="inclusive" \
                                   --binned \
                                   --fit_region="region1" &> logs/reweight_data_region1_binned_log &
python main_background_analysis.py --full_analysis --bkg_function 0 \
                                   --fit_jpsi_prompt --floating_resonant \
                                   --data --tag="data" \
                                   --category="inclusive" \
                                   --binned \
                                   --fit_region="region2" &> logs/reweight_data_region2_binned_log &

# ==========================
#        ALT BKG TEST
# ==========================

### Polynomial x Exponential
python main_background_analysis.py --full_analysis --bkg_function 1 \
                                   --fit_jpsi_prompt --floating_resonant \
                                   --data --tag="data_altbkg_poly" \
                                   --category="inclusive" \
                                   --fit_region="region0" &> logs/reweight_data_region0_altbkg_poly_log &

python main_background_analysis.py --full_analysis --bkg_function 1 \
                                   --fit_jpsi_prompt --floating_resonant \
                                   --data --tag="data_altbkg_poly" \
                                   --category="inclusive" \
                                   --fit_region="region1" &> logs/reweight_data_region1_altbkg_poly_log &

python main_background_analysis.py --full_analysis --bkg_function 1 \
                                   --fit_jpsi_prompt --floating_resonant \
                                   --data --tag="data_altbkg_poly" \
                                   --category="inclusive" \
                                   --fit_region="region2" &> logs/reweight_data_region2_altbkg_poly_log &

# binned
python main_background_analysis.py --full_analysis --bkg_function 1 \
                                   --fit_jpsi_prompt --floating_resonant \
                                   --data --tag="data_altbkg_poly" \
                                   --category="inclusive" \
                                   --binned \
                                   --fit_region="region0" &> logs/reweight_data_region0_altbkg_poly_binned_log &

python main_background_analysis.py --full_analysis --bkg_function 1 \
                                   --fit_jpsi_prompt --floating_resonant \
                                   --data --tag="data_altbkg_poly" \
                                   --category="inclusive" \
                                   --binned \
                                   --fit_region="region1" &> logs/reweight_data_region1_altbkg_poly_binned_log &

# ### TEMPORARY!!!!
# python main_background_analysis.py --full_analysis --bkg_function 1 \
#                                    --fit_jpsi_prompt --floating_resonant \
#                                    --data --tag="data_altbkg_purepoly" \
#                                    --category="inclusive" \
#                                    --binned \
#                                    --fit_region="region1" &> logs/reweight_data_region1_altbkg_purepoly_binned_log &

# python main_background_analysis.py --full_analysis --bkg_function 1 \
#                                    --fit_jpsi_prompt --floating_resonant \
#                                    --data --tag="data_altbkg_polyexp" \
#                                    --category="inclusive" \
#                                    --binned \
#                                    --fit_region="region1" &> logs/reweight_data_region1_altbkg_polyexp_binned_log &
# ### END TEMPORARY!!!!

python main_background_analysis.py --full_analysis --bkg_function 1 \
                                   --fit_jpsi_prompt --floating_resonant \
                                   --data --tag="data_altbkg_poly" \
                                   --category="inclusive" \
                                   --binned \
                                   --fit_region="region2" &> logs/reweight_data_region2_altbkg_poly_binned_log &


### Sum of Exponentials

python main_background_analysis.py --full_analysis --bkg_function 2 \
                                   --fit_jpsi_prompt --floating_resonant \
                                   --data --tag="data_altbkg_sumexp" \
                                   --category="inclusive" \
                                   --fit_region="region1" &> logs/reweight_data_region1_altbkg_sumexp_log &

python main_background_analysis.py --full_analysis --bkg_function 2 \
                                   --fit_jpsi_prompt --floating_resonant \
                                   --data --tag="data_altbkg_sumexp" \
                                   --category="inclusive" \
                                   --fit_region="region0" &> logs/reweight_data_region0_altbkg_sumexp_log &

python main_background_analysis.py --full_analysis --bkg_function 2 \
                                   --fit_jpsi_prompt --floating_resonant \
                                   --data --tag="data_altbkg_sumexp" \
                                   --category="inclusive" \
                                   --fit_region="region2" &> logs/reweight_data_region2_altbkg_sumexp_log &


### Chebyshev Polynomial
python main_background_analysis.py --full_analysis --bkg_function 4 \
                                   --fit_jpsi_prompt --floating_resonant \
                                   --data --tag="data_altbkg_chebyshev" \
                                   --category="inclusive" \
                                   --fit_region="region0" &> logs/reweight_data_region0_altbkg_chebyshev_log &

python main_background_analysis.py --full_analysis --bkg_function 4 \
                                   --fit_jpsi_prompt --floating_resonant \
                                   --data --tag="data_altbkg_chebyshev" \
                                   --category="inclusive" \
                                   --fit_region="region1" &> logs/reweight_data_region1_altbkg_chebyshev_log &

python main_background_analysis.py --full_analysis --bkg_function 4 \
                                   --fit_jpsi_prompt --floating_resonant \
                                   --data --tag="data_altbkg_chebyshev" \
                                   --category="inclusive" \
                                   --fit_region="region2" &> logs/reweight_data_region2_altbkg_chebyshev_log &

# binned
python main_background_analysis.py --full_analysis --bkg_function 4 \
                                   --fit_jpsi_prompt --floating_resonant \
                                   --data --tag="data_altbkg_chebyshev" \
                                   --category="inclusive" \
                                   --binned \
                                   --fit_region="region0" &> logs/reweight_data_region0_altbkg_chebyshev_binned_log &

python main_background_analysis.py --full_analysis --bkg_function 4 \
                                   --fit_jpsi_prompt --floating_resonant \
                                   --data --tag="data_altbkg_chebyshev" \
                                   --category="inclusive" \
                                   --binned \
                                   --fit_region="region1" &> logs/reweight_data_region1_altbkg_chebyshev_binned_log &

python main_background_analysis.py --full_analysis --bkg_function 4 \
                                   --fit_jpsi_prompt --floating_resonant \
                                   --data --tag="data_altbkg_chebyshev" \
                                   --category="inclusive" \
                                   --binned \
                                   --fit_region="region2" &> logs/reweight_data_region2_altbkg_chebyshev_binned_log &

### Bernstein + exp
# binned
python main_background_analysis.py --full_analysis --bkg_function 5 \
                                   --fit_jpsi_prompt --floating_resonant \
                                   --data --tag="data_altbkg_bernsteinexp" \
                                   --category="inclusive" \
                                   --binned \
                                   --fit_region="region0" &> logs/reweight_data_region0_altbkg_bernsteinexp_binned_log &

python main_background_analysis.py --full_analysis --bkg_function 5 \
                                   --fit_jpsi_prompt --floating_resonant \
                                   --data --tag="data_altbkg_bernsteinexp" \
                                   --category="inclusive" \
                                   --binned \
                                   --fit_region="region1" &> logs/reweight_data_region1_altbkg_bernsteinexp_binned_log &

python main_background_analysis.py --full_analysis --bkg_function 5 \
                                   --fit_jpsi_prompt --floating_resonant \
                                   --data --tag="data_altbkg_bernsteinexp" \
                                   --category="inclusive" \
                                   --binned \
                                   --fit_region="region2" &> logs/reweight_data_region2_altbkg_bernsteinexp_binned_log &


### Modified BW
# binned
python main_background_analysis.py --full_analysis --bkg_function 6 \
                                   --fit_jpsi_prompt --floating_resonant \
                                   --data --tag="data_altbkg_modifiedbw" \
                                   --category="inclusive" \
                                   --binned \
                                   --fit_region="region0" &> logs/reweight_data_region0_altbkg_modifiedbw_binned_log &

python main_background_analysis.py --full_analysis --bkg_function 6 \
                                   --fit_jpsi_prompt --floating_resonant \
                                   --data --tag="data_altbkg_modifiedbw" \
                                   --category="inclusive" \
                                   --binned \
                                   --fit_region="region1" &> logs/reweight_data_region1_altbkg_modifiedbw_binned_log &

python main_background_analysis.py --full_analysis --bkg_function 6 \
                                   --fit_jpsi_prompt --floating_resonant \
                                   --data --tag="data_altbkg_modifiedbw" \
                                   --category="inclusive" \
                                   --binned \
                                   --fit_region="region2" &> logs/reweight_data_region2_altbkg_modifiedbw_binned_log &


###### ENVELOPE

python3 main_background_analysis.py --full_analysis --bkg_function -1 \
                                    --data --tag="data" \
                                    --category="inclusive" \
                                    --input_workspaces "datasets/dataset_data_region0_binned_data_altbkg_chebyshev_full.root" \
                                                       "datasets/dataset_data_region0_binned_data_altbkg_poly_full.root" \
                                                       "datasets/dataset_data_region0_binned_data_full.root" \
                                    --binned \
                                    --fit_region="region0" &> logs/reweight_data_region0_envelope_binned_log &

python3 main_background_analysis.py --full_analysis --bkg_function -1 \
                                    --data --tag="data" \
                                    --category="inclusive" \
                                    --input_workspaces "datasets/dataset_data_region1_binned_data_altbkg_chebyshev_full.root" \
                                                       "datasets/dataset_data_region1_binned_data_altbkg_poly_full.root" \
                                                       "datasets/dataset_data_region1_binned_data_full.root" \
                                    --binned \
                                    --fit_region="region1" &> logs/reweight_data_region1_envelope_binned_log &

python3 main_background_analysis.py --full_analysis --bkg_function -1 \
                                    --data --tag="data" \
                                    --category="inclusive" \
                                    --input_workspaces "datasets/dataset_data_region2_binned_data_altbkg_chebyshev_full.root" \
                                                       "datasets/dataset_data_region2_binned_data_altbkg_poly_full.root" \
                                                       "datasets/dataset_data_region2_binned_data_full.root" \
                                    --binned \
                                    --fit_region="region2" &> logs/reweight_data_region2_envelope_binned_log &

# ==================================================
# TEST: freeze resonant on MinBias
python main_background_analysis.py --full_analysis --bkg_function 0 \
                                   --fit_jpsi_prompt --floating_resonant \
                                   --data --tag="data_altbkg_chebyshev_freezeResOnMinBias" \
                                   --category="inclusive" \
                                   --binned \
                                   --cached \
                                   --fit_region="region1" &> logs/reweight_data_freezeResOnMinBias_region1_binned_log &

# TEST: produce updated signal model
python main_background_analysis.py --full_analysis --bkg_function 4 \
                                   --fit_jpsi_prompt --floating_resonant \
                                   --data --tag="data_altbkg_chebyshev_newsignal" \
                                   --category="inclusive" \
                                   --binned \
                                   --cached \
                                   --fit_region="region0" &> logs/reweight_data_region0_altbkg_chebyshev_newsignal_binned_log &
                                   
python main_background_analysis.py --full_analysis --bkg_function 4 \
                                   --fit_jpsi_prompt --floating_resonant \
                                   --data --tag="data_altbkg_chebyshev_newsignal" \
                                   --category="inclusive" \
                                   --binned \
                                   --cached \
                                   --fit_region="region1" &> logs/reweight_data_region1_altbkg_chebyshev_newsignal_binned_log &

python main_background_analysis.py --full_analysis --bkg_function 4 \
                                   --fit_jpsi_prompt --floating_resonant \
                                   --data --tag="data_altbkg_chebyshev_newsignal" \
                                   --category="inclusive" \
                                   --binned \
                                   --cached \
                                   --fit_region="region2" &> logs/reweight_data_region2_altbkg_chebyshev_newsignal_binned_log &