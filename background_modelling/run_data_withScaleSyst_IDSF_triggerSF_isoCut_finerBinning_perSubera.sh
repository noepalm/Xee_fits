# for era in 2022 2022EE 2023 2023BPix; do
#     for region in region0 region1 region2; do
#         BKG_FUNCTION=7
#         if [ "$region" == "region1" ]; then
#             BKG_FUNCTION=4
#         fi
#         python main_background_analysis.py --full_analysis --bkg_function $BKG_FUNCTION \
#                                         --fit_jpsi_prompt --floating_resonant \
#                                         --data --tag="data_altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_isoCut_finerBinning_${era}" \
#                                         --era $era \
#                                         --categories="inclusive" \
#                                         --binned \
#                                         --fit_data \
#                                         --cached \
#                                         --withSyst --corrected \
#                                         --folder_tag="260316/${era}" \
#                                         --signal_folder_tag="260312" \
#                                         --fit_region="${region}" &> logs/260316/reweight_data_${region}_altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_isoCut_finerBinning_${era}_binned_log &
#     done
# done

for era in 2022 2022EE 2023 2023BPix; do
    for region in region0 region1 region2; do
        BKG_FUNCTION=7
        if [ "$region" == "region1" ]; then
            BKG_FUNCTION=4
        fi
        python main_background_analysis.py --full_analysis --bkg_function $BKG_FUNCTION \
                                        --fit_jpsi_prompt --floating_resonant \
                                        --data --tag="data_altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_isoCut_finerBinning_${era}" \
                                        --era $era \
                                        --categories="inclusive" \
                                        --binned \
                                        --fit_data \
                                        --cached \
                                        --withSyst --corrected \
                                        --folder_tag="260316/${era}" \
                                        --signal_folder_tag="260312" \
                                        --fit_region="${region}" &> logs/260316/reweight_data_${region}_altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_isoCut_finerBinning_${era}_binned_log &
    done
done


for era in 2022; do
    for region in region2; do
        BKG_FUNCTION=7
        if [ "$region" == "region1" ]; then
            BKG_FUNCTION=4
        fi
        python main_background_analysis.py --full_analysis --bkg_function $BKG_FUNCTION \
                                        --fit_jpsi_prompt --floating_resonant \
                                        --data --tag="data_altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_isoCut_finerBinning_${era}" \
                                        --era $era \
                                        --categories="inclusive" \
                                        --binned \
                                        --fit_data \
                                        --cached \
                                        --withSyst --corrected \
                                        --folder_tag="260316/${era}" \
                                        --signal_folder_tag="260312" \
                                        --fit_region="${region}" &> logs/260316/reweight_data_${region}_altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_isoCut_finerBinning_${era}_binned_log &
    done
done

# # altbkg bernstein
# for era in 2022 2023 2022EE 2023BPix; do
#     python main_background_analysis.py --full_analysis --bkg_function 0 \
#                                     --fit_jpsi_prompt --floating_resonant \
#                                     --data --tag="data_altbkg_bernstein_withScaleSyst_IDSF_triggerSF_isoCut_finerBinning_${era}" \
#                                     --era $era \
#                                     --categories="inclusive" \
#                                     --binned \
#                                     --fit_data \
#                                     --cached \
#                                     --withSyst --corrected \
#                                     --folder_tag="260316/${era}" \
#                                     --signal_folder_tag="260312" \
#                                     --fit_region="region1" &> logs/260316/reweight_data_region1_altbkg_bernstein_withScaleSyst_IDSF_triggerSF_isoCut_finerBinning_${era}_binned_log &

#     python main_background_analysis.py --full_analysis --bkg_function 0 \
#                                     --fit_jpsi_prompt --floating_resonant \
#                                     --data --tag="data_altbkg_bernstein_withScaleSyst_IDSF_triggerSF_isoCut_finerBinning_${era}" \
#                                     --era $era \
#                                     --categories="inclusive" \
#                                     --fit_data \
#                                     --binned \
#                                     --cached \
#                                     --withSyst --corrected \
#                                     --folder_tag="260316/${era}" \
#                                     --signal_folder_tag="260312" \
#                                     --fit_region="region2" &> logs/260316/reweight_data_region2_altbkg_bernstein_withScaleSyst_IDSF_triggerSF_isoCut_finerBinning_${era}_binned_log &

#     python main_background_analysis.py --full_analysis --bkg_function 0 \
#                                     --fit_jpsi_prompt --floating_resonant \
#                                     --data --tag="data_altbkg_bernstein_withScaleSyst_IDSF_triggerSF_isoCut_finerBinning_${era}" \
#                                     --era $era \
#                                     --categories="inclusive" \
#                                     --binned \
#                                     --fit_data \
#                                     --cached \
#                                     --withSyst --corrected \
#                                     --folder_tag="260316/${era}" \
#                                     --signal_folder_tag="260312" \
#                                     --fit_region="region0" &> logs/260316/reweight_data_region0_altbkg_bernstein_withScaleSyst_IDSF_triggerSF_isoCut_finerBinning_${era}_binned_log &
# done

# # altbkg polynomial x exponential
# for era in 2022 2023 2022EE 2023BPix; do
#     python main_background_analysis.py --full_analysis --bkg_function 1 \
#                                     --fit_jpsi_prompt --floating_resonant \
#                                     --data --tag="data_altbkg_polyexp_withScaleSyst_IDSF_triggerSF_isoCut_finerBinning_${era}" \
#                                     --era $era \
#                                     --categories="inclusive" \
#                                     --binned \
#                                     --fit_data \
#                                     --cached \
#                                     --withSyst --corrected \
#                                     --folder_tag="260316/${era}" \
#                                     --signal_folder_tag="260312" \
#                                     --fit_region="region1" &> logs/260316/reweight_data_region1_altbkg_polyexp_withScaleSyst_IDSF_triggerSF_isoCut_finerBinning_${era}_binned_log &

