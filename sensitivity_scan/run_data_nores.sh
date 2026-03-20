### TESTING UPDATED SIGNAL MODEL

python3 make_combine_workspace.py --cat="inclusive" --region region1 --data \
                                  --no_res \
                                  --input_tag altbkg_chebyshev_newsignal_nores_sb1 --tag altbkg_chebyshev_newsignal_nores_sb1 \
                                  --folder_tag 251216 \
                                  --binned &> logs/251216/workspace_inclusive_region1_data_altbkg_chebyshev_newsignal_nores_sb1_binned_log &
python3 make_combine_workspace.py --cat="inclusive" --region region1 --data \
                                  --no_res \
                                  --input_tag altbkg_chebyshev_newsignal_nores_sb2 --tag altbkg_chebyshev_newsignal_nores_sb2 \
                                  --folder_tag 251216 \
                                  --binned &> logs/251216/workspace_inclusive_region1_data_altbkg_chebyshev_newsignal_nores_sb2_binned_log &

cd /eos/home-n/npalmeri/DiEleAnalyzer/Xee_fits/sensitivity_scan/cards/251216/cards_region1_data_altbkg_chebyshev_newsignal_nores_sb1_binned/ee/2.0

combineCards.py Xee_ee_4_2023.txt ../../../cards_region1_data_altbkg_chebyshev_newsignal_nores_sb2_binned/ee/2.0/Xee_ee_4_2023.txt > Xee_ee_4_combined_2023.txt
# then manually cha ge shapes of ch2 to match those of ch1
text2workspace.py Xee_ee_4_combined_2023.txt Xee_ee_4_combined_2023.root

for point in 0.001 0.005 0.0100 0.0207 0.0336 0.0546 0.0886 0.1000 0.15 0.2 0.3 0.4 0.5 0.6 0.7 1 2.5 5; do
    combine -M AsymptoticLimits Xee_ee_4_combined_2023.root --rMin 0 --rMax 10 \
            --singlePoint "$point" \
            -n "_point_$point" \
            --cminDefaultMinimizerStrategy 0 \
            -v 3 &> "fitAsymptotic_point_$point.log"
done

hadd -f limits_from_grid.root higgsCombine_point_*.AsymptoticLimits.mH120.root

combine -M AsymptoticLimits Xee_ee_4_combined_2023.root --rMin 0 --rMax 10 \
        --getLimitFromGrid limits_from_grid.root \
        -v 3 &> "fitAsymptotic.log"
