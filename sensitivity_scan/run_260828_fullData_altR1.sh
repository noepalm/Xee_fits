mkdir -p logs/260828

for era in 2022EE; do
    for region in region0; do
        python3 make_combine_workspace.py --cat="inclusive" --region ${region} --data \
                                        --withSyst \
                                        --input_tag envelope_allCorrections \
                                        --tag envelope_allCorrections \
                                        --era ${era} \
                                        --envelope \
                                        --folder_tag 260828 \
                                        --binned &> logs/260828/workspace_inclusive_${region}_data_envelope_allCorrections_${era}_binned_log
    done
done

# # ------------------------------------------ #
# # ------------ UNBLINDING TESTS ------------ #
# # ------------------------------------------ #

for era in 2022EE; do
    for region in region0; do
        python3 make_combine_workspace.py --cat="inclusive" --region ${region} --data \
                                        --withSyst \
                                        --input_tag altbkg_chebyshev_allCorrections \
                                        --tag altbkg_chebyshev_allCorrections \
                                        --era ${era} \
                                        --folder_tag 260828 \
                                        --binned &> logs/260828/workspace_inclusive_${region}_data_altbkg_chebyshev_allCorrections_${era}_binned_log
        python3 make_combine_workspace.py --cat="inclusive" --region ${region} --data \
                                        --withSyst \
                                        --input_tag altbkg_bernstein_allCorrections \
                                        --tag altbkg_bernstein_allCorrections \
                                        --era ${era} \
                                        --folder_tag 260828 \
                                        --binned &> logs/260828/workspace_inclusive_${region}_data_altbkg_bernstein_allCorrections_${era}_binned_log
    done
done

# mu = 0
python3 scripts/run_bias_test.py --cat inclusive \
                                 --folder_tag 260828 \
                                 --tag envelope_allCorrections_binned \
                                 --regions region0 region1 region2 \
                                 --ntoys 100 \
                                 --jobs `nproc` \
                                 --plot_only \
                                 --data --binned \
                                 --eras 2022 2022EE 2023 2023BPix

python3 scripts/run_gof_parallel.py --cat inclusive \
                                    --folder_tag 260828 \
                                    --tag envelope_allCorrections_binned \
                                    --regions region0 \
                                    --no_caching \
                                    --data --binned \
                                    --jobs `nproc` \
                                    --gof_expected 450 \
                                    --eras 2022EE

python3 scripts/run_gof_parallel.py --cat inclusive \
                                    --folder_tag 260828 \
                                    --tag envelope_allCorrections_binned \
                                    --regions region0 region1 region2 \
                                    --data --binned \
                                    --plot_only \
                                    --jobs `nproc` \
                                    --gof_expected 450 \
                                    --eras 2022 2022EE 2023 2023BPix


# copy results to common folder
export BASE_EOS_FOLDER="/eos/home-n/npalmeri/www/DiElectron/sensitivity/260828/fitDiagnostics_grid_data_envelope_allCorrections_binned"
for era in 2022 2022EE 2023 2023BPix; do
    for ext in png pdf; do
        cp ${BASE_EOS_FOLDER}/bias_test/inclusive_${era}/no_signal/bias_test_region0_region1_region2.${ext} ${BASE_EOS_FOLDER}/bias_mu0_${era}.${ext}
        cp ${BASE_EOS_FOLDER}/bias_test/inclusive_${era}/signal_injected_mu0.10/bias_test_region0_region1_region2.${ext} ${BASE_EOS_FOLDER}/bias_mu1_${era}.${ext}
        cp ${BASE_EOS_FOLDER}/bias_test/inclusive_${era}/signal_injected_mu1/bias_test_region0_region1_region2.${ext} ${BASE_EOS_FOLDER}/bias_mu0.1_${era}.${ext}
        cp ${BASE_EOS_FOLDER}/mu0/gof_pvalue_vs_mass_${era}.${ext} ${BASE_EOS_FOLDER}/gof_${era}.${ext}
    done
done

# ---------------------------------------- #
# ---------- FITS AND IMPACTS ------------ #
# ---------------------------------------- #

python3 scripts/run_diagnostics_parallel.py --cat inclusive \
                                            --folder_tag 260828 \
                                            --tag envelope_allCorrections_binned \
                                            --regions region0 \
                                            --no_caching \
                                            --data --binned \
                                            --jobs `nproc` \
                                            --eras 2022EE

