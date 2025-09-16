#!/bin/bash

BASEDIR=$PWD

# Parse command line arguments
## appended to input, output folder names -- use when changing dataset
TAG=""
TAG_LABEL="" # same but with _ in front
## appended to output filenames only -- use when changing fit settings (e.g. freezing parameters)
FIT_TAG=""
FIT_TAG_LABEL="" # same but with _ in front
CATEGORY_TYPE="eta"  # Default to eta categories
REGION="region1"
INPUT_FOLDER="cards"  # Default input folder
USE_REWEIGHT=true     # Default to using reweighting
PLOT_ONLY=false
FREEZE_JPSI=false
while [[ $# -gt 0 ]]; do
    case $1 in
        --tag)
            TAG="$2"
            TAG_LABEL="_$TAG"
            shift # past argument
            shift # past value
            ;;
        --fit_tag)
            FIT_TAG="$2"
            FIT_TAG_LABEL="_$FIT_TAG"
            shift # past argument
            shift # past value
            ;;
        --category|--cat)
            CATEGORY_TYPE="$2"
            if [[ "$CATEGORY_TYPE" != "eta" && "$CATEGORY_TYPE" != "dR" && "$CATEGORY_TYPE" != "inclusive" ]]; then
                echo "Error: Category type must be 'eta', 'dR' or 'inclusive'"
                echo "Usage: $0 [--tag TAG_VALUE] [--fit_tag FIT_TAG_VALUE] [--category eta|dR|inclusive] [--no_reweight] [--plot_only]"
                return 1
            fi
            shift # past argument
            shift # past value
            ;;
        --region)
            REGION="$2"
            if [["$REGION" != "region0" && "$REGION" != "region1" && "$REGION" != "region2" ]]; then
                echo "Error: Region must be region0, 1 or 2"
                return 1
            fi
            INPUT_FOLDER="$INPUT_FOLDER"_"$REGION"
            shift # past argument
            shift # past value
            ;;
        --no_reweight)
            INPUT_FOLDER="cards_noReweight"
            USE_REWEIGHT=false
            shift # past argument
            ;;
        --plot_only)
            PLOT_ONLY=true
            echo "Only generating plots, skipping AsymptoticLimits runs."
            shift # past argument
            ;;
        --freeze_jpsi)
            FREEZE_JPSI=true
            echo "Freezing J/psi scale parameter in fits."
            shift # past argument
            ;;
        *)
            # Check if there are actually arguments to process
            if [[ -n "$1" ]]; then
                echo "Unknown argument: $1"
                echo "Usage: $0 [--tag TAG_VALUE] [--fit_tag FIT_TAG_VALUE] [--category eta|dR|inclusive] [--no_reweight] [--plot_only]"
                return 1
            else
                # No more arguments, break out of the loop
                break
            fi
            ;;
    esac
done

# Set output folder based on reweighting setting
OUTFOLDER="/eos/home-n/npalmeri/www/DiElectron/sensitivity/forPresentation_160925/fitDiagnostics"
if [ "$USE_REWEIGHT" = true ]; then
    OUTFOLDER="${OUTFOLDER}_reweight_categories"
else
    OUTFOLDER="${OUTFOLDER}_noReweight"
fi

# If tag is set and different from "", append it to input folder
if [[ "$TAG" != "" ]]; then
    INPUT_FOLDER="${INPUT_FOLDER}_${TAG}"
    OUTFOLDER="${OUTFOLDER}_${TAG}"
fi

# append final suffix to outfolder
OUTFOLDER="${OUTFOLDER}/mu0"

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

