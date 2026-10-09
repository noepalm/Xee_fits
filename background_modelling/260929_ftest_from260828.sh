#!/usr/bin/env bash

# eras=(2022 2023)
# regions=(region0 region1 region2)
# # models=(chebyshev4 chebyshev5 chebyshev6 chebyshev7 chebyshev8 chebyshev9 chebyshev10 chebyshev11 chebyshev12 chebyshev13)
# models=(bernstein4 bernstein5 bernstein6 bernstein7 bernstein8 bernstein9 bernstein10 bernstein11 bernstein12 bernstein13 bernstein14 bernstein15)

# eras=(2022)
# regions=(region2)
# models=(chebyshev13)

eras=(2023)
regions=(region0)
models=(bernstein4 bernstein5 bernstein6 bernstein10 bernstein11)
# regions=(region2)
# models=(bernstein4 bernstein5 bernstein8 bernstein11 bernstein15)
# regions=(region0)
# models=(chebyshev4 chebyshev5)
# regions=(region2)
# models=(chebyshev4 chebyshev5 chebyshev10 chebyshev11 chebyshev13)

# log_dir="logs/260529"
# folder_tag_base="260529"
log_dir="logs/260929"
folder_tag_base="260929"
signal_folder_tag="260727"
# signal_folder_tag="260320"

# Keep envelope as a dedicated stage. Set to 1 to run it after model fits.
run_envelope=1

mkdir -p "$log_dir"
mkdir -p "datasets/${folder_tag_base}"

# UPDATED BKG FUNCTIONS with result from F-test
get_bkg_function() {
    local model="$1"
    local region="$2"
    case "$model" in
        chebyshev3)
            echo 33
            ;;
        chebyshev4)
            echo 8
            ;;
        chebyshev5)
            echo 4
            ;;
        chebyshev6)
            echo 7
            ;;
        chebyshev7)
            echo 24
            ;;
        chebyshev8)
            echo 25
            ;;
        chebyshev9)
            echo 26
            ;;
        chebyshev10)
            echo 27
            ;;
        chebyshev11)
            echo 28
            ;;
        chebyshev12)
            echo 31
            ;;
        chebyshev13)
            echo 32
            ;;
        bernstein4)
            echo 9
            ;;
        bernstein5)
            echo 10
            ;;
        bernstein6)
            echo 11
            ;;
        bernstein7)
            echo 0
            ;;
        bernstein8)
            echo 18
            ;;
        bernstein9)
            echo 19
            ;;
        bernstein10)
            echo 20
            ;;
        bernstein11)
            echo 21
            ;;
        bernstein12)
            echo 22
            ;;
        bernstein13)
            echo 23
            ;;
        bernstein14)
            echo 29
            ;;
        bernstein15)
            echo 30
            ;;
        *)
            echo "Unknown model: $model" >&2
            return 1
            ;;
    esac
}

# Run alternative background fits
for era in "${eras[@]}"; do
    for region in "${regions[@]}"; do
        for model in "${models[@]}"; do
            bkg_function="$(get_bkg_function "$model" "$region")" || exit 1
            tag="data_altbkg_${model}_allCorrections_${era}"
            log_file="${log_dir}/reweight_data_${region}_altbkg_${model}_allCorrections_${era}_binned_log"

            python3 main_background_analysis.py --full_analysis --bkg_function "$bkg_function" \
                                                --fit_jpsi_prompt --floating_resonant \
                                                --data --tag="$tag" \
                                                --era "$era" \
                                                --categories="inclusive" \
                                                --binned \
                                                --cached \
                                                --fit_data \
                                                --withSyst --corrected \
                                                --folder_tag="${folder_tag_base}/${era}" \
                                                --signal_folder_tag="$signal_folder_tag" \
                                                --fit_region="$region" \
                                                &> $log_file &
        done
    done
done

wait

echo "All background fits completed. Generating summary report..."

for era in "${eras[@]}"; do
    for region in "${regions[@]}"; do
        for model in "${models[@]}"; do
            python3 report.py --log_dir "$log_dir" --era "$era" --region "$region" --model "$model"
        done
    done
done

# # Produce workspace with envelope
# # NOTE: requires combine environment.
# if [[ "$run_envelope" -eq 1 ]]; then
#     for era in "${eras[@]}"; do
#         for region in "${regions[@]}"; do
#             envelope_tag="data_envelope_allCorrections_${era}"
#             envelope_log="${log_dir}/reweight_data_${region}_envelope_allCorrections_${era}_binned_log"

#             input_workspaces=()
#             for model in "${models[@]}"; do
#                 input_workspaces+=("datasets/${folder_tag_base}/${era}/dataset_data_${region}_binned_data_altbkg_${model}_allCorrections_${era}_full.root")
#             done

#             python3 main_background_analysis.py --full_analysis --bkg_function -1 \
#                                                --fit_jpsi_prompt --floating_resonant \
#                                                --data --tag="$envelope_tag" \
#                                                --era "$era" \
#                                                --categories="inclusive" \
#                                                --binned \
#                                                --fit_data \
#                                                --cached \
#                                                --withSyst --corrected \
#                                                --folder_tag="${folder_tag_base}/${era}" \
#                                                --signal_folder_tag="$signal_folder_tag" \
#                                                --input_workspaces "${input_workspaces[@]}" \
#                                                --fit_region="$region" \
#                                                &> "$envelope_log" &
#         done
#     done
# fi

# wait