python3 scripts/run_limits_parallel.py --cat inclusive \
                                      --tag envelope_allCorrections_binned \
                                      --folder_tag 260828 \
                                      --eras allYears \
                                      --no_caching \
                                      --regions region0 region1 region2 \
                                      --data \
                                      --noGrid 

python3 scripts/plot_limits_result.py -i cards/260828/cards_region0_data_envelope_allCorrections_binned cards/260828/cards_region1_data_envelope_allCorrections_binned cards/260828/cards_region2_data_envelope_allCorrections_binned \
                                      -c inclusive -r region0 region1 region2 \
                                      --era allYears \
                                      -o /eos/home-n/npalmeri/www/DiElectron/sensitivity/260828/fitDiagnostics_grid_data_envelope_allCorrections_binned/mu0/inclusive_allYears &> /eos/home-n/npalmeri/www/DiElectron/sensitivity/260828/fitDiagnostics_grid_data_envelope_allCorrections_binned/mu0/inclusive_allYears/limits_summary_region0_region1_region2.log

python3 scripts/run_limits_parallel.py --cat inclusive \
                                      --tag envelope_allCorrections_binned \
                                      --folder_tag 260828 \
                                      --eras 2022 2022EE 2023 2023BPix \
                                      --no_caching \
                                      --regions region0 region1 region2 \
                                      --data \
                                      --noGrid 

for era in 2022 2022EE 2023 2023BPix allYears; do
    python3 scripts/plot_limits_result.py -i cards/260828/cards_region0_data_envelope_allCorrections_binned cards/260828/cards_region1_data_envelope_allCorrections_binned cards/260828/cards_region2_data_envelope_allCorrections_binned \
                                        -c inclusive -r region0 region1 region2 \
                                        --era ${era} \
                                        --unblind \
                                        -o /eos/home-n/npalmeri/www/DiElectron/sensitivity/260828/fitDiagnostics_grid_data_envelope_allCorrections_binned/mu0/inclusive_${era} &> /eos/home-n/npalmeri/www/DiElectron/sensitivity/260828/fitDiagnostics_grid_data_envelope_allCorrections_binned/mu0/inclusive_${era}/limits_summary_region0_region1_region2.log
done

mkdir -p /eos/home-n/npalmeri/www/DiElectron/sensitivity/260828/fitDiagnostics_grid_data_envelope_allCorrections_binned/mu0/limits
for era in 2022 2022EE 2023 2023BPix allYears; do
    for ext in png pdf; do
        cp /eos/home-n/npalmeri/www/DiElectron/sensitivity/260828/fitDiagnostics_grid_data_envelope_allCorrections_binned/mu0/inclusive_${era}/mu_limit_results_indep_xsecBR_noaccept_region0_region1_region2.${ext} /eos/home-n/npalmeri/www/DiElectron/sensitivity/260828/fitDiagnostics_grid_data_envelope_allCorrections_binned/mu0/limits/limits_${era}.${ext}
    done
done

python3 scripts/run_pvalue_scan.py --folder-tag 260828 --fit-tag allCorrections --observed
python3 scripts/run_impacts.py --folder-tag 260828 --eras 2022 2022EE 2023 2023BPix allYears &> impacts.log

### NLL SCANS 
# default, allYears, with envelope
python3 scripts/run_nll_scan.py --folder-tag 260828 --jobs `nproc`  # same, but freeze nuisances for stats/syst breakdown
python3 scripts/run_nll_scan.py --folder-tag 260828 --jobs `nproc` --breakdown # envelope scan (-> compare single-bkg function vs envelope NLL)
python3 scripts/run_nll_scan.py --folder-tag 260828 --jobs `nproc` --envelope-scan  ## DEBUGGING: same, but done separately for each era
python3 scripts/run_nll_scan.py --folder-tag 260828 --jobs `nproc` --by-era
python3 scripts/run_nll_scan.py --folder-tag 260828 --jobs `nproc` --envelope-scan --by-era

