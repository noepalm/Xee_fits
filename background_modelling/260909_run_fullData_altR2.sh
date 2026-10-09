#!/usr/bin/env bash

eras=(2022 2022EE 2023 2023BPix)
regions=(region0 region1 region2)
models=(bernstein chebyshev)

# eras=(2023)
# regions=(region2)
# models=(chebyshev bernstein)

# log_dir="logs/260529"
# folder_tag_base="260529"
log_dir="logs/260909"
folder_tag_base="260909"
signal_folder_tag="260727"
# signal_folder_tag="260320"

# Keep envelope as a dedicated stage. Set to 1 to run it after model fits.
run_envelope=1

mkdir -p "$log_dir"
mkdir -p "datasets/${folder_tag_base}"

# UPDATED BKG FUNCTIONS with result from F-test
get_bkg_function() {
    # implements the following function choices:
    # 2022:
    # Bernstein: 9th order (region 0), 5th order (region 1), 11th order (region2)
    # Chebyshev: 7th order (region 0), 5th order (region 1), 11th order (region2)
    # 2023:
    # Bernstein: 10th order (region 0), 7th order (region 1), 11th order (region2)
    # Chebyshev: 7th order (region 0), 5th order (region 1), 11th order (region2)
    local model="$1"
    local region="$2"
    local era="$3"
    case "$model" in
        chebyshev)
            if [[ "$era" == "2022" ]]; then
                case "$region" in
                    region0)
                        echo 24 #7th order
                        ;;
                    region1)
                        echo 7 #6th order
                        ;;
                    region2)
                        echo 24 #7th order
                        ;;
                    *)
                        echo "Unknown region: $region" >&2
                        return 1
                        ;;
                esac
            elif [[ "$era" == "2023" ]]; then
                case "$region" in
                    region0)
                        echo 31 #12th order
                        ;;
                    region1)
                        echo 24 #7th order
                        ;;
                    region2)
                        echo 24 #7th order
                        ;;
                    *)
                        echo "Unknown region: $region" >&2
                        return 1
                        ;;
                esac
            elif [[ "$era" == "2023BPix" ]]; then
                case "$region" in
                    region0)
                        echo 24 #7th order
                        ;;
                    region1)
                        echo 26 #9th order
                        ;;
                    region2)
                        echo 24 #7th order
                        ;;
                    *)
                        echo "Unknown region: $region" >&2
                        return 1
                        ;;
                esac                
            else # 2022EE
                case "$region" in
                    region0)
                        echo 24 #7th order
                        ;;
                    region1)
                        echo 26 #9th order
                        ;;
                    region2)
                        echo 24 #7th order
                        ;;
                    *)
                        echo "Unknown region: $region" >&2
                        return 1
                        ;;
                esac
            fi
            ;;

        bernstein)
            if [[ "$era" == "2022" ]]; then
                case "$region" in
                    region0)
                        echo 19 #9th order
                        ;;
                    region1)
                        echo 0 #7th order
                        ;;
                    region2)
                        echo 18 #8th order
                        ;;
                esac
            elif [[ "$era" == "2022EE" ]]; then
                case "$region" in
                    region0)
                        echo 21 #11th order
                        ;;
                    region1)
                        echo 20 #10th order
                        ;;
                    region2)
                        echo 18 #8th order
                        ;;
                esac
            elif [[ "$era" == "2023" ]]; then
                case "$region" in
                    region0)
                        echo 29 #14th order
                        ;;
                    region1)
                        echo 19 #9th order
                        ;;
                    region2)
                        echo 18 #8th order
                        ;;
                esac
            else #2023BPix
                case "$region" in
                    region0)
                        echo 19 #9th order
                        ;;
                    region1)
                        echo 19 #9th order
                        ;;
                    region2)
                        echo 18 #8th order
                        ;;
                esac
            fi
            ;;
        *)
            echo "Unknown model: $model" >&2
            return 1
            ;;
    esac
}

if [[ "$run_envelope" -eq 0 ]]; then
    # Run alternative background fits
    for era in "${eras[@]}"; do
        for region in "${regions[@]}"; do
            for model in "${models[@]}"; do
                bkg_function="$(get_bkg_function "$model" "$region" "$era")" || exit 1
                tag="data_altbkg_${model}_allCorrections_${era}"
                log_file="${log_dir}/reweight_data_${region}_altbkg_${model}_allCorrections_${era}_binned_log"

                python3 main_background_analysis.py --full_analysis --bkg_function "$bkg_function" \
                                                    --fit_jpsi_prompt --floating_resonant \
                                                    --data --tag="$tag" \
                                                    --era "$era" \
                                                    --categories="inclusive" \
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

    # copy the scripts themselves to the output folder (contain inits, fit strategies, etc)
    mkdir -p datasets/${folder_tag_base}/${era}/scripts
    cp background_config.py background_fitter.py datasets/${folder_tag_base}/${era}/scripts

    echo "All background fits completed. Generating summary report..."

    for era in "${eras[@]}"; do
        for region in "${regions[@]}"; do
            for model in "${models[@]}"; do
                python3 report.py --log_dir "$log_dir" --era "$era" --region "$region" --model "$model"
            done
        done
    done
else
    # Produce workspace with envelope
    # NOTE: requires combine environment.
    if [[ "$run_envelope" -eq 1 ]]; then
        for era in "${eras[@]}"; do
            for region in "${regions[@]}"; do
                envelope_tag="data_envelope_allCorrections_${era}"
                envelope_log="${log_dir}/reweight_data_${region}_envelope_allCorrections_${era}_binned_log"

                input_workspaces=()
                for model in "${models[@]}"; do
                    input_workspaces+=("datasets/${folder_tag_base}/${era}/dataset_data_${region}_binned_data_altbkg_${model}_allCorrections_${era}_full.root")
                done

                python3 main_background_analysis.py --full_analysis --bkg_function -1 \
                                                --fit_jpsi_prompt --floating_resonant \
                                                --data --tag="$envelope_tag" \
                                                --era "$era" \
                                                --categories="inclusive" \
                                                --binned \
                                                --fit_data \
                                                --cached \
                                                --withSyst --corrected \
                                                --folder_tag="${folder_tag_base}/${era}" \
                                                --signal_folder_tag="$signal_folder_tag" \
                                                --input_workspaces "${input_workspaces[@]}" \
                                                --fit_region="$region" \
                                                &> "$envelope_log" &
            done
        done
    fi

    wait
fi