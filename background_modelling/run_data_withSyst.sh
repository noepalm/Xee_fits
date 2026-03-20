### TEST: using new signal model with systematics
# chebyshev only, region 1 only

python main_background_analysis.py --full_analysis --bkg_function 4 \
                                   --fit_jpsi_prompt --floating_resonant \
                                   --data --tag="data_altbkg_chebyshev_withSyst" \
                                   --categories="inclusive" \
                                   --binned \
                                   --cached \
                                   --withSyst --corrected \
                                   --folder_tag="260122" \
                                   --fit_region="region1" &> logs/reweight_data_region1_altbkg_chebyshev_withSyst_binned_log &

python main_background_analysis.py --full_analysis --bkg_function 7 \
                                   --fit_jpsi_prompt --floating_resonant \
                                   --data --tag="data_altbkg_chebyshev_withSyst" \
                                   --categories="inclusive" \
                                   --binned \
                                   --cached \
                                   --withSyst --corrected \
                                   --folder_tag="260122" \
                                   --fit_region="region2" &> logs/reweight_data_region2_altbkg_chebyshev_withSyst_binned_log &

python main_background_analysis.py --full_analysis --bkg_function 7 \
                                   --fit_jpsi_prompt --floating_resonant \
                                   --data --tag="data_altbkg_chebyshev_withSyst" \
                                   --categories="inclusive" \
                                   --binned \
                                   --cached \
                                   --withSyst --corrected \
                                   --folder_tag="260122" \
                                   --fit_region="region0" &> logs/reweight_data_region0_altbkg_chebyshev_withSyst_binned_log &

# # ---------------------------------------------------------------- #
# ### bkg 0: Bernstein
# python main_background_analysis.py --full_analysis --bkg_function 0 \
#                                    --fit_jpsi_prompt --floating_resonant \
#                                    --data --tag="data" \
#                                    --categories="inclusive" \
#                                    --binned \
#                                    --fit_region="region0" &> logs/reweight_data_region0_binned_log &
# python main_background_analysis.py --full_analysis --bkg_function 0 \
#                                    --fit_jpsi_prompt --floating_resonant \
#                                    --data --tag="data" \
#                                    --categories="inclusive" \
#                                    --binned \
#                                    --fit_region="region1" &> logs/reweight_data_region1_binned_log &
# python main_background_analysis.py --full_analysis --bkg_function 0 \
#                                    --fit_jpsi_prompt --floating_resonant \
#                                    --data --tag="data" \
#                                    --categories="inclusive" \
#                                    --binned \
#                                    --fit_region="region2" &> logs/reweight_data_region2_binned_log &

# ### bkg 1: Polynomial x Exponential
# python main_background_analysis.py --full_analysis --bkg_function 1 \
#                                    --fit_jpsi_prompt --floating_resonant \
#                                    --data --tag="data_altbkg_poly" \
#                                    --categories="inclusive" \
#                                    --binned \
#                                    --fit_region="region0" &> logs/reweight_data_region0_altbkg_poly_binned_log &

# python main_background_analysis.py --full_analysis --bkg_function 1 \
#                                    --fit_jpsi_prompt --floating_resonant \
#                                    --data --tag="data_altbkg_poly" \
#                                    --categories="inclusive" \
#                                    --binned \
#                                    --fit_region="region1" &> logs/reweight_data_region1_altbkg_poly_binned_log &

# python main_background_analysis.py --full_analysis --bkg_function 1 \
#                                    --fit_jpsi_prompt --floating_resonant \
#                                    --data --tag="data_altbkg_poly" \
#                                    --categories="inclusive" \
#                                    --binned \
#                                    --fit_region="region2" &> logs/reweight_data_region2_altbkg_poly_binned_log &

# ### bkg 4: Chebyshev Polynomial
# python main_background_analysis.py --full_analysis --bkg_function 4 \
#                                    --fit_jpsi_prompt --floating_resonant \
#                                    --data --tag="data_altbkg_chebyshev" \
#                                    --categories="inclusive" \
#                                    --binned \
#                                    --fit_region="region0" &> logs/reweight_data_region0_altbkg_chebyshev_binned_log &

# python main_background_analysis.py --full_analysis --bkg_function 4 \
#                                    --fit_jpsi_prompt --floating_resonant \
#                                    --data --tag="data_altbkg_chebyshev" \
#                                    --categories="inclusive" \
#                                    --binned \
#                                    --fit_region="region1" &> logs/reweight_data_region1_altbkg_chebyshev_binned_log &

# python main_background_analysis.py --full_analysis --bkg_function 4 \
#                                    --fit_jpsi_prompt --floating_resonant \
#                                    --data --tag="data_altbkg_chebyshev" \
#                                    --categories="inclusive" \
#                                    --binned \
#                                    --fit_region="region2" &> logs/reweight_data_region2_altbkg_chebyshev_binned_log &

# ###### ENVELOPE
# python3 main_background_analysis.py --full_analysis --bkg_function -1 \
#                                     --data --tag="data" \
#                                     --categories="inclusive" \
#                                     --input_workspaces "datasets/dataset_data_region0_binned_data_altbkg_chebyshev_full.root" \
#                                                        "datasets/dataset_data_region0_binned_data_altbkg_poly_full.root" \
#                                                        "datasets/dataset_data_region0_binned_data_full.root" \
#                                     --binned \
#                                     --fit_region="region0" &> logs/reweight_data_region0_envelope_binned_log &

# python3 main_background_analysis.py --full_analysis --bkg_function -1 \
#                                     --data --tag="data" \
#                                     --categories="inclusive" \
#                                     --input_workspaces "datasets/dataset_data_region1_binned_data_altbkg_chebyshev_full.root" \
#                                                        "datasets/dataset_data_region1_binned_data_altbkg_poly_full.root" \
#                                                        "datasets/dataset_data_region1_binned_data_full.root" \
#                                     --binned \
#                                     --fit_region="region1" &> logs/reweight_data_region1_envelope_binned_log &

# python3 main_background_analysis.py --full_analysis --bkg_function -1 \
#                                     --data --tag="data" \
#                                     --categories="inclusive" \
#                                     --input_workspaces "datasets/dataset_data_region2_binned_data_altbkg_chebyshev_full.root" \
#                                                        "datasets/dataset_data_region2_binned_data_altbkg_poly_full.root" \
#                                                        "datasets/dataset_data_region2_binned_data_full.root" \
#                                     --binned \
#                                     --fit_region="region2" &> logs/reweight_data_region2_envelope_binned_log &                                