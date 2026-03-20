# for era in 2022 2023 2022EE 2023BPix; do
#     python main_background_analysis.py --full_analysis --bkg_function 4 \
#                                     --fit_jpsi_prompt --floating_resonant \
#                                     --data --tag="data_altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_${era}" \
#                                     --era $era \
#                                     --categories="inclusive" \
#                                     --binned \
#                                     --fit_data \
#                                     --cached \
#                                     --withSyst --corrected \
#                                     --folder_tag="260226/${era}" \
#                                     --signal_folder_tag="260226" \
#                                     --fit_region="region1" &> logs/260226/reweight_data_region1_altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_${era}_binned_log &

#     python main_background_analysis.py --full_analysis --bkg_function 7 \
#                                     --fit_jpsi_prompt --floating_resonant \
#                                     --data --tag="data_altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_${era}" \
#                                     --era $era \
#                                     --categories="inclusive" \
#                                     --fit_data \
#                                     --binned \
#                                     --cached \
#                                     --withSyst --corrected \
#                                     --folder_tag="260226/${era}" \
#                                     --signal_folder_tag="260226" \
#                                     --fit_region="region2" &> logs/260226/reweight_data_region2_altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_${era}_binned_log &

#     python main_background_analysis.py --full_analysis --bkg_function 7 \
#                                     --fit_jpsi_prompt --floating_resonant \
#                                     --data --tag="data_altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_${era}" \
#                                     --era $era \
#                                     --categories="inclusive" \
#                                     --binned \
#                                     --fit_data \
#                                     --cached \
#                                     --withSyst --corrected \
#                                     --folder_tag="260226/${era}" \
#                                     --fit_region="region0" &> logs/260226/reweight_data_region0_altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_${era}_binned_log &
# done

# # altbkg bernstein
# for era in 2022 2023 2022EE 2023BPix; do
#     python main_background_analysis.py --full_analysis --bkg_function 0 \
#                                     --fit_jpsi_prompt --floating_resonant \
#                                     --data --tag="data_altbkg_bernstein_withScaleSyst_IDSF_triggerSF_${era}" \
#                                     --era $era \
#                                     --categories="inclusive" \
#                                     --binned \
#                                     --fit_data \
#                                     --cached \
#                                     --withSyst --corrected \
#                                     --folder_tag="260226/${era}" \
#                                     --signal_folder_tag="260226" \
#                                     --fit_region="region1" &> logs/260226/reweight_data_region1_altbkg_bernstein_withScaleSyst_IDSF_triggerSF_${era}_binned_log &

#     python main_background_analysis.py --full_analysis --bkg_function 0 \
#                                     --fit_jpsi_prompt --floating_resonant \
#                                     --data --tag="data_altbkg_bernstein_withScaleSyst_IDSF_triggerSF_${era}" \
#                                     --era $era \
#                                     --categories="inclusive" \
#                                     --fit_data \
#                                     --binned \
#                                     --cached \
#                                     --withSyst --corrected \
#                                     --folder_tag="260226/${era}" \
#                                     --signal_folder_tag="260226" \
#                                     --fit_region="region2" &> logs/260226/reweight_data_region2_altbkg_bernstein_withScaleSyst_IDSF_triggerSF_${era}_binned_log &

#     python main_background_analysis.py --full_analysis --bkg_function 0 \
#                                     --fit_jpsi_prompt --floating_resonant \
#                                     --data --tag="data_altbkg_bernstein_withScaleSyst_IDSF_triggerSF_${era}" \
#                                     --era $era \
#                                     --categories="inclusive" \
#                                     --binned \
#                                     --fit_data \
#                                     --cached \
#                                     --withSyst --corrected \
#                                     --folder_tag="260226/${era}" \
#                                     --fit_region="region0" &> logs/260226/reweight_data_region0_altbkg_bernstein_withScaleSyst_IDSF_triggerSF_${era}_binned_log &
# done

# # altbkg polynomial x exponential
# for era in 2022 2023 2022EE 2023BPix; do
#     python main_background_analysis.py --full_analysis --bkg_function 1 \
#                                     --fit_jpsi_prompt --floating_resonant \
#                                     --data --tag="data_altbkg_polyexp_withScaleSyst_IDSF_triggerSF_${era}" \
#                                     --era $era \
#                                     --categories="inclusive" \
#                                     --binned \
#                                     --fit_data \
#                                     --cached \
#                                     --withSyst --corrected \
#                                     --folder_tag="260226/${era}" \
#                                     --signal_folder_tag="260226" \
#                                     --fit_region="region1" &> logs/260226/reweight_data_region1_altbkg_polyexp_withScaleSyst_IDSF_triggerSF_${era}_binned_log &

