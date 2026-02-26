#!/bin/bash

BASEDIR=$PWD

# Parse command line arguments
## appended to input, output folder names -- use when changing dataset
TAG=""
TAG_LABEL="" # same but with _ in front
## appended to output filenames only -- use when changing fit settings (e.g. freezing parameters)
FIT_TAG=""
FIT_TAG_LABEL="" # same but with _ in front
FOLDER_TAG=""
CATEGORY_TYPE="eta"  # Default to eta categories
REGION="region1"
INPUT_FOLDER="cards/cards"  # Default input folder
USE_REWEIGHT=true     # Default to using reweighting
PLOT_ONLY=false
FREEZE_JPSI=false
RUN_COMBINATION=false  # Default to individual categories
USE_SB_SNAPSHOT=false
USE_DATA=false
CACHING=true

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
        --folder_tag)
            FOLDER_TAG="$2/"
            INPUT_FOLDER="cards/${FOLDER_TAG}cards"
            shift # past argument
            shift # past value
            ;;
        --category|--cat)
            CATEGORY_TYPE="$2"
            if [[ "$CATEGORY_TYPE" != "eta" && "$CATEGORY_TYPE" != "dR" && "$CATEGORY_TYPE" != "inclusive" ]]; then
                echo "Error: Category type must be 'eta', 'dR' or 'inclusive'"
                echo "Usage: $0 [--tag TAG_VALUE] [--fit_tag FIT_TAG_VALUE] [--category eta|dR|inclusive] [--region region0|region1|region2] [--no_reweight] [--plot_only] [--freeze_jpsi] [--combination]"
                return 1
            fi
            shift # past argument
            shift # past value
            ;;
        --region)
            REGION="$2"
            if [[ "$REGION" != "region0" && "$REGION" != "region1" && "$REGION" != "region2" ]]; then
                echo "Error: Region must be region0, 1 or 2"
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
        --data)
            USE_DATA=true
            echo "Running on data instead of MC."
            shift # past argument
            ;;
        --freeze_jpsi)
            FREEZE_JPSI=true
            echo "Freezing J/psi scale parameter in fits."
            shift # past argument
            ;;
        --use_sb_snapshot)
            USE_SB_SNAPSHOT=true
            echo "Using S+B MultiDimFit snapshot as input for limits."
            shift # past argument
            ;;
        --combination)
            RUN_COMBINATION=true
            echo "Running combination of categories instead of individual fits."
            shift # past argument
            ;;
        --no_caching)
            CACHING=false
            echo "Disabling caching of grid points."
            shift # past argument
            ;;
        *)
            # Check if there are actually arguments to process
            if [[ -n "$1" ]]; then
                echo "Unknown argument: $1"
                echo "Usage: $0 [--tag TAG_VALUE] [--fit_tag FIT_TAG_VALUE] [--category eta|dR|inclusive] [--region region0|region1|region2] [--no_reweight] [--plot_only] [--freeze_jpsi] [--combination]"
                return 1
            else
                # No more arguments, break out of the loop
                break
            fi
            ;;
    esac
done

# Set input folder
INPUT_FOLDER="$INPUT_FOLDER"_"$REGION"

OUTFOLDER="/eos/home-n/npalmeri/www/DiElectron/sensitivity/${FOLDER_TAG}fitDiagnostics_grid"
if [ "$USE_DATA" = true ]; then
    OUTFOLDER="${OUTFOLDER}_data"
elif [ "$USE_REWEIGHT" = true ]; then
    OUTFOLDER="${OUTFOLDER}_reweight_categories"
else
    OUTFOLDER="${OUTFOLDER}_noReweight"
fi

if [ "$USE_DATA" = true ]; then
    INPUT_FOLDER="${INPUT_FOLDER}_data"
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
        MIN_MASS=0.3            # was 0.2
        MIN_MASS_LIMIT=0.5      # was 0.4
        MAX_MASS=2.4            # was 2.0
        MAX_MASS_LIMIT=2.2      # was 1.8
        ;;
    "region1")
        MIN_MASS=1.6            # was 2.0
        MIN_MASS_LIMIT=1.8      # was 2.2
        MAX_MASS=4.6            # was 4.2
        MAX_MASS_LIMIT=4.4      # was 4.0
        ;;
    "region2")
        MIN_MASS=3.8            # was 4.2
        MIN_MASS_LIMIT=4.0      # was 4.4
        MAX_MASS=11
        MAX_MASS_LIMIT=10.8
        ;;
    *)
        echo "Error: Region must be region0, 1 or 2"
        return 1
        ;;
