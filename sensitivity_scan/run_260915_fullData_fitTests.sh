mkdir -p logs/260915

for era in 2022EE; do
    for region in region0; do
        python3 make_combine_workspace_slidingWindow.py --cat="inclusive" --region ${region} --data \
                                        --withSyst \
                                        --input_tag envelope_allCorrections \
                                        --tag envelope_allCorrections \
                                        --era ${era} \
                                        --envelope \
                                        --folder_tag 260915 \
                                        --binned &> logs/260915/workspace_inclusive_${region}_data_envelope_allCorrections_${era}_binned_log
    done
done

# python3 scripts/run_diagnostics_parallel.py --cat inclusive \
#                                             --folder_tag 260915 \
#                                             --tag envelope_allCorrections_binned \
#                                             --regions region0 \
#                                             --no_caching \
#                                             --mass_select 1.8,1.9,2.0,2.1 \
#                                             --data --binned \
#                                             --jobs `nproc` \
#                                             --eras 2022EE

# python3 scripts/run_limits_parallel.py --cat inclusive \
#                                       --tag envelope_allCorrections_binned \
#                                       --folder_tag 260915 \
#                                       --eras 2022EE \
#                                       --no_caching \
#                                       --mass_select 1.8,1.9,2.0,2.1 \
#                                       --regions region0 \
#                                       --unblind \
#                                       --data \
#                                       --noGrid

# python3 scripts/run_diagnostics_parallel.py --cat inclusive \
#                                             --folder_tag 260915 \
#                                             --tag envelope_allCorrections_binned \
#                                             --regions region0 \
#                                             --fit_tag lowOrders \
#                                             --no_caching \
#                                             --mass_select 1.8,1.9,2.0,2.1 \
#                                             --data --binned \
#                                             --jobs `nproc` \
#                                             --eras 2022EE

# python3 scripts/run_limits_parallel.py --cat inclusive \
#                                       --tag envelope_allCorrections_binned \
#                                       --folder_tag 260915 \
#                                       --eras 2022EE \
#                                       --no_caching \
#                                       --fit_tag lowOrders \
#                                       --mass_select 1.8,1.9,2.0,2.1 \
#                                       --regions region0 \
#                                       --unblind \
#                                       --data \
#                                       --noGrid

# python3 scripts/run_diagnostics_parallel.py --cat inclusive \
#                                             --folder_tag 260915 \
#                                             --tag envelope_allCorrections_binned \
#                                             --regions region0 \
#                                             --fit_tag slightlySmallerWindow \
#                                             --no_caching \
#                                             --mass_select 1.8,1.9,2.0,2.1 \
#                                             --data --binned \
#                                             --jobs `nproc` \
#                                             --eras 2022EE

# python3 scripts/run_limits_parallel.py --cat inclusive \
#                                       --tag envelope_allCorrections_binned \
#                                       --folder_tag 260915 \
#                                       --eras 2022EE \
#                                       --no_caching \
#                                       --fit_tag slightlySmallerWindow \
#                                       --mass_select 1.8,1.9,2.0,2.1 \
#                                       --regions region0 \
#                                       --unblind \
#                                       --data \
#                                       --noGrid

# python3 scripts/run_diagnostics_parallel.py --cat inclusive \
#                                             --folder_tag 260915 \
#                                             --tag envelope_allCorrections_binned \
#                                             --regions region0 \
#                                             --fit_tag rebinned \
#                                             --no_caching \
#                                             --mass_select 1.8,1.9,2.0,2.1 \
#                                             --data --binned \
#                                             --jobs `nproc` \
#                                             --eras 2022EE

# python3 scripts/run_limits_parallel.py --cat inclusive \
#                                       --tag envelope_allCorrections_binned \
#                                       --folder_tag 260915 \
#                                       --eras 2022EE \
#                                       --no_caching \
#                                       --fit_tag rebinned \
#                                       --mass_select 1.8,1.9,2.0,2.1 \
#                                       --regions region0 \
#                                       --unblind \
#                                       --data \
#                                       --noGrid


# export TAG="smallerWindow_lowOrders"
export TAG="smallerWindow"

python3 scripts/run_diagnostics_parallel.py --cat inclusive \
                                            --folder_tag 260915 \
                                            --tag envelope_allCorrections_binned \
                                            --regions region0 \
                                            --no_caching \
                                            --mass_select 1.8,1.9,2.0,2.1 \
                                            --fit_tag ${TAG} \
                                            --data --binned \
                                            --jobs `nproc` \
                                            --eras 2022EE

# export OUTFOLDER="/eos/home-n/npalmeri/www/DiElectron/sensitivity/260915/fitDiagnostics_grid_data_envelope_allCorrections_binned/mu0/inclusive_2022EE/s/tests"
# mv /eos/home-n/npalmeri/www/DiElectron/sensitivity/260915/fitDiagnostics_grid_data_envelope_allCorrections_binned/mu0/inclusive_2022EE/s/*${TAG}* ${OUTFOLDER}

# for ext in pdf png; do
#     mv ${OUTFOLDER}/mu0_fit_s_M2.0_${TAG}.${ext} ${OUTFOLDER}/mu0_fit_s_M2.0_smallerWindow_chebDeg4.${ext}
# done


python3 scripts/run_nll_scan.py --folder-tag 260915 --jobs `nproc` --by-era

