#!/bin/bash

BASEDIR=$PWD

# Set output folder base
OUTFOLDER="/eos/home-n/npalmeri/www/DiElectron/sensitivity/fitDiagnostics"

# Parse command line arguments
## appended to input, output folder names -- use when changing dataset
TAG=""
TAG_LABEL="" # same but with _ in front
## appended to output filenames only -- use when changing fit settings (e.g. freezing parameters)
FIT_TAG=""
FIT_TAG_LABEL="" # same but with _ in front
CATEGORY_TYPE="eta"  # Default to eta categories
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
                echo "Usage: $0 [--tag TAG_VALUE] [--fit_tag FIT_TAG_VALUE] [--category eta|dR|inclusive] [--no_reweight] [--plot_only] [--freeze_jpsi]"
                return 1
            fi
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
                echo "Usage: $0 [--tag TAG_VALUE] [--fit_tag FIT_TAG_VALUE] [--category eta|dR|inclusive] [--no_reweight] [--plot_only] [--freeze_jpsi]"
                return 1
            else
                # No more arguments, break out of the loop
                break
            fi
            ;;
    esac
done

# Set output folder based on reweighting setting
if [ "$USE_REWEIGHT" = true ]; then
    OUTFOLDER="${OUTFOLDER}_reweight_categories"
else
    OUTFOLDER="${OUTFOLDER}_noReweight"
fi

# If tag is set and different from "", append it to input and output folders
if [[ "$TAG" != "" ]]; then
    INPUT_FOLDER="${INPUT_FOLDER}_${TAG}"
    OUTFOLDER="${OUTFOLDER}_${TAG}"
fi

# append final suffix to outfolder
OUTFOLDER="${OUTFOLDER}/mu0"

# Category ID to name mapping (based on shared_config.py categories)
# Define as a function that can be exported and called from parallel processes
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
export CATEGORY_TYPE TAG_LABEL FIT_TAG_LABEL INPUT_FOLDER USE_REWEIGHT FREEZE_JPSI

# Print configuration
echo "Configuration:"
echo "  Use reweighting: $USE_REWEIGHT"
echo "  Input folder: $INPUT_FOLDER"
echo "  Output folder: $OUTFOLDER"
echo "  Tag: ${TAG:-'(none)'}"
echo "  Fit tag: ${FIT_TAG:-'(none)'}"
echo "  Category type: $CATEGORY_TYPE"
echo "  Categories: $(get_all_category_ids)"
echo "  Plot only: $PLOT_ONLY"
echo "  Freeze J/psi: $FREEZE_JPSI"

echo "Creating output folders $OUTFOLDER/${CATEGORY_TYPE}Combination/s, b"
mkdir -p $OUTFOLDER/${CATEGORY_TYPE}Combination/s
mkdir -p $OUTFOLDER/${CATEGORY_TYPE}Combination/b

# copy input .root file
cp $INPUT_FOLDER/ee/common/Xee_ee.input.root $OUTFOLDER/