esac

# Function to get points based on mass value and region
# Points are tuned per region for optimal scan resolution
get_points_for_mass() {
    local mass=$1
    local region=$2
    
    case "$region" in
        "region0")
            # # Region 0: 0-2.0 GeV
            # if (( $(echo "$mass >= 0.7 && $mass < 0.9" | bc -l) )); then
            #     echo "0.05 0.1 0.2 0.3 0.5 0.8 0.9 0.92 0.9 0.95 0.97 1 1.1 1.3 1.5 1.7 1.9 2 2.1 2.2 2.5 3 4 4.1 4.2 4.5 4.7 4.9 5 7 10 15 20"
            # elif (( $(echo "$mass >= 0.9 && $mass < 1.1" | bc -l) )); then
            #     echo "0.3 0.5 0.8 0.9 0.92 0.9 0.95 0.97 1 2 3 4 4.1 4.2 4.4 4.5 4.55 4.6 4.65 4.7 4.9 5 5.05 5.1 5.15 5.25 5.5 5.75 6 6.25 6.5 6.75 7 10 15 20"
            # elif (( $(echo "$mass >= 1.1 && $mass < 1.5" | bc -l) )); then
            #     echo "1 1.2 1.5 2 3 4 5 5.005 5.01 5.02 5.03 5.05 5.15 5.25 5.5 5.75 5.9 6 9 10"
            # elif (( $(echo "$mass < 0.7" | bc -l) )); then
            #     echo "0.9 0.925 0.93 0.94 0.95 0.965 0.975 0.98 0.99 1 1.05 1.1 1.2 1.25 1.27 1.28 1.29 1.3 1.31 1.325 1.35 1.375 1.4 1.45 1.5 2 3 4 4.5 5 5.5 6 9 10"
            # else
            #     echo "0.8 0.85 0.87 0.89 0.9 0.925 0.93 0.94 0.95 0.965 0.975 0.98 0.99 1 1.05 1.1 1.2 1.25 1.27 1.28 1.29 1.3 1.31 1.325 1.35 1.375 1.4 1.45 1.5 2 3 4 5 6 9 10"
            # fi

            # # THIS WORKS but gives weird results:
            # echo "0.001 0.005 0.007 0.01 0.02 0.05 0.07 0.1 0.2 0.5 0.8 0.85 0.9 0.925 0.95 0.975 0.98 0.99 1 1.1 1.25 1.3 1.5 1.75 2 3 4 5 6 9 10"

            # NEW ONE AFTER rMin = 0!
            # NOTE: for nanov15 w.o overlap, <0.6 worked
            if (( $(echo "$mass < 0.65" | bc -l) )); then
                echo "0.1 0.2 0.25 0.3 0.35 0.37 0.39 0.4 0.45 0.5 0.55 0.57 0.6 0.7 0.9 1 1.2 1.5 1.7 2 5 10"
            elif (( $(echo "$mass < 0.9" | bc -l) )); then
                echo "0.0005 0.001 0.002 0.0025 0.00275 0.003 0.0035 0.004 0.005 0.007 0.008 0.009 0.01 0.0125 0.015 0.0175 0.018 0.02 0.021 0.023 0.025 0.027 0.028 0.03 0.05 0.06 0.07 0.08 0.1 0.2 0.3 0.4 0.5 0.6 0.7 0.9 1"
            else
                echo "0.007 0.01 0.015 0.017 0.02 0.0225 0.025 0.03 0.035 0.04 0.045 0.05 0.55 0.06 0.065 0.07 0.08 0.09 0.1 0.11 0.12 0.13 0.15 0.16 0.17 0.19 0.2 0.21 0.23 0.25 0.27 0.29 0.3 0.32 0.33 0.34 0.35 0.37 0.39 0.4 0.41 0.42 0.43 0.45 0.5 0.55 0.57 0.6 0.62 0.65 0.7 0.8  0.9 1 1.25 1.5 2 5 10"
            fi
            ;;
        "region1")
            # Region 1: 2.0-4.2 GeV
            # For mass close to 3.1 (between 3.05 and 3.15), scan higher values
            if (( $(echo "$mass >= 3.05 && $mass <= 3.15" | bc -l) )); then
                # echo "1 1.5 1.7 1.9 2.1 2.3 2.5 2.7 3 3.1 3.3 3.5 3.7 3.9 4 4.1 4.2 4.3 4.4 4.5 4.6 4.7 4.8 4.9 5.0 5.1 5.15 5.17 5.18 5.19 5.2 5.3 5.4 5.5 5.7 5.75 5.8 5.85 5.9 5.95 6 6.1 6.25 6.3 6.5 6.75 10 15"
                # echo "1 1.5 2 2.5 3.5 4 4.2 4.3 4.6 4.7 5.1 5.4 6 7"
                # echo "5 5.1 5.2 5.3 5.4 5.5 6 6.5 7 7.5 8 8.5 9 10 15 20"
                # # just for testing (nanov15 overlap MC)
                # echo "0.005 0.01 0.05 0.1 0.5 1 2 3 4 5"
                # # DATA TESTING (reduced set)
                # echo "0.2 0.203 0.2035 0.204 0.2045 0.205 0.207 0.209 0.21 0.22 0.23 0.24 0.25 0.27 0.3 0.4 0.5 0.6 0.65 0.7 1 1.5 2 2.5 3.5 4 4.2 4.3 4.6 4.7 5.1 5.4 6 7"
                echo "0.01 0.03 0.05 0.1 0.2 0.3 0.4 0.5 0.6 0.7 1 1.5 2 2.5 3.5 4 4.2 4.3 4.6 4.7 5.1 5.4 6 7"
            elif (( $(echo "$mass >= 3.67 && $mass <= 3.73" | bc -l) )); then
                echo "0.01 0.025 0.05 0.075 0.1 0.15 0.2 0.25 0.27 0.3 0.35 0.4 0.5 0.9 1 10"
            else
                # otherwise, look at 10^-2 - 10^-1 range (uniform in log space)
                # TEMPORARY SHORT LIST FOR DEBUG
                echo "0.001 0.005 0.0100 0.0207 0.0336 0.0546 0.0886 0.1000 0.15 0.2 0.3 0.4 0.5 0.6 0.7 1 2.5 5"
                # echo "0.001 0.005 0.006 0.007 0.008 0.009 0.0100 0.0113 0.0127 0.0144 0.0162 0.0183 0.0207 0.0234 0.0264 0.0298 0.0336 0.0379 0.0428 0.0483 0.0546 0.0616 0.0695 0.0785 0.0886 0.1000 0.2 0.3 0.4 0.5 0.6 0.7 0.8 0.9 1 5 10 11 13 15 20"
                # echo "0.001 0.005 0.0100 0.0113 0.0183 0.0207 0.023 0.0428 0.0483 0.0886 0.1000 0.2 0.6 0.7"
                # echo "0.0183 0.0207 0.023 0.0428 0.0483 0.0886 0.1000 0.2 0.6 0.7 1 5 10"
            fi
            ;;
        "region2")
            # Region 2: 4.2-11.0 GeV
            if (( $(echo "$mass >= 7 && $mass < 7.5" | bc -l) )); then
                echo "0.0100 0.0113 0.0127 0.0144 0.0162 0.0183 0.0207 0.0234 0.0264 0.0298 0.0336 0.0379 0.0428 0.0483 0.0546 0.0616 0.0695 0.0785 0.0886 0.1000 0.2 0.3 0.4 0.5 0.6 0.7 0.8 0.9 1 2 3 5 7 10 12 15 17 20 25 30 35 40 50 60"
            elif (( $(echo "$mass >= 7.5 && $mass < 10" | bc -l) )); then
                #NEW! same as above before
                echo "0.0100 0.02 0.03 0.05 0.06 0.0785 0.0886 0.1000 0.2 0.3 0.4 0.5 0.6 0.7 0.8 0.9 1 2 3 5 7 10 12 15 17 20 25 30 35 40 50 60 70 80 90 100"
            # elif (( $(echo "$mass >= 8 && $mass < 9" | bc -l) )); then
            #     echo "0.01 0.02 0.05 0.1000 0.2 0.3 0.4 0.5 0.6 0.7 0.8 0.9 1 2 3 5 7 10 12 15 17 20 25 30 35 40 50 60"
            elif (( $(echo "$mass >= 10 && $mass < 12" | bc -l) )); then
                echo "0.5 0.7 0.9 1 2 3 4 5 5.5 6 7 7.5 8 8.5 9 10 12 15 17 20 25 30 35 40 50 60 70 80 90 100 105 110 115 120 130 140 150 160 170 180 190 200 210 220 230 240 250 280 300 350 400 450 500 550 600 650 700 750 800"
            else
                echo "0.001 0.005 0.006 0.007 0.008 0.009 0.0100 0.0113 0.0127 0.0144 0.0162 0.0183 0.0207 0.0234 0.0264 0.0298 0.0336 0.0379 0.0428 0.0483 0.0546 0.0616 0.0695 0.0785 0.0886 0.1000 0.2 0.3 0.6 0.8 1.2 1.8 2.5 3 3.5 4 4.5 5"
            fi
            ;;
        *)
            echo "ERROR: Unknown region $region" >&2
            return 1
            ;;
    esac
}