#     python main_background_analysis.py --full_analysis --bkg_function 1 \
#                                     --fit_jpsi_prompt --floating_resonant \
#                                     --data --tag="data_altbkg_polyexp_withScaleSyst_IDSF_triggerSF_isoCut_finerBinning_${era}" \
#                                     --era $era \
#                                     --categories="inclusive" \
#                                     --fit_data \
#                                     --binned \
#                                     --cached \
#                                     --withSyst --corrected \
#                                     --folder_tag="260316/${era}" \
#                                     --signal_folder_tag="260312" \
#                                     --fit_region="region2" &> logs/260316/reweight_data_region2_altbkg_polyexp_withScaleSyst_IDSF_triggerSF_isoCut_finerBinning_${era}_binned_log &

#     python main_background_analysis.py --full_analysis --bkg_function 1 \
#                                     --fit_jpsi_prompt --floating_resonant \
#                                     --data --tag="data_altbkg_polyexp_withScaleSyst_IDSF_triggerSF_isoCut_finerBinning_${era}" \
#                                     --era $era \
#                                     --categories="inclusive" \
#                                     --binned \
#                                     --fit_data \
#                                     --cached \
#                                     --withSyst --corrected \
#                                     --folder_tag="260316/${era}" \
#                                     --signal_folder_tag="260312" \
#                                     --fit_region="region0" &> logs/260316/reweight_data_region0_altbkg_polyexp_withScaleSyst_IDSF_triggerSF_isoCut_finerBinning_${era}_binned_log &
# done

# wait 
# ### ENVELOPE
# #### NOTE: requires combine environment
# for era in 2022 2023 2022EE 2023BPix; do
#     python3 main_background_analysis.py --full_analysis --bkg_function -1 \
#                                     --fit_jpsi_prompt --floating_resonant \
#                                     --data --tag="data_envelope_withScaleSyst_IDSF_triggerSF_isoCut_finerBinning_${era}" \
#                                     --era $era \
#                                     --categories="inclusive" \
#                                     --binned \
#                                     --fit_data \
#                                     --cached \
#                                     --withSyst --corrected \
#                                     --folder_tag="260316/${era}" \
#                                     --signal_folder_tag="260312" \
#                                     --input_workspaces "datasets/260316/${era}/dataset_data_region1_binned_data_altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_isoCut_finerBinning_${era}_full.root" \
#                                                        "datasets/260316/${era}/dataset_data_region1_binned_data_altbkg_polyexp_withScaleSyst_IDSF_triggerSF_isoCut_finerBinning_${era}_full.root" \
#                                                        "datasets/260316/${era}/dataset_data_region1_binned_data_altbkg_bernstein_withScaleSyst_IDSF_triggerSF_isoCut_finerBinning_${era}_full.root" \
#                                     --fit_region="region1" &> logs/260316/reweight_data_region1_envelope_withScaleSyst_IDSF_triggerSF_isoCut_finerBinning_${era}_binned_log

#     python3 main_background_analysis.py --full_analysis --bkg_function -1 \
#                                     --fit_jpsi_prompt --floating_resonant \
#                                     --data --tag="data_envelope_withScaleSyst_IDSF_triggerSF_isoCut_finerBinning_${era}" \
#                                     --era $era \
#                                     --categories="inclusive" \
#                                     --binned \
#                                     --fit_data \
#                                     --cached \
#                                     --withSyst --corrected \
#                                     --folder_tag="260316/${era}" \
#                                     --signal_folder_tag="260312" \
#                                     --input_workspaces "datasets/260316/${era}/dataset_data_region0_binned_data_altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_isoCut_finerBinning_${era}_full.root" \
#                                                        "datasets/260316/${era}/dataset_data_region0_binned_data_altbkg_polyexp_withScaleSyst_IDSF_triggerSF_isoCut_finerBinning_${era}_full.root" \
#                                                        "datasets/260316/${era}/dataset_data_region0_binned_data_altbkg_bernstein_withScaleSyst_IDSF_triggerSF_isoCut_finerBinning_${era}_full.root" \
#                                     --fit_region="region0" &> logs/260316/reweight_data_region0_envelope_withScaleSyst_IDSF_triggerSF_isoCut_finerBinning_${era}_binned_log

#     python3 main_background_analysis.py --full_analysis --bkg_function -1 \
#                                     --fit_jpsi_prompt --floating_resonant \
#                                     --data --tag="data_envelope_withScaleSyst_IDSF_triggerSF_isoCut_finerBinning_${era}" \
#                                     --era $era \
#                                     --categories="inclusive" \
#                                     --binned \
#                                     --fit_data \
#                                     --cached \
#                                     --withSyst --corrected \
#                                     --folder_tag="260316/${era}" \
#                                     --signal_folder_tag="260312" \
#                                     --input_workspaces "datasets/260316/${era}/dataset_data_region2_binned_data_altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_isoCut_finerBinning_${era}_full.root" \
#                                                        "datasets/260316/${era}/dataset_data_region2_binned_data_altbkg_polyexp_withScaleSyst_IDSF_triggerSF_isoCut_finerBinning_${era}_full.root" \
#                                                        "datasets/260316/${era}/dataset_data_region2_binned_data_altbkg_bernstein_withScaleSyst_IDSF_triggerSF_isoCut_finerBinning_${era}_full.root" \
#                                     --fit_region="region2" &> logs/260316/reweight_data_region2_envelope_withScaleSyst_IDSF_triggerSF_isoCut_finerBinning_${era}_binned_log
# done