process_dir() {
    dir="$1"

    # check folder format -- should be cards/ee/<mass> (or cards_TAG/ee/<mass>)
    if [[ ! "$dir" =~ ^${INPUT_FOLDER}/ee/[0-9]+(\.[0-9]+)?$ ]]; then
        echo "Skipping $dir, does not match expected format"
        return
    fi

    mass=$(basename "$dir")
    if (( $(echo "$mass < 2" | bc -l) )) || (( $(echo "$mass > 4.2" | bc -l) )); then
        echo "Skipping $dir, mass $mass is out of range (2 to 4.2)"
        return
    fi

    echo "Processing directory: $dir"
    cd "$dir" || return

    # Check if the directory contains the datacard for BOTH categories in the type
    # that's 0, 1 if CATEGORY_TYPE is "eta" or 2, 3 if it's "dR"
    for cat_id in $(get_all_category_ids); do
        if [[ ! -f "Xee_ee_${cat_id}_2023.txt" ]]; then
            echo "WARNING: missing datacard for category ID $cat_id for $dir. Skipping this directory."
            return
        fi
    done

    # Combine the two categories
    echo "Combining the two categories"
    txt_file="Xee_ee_${CATEGORY_TYPE}Combination_2023.txt"
    root_file="Xee_ee_${CATEGORY_TYPE}Combination_2023.root"

    # Combine the two categories into a single datacard
    card_files=()
    for cat_id in $(get_all_category_ids); do
        card_files+=("Xee_ee_${cat_id}_2023.txt")
    done
    combineCards.py "${card_files[@]}" > "$txt_file"
    
    echo "  Processing combination in eta categories: $txt_file"
    text2workspace.py "$txt_file"

    # Run MultiDimFit first to get a snapshot
    echo "  Running MultiDimFit for ${CATEGORY_TYPE} combination"
    combine -M MultiDimFit "$root_file" \
            --saveWorkspace \
            --setParameters r=0 \
            --freezeParameters r \
            --setParameterRanges mass=2,4.2 \
            -n "_${CATEGORY_TYPE}Combination_Bonly${FIT_TAG_LABEL}" \
            -v 3 &> "fitMultiDimFit_Bonly_${CATEGORY_TYPE}Combination${FIT_TAG_LABEL}.log"
    cp combine_logger.out "$OUTFOLDER/${CATEGORY_TYPE}Combination/M$mass/combine_logger_MultiDimFit_${CATEGORY_TYPE}Combination_Bonly${FIT_TAG_LABEL}.out" 2>/dev/null || true

    # Run AsymptoticLimits on the combined datacard
    echo "  Running AsymptoticLimits for ${CATEGORY_TYPE} combination"
    
    if [ "$FREEZE_JPSI" = true ]; then
        # Build list of parameters to freeze (J/psi scales for each category)
        card_files=()
        for cat_id in $(get_all_category_ids); do
            cat_name=$(get_category_name "$cat_id")
            card_files+=("scale_jpsi_$(get_category_label $cat_name)")
            # Optionally also freeze psi2s - uncomment the line below if needed
            # card_files+=("scale_psi2s_$(get_category_label $cat_name)")
        done
        params_to_freeze=$(IFS=,; echo "${card_files[*]}")
        echo "Freezing parameters: $params_to_freeze"

        combine -M AsymptoticLimits higgsCombine_${CATEGORY_TYPE}Combination_Bonly${FIT_TAG_LABEL}.MultiDimFit.mH120.root --rMin 0 --rMax 40 \
                --snapshotName MultiDimFit \
                --freezeParameters $params_to_freeze \
                -n ".AsymptoticLimit_${CATEGORY_TYPE}Combination${FIT_TAG_LABEL}" \
                -v 3 &> "fitAsymptotic_${CATEGORY_TYPE}Combination${FIT_TAG_LABEL}.log"
    else
        # Default behavior without freezing parameters
        combine -M AsymptoticLimits "$root_file" --rMin 0 --rMax 1 \
                -n ".AsymptoticLimit_${CATEGORY_TYPE}Combination${FIT_TAG_LABEL}" \
                -v 3 &> "fitAsymptotic_${CATEGORY_TYPE}Combination${FIT_TAG_LABEL}.log"
    fi
    tail -n 10 "fitAsymptotic_${CATEGORY_TYPE}Combination${FIT_TAG_LABEL}.log"
    
    # Create category-specific output folder
    mkdir -p "$OUTFOLDER/${CATEGORY_TYPE}Combination/M$mass"
    cp "fitAsymptotic_${CATEGORY_TYPE}Combination${FIT_TAG_LABEL}.log" "higgsCombine.AsymptoticLimit_${CATEGORY_TYPE}Combination${FIT_TAG_LABEL}.AsymptoticLimits.mH120.root" "$OUTFOLDER/${CATEGORY_TYPE}Combination/M$mass/"
    [ -f combine_logger.out ] && cp combine_logger.out "$OUTFOLDER/${CATEGORY_TYPE}Combination/M$mass/combine_logger_AsymptoticLimit_${CATEGORY_TYPE}Combination${FIT_TAG_LABEL}.out"
    
    cd - > /dev/null || exit
}

export -f process_dir
export OUTFOLDER BASEDIR

if [ "$PLOT_ONLY" == false ]; then
    find $INPUT_FOLDER/ee -mindepth 1 -maxdepth 1 -type d | \
        parallel --jobs 8 process_dir {}
fi

echo "Creating summary plots for ${CATEGORY_TYPE} combination"
plot_cmd="python3 $BASEDIR/scripts/plot_limits_result.py -o \"$OUTFOLDER/${CATEGORY_TYPE}Combination\" -i \"$INPUT_FOLDER\" -c ${CATEGORY_TYPE}Combination"
if [[ -n "$FIT_TAG" ]]; then
    plot_cmd="$plot_cmd --tag \"$FIT_TAG\""
fi

# Execute the command
eval "$plot_cmd" &> "$OUTFOLDER/${CATEGORY_TYPE}Combination/limits_summary${FIT_TAG_LABEL}.log"