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