### MISC DEBUGGING
python3 scripts/utilities/plot_envelope_indices.py \
        -i cards/260828/cards_{region}_data_envelope_allCorrections_binned/ee \
        -o /eos/home-n/npalmeri/www/DiElectron/sensitivity/260828/fitDiagnostics_grid_data_envelope_allCorrections_binned/mu0 \
        --regions region0 region1 region2 \
        --eras 2022 2022EE 2023 2023BPix

# mu = 1
python3 scripts/run_bias_test.py --cat inclusive \
                                 --folder_tag 260828 \
                                 --tag envelope_allCorrections_binned \
                                 --regions region0 region1 region2 \
                                 --expectSignal 1 \
                                 --no_caching \
                                 --ntoys 100 \
                                 --jobs `nproc` \
                                 --data --binned \
                                 --eras 2022 2022EE 2023 2023BPix

# mu = 0.1
python3 scripts/run_bias_test.py --cat inclusive \
                                 --folder_tag 260828 \
                                 --tag envelope_allCorrections_binned \
                                 --regions region0 region1 region2 \
                                 --expectSignal 0.1 \
                                 --ntoys 100 \
                                 --no_caching \
                                 --jobs `nproc` \
                                 --data --binned \
                                 --eras 2022 2022EE 2023 2023BPix

# mu = 10 (just region 0)
python3 scripts/run_bias_test.py --cat inclusive \
                                 --folder_tag 260828 \
                                 --tag envelope_allCorrections_binned \
                                 --regions region0 \
                                 --expectSignal 10 \
                                 --no_caching \
                                 --ntoys 100 \
                                 --jobs `nproc` \
                                 --data --binned \
                                 --eras 2022 2022EE 2023 2023BPix

### S+B fits for review
python3 scripts/run_diagnostics_parallel.py --cat inclusive \
                                            --folder_tag 260828 \
                                            --tag envelope_allCorrections_binned \
                                            --regions region0 region1 region2 \
                                            --plot_only \
                                            --data --binned \
                                            --jobs `nproc` \
                                            --mass_selector 1.2,2.1,3.3,4.8,5.8,7.1,9.1,9.8 \
                                            --eras 2022 2022EE 2023 2023BPix

for era in 2022 2022EE 2023 2023BPix; do 
        mkdir -p $MYEOS/DiElectron/sensitivity/260828/fitDiagnostics_grid_data_envelope_allCorrections_binned/mu0/inclusive_${era}/s_selected
        for mass in 1.2 2.1 3.3 4.8 5.8 7.1 9.1 9.8; do
                cp $MYEOS/DiElectron/sensitivity/260828/fitDiagnostics_grid_data_envelope_allCorrections_binned/mu0/inclusive_${era}/s/mu0_fit_s_M${mass}.p* $MYEOS/DiElectron/sensitivity/260828/fitDiagnostics_grid_data_envelope_allCorrections_binned/mu0/inclusive_${era}/s_selected
        done
done

### S+B fits for p-value and limits debugging
python3 scripts/run_diagnostics_parallel.py --cat inclusive \
                                            --folder_tag 260828 \
                                            --tag envelope_allCorrections_binned \
                                            --regions region0 region2 \
                                            --no_caching \
                                            --data --binned \
                                            --jobs `nproc` \
                                            --mass_selector 2.0 8.1 9.1 \
                                            --eras 2022 2022EE 2023 2023BPix

mkdir -p $MYEOS/DiElectron/sensitivity/260828/fitDiagnostics_grid_data_envelope_allCorrections_binned/mu0/limits/debug
for era in 2022 2022EE 2023 2023BPix; do 
    for mass in 2.0 8.1 9.1; do
        cp $MYEOS/DiElectron/sensitivity/260828/fitDiagnostics_grid_data_envelope_allCorrections_binned/mu0/inclusive_${era}/s/mu0_fit_s_M${mass}.png $MYEOS/DiElectron/sensitivity/260828/fitDiagnostics_grid_data_envelope_allCorrections_binned/mu0/limits/debug/mu0_fit_M${mass}_${era}.png
    done
done


# ---------------------------------
# ------ ALTERNATIVE LIMITS -------
# ---------------------------------


### frozen energy scale systematic
python3 scripts/run_limits_parallel.py --cat inclusive \
                                      --tag envelope_allCorrections_binned \
                                      --folder_tag 260828 \
                                      --fit_tag frozenScale \
                                      --eras allYears \
                                      --regions region0 region1 region2 \
                                      --data \
                                      --no_caching \
                                      --setParameters CMS_scale_e=0 \
                                      --freezeParameters CMS_scale_e \
                                      --noGrid 