#     python main_background_analysis.py --full_analysis --bkg_function 1 \
#                                     --fit_jpsi_prompt --floating_resonant \
#                                     --data --tag="data_altbkg_polyexp_withScaleSyst_IDSF_triggerSF_${era}" \
#                                     --era $era \
#                                     --categories="inclusive" \
#                                     --fit_data \
#                                     --binned \
#                                     --cached \
#                                     --withSyst --corrected \
#                                     --folder_tag="260226/${era}" \
#                                     --signal_folder_tag="260226" \
#                                     --fit_region="region2" &> logs/260226/reweight_data_region2_altbkg_polyexp_withScaleSyst_IDSF_triggerSF_${era}_binned_log &

#     python main_background_analysis.py --full_analysis --bkg_function 1 \
#                                     --fit_jpsi_prompt --floating_resonant \
#                                     --data --tag="data_altbkg_polyexp_withScaleSyst_IDSF_triggerSF_${era}" \
#                                     --era $era \
#                                     --categories="inclusive" \
#                                     --binned \
#                                     --fit_data \
#                                     --cached \
#                                     --withSyst --corrected \
#                                     --folder_tag="260226/${era}" \
#                                     --fit_region="region0" &> logs/260226/reweight_data_region0_altbkg_polyexp_withScaleSyst_IDSF_triggerSF_${era}_binned_log &
# done


# ### ENVELOPE
# #### NOTE: requires combine environment
# for era in 2022 2023 2022EE 2023BPix; do
#     python3 main_background_analysis.py --full_analysis --bkg_function -1 \
#                                     --fit_jpsi_prompt --floating_resonant \
#                                     --data --tag="data_envelope_withScaleSyst_IDSF_triggerSF_${era}" \
#                                     --era $era \
#                                     --categories="inclusive" \
#                                     --binned \
#                                     --fit_data \
#                                     --cached \
#                                     --withSyst --corrected \
#                                     --folder_tag="260226/${era}" \
#                                     --signal_folder_tag="260226" \
#                                     --input_workspaces "datasets/260226/${era}/dataset_data_region1_binned_data_altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_${era}_full.root" \
#                                                        "datasets/260226/${era}/dataset_data_region1_binned_data_altbkg_polyexp_withScaleSyst_IDSF_triggerSF_${era}_full.root" \
#                                                        "datasets/260226/${era}/dataset_data_region1_binned_data_altbkg_bernstein_withScaleSyst_IDSF_triggerSF_${era}_full.root" \
#                                     --fit_region="region1" &> logs/260226/reweight_data_region1_envelope_withScaleSyst_IDSF_triggerSF_${era}_binned_log

#     python3 main_background_analysis.py --full_analysis --bkg_function -1 \
#                                     --fit_jpsi_prompt --floating_resonant \
#                                     --data --tag="data_envelope_withScaleSyst_IDSF_triggerSF_${era}" \
#                                     --era $era \
#                                     --categories="inclusive" \
#                                     --binned \
#                                     --fit_data \
#                                     --cached \
#                                     --withSyst --corrected \
#                                     --folder_tag="260226/${era}" \
#                                     --signal_folder_tag="260226" \
#                                     --input_workspaces "datasets/260226/${era}/dataset_data_region0_binned_data_altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_${era}_full.root" \
#                                                        "datasets/260226/${era}/dataset_data_region0_binned_data_altbkg_polyexp_withScaleSyst_IDSF_triggerSF_${era}_full.root" \
#                                                        "datasets/260226/${era}/dataset_data_region0_binned_data_altbkg_bernstein_withScaleSyst_IDSF_triggerSF_${era}_full.root" \
#                                     --fit_region="region0" &> logs/260226/reweight_data_region0_envelope_withScaleSyst_IDSF_triggerSF_${era}_binned_log

#     python3 main_background_analysis.py --full_analysis --bkg_function -1 \
#                                     --fit_jpsi_prompt --floating_resonant \
#                                     --data --tag="data_envelope_withScaleSyst_IDSF_triggerSF_${era}" \
#                                     --era $era \
#                                     --categories="inclusive" \
#                                     --binned \
#                                     --fit_data \
#                                     --cached \
#                                     --withSyst --corrected \
#                                     --folder_tag="260226/${era}" \
#                                     --signal_folder_tag="260226" \
#                                     --input_workspaces "datasets/260226/${era}/dataset_data_region2_binned_data_altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_${era}_full.root" \
#                                                        "datasets/260226/${era}/dataset_data_region2_binned_data_altbkg_polyexp_withScaleSyst_IDSF_triggerSF_${era}_full.root" \
#                                                        "datasets/260226/${era}/dataset_data_region2_binned_data_altbkg_bernstein_withScaleSyst_IDSF_triggerSF_${era}_full.root" \
#                                     --fit_region="region2" &> logs/260226/reweight_data_region2_envelope_withScaleSyst_IDSF_triggerSF_${era}_binned_log
# done