# echo "WARNING!! Temporarily dividing grid single points by 10 to run on 1/100 bkg sample. CHANGE BACK FOR PRODUCTION!"
# # TEMPORARY: Function to get points based on mass value DIVIDED BY 10 (for div100wgt sample)
# get_points_for_mass() {
#     local mass=$1
#     # For mass close to 3.1 (between 3.05 and 3.15), scan higher values
#     if (( $(echo "$mass >= 3.05 && $mass <= 3.15" | bc -l) )); then
#         echo "0.1 0.15 0.17 0.19 0.21 0.23 0.25 0.27 0.3 0.31 0.33 0.35 0.37 0.39 0.4 0.41 0.42 0.43 0.44 0.45 0.46 0.47 0.48 0.49 0.50 0.51 0.515 0.517 0.518 0.519 0.52 0.53 0.54 0.55 0.57 0.6 1.0 1.5"
#     elif (( $(echo "$mass >= 3.67 && $mass <= 3.73" | bc -l) )); then
#         echo "0.01 0.015 0.02 0.025 0.027 0.03 0.035 0.04 0.05"
#     else
#         # otherwise, look at 10^-2 - 10^-1 range (uniform in log space)
#         echo "0.00100 0.00113 0.00127 0.00144 0.00162 0.00183 0.00207 0.00234 0.00264 0.00298 0.00336 0.00379 0.00428 0.00483 0.00546 0.00616 0.00695 0.00785 0.00886 0.01000 0.02 0.03 0.04 0.05 0.06 0.07 0.08 0.09 0.1"
#     fi
# }

