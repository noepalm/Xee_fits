mkdir -p logs/260604

for era in 2022 2022EE 2023 2023BPix; do
    for region in region0 region1 region2; do
        python3 make_combine_workspace.py --cat="inclusive" --region ${region} --data \
                                        --withSyst \
                                        --input_tag envelope_allCorrections \
                                        --tag envelope_allCorrections \
                                        --era ${era} \
                                        --envelope \
                                        --folder_tag 260604 \
                                        --binned &> logs/260604/workspace_inclusive_${region}_data_envelope_allCorrections_${era}_binned_log
    done
done

# ------------------------------------------------------------
# LIMITS AND FITS WITH ENVELOPE (No index freeze)
### with NEW SIGNAL MODEL UNCERTAINTIES

python3 scripts/run_limits_parallel.py --cat inclusive \
                                      --tag envelope_allCorrections_binned \
                                      --folder_tag 260604 \
                                      --eras allYears \
                                      --regions region0 region1 region2 \
                                      --data

python3 scripts/plot_limits_result.py -i cards/260604/cards_region0_data_envelope_allCorrections_binned cards/260604/cards_region1_data_envelope_allCorrections_binned cards/260604/cards_region2_data_envelope_allCorrections_binned \
                                      -c inclusive -r region0 region1 region2 \
                                      --era allYears \
                                      --rescale_full \
                                      -o /eos/home-n/npalmeri/www/DiElectron/sensitivity/260604/fitDiagnostics_grid_data_envelope_allCorrections_binned/mu0/inclusive_allYears &> /eos/home-n/npalmeri/www/DiElectron/sensitivity/260604/fitDiagnostics_grid_data_envelope_allCorrections_binned/mu0/inclusive_allYears/limits_summary_region0_region1_region2.log

python3 scripts/run_diagnostics_parallel.py --cat inclusive \
                                            --folder_tag 260604 \
                                            --tag envelope_allCorrections_binned \
                                            --regions region0 region1 region2 \
                                            --data --binned \
                                            --jobs `nproc` \
                                            --eras 2022 2022EE 2023 2023BPix
                                            # --no_caching \

python3 scripts/run_gof_parallel.py --cat inclusive \
                                    --folder_tag 260604 \
                                    --tag envelope_allCorrections_binned \
                                    --regions region0 region1 region2 \
                                    --data --binned \
                                    --jobs `nproc` \
                                    --plot_only \
                                    --gof_expected 450 \
                                    --eras 2022 2022EE 2023 2023BPix
                                    # --no_caching \

python3 scripts/run_pvalue_scan.py --folder-tag 260604 --fit-tag allCorrections --observed
# #python scripts/run_pvalue_scan.py --toys --expect-signal 10 --eras 2022 2022EE 2023 2023BPix
# #python scripts/run_pvalue_scan.py --input-name-template Xee_ee_4_{era}.root --eras allYears