python3 scripts/run_limits_parallel.py --cat inclusive \
                                      --tag envelope_allCorrections_binned \
                                      --folder_tag 260828 \
                                      --fit_tag frozenScale \
                                      --eras 2022 2022EE 2023 2023BPix \
                                      --regions region0 region1 region2 \
                                      --data \
                                      --no_caching \
                                      --setParameters CMS_scale_e=0 \
                                      --freezeParameters CMS_scale_e \
                                      --noGrid 

for era in 2022 2022EE 2023 2023BPix allYears; do
    python3 scripts/plot_limits_result.py -i cards/260828/cards_region0_data_envelope_allCorrections_binned cards/260828/cards_region1_data_envelope_allCorrections_binned cards/260828/cards_region2_data_envelope_allCorrections_binned \
                                        -c inclusive -r region0 region1 region2 \
                                        --tag frozenScale \
                                        --era ${era} \
                                        --unblind \
                                        -o /eos/home-n/npalmeri/www/DiElectron/sensitivity/260828/fitDiagnostics_grid_data_envelope_allCorrections_binned/mu0/inclusive_${era} &> /eos/home-n/npalmeri/www/DiElectron/sensitivity/260828/fitDiagnostics_grid_data_envelope_allCorrections_binned/mu0/inclusive_${era}/limits_summary_region0_region1_region2_frozenScale.log
done

for era in 2022 2022EE 2023 2023BPix allYears; do
    for ext in png pdf; do
        cp /eos/home-n/npalmeri/www/DiElectron/sensitivity/260828/fitDiagnostics_grid_data_envelope_allCorrections_binned/mu0/inclusive_${era}/mu_limit_results_indep_xsecBR_region0_region1_region2.${ext} /eos/home-n/npalmeri/www/DiElectron/review/260819_Unblinding/Step3/limits/limits_${era}.${ext}
        cp /eos/home-n/npalmeri/www/DiElectron/sensitivity/260828/fitDiagnostics_grid_data_envelope_allCorrections_binned/mu0/inclusive_${era}/mu_limit_results_indep_xsecBR_frozenScale_region0_region1_region2.${ext} /eos/home-n/npalmeri/www/DiElectron/review/260819_Unblinding/Step3/limits/frozenScale/limits_${era}.${ext}
    done
done

cp -r $MYEOS/DiElectron/sensitivity/260828/fitDiagnostics_grid_data_envelope_allCorrections_binned/mu0/pvalue/* pvalue/

python3 scripts/run_diagnostics_parallel.py --cat inclusive \
                                            --folder_tag 260828 \
                                            --fit_tag frozenScale \
                                            --tag envelope_allCorrections_binned \
                                            --regions region0 \
                                            --no_caching \
                                            --data --binned \
                                            --jobs `nproc` \
                                            --mass_selector 1.8 1.9 2.0 2.1 \
                                            --eras 2022 2022EE 2023 2023BPix

source fit_debug.sh
cp /eos/home-n/npalmeri/www/DiElectron/sensitivity/260828/fitDiagnostics_grid_data_envelope_allCorrections_binned/mu0/limits/debug/zoom/* /eos/home-n/npalmeri/www/DiElectron/review/260819_Unblinding/Step3/fits_2gev_zoomed
cp /eos/home-n/npalmeri/www/DiElectron/sensitivity/260828/fitDiagnostics_grid_data_envelope_allCorrections_binned/mu0/limits/debug/zoom/frozenScale/* /eos/home-n/npalmeri/www/DiElectron/review/260819_Unblinding/Step3/fits_2gev_zoomed/frozenScale


#### GLOBAL P-VALUE
python3 scripts/run_global_pvalue_scan.py \
        --folder-tag 260828 \
        --fit-tag allCorrections \
        --nproc 96 \
        --ntoys 500 \
        --obs-pkl /eos/home-n/npalmeri/www/DiElectron/sensitivity/260828/fitDiagnostics_grid_data_envelope_allCorrections_binned/mu0/pvalue/pvalues_observed_allYears.pkl &> logs/260828/global_pvalue.log