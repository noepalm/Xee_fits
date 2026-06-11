#!/usr/bin/env bash

# eras=(2022 2022EE 2023 2023BPix)
# regions=(region0 region1 region2)
# models=(chebyshev bernstein)

# eras=(2022EE 2023 2023BPix)
# regions=(region2)
# models=(chebyshev bernstein)

eras=(2022EE)
regions=(region2)
models=(chebfermi)
# models=(dijet)

# log_dir="logs/260529"
# folder_tag_base="260529"
log_dir="logs/260605"
folder_tag_base="260605"
signal_folder_tag="260430"
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
        chebyshev)
            if [[ "$region" == "region1" ]]; then
                echo 7 # 6th order
            else
                echo 4 # 5th order 
            fi
            ;;
        bernstein)
            if [[ "$region" == "region1" ]]; then
                echo 0 # 7th order
            else
                echo 11 # 6th order 
            fi
            ;;
        exppoly)
            echo 15
            ;;
        dijet)
            echo 16
            ;;
        chebfermi)
            echo 17
            ;;
        polyexp)
            if [[ "$region" == "region2" ]]; then
                echo 12 #4th order
            else 
                echo 1 #5th order
            fi
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
                                                --cached \
                                                --binned \
                                                --fit_data \
                                                --withSyst --corrected \
                                                --folder_tag="${folder_tag_base}/${era}" \
                                                --signal_folder_tag="$signal_folder_tag" \
                                                --fit_region="$region" \
                                                &> "$log_file" &
        done
    done
done

wait

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