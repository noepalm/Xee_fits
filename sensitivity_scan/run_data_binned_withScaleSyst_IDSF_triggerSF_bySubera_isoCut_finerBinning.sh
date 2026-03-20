############################
#### WITH MEAN NUISANCE ####
############################

mkdir -p logs/260316

for era in 2022 2022EE 2023 2023BPix; do
    for region in region0 region1 region2; do
        python3 make_combine_workspace.py --cat="inclusive" --region ${region} --data \
                                        --withSyst \
                                        --input_tag altbkg_chebyshev_withScaleSyst_IDSF_triggerSF_isoCut_finerBinning \
                                        --tag altbkg_chebyshev_withScaleSyst_withMeanNuisance_IDSF_triggerSF_isoCut_finerBinning_bySubera \
                                        --era ${era} \
                                        --folder_tag 260316 \
                                        --binned &> logs/260316/workspace_inclusive_${region}_data_altbkg_chebyshev_withScaleSyst_withMeanNuisance_IDSF_triggerSF_isoCut_finerBinning_bySubera_${era}_binned_log
    done
done

python3 scripts/run_limits_parallel.py --cat inclusive \
                                      --tag altbkg_chebyshev_withScaleSyst_withMeanNuisance_IDSF_triggerSF_isoCut_finerBinning_bySubera_binned \
                                      --folder_tag 260316 \
                                      --eras allYears \
                                      --regions region0 region 1region2 \
                                      --data

python3 scripts/plot_limits_result.py -i cards/260316/cards_region0_data_altbkg_chebyshev_withScaleSyst_withMeanNuisance_IDSF_triggerSF_isoCut_finerBinning_bySubera_binned cards/260316/cards_region1_data_altbkg_chebyshev_withScaleSyst_withMeanNuisance_IDSF_triggerSF_isoCut_finerBinning_bySubera_binned cards/260316/cards_region2_data_altbkg_chebyshev_withScaleSyst_withMeanNuisance_IDSF_triggerSF_isoCut_finerBinning_bySubera_binned \
                                      -c inclusive -r region0 region1 region2 \
                                      --era allYears \
                                      -o /eos/home-n/npalmeri/www/DiElectron/sensitivity/260316/fitDiagnostics_grid_data_altbkg_chebyshev_withScaleSyst_withMeanNuisance_IDSF_triggerSF_isoCut_finerBinning_bySubera_binned/mu0/inclusive_allYears &> /eos/home-n/npalmeri/www/DiElectron/sensitivity/260316/fitDiagnostics_grid_data_altbkg_chebyshev_withScaleSyst_withMeanNuisance_IDSF_triggerSF_isoCut_finerBinning_bySubera_binned/mu0/inclusive_allYears/limits_summary_region0_region1_region2.log

python3 scripts/run_diagnostics_parallel.py --cat inclusive \
                                            --folder_tag 260316 \
                                            --tag altbkg_chebyshev_withScaleSyst_withMeanNuisance_IDSF_triggerSF_isoCut_finerBinning_bySubera_binned \
                                            --regions region0 region1 region2 \
                                            --data --binned \
                                            --eras 2022 2022EE 2023 2023BPix

python3 scripts/plot_limits_comparison.py --input_folders "260316/fitDiagnostics_grid_data_altbkg_chebyshev_withScaleSyst_withMeanNuisance_IDSF_triggerSF_isoCut_finerBinning_bySubera_binned/mu0/inclusive_allYears" \
                                                          "260316/fitDiagnostics_grid_data_altbkg_chebyshev_withScaleSyst_withMeanNuisance_IDSF_triggerSF_finerBinning_bySubera_binned/mu0/inclusive_allYears" \
                                          -o "/eos/home-n/npalmeri/www/DiElectron/sensitivity/260316/fitDiagnostics_grid_data_altbkg_chebyshev_withScaleSyst_withMeanNuisance_IDSF_triggerSF_isoCut_finerBinning_bySubera_binned/mu0/inclusive_allYears" \
                                          --region region0 region1 region2 \
                                          --labels "With iso cut" "No iso cut"\
                                          --tag "data_isoCut_finerBinning"