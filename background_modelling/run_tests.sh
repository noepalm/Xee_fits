python main_background_analysis.py --full_analysis --bkg_function 0 \
                                   --fit_jpsi_prompt --floating_resonant \
                                   --tag="reweight" &> logs/reweight_cats_log

python main_background_analysis.py --full_analysis --bkg_function 0 \
                                   --fit_jpsi_prompt --floating_resonant \
                                   --fit_region="region1" \
                                   --tag="test" &> logs/reweight_cats_test_region1_log

python main_background_analysis.py --full_analysis --bkg_function 0 \
                                   --fit_jpsi_prompt --floating_resonant \
                                   --fit_region="region2" \
                                   --tag="test" &> logs/reweight_cats_test_region2_log

# DEBUGGING
python main_background_analysis.py --full_analysis --bkg_function 0 \
                                   --fit_jpsi_prompt --floating_resonant \
                                   --weight_multiplier 0.01 \
                                   --tag="reweight_div100wgt" &> logs/reweight_div100w_cats_log

python main_background_analysis.py --full_analysis --bkg_function 0 \
                                   --fit_jpsi_prompt --floating_resonant \
                                   --no_reweighting &> logs/noreweight_cats_log

python main_background_analysis.py --full_analysis --bkg_function 0 \
                                   --fit_jpsi_prompt --floating_resonant \
                                   --no_reweighting \
                                   --weight_multiplier 2 \
                                   --tag="x2wgt" &> logs/noreweight_x2w_cats_log

python main_background_analysis.py --full_analysis --bkg_function 0 \
                                   --fit_jpsi_prompt --floating_resonant \
                                   --no_reweighting \
                                   --weight_multiplier 0.01 \
                                   --tag="div100wgt" &> logs/noreweight_div100w_cats_log

# Binned
python main_background_analysis.py --full_analysis --bkg_function 0 \
                                   --fit_jpsi_prompt --floating_resonant \
                                   --binned \
                                   --tag="reweight" &> logs/reweight_binned_cats_log

python main_background_analysis.py --full_analysis --bkg_function 0 \
                                   --fit_jpsi_prompt --floating_resonant \
                                   --binned \
                                   --no_reweighting &> logs/noreweight_binned_cats_log

python main_background_analysis.py --full_analysis --bkg_function 0 \
                                   --fit_jpsi_prompt --floating_resonant \
                                   --binned --no_reweighting \
                                   --weight_multiplier 2 \
                                   --tag="x2wgt" &> logs/noreweight_x2w_binned_cats_log

python main_background_analysis.py --full_analysis --bkg_function 0 \
                                   --fit_jpsi_prompt --floating_resonant \
                                   --binned --no_reweighting \
                                   --weight_multiplier 0.01 \
                                   --tag="div100wgt" &> logs/noreweight_div100w_binned_cats_log