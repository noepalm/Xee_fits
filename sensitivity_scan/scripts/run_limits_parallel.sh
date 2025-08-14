#!/bin/bash

OUTFOLDER="/eos/home-n/npalmeri/www/DiElectron/sensitivity/fitDiagnostics_reweight_categories/mu0"
BASEDIR=$PWD

# Parse command line arguments
TAG=""
TAG_LABEL="" # same but with _ in front
CATEGORY_TYPE="eta"  # Default to eta categories
PLOT_ONLY=false
while [[ $# -gt 0 ]]; do
    case $1 in
        --tag)
            TAG="$2"
            TAG_LABEL="_$TAG"  # Use underscore for consistency in filenames
            shift # past argument
            shift # past value
            ;;
        --category|--cat)
            CATEGORY_TYPE="$2"
            if [[ "$CATEGORY_TYPE" != "eta" && "$CATEGORY_TYPE" != "dR" && "$CATEGORY_TYPE" != "inclusive" ]]; then
                echo "Error: Category type must be 'eta', 'dR' or 'inclusive'"
                echo "Usage: $0 [--tag TAG_VALUE] [--category eta|dR] [--plot-only]"
                return 1
            fi
            shift # past argument
            shift # past value
            ;;
        --plot-only)
            PLOT_ONLY=true
            echo "Only generating plots, skipping AsymptoticLimits runs."
            shift # past argument
            ;;
        *)
            # Check if there are actually arguments to process
            if [[ -n "$1" ]]; then
                echo "Unknown argument: $1"
                echo "Usage: $0 [--tag TAG_VALUE] [--category eta|dR] [--plot-only]"
                return 1
            else
                # No more arguments, break out of the loop
                break
            fi
            ;;
    esac
done

# Category ID to name mapping (based on shared_config.py categories)
# Define as a function that can be exported and called from parallel processes

# create a translation map between category names and category labels
# e.g. if category name is etaHigh, return etap0p6
get_category_label() {
    case "$1" in
        "etaHigh") echo "etap0p6" ;;
        "etaLow") echo "etam0p6" ;;
        "dRHigh") echo "dRp0p3" ;;
        "dRLow") echo "dRm0p3" ;;
        "inclusive") echo "inclusive" ;;
        *) echo "unknown" ;;
    esac
}

get_category_name() {
    case "$1" in
        0) echo "etaHigh" ;;
        1) echo "etaLow" ;;
        2) echo "dRHigh" ;;
        3) echo "dRLow" ;;
        4) echo "inclusive" ;;
        *) echo "unknown" ;;
    esac
}

# Get all category IDs
get_all_category_ids() {
    case "$CATEGORY_TYPE" in
        "eta")
            echo "0 1"
            ;;
        "dR")
            echo "2 3"
            ;;
        "inclusive")
            echo "4"
            ;;
        *)
            echo "0 1"  # Default to eta
            ;;
    esac
}

# Export the functions so parallel processes can use them
export -f get_category_name
export -f get_category_label
export -f get_all_category_ids
# Export the category type so parallel processes can access it
export CATEGORY_TYPE TAG_LABEL

# Print configuration
echo "Configuration:"
echo "  Output folder: $OUTFOLDER"
echo "  Tag: ${TAG:-'(none)'}"
echo "  Category type: $CATEGORY_TYPE"
echo "  Categories: $(get_all_category_ids)"
echo "  Plot only: $PLOT_ONLY"

# Create output folders for each category
for cat_id in $(get_all_category_ids); do
    cat_name=$(get_category_name "$cat_id")
    echo "Creating output folders $OUTFOLDER/$cat_name/s, b"
    mkdir -p $OUTFOLDER/$cat_name/s
    mkdir -p $OUTFOLDER/$cat_name/b
done