# Unified helper to run grid-based AsymptoticLimits for a target (category or combination)
# Snapshot usage matches original logic: snapshot is ONLY used when freezing parameters
# Args:
#   $1 = target label (e.g. etaHigh, etaLow, dRHigh, dRLow, inclusive, or etaCombination/dRCombination/inclusiveCombination)
#   $2 = input ROOT path to use (either workspace .root or MultiDimFit snapshot .root)
#   $3 = freeze_params (comma-separated) or empty; if non-empty, snapshot mode is enabled
#   $4 = mass (used to choose points and output folder)
run_combine_limits() {
    local label="$1"
    local input_root="$2"
    local freeze_params="$3"
    local mass="$4"

    # Build per-mass points list (region-specific)
    local points
    points=$(get_points_for_mass "$mass" "$REGION")

    # =============================================================
    # # ALTERNATIVE: SIMPLE AsymptoticLimits (no grid)
    # #
    # # Uncomment one of the blocks below and comment out the grid block
    # # further down if you want to run the classic single AsymptoticLimits
    # # instead of the grid + getLimitFromGrid workflow.
    #
    # if [[ -n "$freeze_params" ]]; then
    #     combine -M AsymptoticLimits "$input_root" --rMin 0 --rMax 20 \
    #             --snapshotName MultiDimFit \
    #             --freezeParameters "$freeze_params" \
    #             -n "_${label}${FIT_TAG_LABEL}" \
    #             -v 3 &> "fitAsymptotic_${label}${FIT_TAG_LABEL}.log"
    # else
    #     # OLD IMPLEMENTATION: uses original workspace
    #     combine -M AsymptoticLimits "$input_root" \
    #             -n "_${label}${FIT_TAG_LABEL}" \
    #             -v 3 &> "fitAsymptotic_${label}${FIT_TAG_LABEL}.log"
    
    #     # CAT TEST: use extra minimizer arguments (optional)
    #     # combine -M AsymptoticLimits "$input_root" \
    #     #         -n "_${label}${FIT_TAG_LABEL}" \
    #     #         --cminDefaultMinimizerStrategy 0 --cminFallbackAlgo Minuit2,Migrad,0:1.0 \
    #     #         --cminFallbackAlgo Minuit2,Migrad,1:1.0 --cminFallbackAlgo Minuit2,Migrad,0:5.0 \
    #     #         --cminApproxPreFitTolerance=100 --X-rtd MINIMIZER_MaxCalls=9999999 --X-rtd MINIMIZER_analytic \
    #     #         --X-rtd FAST_VERTICAL_MORPH --cminDefaultMinimizerPrecision 1E-8 \
    #     #         -v 3 &> "fitAsymptotic_${label}${FIT_TAG_LABEL}.log"
    # fi
    # =============================================================

    ### LIMIT FROM GRID
    # Single-point runs with caching

    # Adjust rMin/rMax for high mass points

    local rmin_val=0
    # if (( $(echo "$mass > 9.9" | bc -l) )); then
    #     rmin_val=0.5
    #     echo "    Setting rMin to $rmin_val for mass $mass"
    # fi

    local rmax_val=10 #was 1, 10, 40, 50
    if (( $(echo "$mass > 9.4" | bc -l) )); then # WAS 9.9
        # rmax_val=30
        rmax_val=150 # after trigger SF implemented, worse limits
        echo "    Setting rMax to $rmax_val for mass $mass"
    fi

    # local rmin_val=0
    # if (( $(echo "$mass > 9" | bc -l) )); then
    #     rmin_val=1
    #     echo "Setting rMin to $rmin_val for mass $mass"
    # fi

    # local rmax_val=10 #was 1, 10, 40, 50
    # if (( $(echo "$mass > 8.5" | bc -l) )); then
    #     rmax_val=120
    #     echo "Setting rMax to $rmax_val for mass $mass"
    # fi

    # if (( $(echo "$mass > 9" | bc -l) )); then
    #     rmax_val=300
    #     echo "Setting rMax to $rmax_val for mass $mass"
    # fi

    for point in $points; do
        local output_file="higgsCombine_${label}${FIT_TAG_LABEL}_point_${point}.AsymptoticLimits.mH120.root"
        if [ -f "$output_file" ] && [ "$CACHING" = true ]; then
            echo "    Point $point already exists for target $label, skipping..."
        else
            echo "    Running point $point for target $label... (rmin = $rmin_val, rmax = $rmax_val)"

            if [ "$USE_SB_SNAPSHOT" = true ]; then
                combine -M AsymptoticLimits "$input_root" --rMin $rmin_val --rMax $rmax_val \
                        --snapshotName MultiDimFit \
                        --singlePoint "$point" \
                        -n "_${label}${FIT_TAG_LABEL}_point_$point" \
                        -v 3 &> "fitAsymptotic_${label}${FIT_TAG_LABEL}_point_$point.log"
            else
                combine -M AsymptoticLimits "$input_root" --rMin $rmin_val --rMax $rmax_val \
                        --singlePoint "$point" \
                        -n "_${label}${FIT_TAG_LABEL}_point_$point" \
                        --cminDefaultMinimizerStrategy 0 \
                        -v 3 &> "fitAsymptotic_${label}${FIT_TAG_LABEL}_point_$point.log"
                        # --X-rtd MINIMIZER_freezeDisassociatedParams \
                        # --freezeParameters "mean_nuisance_electronScaleVariation" \
                        # --freezeParameters bb0=0 \
                        # --freezeParameters "sigma_nuisance,alphaR_nuisance,alphaL_nuisance,nR_nuisance,nL_nuisance"\
                        # --setParameters b0=-3.0,b1=3.3,b2=-1.4,b3=0.3,b4=-0.02 \
            fi
        fi

        # # Count background jobs and wait if we have 4 running
        # local job_count=$(jobs -r | wc -l)
        # if [ "$job_count" -ge 4 ]; then
        #     echo "    Waiting for batch of 4 jobs to complete..."
        #     wait -n  # Wait for next job to finish
        # fi

    done
    
    # echo "    Waiting for all remaining jobs to complete..."
    # wait  # Wait for all background jobs to finish

    # Merge grid and compute final limit from grid
    local grid_files=()
    for point in $points; do
        grid_files+=("higgsCombine_${label}${FIT_TAG_LABEL}_point_${point}.AsymptoticLimits.mH120.root")
    done
        
    hadd -f limits_from_grid_${label}.root "${grid_files[@]}"

    combine -M AsymptoticLimits "$input_root" --rMin $rmin_val --rMax $rmax_val \
            --getLimitFromGrid limits_from_grid_${label}.root \
            -n "_${label}${FIT_TAG_LABEL}" \
            -v 3 &> "fitAsymptotic_${label}${FIT_TAG_LABEL}.log"

    # =============================================================

    tail -n 10 "fitAsymptotic_${label}${FIT_TAG_LABEL}.log"

    # Ship outputs to outfolder
    mkdir -p "$OUTFOLDER/$label/M$mass"
    cp "fitAsymptotic_${label}${FIT_TAG_LABEL}.log" "higgsCombine_${label}${FIT_TAG_LABEL}.AsymptoticLimits.mH120.root" "$OUTFOLDER/$label/M$mass/"
    [ -f combine_logger.out ] && cp combine_logger.out "$OUTFOLDER/$label/M$mass/combine_logger_${label}${FIT_TAG_LABEL}.out"
}


