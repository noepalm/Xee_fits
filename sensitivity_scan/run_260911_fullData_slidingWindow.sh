# mkdir -p logs/260911

for era in 2022 2022EE 2023 2023BPix; do
    for region in region0 region1 region2; do
        python3 make_combine_workspace_slidingWindow.py --cat="inclusive" --region ${region} --data \
                                            --withSyst \
                                            --input_tag envelope_allCorrections \
                                            --tag envelope_allCorrections \
                                            --era ${era} \
                                            --envelope \
                                            --folder_tag 260911 \
                                            --binned &> logs/260911/workspace_inclusive_${region}_data_envelope_allCorrections_${era}_binned_log 
    done
done

# for era in 2022EE; do
#     for region in region1 region2; do
#         python3 make_combine_workspace_slidingWindow.py --cat="inclusive" --region ${region} --data \
#                                             --withSyst \
#                                             --input_tag envelope_allCorrections \
#                                             --tag envelope_allCorrections \
#                                             --era ${era} \
#                                             --envelope \
#                                             --folder_tag 260911 \
#                                             --binned &> logs/260911/workspace_inclusive_${region}_data_envelope_allCorrections_${era}_binned_log 
#     done
# done

# # ------------------------------------------ #
# # ------------ UNBLINDING TESTS ------------ #
# # ------------------------------------------ #


# python3 scripts/run_diagnostics_parallel.py --cat inclusive \
#                                             --folder_tag 260911 \
#                                             --tag envelope_allCorrections_binned \
#                                             --regions region1 \
#                                             --data --binned \
#                                             --no_caching \
#                                             --mass_select 4.1 \
#                                             --jobs `nproc` \
#                                             --eras 2022EE 

python3 scripts/run_diagnostics_parallel.py --cat inclusive \
                                            --folder_tag 260911 \
                                            --tag envelope_allCorrections_binned \
                                            --regions region0 region1 region2 \
                                            --data --binned \
                                            --no_caching \
                                            --jobs `nproc` \
                                            --eras 2022 2022EE 2023 2023BPix

########################

python3 scripts/run_limits_parallel.py --cat inclusive \
                                      --tag envelope_allCorrections_binned \
                                      --folder_tag 260911 \
                                      --eras allYears \
                                      --no_caching \
                                      --unblind \
                                      --fit_tag lowOrders \
                                      --regions region0 region1 region2 \
                                      --data \
                                      --noGrid

# python3 scripts/run_limits_parallel.py --cat inclusive \
#                                       --tag envelope_allCorrections_binned \
#                                       --folder_tag 260911 \
#                                       --eras 2022 2022EE 2023 2023BPix \
#                                       --regions region0 region1 region2 \
#                                       --no_caching \
#                                       --fit_tag lowOrders \
#                                       --data \
#                                       --noGrid

# for era in 2022 2022EE 2023 2023BPix allYears; do
for era in allYears; do
    python3 scripts/plot_limits_result.py -i cards/260911/cards_region0_data_envelope_allCorrections_binned cards/260911/cards_region1_data_envelope_allCorrections_binned cards/260911/cards_region2_data_envelope_allCorrections_binned \
                                        -c inclusive -r region0 region1 region2 \
                                        --era ${era} \
                                        --unblind \
                                        --tag lowOrders \
                                        -o /eos/home-n/npalmeri/www/DiElectron/sensitivity/260911/fitDiagnostics_grid_data_envelope_allCorrections_binned/mu0/inclusive_${era} &> /eos/home-n/npalmeri/www/DiElectron/sensitivity/260911/fitDiagnostics_grid_data_envelope_allCorrections_binned/mu0/inclusive_${era}/limits_summary_region0_region1_region2_lowOrders.log
done

python3 scripts/run_pvalue_scan.py --folder-tag 260911 --fit-tag allCorrections --observed --nproc `nproc`

# -----------