# TEST: produce updated signal model
python main_background_analysis.py --full_analysis --bkg_function 4 \
                                   --fit_jpsi_prompt --floating_resonant \
                                   --folder_tag "251216" \
                                   --data --tag="data_altbkg_chebyshev_newsignal_nores" \
                                   --category="inclusive" \
                                   --binned \
                                   --no_res \
                                   --cached \
                                   --fit_region="region0" &> logs/reweight_data_region0_altbkg_chebyshev_newsignal_binned_log &
                                   
python main_background_analysis.py --full_analysis --bkg_function 4 \
                                   --fit_jpsi_prompt --floating_resonant \
                                   --data \
                                   --folder_tag "251216" \
                                   --tag="data_altbkg_chebyshev_newsignal_nores" \
                                   --category="inclusive" \
                                   --binned \
                                   --no_res \
                                   --fit_region="region1" &> logs/251216/reweight_data_region1_altbkg_chebyshev_newsignal_binned_log &

python main_background_analysis.py --full_analysis --bkg_function 4 \
                                   --fit_jpsi_prompt --floating_resonant \
                                   --folder_tag "251216" \
                                   --data --tag="data_altbkg_chebyshev_newsignal_nores" \
                                   --category="inclusive" \
                                   --binned \
                                   --cached \
                                   --no_res \
                                   --fit_region="region2" &> logs/251216/reweight_data_region2_altbkg_chebyshev_newsignal_binned_log &