# Mapping region to min, max in mass range
# NOTE: region definition
# region0: 0-2.0
# region1: 2.0-4.2
# region2: 4.2-11.0
# however, min/max mass range is tighter due to boundary fits being unreliable
case "$REGION" in
    "region0")
        MIN_MASS=0
        MIN_MASS_LIMIT=0
        MAX_MASS=2.0
        MAX_MASS_LIMIT=2.2
        ;;
    "region1")
        MIN_MASS=2.0
        MIN_MASS_LIMIT=2.2
        MAX_MASS=4.2
        MAX_MASS_LIMIT=4.0
        ;;
    "region2")
        MIN_MASS=4.2
        MIN_MASS_LIMIT=4.4
        MAX_MASS=11
        MAX_MASS_LIMIT=10.8
        ;;
    *)
        echo "Error: Region must be region0, 1 or 2"
        return 1
        ;;
esac

# Export the functions so parallel processes can use them
export -f get_category_name
export -f get_category_label
export -f get_all_category_ids
# Export the category type so parallel processes can access it
export CATEGORY_TYPE TAG_LABEL FIT_TAG_LABEL INPUT_FOLDER USE_REWEIGHT FREEZE_JPSI PLOT_ONLY
export MIN_MASS MIN_MASS_LIMIT MAX_MASS MAX_MASS_LIMIT

# Print configuration
echo "Configuration:"
echo "  Use reweighting: $USE_REWEIGHT"
echo "  Input folder: $INPUT_FOLDER"
echo "  Output folder: $OUTFOLDER"
echo "  Tag: ${TAG:-'(none)'}"
echo "  Category type: $CATEGORY_TYPE"
echo "  Categories: $(get_all_category_ids)"
echo "  Region: $REGION (mass min: $MIN_MASS [limit from $MIN_MASS_LIMIT], max: $MAX_MASS [limit up to $MAX_MASS_LIMIT])"
echo "  Plot only: $PLOT_ONLY"

# Create output folders for each category
for cat_id in $(get_all_category_ids); do
    cat_name=$(get_category_name "$cat_id")
    echo "Creating output folders $OUTFOLDER/$cat_name/s, b"
    mkdir -p $OUTFOLDER/$cat_name/s
    mkdir -p $OUTFOLDER/$cat_name/b
done

# copy input .root file
cp $INPUT_FOLDER/ee/common/Xee_ee.input.root $OUTFOLDER/

