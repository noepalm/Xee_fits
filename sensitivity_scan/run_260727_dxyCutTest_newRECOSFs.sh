mkdir -p logs/260727

for era in 2022 2022EE 2023 2023BPix; do
    for region in region0 region1 region2; do
        python3 make_combine_workspace.py --cat="inclusive" --region ${region} --data \
                                        --withSyst \
                                        --input_tag envelope_allCorrections \
                                        --tag envelope_allCorrections \
                                        --era ${era} \
                                        --envelope \
                                        --folder_tag 260727 \
                                        --binned &> logs/260727/workspace_inclusive_${region}_data_envelope_allCorrections_${era}_binned_log
    done
done

# ------------------------------------------------------------
# LIMITS AND FITS WITH ENVELOPE (No index freeze)
### with NEW SIGNAL MODEL UNCERTAINTIES

python3 scripts/run_limits_parallel.py --cat inclusive \
                                      --tag envelope_allCorrections_binned \
                                      --folder_tag 260727 \
                                      --eras allYears \
                                      --regions region0 region1 region2 \
                                      --data \
                                      --noGrid 

python3 scripts/plot_limits_result.py -i cards/260727/cards_region0_data_envelope_allCorrections_binned cards/260727/cards_region1_data_envelope_allCorrections_binned cards/260727/cards_region2_data_envelope_allCorrections_binned \
                                      -c inclusive -r region0 region1 region2 \
                                      --era allYears \
                                      --rescale_full \
                                      -o /eos/home-n/npalmeri/www/DiElectron/sensitivity/260727/fitDiagnostics_grid_data_envelope_allCorrections_binned/mu0/inclusive_allYears &> /eos/home-n/npalmeri/www/DiElectron/sensitivity/260727/fitDiagnostics_grid_data_envelope_allCorrections_binned/mu0/inclusive_allYears/limits_summary_region0_region1_region2.log

python3 scripts/plot_limits_comparison.py --input_folders "260727/fitDiagnostics_grid_data_envelope_allCorrections_binned/mu0/inclusive_allYears" \
                                                          "260604/fitDiagnostics_grid_data_envelope_allCorrections_binned/mu0/inclusive_allYears" \
                                          -o "/eos/home-n/npalmeri/www/DiElectron/sensitivity/260727/fitDiagnostics_grid_data_envelope_allCorrections_binned/mu0/inclusive_allYears" \
                                          --region region0 region1 region2 \
                                          --labels "With dxySig cut" "Nominal" \
                                          --rescale_full \
                                          --tag "dxyCutComparison"

python3 scripts/run_diagnostics_parallel.py --cat inclusive \
                                            --folder_tag 260727 \
                                            --tag envelope_allCorrections_binned \
                                            --regions region0 region1 region2 \
                                            --no_caching \
                                            --data --binned \
                                            --jobs `nproc` \
                                            --eras 2022 2022EE 2023 2023BPix

python3 scripts/run_impacts.py