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
            INPUT_FOLDER="$INPUT_FOLDER"_noReweight
            USE_REWEIGHT=false
            shift # past argument
            ;;
        --plot_only)
            PLOT_ONLY=true
            echo "Only generating plots, skipping AsymptoticLimits runs."
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
OUTFOLDER="/eos/home-n/npalmeri/www/DiElectron/sensitivity/fitDiagnostics_grid"
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
        MIN_MASS=0.3            # was 0.2
        MIN_MASS_LIMIT=0.4      # was 0.4
        MAX_MASS=2.0
        MAX_MASS_LIMIT=1.8
        ;;
    "region1")
        MIN_MASS=2.0
        MIN_MASS_LIMIT=2.2
        MAX_MASS=4.2 #was 4.6
        MAX_MASS_LIMIT=4.0 #was 4.4
        ;;
    "region2")
        MIN_MASS=4.2 #was 3.8
        MIN_MASS_LIMIT=4.4 #was 4.0
        MAX_MASS=11
        MAX_MASS_LIMIT=10.8
        ;;
    *)
        echo "Error: Region must be region0, 1 or 2"
        return 1
        ;;
esac

# Export functions and vars so parallel processes can use them
export -f get_category_name
export -f get_category_label
export -f get_all_category_ids
export CATEGORY_TYPE REGION TAG_LABEL FIT_TAG_LABEL INPUT_FOLDER USE_REWEIGHT PLOT_ONLY
export MIN_MASS MIN_MASS_LIMIT MAX_MASS MAX_MASS_LIMIT

# Print configuration
echo "Configuration:"
echo "  Use reweighting: $USE_REWEIGHT"
echo "  Input folder: $INPUT_FOLDER"
echo "  Output folder: $OUTFOLDER"
echo "  Tag: ${TAG:-'(none)'}"
echo "  Fit tag: ${FIT_TAG:-'(none)'}"
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

# Copy common .root file to output folder (for future workspace recreation)
cp $INPUT_FOLDER/ee/common/Xee_ee.input.root $OUTFOLDER/

process_dir() {
    dir="$1"
    if [[ ! -d "$dir" ]]; then
        echo "Skipping $dir, not a directory"
        return
    fi

    if [[ ! "$dir" =~ ^${INPUT_FOLDER}/ee/[0-9]+(\.[0-9]+)?$ ]]; then
        echo "Skipping $dir, does not match expected format"
        return
    fi

    mass=$(basename "$dir")
    if (( $(echo "$mass < $MIN_MASS_LIMIT" | bc -l) )) || (( $(echo "$mass > $MAX_MASS_LIMIT" | bc -l) )); then #NOTE: nominally 2-4.2, but fits at the boundaries are unreliable
        echo "Skipping $dir, mass $mass is out of range for $REGION ($MIN_MASS_LIMIT to $MAX_MASS_LIMIT)"
        return
    fi

    # # TEMPORARY: only process mass = 3.1
    # if (( $(echo "$mass != 3.1" | bc -l) )); then
    #     echo "Skipping $dir, temporary restriction to mass = 3.1"
    #     return
    # fi

    echo "Processing directory: $dir"
    cd "$dir" || return
    
    # Process each category
    for cat_id in $(get_all_category_ids); do
        cat_name=$(get_category_name "$cat_id")
        txt_file="Xee_ee_${cat_id}_2023.txt"
        root_file="Xee_ee_${cat_id}_2023.root"
        
        if [ -f "$txt_file" ]; then
            echo "  Processing category $cat_id ($cat_name): $txt_file"
            echo $PLOT_ONLY

            if [ "$PLOT_ONLY" == false ]; then
                echo "    Running combine for category $cat_name"
                text2workspace.py "$txt_file"
                combine -M FitDiagnostics "$root_file" \
                        --saveNormalizations \
                        --saveShapes \
                        --setParameterRanges mass=$MIN_MASS,$MAX_MASS \
                        --keepFailures \
                        -n "_${cat_name}${FIT_TAG_LABEL}" \
                        -v 3 &> "fitDiagnostics_${cat_name}${FIT_TAG_LABEL}.log"
                        # --preFitValue 0 \
                tail -n 10 "fitDiagnostics_${cat_name}${FIT_TAG_LABEL}.log"
                cp combine_logger.out "$OUTFOLDER/$cat_name/M$mass/combine_logger_fitDiagnostics_${cat_name}.out" 2>/dev/null || true

                # [FIXME] Temporary double, can be optimized
                # Also run a MultiDimFit to save a post-fit snapshot for B-only fit (serves as input for limits later)
                combine -M MultiDimFit "$root_file" \
                        --saveWorkspace \
                        --setParameters r=0 \
                        --freezeParameters r \
                        --setParameterRanges mass=$MIN_MASS,$MAX_MASS \
                        -n "_${cat_name}${FIT_TAG_LABEL}_Bonly" \
                        -v 3 &> "fitMultiDimFit_Bonly_${cat_name}${FIT_TAG_LABEL}.log"
                cp combine_logger.out "$OUTFOLDER/$cat_name/M$mass/combine_logger_MultiDimFit_Bonly_${cat_name}${FIT_TAG_LABEL}.out" 2>/dev/null || true

                # Create category-specific output folder
                mkdir -p "$OUTFOLDER/$cat_name/M$mass"
                cp "fitDiagnostics_${cat_name}${FIT_TAG_LABEL}.log" "$txt_file" "fitDiagnostics_${cat_name}${FIT_TAG_LABEL}.root" higgsCombine_${cat_name}${FIT_TAG_LABEL}.FitDiagnostics.mH120.root higgsCombine_${cat_name}${FIT_TAG_LABEL}_Bonly.MultiDimFit.mH120.root fitMultiDimFit_Bonly_${cat_name}${FIT_TAG_LABEL}.log  "$OUTFOLDER/$cat_name/M$mass/"
            fi

            echo "    Plotting for category $cat_name"
            python3 $BASEDIR/scripts/draw_mu0_fit.py -i "$root_file" -f fitDiagnostics_${cat_name}${FIT_TAG_LABEL}.root -o "$OUTFOLDER/$cat_name" -m $mass -c $cat_id -r $REGION --tag "$FIT_TAG"
        else
            echo "  $txt_file not found for category $cat_id ($cat_name)"
        fi
    done
    
    cd - || exit
}

export -f process_dir
export OUTFOLDER BASEDIR PLOT_ONLY INPUT_FOLDER USE_REWEIGHT TAG_LABEL FIT_TAG_LABEL

find $INPUT_FOLDER/ee -mindepth 1 -maxdepth 1 -type d | parallel -j 8 process_dir {}

# Create summary plots for each category
for cat_id in $(get_all_category_ids); do
    cat_name=$(get_category_name "$cat_id")

    # Build the command with optional tag argument
    plot_cmd="python3 $BASEDIR/scripts/plot_diagnostics_result.py -o \"$OUTFOLDER/$cat_name\" -c $cat_name"
    if [[ -n "$TAG" ]]; then
        plot_cmd="$plot_cmd --tag \"${REGION}_${FIT_TAG}\""
    fi
    
    # Execute the command
    echo "Creating summary plots for category $cat_name"
    eval "$plot_cmd" &> "$OUTFOLDER/$cat_name/diagnostics_summary_${REGION}${FIT_TAG_LABEL}.log"
done