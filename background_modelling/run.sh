python main_background_analysis.py --full_analysis --bkg_function 0 \
                                   --fit_jpsi_prompt --floating_resonant \
                                   --fit_region="region0" &> logs/reweight_cats_region0_log

python main_background_analysis.py --full_analysis --bkg_function 0 \
                                   --fit_jpsi_prompt --floating_resonant \
                                   --fit_region="region1" &> logs/reweight_cats_region1_log

python main_background_analysis.py --full_analysis --bkg_function 0 \
                                   --fit_jpsi_prompt --floating_resonant \
                                   --fit_region="region2" &> logs/reweight_cats_region2_log

python main_background_analysis.py --full_analysis --bkg_function 0 \
                                   --fit_jpsi_prompt --floating_resonant \
                                   --fit_region="region1" \
                                   --weight_multiplier 0.01 \
                                   --tag="div100wgt" &> logs/reweight_cats_region1_div100wgt_log

python main_background_analysis.py --full_analysis --bkg_function 0 \
                                   --fit_jpsi_prompt --floating_resonant \
                                   --fit_region="region2" \
                                   --weight_multiplier 0.01 \
                                   --tag="div100wgt" &> logs/reweight_cats_region2_div100wgt_log

# ---------------------------------

python main_background_analysis.py --full_analysis --bkg_function 0 \
                                   --fit_jpsi_prompt --floating_resonant \
                                   --create_dataset \
                                   --fit_region="region1" --tag="debug_test" &> logs/reweight_cats_region1_debug_test_log

python main_background_analysis.py --full_analysis --bkg_function 0 \
                                   --fit_jpsi_prompt --floating_resonant \
                                   --tag="debug_test" \
                                   --fit_region="region0" &> logs/reweight_cats_region0_debug_log

# ---------------------------------
# FULL STATS TEST

python main_background_analysis.py --full_analysis --bkg_function 0 \
                                   --fit_jpsi_prompt --floating_resonant \
                                   --tag="nanov15" \
                                   --fit_region="region0" &> logs/reweight_cats_region0_nanov15_log

python main_background_analysis.py --full_analysis --bkg_function 0 \
                                   --fit_jpsi_prompt --floating_resonant \
                                   --tag="nanov15" \
                                   --fit_region="region1" &> logs/reweight_cats_region1_nanov15_log

python main_background_analysis.py --full_analysis --bkg_function 0 \
                                   --fit_jpsi_prompt --floating_resonant \
                                   --tag="nanov15" \
                                   --fit_region="region2" &> logs/reweight_cats_region2_nanov15_log

########################################
###        FULL STATS, OVERLAP       ###
########################################

python main_background_analysis.py --full_analysis --bkg_function 0 \
                                   --fit_jpsi_prompt --floating_resonant \
                                   --tag="nanov15_overlap" \
                                   --fit_region="region0" &> logs/reweight_cats_region0_nanov15_overlap_log &

python main_background_analysis.py --full_analysis --bkg_function 0 \
                                   --fit_jpsi_prompt --floating_resonant \
                                   --tag="nanov15_overlap" \
                                   --fit_region="region1" &> logs/reweight_cats_region1_nanov15_overlap_log &

python main_background_analysis.py --full_analysis --bkg_function 0 \
                                   --fit_jpsi_prompt --floating_resonant \
                                   --tag="nanov15_overlap" \
                                   --fit_region="region2" &> logs/reweight_cats_region2_nanov15_overlap_log &

# alt bkg (polynomial × exponential)
python main_background_analysis.py --full_analysis --bkg_function 1 \
                                   --fit_jpsi_prompt --floating_resonant \
                                   --tag="nanov15_overlap_altbkg_poly" \
                                   --category="inclusive" \
                                   --fit_region="region0" &> logs/reweight_cats_region0_nanov15_overlap_altbkg_poly_log &

python main_background_analysis.py --full_analysis --bkg_function 1 \
                                   --fit_jpsi_prompt --floating_resonant \
                                   --tag="nanov15_overlap_altbkg_poly" \
                                   --category="inclusive" \
                                   --fit_region="region1" &> logs/reweight_cats_region1_nanov15_overlap_altbkg_poly_log &