process_dir() {
    dir="$1"

    # check folder format -- should be cards/ee/<mass>
    if [[ ! "$dir" =~ ^cards/ee/[0-9]+(\.[0-9]+)?$ ]]; then
        echo "Skipping $dir, does not match expected format"
        return
    fi

    mass=$(basename "$dir")
    # TODO: add more robust check (check signal model width and compare to region boundaries)
    if (( $(echo "$mass < 2.2" | bc -l) )) || (( $(echo "$mass > 4.0" | bc -l) )); then #NOTE: nominally 2-4.2, but fits at the boundaries are unreliable
        echo "Skipping $dir, mass $mass is out of range (2.2 to 4)" #FIXME: 2-4.2
        return
    fi

    echo "Processing directory: $dir"
    cd "$dir" || return
    
    # Process each category
    for cat_id in $(get_all_category_ids); do
        cat_name=$(get_category_name "$cat_id")
        txt_file="Xee_ee_${cat_id}_2023.txt"
        root_file="Xee_ee_${cat_id}_2023.root"
        
        if [ -f "$txt_file" ]; then
            if [ "$PLOT_ONLY" == false ]; then
                echo "  Processing category $cat_id ($cat_name): $txt_file"
                echo "    Running AsymptoticLimits for category $cat_name"
                text2workspace.py "$txt_file"

                # # OLD IMPLEMENTATION: uses original workspace
                # combine -M AsymptoticLimits "$root_file" --rMin 0 --rMax 40 \
                #         -n "_${cat_name}" \
                #         --minosAlgo bisection \
		        #         --genBinnedChannels Xee_ee_${cat_id}_2023 \
                #         -v 3 &> "fitAsymptotic_${cat_name}.log"
                # echo "Freezing parameters scale_jpsi_$(get_category_label $cat_name),scale_psi2s_$(get_category_label $cat_name)"

                combine -M AsymptoticLimits higgsCombine_${cat_name}_Bonly.MultiDimFit.mH120.root --rMin 0 --rMax 40 \
                        --snapshotName MultiDimFit \
                        -n "_${cat_name}${TAG_LABEL}" \
                        -v 3 &> "fitAsymptotic_${cat_name}${TAG_LABEL}.log"
                        # --minosAlgo bisection \
                        # --freezeParameters scale_jpsi_$(get_category_label "$cat_name"),scale_psi2s_$(get_category_label "$cat_name") \
                        # --freezeParameters scale_jpsi_$(get_category_label "$cat_name") \

                tail -n 10 "fitAsymptotic_${cat_name}${TAG_LABEL}.log"
                
                # Create category-specific output folder
                mkdir -p "$OUTFOLDER/$cat_name/M$mass"
                cp "fitAsymptotic_${cat_name}${TAG_LABEL}.log" "higgsCombine_${cat_name}${TAG_LABEL}.AsymptoticLimits.mH120.root" "$OUTFOLDER/$cat_name/M$mass/"
                [ -f combine_logger.out ] && cp combine_logger.out "$OUTFOLDER/$cat_name/M$mass/combine_logger_${cat_name}${TAG_LABEL}.out"
            fi
        else
            echo "  $txt_file not found for category $cat_id ($cat_name)"
        fi
    done
    
    cd - > /dev/null || exit
}

export -f process_dir
export OUTFOLDER BASEDIR PLOT_ONLY

find cards/ee -mindepth 1 -maxdepth 1 -type d | \
    parallel --jobs 8 process_dir {}

# produce summary plots for each category
for cat_id in $(get_all_category_ids); do
    cat_name=$(get_category_name "$cat_id")
    echo "Creating summary plots for category $cat_name"
    
    # Build the command with optional tag argument
    plot_cmd="python3 $BASEDIR/scripts/plot_limits_result.py -o \"$OUTFOLDER/$cat_name\" -c $cat_name"
    if [[ -n "$TAG" ]]; then
        plot_cmd="$plot_cmd --tag \"$TAG\""
    fi
    
    # Execute the command
    eval "$plot_cmd" &> "$OUTFOLDER/$cat_name/limits_summary${TAG_LABEL}.log"
done