process_dir() {
    dir="$1"

    # check folder format -- should be cards/ee/<mass>
    if [[ ! "$dir" =~ ^${INPUT_FOLDER}/ee/[0-9]+(\.[0-9]+)?$ ]]; then
        echo "Skipping $dir, does not match expected format"
        return
    fi

    mass=$(basename "$dir")
    if (( $(echo "$mass < $MIN_MASS_LIMIT" | bc -l) )) || (( $(echo "$mass > $MAX_MASS_LIMIT" | bc -l) )); then #NOTE: nominally 2-4.2, but fits at the boundaries are unreliable
        echo "Skipping $dir, mass $mass is out of range for $REGION ($MIN_MASS_LIMIT to $MAX_MASS_LIMIT)"
        return
    fi

    # TEMPORARY: run only on 3.1
    if (( $(echo "$mass != 3.1" | bc -l) )); then
        echo "Skipping $dir, mass $mass is not 3.1 (TEMPORARY)"
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

                if [ "$FREEZE_JPSI" = true ]; then
                    echo "Freezing parameters scale_jpsi_$(get_category_label $cat_name),scale_psi2s_$(get_category_label $cat_name)"

                    combine -M AsymptoticLimits higgsCombine_${cat_name}_Bonly.MultiDimFit.mH120.root --rMin 0 --rMax 40 \
                            --snapshotName MultiDimFit \
                            -n "_${cat_name}${FIT_TAG_LABEL}" \
                            --freezeParameters scale_jpsi_$(get_category_label "$cat_name") \
                            -v 3 &> "fitAsymptotic_${cat_name}${FIT_TAG_LABEL}.log"
                            # --minosAlgo bisection \
                            # --freezeParameters scale_jpsi_$(get_category_label "$cat_name"),scale_psi2s_$(get_category_label "$cat_name") \
                else
                    # OLD IMPLEMENTATION: uses original workspace
                    ### NB: rMax was 1 before -- shouldn't change anything when it's reasonable
                    ### could bear an impact when fitting over peaks
                    combine -M AsymptoticLimits "$root_file" \
                            -n "_${cat_name}${FIT_TAG_LABEL}" \
                            -v 3 &> "fitAsymptotic_${cat_name}${FIT_TAG_LABEL}.log"
                            # --minosAlgo bisection \
                            # --genBinnedChannels Xee_ee_${cat_id}_2023 \

                    # # # GRID TEST
                    # # for point in 1 1.5 1.7 1.9 2.1 2.3 2.5 2.7 3 3.1 3.3 3.5 3.7 3.9 4 4.1 4.2 4.3 4.4 4.5 4.6 4.7 4.8 4.9 5.0 5.1 5.15 5.17 5.18 5.19 5.2 5.3 5.4 5.5 5.7 6 10 15; do
                    # for point in 1.5 1.7 1.9 2.1 2.3 2.5 2.7; do
                    #     combine -M AsymptoticLimits "$root_file" --rMin 0 --rMax 20 \
                    #             --singlePoint $point \
                    #             -n "_${cat_name}${FIT_TAG_LABEL}_point_$point" \
                    #             -v 3 &> "fitAsymptotic_${cat_name}${FIT_TAG_LABEL}_point_$point.log"
                    # done

                    # hadd -f limits_from_grid_${cat_name}.root higgsCombine_${cat_name}${FIT_TAG_LABEL}_point_*AsymptoticLimits* 
                    # combine -M AsymptoticLimits "$root_file" --rMin 0 --rMax 20 \
                    #         --getLimitFromGrid limits_from_grid_${cat_name}.root \
                    #         -n "_${cat_name}${FIT_TAG_LABEL}" \
                    #         -v 3 &> "fitAsymptotic_${cat_name}${FIT_TAG_LABEL}.log"
                    #         # --minosAlgo bisection \
                    #         # --genBinnedChannels Xee_ee_${cat_id}_2023 \
                fi

                tail -n 10 "fitAsymptotic_${cat_name}${FIT_TAG_LABEL}.log"
                
                # Create category-specific output folder
                mkdir -p "$OUTFOLDER/$cat_name/M$mass"
                cp "fitAsymptotic_${cat_name}${FIT_TAG_LABEL}.log" "higgsCombine_${cat_name}${FIT_TAG_LABEL}.AsymptoticLimits.mH120.root" "$OUTFOLDER/$cat_name/M$mass/"
                [ -f combine_logger.out ] && cp combine_logger.out "$OUTFOLDER/$cat_name/M$mass/combine_logger_${cat_name}${FIT_TAG_LABEL}.out"
            fi
        else
            echo "  $txt_file not found for category $cat_id ($cat_name)"
        fi
    done
    
    cd - > /dev/null || exit
}

export -f process_dir
export OUTFOLDER BASEDIR PLOT_ONLY INPUT_FOLDER USE_REWEIGHT

find $INPUT_FOLDER/ee -mindepth 1 -maxdepth 1 -type d | \
    parallel --jobs 8 process_dir {}

# produce summary plots for each category
for cat_id in $(get_all_category_ids); do
    cat_name=$(get_category_name "$cat_id")
    echo "Creating summary plots for category $cat_name"
    
    # Build the command with optional tag argument
    plot_cmd="python3 $BASEDIR/scripts/plot_limits_result.py -o \"$OUTFOLDER/$cat_name\" -i \"$INPUT_FOLDER\" -c $cat_name -r $REGION"
    if [[ -n "$FIT_TAG" ]]; then
        plot_cmd="$plot_cmd --tag \"${REGION}_${FIT_TAG}\""
    fi
    
    # Execute the command
    eval "$plot_cmd" &> "$OUTFOLDER/$cat_name/limits_summary_${REGION}${FIT_TAG_LABEL}.log"
done