# Export the functions so parallel processes can use them
export -f get_category_name
export -f get_category_label
export -f get_all_category_ids
export -f get_points_for_mass
export -f run_combine_limits
# Export the category type so parallel processes can access it
export CATEGORY_TYPE TAG_LABEL FIT_TAG_LABEL INPUT_FOLDER USE_REWEIGHT FREEZE_JPSI PLOT_ONLY RUN_COMBINATION REGION USE_SB_SNAPSHOT USE_DATA CACHING
export MIN_MASS MIN_MASS_LIMIT MAX_MASS MAX_MASS_LIMIT

# Print configuration
echo "Configuration:"
echo "  Use data: $USE_DATA"
echo "  Use reweighting: $USE_REWEIGHT"
echo "  Input folder: $INPUT_FOLDER"
echo "  Output folder: $OUTFOLDER"
echo "  Tag: ${TAG:-'(none)'}"
echo "  Category type: $CATEGORY_TYPE"
echo "  Categories: $(get_all_category_ids)"
echo "  Region: $REGION (mass min: $MIN_MASS [limit from $MIN_MASS_LIMIT], max: $MAX_MASS [limit up to $MAX_MASS_LIMIT])"
echo "  Plot only: $PLOT_ONLY"
echo "  Run combination: $RUN_COMBINATION"
echo "  Caching grid points?: $CACHING"

