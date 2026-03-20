### Creating workspaces using different shapes for resonant backgrounds
# chebyshev only, region 1 only

# ### TEST 1: freeze to prompt MC
# python main_background_analysis.py --full_analysis --bkg_function 4 \
#                                    --fit_jpsi_prompt --floating_resonant \
#                                    --tag="data_altbkg_chebyshev_promptMCFreeze" \
#                                    --categories="inclusive" \
#                                    --binned \
#                                    --cached \
#                                    --data \
#                                    --withSyst --corrected \
#                                    --folder_tag="260205" \
#                                    --fit_region="region1" &> logs/reweight_data_region1_altbkg_chebyshev_promptMCFreeze_binned_log &

# python main_background_analysis.py --full_analysis --bkg_function 7 \
#                                    --fit_jpsi_prompt --floating_resonant \
#                                    --tag="data_altbkg_chebyshev_promptMCFreeze" \
#                                    --categories="inclusive" \
#                                    --binned \
#                                    --cached \
#                                    --data \
#                                    --withSyst --corrected \
#                                    --folder_tag="260205" \
#                                    --fit_region="region2" &> logs/reweight_data_region2_altbkg_chebyshev_promptMCFreeze_binned_log &

# python main_background_analysis.py --full_analysis --bkg_function 7 \
#                                    --fit_jpsi_prompt --floating_resonant \
#                                    --tag="data_altbkg_chebyshev_promptMCFreeze" \
#                                    --categories="inclusive" \
#                                    --binned \
#                                    --cached \
#                                    --data \
#                                    --withSyst --corrected \
#                                    --folder_tag="260205" \
#                                    --fit_region="region0" &> logs/reweight_data_region0_altbkg_chebyshev_promptMCFreeze_binned_log &

## TEST 2: freeze to data
python main_background_analysis.py --full_analysis --bkg_function 4 \
                                   --fit_jpsi_prompt --floating_resonant \
                                   --tag="data_altbkg_chebyshev_dataFreeze" \
                                   --categories="inclusive" \
                                   --binned \
                                   --cached \
                                   --data --fit_data \
                                   --withSyst --corrected \
                                   --folder_tag="260205" \
                                   --fit_region="region1" &> logs/reweight_data_region1_altbkg_chebyshev_dataFreeze_binned_log &

# python main_background_analysis.py --full_analysis --bkg_function 7 \
#                                    --fit_jpsi_prompt --floating_resonant \
#                                    --tag="data_altbkg_chebyshev_dataFreeze" \
#                                    --categories="inclusive" \
#                                    --binned \
#                                    --cached \
#                                    --data --fit_data \
#                                    --withSyst --corrected \
#                                    --folder_tag="260205" \
#                                    --fit_region="region2" &> logs/reweight_data_region2_altbkg_chebyshev_dataFreeze_binned_log &

# python main_background_analysis.py --full_analysis --bkg_function 7 \
#                                    --fit_jpsi_prompt --floating_resonant \
#                                    --tag="data_altbkg_chebyshev_dataFreeze" \
#                                    --categories="inclusive" \
#                                    --binned \
#                                    --cached \
#                                    --data --fit_data \
#                                    --withSyst --corrected \
#                                    --folder_tag="260205" \
#                                    --fit_region="region0" &> logs/reweight_data_region0_altbkg_chebyshev_dataFreeze_binned_log &

# ## TEST 3: freeze to minbias
# python main_background_analysis.py --full_analysis --bkg_function 4 \
#                                    --fit_jpsi_prompt --floating_resonant \
#                                    --tag="data_altbkg_chebyshev_minbiasFreeze" \
#                                    --categories="inclusive" \
#                                    --binned \
#                                    --cached \
#                                    --data \
#                                    --withSyst --corrected \
#                                    --folder_tag="260205" \
#                                    --fit_region="region1" &> logs/reweight_data_region1_altbkg_chebyshev_minbiasFreeze_binned_log &

# python main_background_analysis.py --full_analysis --bkg_function 7 \
#                                    --fit_jpsi_prompt --floating_resonant \
#                                    --tag="data_altbkg_chebyshev_minbiasFreeze" \
#                                    --categories="inclusive" \
#                                    --binned \
#                                    --cached \
#                                    --data \
#                                    --withSyst --corrected \
#                                    --folder_tag="260205" \
#                                    --fit_region="region2" &> logs/reweight_data_region2_altbkg_chebyshev_minbiasFreeze_binned_log &

# python main_background_analysis.py --full_analysis --bkg_function 7 \
#                                    --fit_jpsi_prompt --floating_resonant \
#                                    --tag="data_altbkg_chebyshev_minbiasFreeze" \
#                                    --categories="inclusive" \
#                                    --binned \
#                                    --cached \
#                                    --data \
#                                    --withSyst --corrected \
#                                    --folder_tag="260205" \
#                                    --fit_region="region0" &> logs/reweight_data_region0_altbkg_chebyshev_minbiasFreeze_binned_log &