### binned
python main_background_analysis.py --full_analysis --bkg_function 1 \
                                   --fit_jpsi_prompt --floating_resonant \
                                   --tag="nanov15_overlap_altbkg_poly" \
                                   --category="inclusive" --binned \
                                   --fit_region="region1" &> logs/reweight_cats_region1_nanov15_overlap_altbkg_poly_binned_log &

python main_background_analysis.py --full_analysis --bkg_function 1 \
                                   --fit_jpsi_prompt --floating_resonant \
                                   --tag="nanov15_overlap_altbkg_poly" \
                                   --category="inclusive" \
                                   --fit_region="region2" &> logs/reweight_cats_region2_nanov15_overlap_altbkg_poly_log &

# alt bkg (chebyshev)
python main_background_analysis.py --full_analysis --bkg_function 4 \
                                   --fit_jpsi_prompt --floating_resonant \
                                   --tag="nanov15_overlap_altbkg_chebyshev" \
                                   --category="inclusive" \
                                   --fit_region="region0" &> logs/reweight_cats_region0_nanov15_overlap_altbkg_chebyshev_log &

python main_background_analysis.py --full_analysis --bkg_function 4 \
                                   --fit_jpsi_prompt --floating_resonant \
                                   --tag="nanov15_overlap_altbkg_chebyshev" \
                                   --category="inclusive" \
                                   --fit_region="region1" &> logs/reweight_cats_region1_nanov15_overlap_altbkg_chebyshev_log &

### binned
python main_background_analysis.py --full_analysis --bkg_function 4 \
                                   --fit_jpsi_prompt --floating_resonant \
                                   --tag="nanov15_overlap_altbkg_chebyshev" \
                                   --category="inclusive" --binned \
                                   --fit_region="region1" &> logs/reweight_cats_region1_nanov15_overlap_altbkg_chebyshev_binned_log &

python main_background_analysis.py --full_analysis --bkg_function 4 \
                                   --fit_jpsi_prompt --floating_resonant \
                                   --tag="nanov15_overlap_altbkg_chebyshev" \
                                   --category="inclusive" \
                                   --fit_region="region2" &> logs/reweight_cats_region2_nanov15_overlap_altbkg_chebyshev_log &

# envelope
### NB: to be run in combine environment
python3 main_background_analysis.py --full_analysis --bkg_function -1 \
                                   --tag="nanov15_overlap" \
                                   --category="inclusive" \
                                   --input_workspaces "datasets/nanov15_overlap/dataset_minbias_region0_full.root" \
                                                      "datasets/nanov15_overlap/dataset_minbias_region0_nanov15_overlap_altbkg_chebyshev_full.root" \
                                                      "datasets/nanov15_overlap/dataset_minbias_region0_nanov15_overlap_altbkg_poly_full.root" \
                                   --fit_region="region0" &> logs/reweight_cats_region0_nanov15_overlap_envelope_log &

python3 main_background_analysis.py --full_analysis --bkg_function -1 \
                                   --tag="nanov15_overlap" \
                                   --category="inclusive" \
                                   --input_workspaces "datasets/nanov15_overlap/dataset_minbias_region1_full.root" \
                                                      "datasets/nanov15_overlap/dataset_minbias_region1_nanov15_overlap_altbkg_chebyshev_full.root" \
                                                      "datasets/nanov15_overlap/dataset_minbias_region1_nanov15_overlap_altbkg_poly_full.root" \
                                   --fit_region="region1" &> logs/reweight_cats_region1_nanov15_overlap_envelope_log &

python3 main_background_analysis.py --full_analysis --bkg_function -1 \
                                   --tag="nanov15_overlap" \
                                   --category="inclusive" \
                                   --input_workspaces "datasets/nanov15_overlap/dataset_minbias_region2_full.root" \
                                                      "datasets/nanov15_overlap/dataset_minbias_region2_nanov15_overlap_altbkg_chebyshev_full.root" \
                                                      "datasets/nanov15_overlap/dataset_minbias_region2_nanov15_overlap_altbkg_poly_full.root" \
                                   --fit_region="region2" &> logs/reweight_cats_region2_nanov15_overlap_envelope_log &