# Create output folders for each category
if [ "$RUN_COMBINATION" = true ]; then
    echo "Creating output folders $OUTFOLDER/${CATEGORY_TYPE}Combination/s, b"
    mkdir -p $OUTFOLDER/${CATEGORY_TYPE}Combination/s
    mkdir -p $OUTFOLDER/${CATEGORY_TYPE}Combination/b
else
    for cat_id in $(get_all_category_ids); do
        cat_name=$(get_category_name "$cat_id")
        echo "Creating output folders $OUTFOLDER/$cat_name/s, b"
        mkdir -p $OUTFOLDER/$cat_name/s
        mkdir -p $OUTFOLDER/$cat_name/b
    done
fi

# copy input .root file
cp $INPUT_FOLDER/ee/common/Xee_ee.input.root $OUTFOLDER/Xee_ee.input.${REGION}.root

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


    # # TEMPORARY: run only on 3.1
    # if (( $(echo "$mass != 3.1" | bc -l) )); then
    #     echo "Skipping $dir, mass $mass is not 3.1 (TEMPORARY)"
    #     return
    # fi    

    # # TEMPORARY: run only on 2.7 (region2 failing point)
    # if (( $(echo "$mass != 2.7" | bc -l) )); then
    #     echo "Skipping $dir, mass $mass is not 3.1 (TEMPORARY)"
    #     return
    # fi    

    # # TEMPORARY: run only on 5.0 (region2 failing point)
    # if (( $(echo "$mass != 0.5" | bc -l) )); then
    #     echo "Skipping $dir, mass $mass is not 3.1 (TEMPORARY)"
    #     return
    # fi    

    # if (( $(echo "$mass > 3.1" | bc -l) )); then
    #     echo "Skipping $dir, mass $mass is not in [2.4, 3.0] range (TEMPORARY)"
    #     return
    # fi

    if (( $(echo "$mass < 9.3" | bc -l) )); then
        echo "Skipping $dir, mass $mass is not below 10 (TEMPORARY)"
        return
    fi


    echo "Processing directory: $dir"

    # If only plotting is requested, skip running combine jobs here
    if [ "$PLOT_ONLY" == true ]; then
        return
    fi

    # Operate in the mass directory and return when done
    pushd "$dir" > /dev/null || { echo "Failed to cd into $dir"; return 1; }

    if [ "$RUN_COMBINATION" = true ]; then
        # Build combination datacard by combining category datacards with the expected names
        # Exactly match naming in run_limits_combination_parallel.sh
        local card_files=()
        for cat_id in $(get_all_category_ids); do
            local card_name="Xee_ee_${cat_id}_2023.txt"
            if [[ -f "$card_name" ]]; then
                card_files+=("$card_name")
            else
                echo "  Warning: missing datacard $card_name at mass ${mass}; skipping this directory"
                popd > /dev/null; return
            fi
        done

        local txt_file="Xee_ee_${CATEGORY_TYPE}Combination_2023.txt"
        local root_file="Xee_ee_${CATEGORY_TYPE}Combination_2023.root"
        echo "  Combining the categories into ${txt_file}"
        combineCards.py "${card_files[@]}" > "$txt_file"

        # echo "  Building workspace: ${root_file}"
        # text2workspace.py "$txt_file"

        local freeze_params=""
        local input_root="$root_file"
        if [ "$FREEZE_JPSI" = true ]; then
            echo "  Running MultiDimFit (B-only snapshot) for ${CATEGORY_TYPE} combination"
            combine -M MultiDimFit "$root_file" \
                    --saveWorkspace \
                    --setParameters r=0 \
                    --freezeParameters r \
                    -n "_${CATEGORY_TYPE}Combination_Bonly${FIT_TAG_LABEL}" \
                    -v 3 &> "fitMultiDimFit_Bonly_${CATEGORY_TYPE}Combination${FIT_TAG_LABEL}.log"

            # Freeze J/psi scale parameters for all categories in this combination
            local freeze_list=()
            for cid in $(get_all_category_ids); do
                local cname
                cname=$(get_category_name "$cid")
                freeze_list+=("scale_jpsi_$(get_category_label "$cname")")
            done
            freeze_params=$(IFS=,; echo "${freeze_list[*]}")
            input_root="higgsCombine_${CATEGORY_TYPE}Combination_Bonly${FIT_TAG_LABEL}.MultiDimFit.mH120.root"
        fi

        run_combine_limits "${CATEGORY_TYPE}Combination" "$input_root" "$freeze_params" "$mass"
    else
        # Per-category loop
        for cat_id in $(get_all_category_ids); do
            local cat_name
            cat_name=$(get_category_name "$cat_id")
            txt_file="Xee_ee_${cat_id}_2023.txt"
            root_file="Xee_ee_${cat_id}_2023.root"

            if [[ -z "$txt_file" ]]; then
                echo "  $txt_file not found for category $cat_id ($cat_name)"
                continue
            fi

            echo "  Processing category $cat_id ($cat_name): $txt_file"
            echo "    Running AsymptoticLimits for category $cat_name"
            # text2workspace.py "$txt_file"

            if [[ -z "$root_file" ]]; then
                echo "  $root_file not found for category $cat_id ($cat_name)"
                continue
            fi

            local freeze_params=""
            local input_root="$root_file"
            if [ "$FREEZE_JPSI" = true ]; then
                echo "    Running MultiDimFit (B-only snapshot) for ${cat_name}"
                combine -M MultiDimFit "$root_file" \
                        --saveWorkspace \
                        --setParameters r=0 \
                        --freezeParameters r \
                        -n "_${cat_name}_Bonly${FIT_TAG_LABEL}" \
                        -v 3 &> "fitMultiDimFit_Bonly_${cat_name}${FIT_TAG_LABEL}.log"

                freeze_params="scale_jpsi_$(get_category_label "$cat_name")"
                input_root="higgsCombine_${cat_name}_Bonly${FIT_TAG_LABEL}.MultiDimFit.mH120.root"
            fi

            if [ "$USE_SB_SNAPSHOT" = true ]; then
                echo "    Using sideband snapshot for category ${cat_name}"                            
                input_root="higgsCombine_${cat_name}${FIT_TAG_LABEL}_SB.MultiDimFit.mH120.root"
            fi

            run_combine_limits "$cat_name" "$input_root" "$freeze_params" "$mass"
        done
    fi

    popd > /dev/null || exit
}

