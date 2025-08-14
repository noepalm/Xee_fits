#!/bin/bash

OUTFOLDER="/eos/home-n/npalmeri/www/DiElectron/sensitivity/fitDiagnostics_reweight_categories/mu0"
BASEDIR=$PWD

# Parse command line arguments
TAG=""
TAG_LABEL="" # same but with _ in front
CATEGORY_TYPE="eta"  # Default to eta categories
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
        *)
            echo "Unknown argument: $1"
            echo "Usage: $0 [--tag TAG_VALUE] [--category eta|dR]"
            exit 1
            ;;
    esac
done

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

# Export functions and vars so parallel processes can use them
export -f get_category_name
export -f get_all_category_ids
export CATEGORY_TYPE

# take optional bool argument to only do plots
PLOT_ONLY=false
if [ "$1" == "--plots-only" ]; then
    PLOT_ONLY=true
    echo "Only generating plots, skipping FitDiagnostics runs."
fi

# Print configuration
echo "Configuration:"
echo "  Output folder: $OUTFOLDER"
echo "  Tag: ${TAG:-'(none)'}"
echo "  Category type: $CATEGORY_TYPE"
echo "  Categories: $(get_all_category_ids)"

# Create output folders for each category
for cat_id in $(get_all_category_ids); do
    cat_name=$(get_category_name "$cat_id")
    echo "Creating output folders $OUTFOLDER/$cat_name/s, b"
    mkdir -p $OUTFOLDER/$cat_name/s
    mkdir -p $OUTFOLDER/$cat_name/b
done

process_dir() {
    dir="$1"
    if [[ ! -d "$dir" ]]; then
        echo "Skipping $dir, not a directory"
        return
    fi

    if [[ ! "$dir" =~ ^cards/ee/[0-9]+(\.[0-9]+)?$ ]]; then
        echo "Skipping $dir, does not match expected format"
        return
    fi

    mass=$(basename "$dir")
    if (( $(echo "$mass < 2.2" | bc -l) )) || (( $(echo "$mass > 4.0" | bc -l) )); then #NOTE: nominally 2-4.2, but fits at the boundaries are unreliable
        echo "Skipping $dir, mass $mass is out of range (2 to 4.2)"
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
            echo "  Processing category $cat_id ($cat_name): $txt_file"
            echo $PLOT_ONLY

            if [ "$PLOT_ONLY" == false ]; then
                echo "    Running combine for category $cat_name"
                text2workspace.py "$txt_file"
                combine -M FitDiagnostics "$root_file" \
                        --saveNormalizations \
                        --saveShapes \
                        --setParameterRanges mass=2,4.2 \
                        --keepFailures \
                        -n "_${cat_name}" \
                        -v 3 &> "fitDiagnostics_${cat_name}.log"
                        # --preFitValue 0 \
                tail -n 10 "fitDiagnostics_${cat_name}.log"
                cp combine_logger.out "$OUTFOLDER/$cat_name/M$mass/combine_logger_fitDiagnostics_${cat_name}.out" 2>/dev/null || true

                # [FIXME] Temporary double, can be optimized
                # Also run a MultiDimFit to save a post-fit snapshot for B-only fit (serves as input for limits later)
                combine -M MultiDimFit "$root_file" \
                        --saveWorkspace \
                        --setParameters r=0 \
                        --freezeParameters r \
                        --setParameterRanges mass=2,4.2 \
                        -n "_${cat_name}_Bonly" \
                        -v 3 &> "fitMultiDimFit_Bonly_${cat_name}.log"
                cp combine_logger.out "$OUTFOLDER/$cat_name/M$mass/combine_logger_MultiDimFit_Bonly_${cat_name}.out" 2>/dev/null || true

                # Create category-specific output folder
                mkdir -p "$OUTFOLDER/$cat_name/M$mass"
                cp "fitDiagnostics_${cat_name}.log" "$txt_file" "fitDiagnostics_${cat_name}.root" higgsCombine_${cat_name}.FitDiagnostics.mH120.root higgsCombine_${cat_name}_Bonly.MultiDimFit.mH120.root fitMultiDimFit_Bonly_${cat_name}.log  "$OUTFOLDER/$cat_name/M$mass/"
            fi

            echo "    Plotting for category $cat_name"
            python3 $BASEDIR/scripts/draw_mu0_fit.py -i "$root_file" -f fitDiagnostics_${cat_name}.root -o "$OUTFOLDER/$cat_name" -m $mass -c $cat_id
        else
            echo "  $txt_file not found for category $cat_id ($cat_name)"
        fi
    done
    
    cd - || exit
}

export -f process_dir
export OUTFOLDER BASEDIR PLOT_ONLY

find cards/ee -mindepth 1 -maxdepth 1 -type d | parallel -j 8 process_dir {}

# Create summary plots for each category
for cat_id in $(get_all_category_ids); do
    cat_name=$(get_category_name "$cat_id")

    # Build the command with optional tag argument
    plot_cmd="python3 $BASEDIR/scripts/plot_diagnostics_result.py -o \"$OUTFOLDER/$cat_name\" -c $cat_name"
    if [[ -n "$TAG" ]]; then
        plot_cmd="$plot_cmd --tag \"$TAG\""
    fi
    
    # Execute the command
    echo "Creating summary plots for category $cat_name"
    eval "$plot_cmd" &> "$OUTFOLDER/$cat_name/limits_summary.log"
done