export -f process_dir
export OUTFOLDER BASEDIR PLOT_ONLY INPUT_FOLDER USE_REWEIGHT

find $INPUT_FOLDER/ee -mindepth 1 -maxdepth 1 -type d | \
    parallel --jobs 8 process_dir {}

# produce summary plots 
if [ "$RUN_COMBINATION" = true ]; then
    echo "Creating summary plots for ${CATEGORY_TYPE} combination"
    plot_cmd="python3 $BASEDIR/scripts/plot_limits_result.py -o \"$OUTFOLDER/${CATEGORY_TYPE}Combination\" -i \"$INPUT_FOLDER\" -c ${CATEGORY_TYPE}Combination -r $REGION" 
    if [[ -n "$FIT_TAG" ]]; then
        plot_cmd="$plot_cmd --tag \"$FIT_TAG\""
    fi

    # Execute the command
    eval "$plot_cmd" &> "$OUTFOLDER/${CATEGORY_TYPE}Combination/limits_summary_${REGION}${FIT_TAG_LABEL}.log"
else
    for cat_id in $(get_all_category_ids); do
        cat_name=$(get_category_name "$cat_id")
        echo "Creating summary plots for category $cat_name (log file: limits_summary_${REGION}${FIT_TAG_LABEL}.log)"
        
        # Build the command with optional tag argument
        plot_cmd="python3 $BASEDIR/scripts/plot_limits_result.py -o \"$OUTFOLDER/$cat_name\" -i \"$INPUT_FOLDER\" -c $cat_name -r $REGION"
        if [[ -n "$FIT_TAG" ]]; then
            plot_cmd="$plot_cmd --tag \"$FIT_TAG\""
        fi

        echo $plot_cmd
        
        # Execute the command
        eval "$plot_cmd" &> "$OUTFOLDER/$cat_name/limits_summary_${REGION}${FIT_TAG_LABEL}.log"
    done
fi

# copy script itself to output folder
cp "$BASEDIR/scripts/run_limits_parallel.sh" "$OUTFOLDER/limits_script.sh"