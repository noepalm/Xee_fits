#!/bin/bash
set -e
MASS=$1; LABEL=$2; INPUT_ROOT=$3; REGION=$4; FIT_TAG_LABEL=$5; WORK_DIR=$6; POINTS="$7"; PLOT_DIR=$8

cd "$WORK_DIR"
source /cvmfs/cms.cern.ch/cmsset_default.sh
eval `scramv1 runtime -sh`

GRID_FILES=()
for point in $POINTS; do
    GRID_FILES+=("higgsCombine_${LABEL}${FIT_TAG_LABEL}_point_${point}.AsymptoticLimits.mH120.root")
done

hadd -f limits_from_grid_${LABEL}.root "${GRID_FILES[@]}"

RMIN=0; RMAX=10
(( $(echo "$MASS > 9" | bc -l) )) && RMIN=1
(( $(echo "$MASS > 8.5" | bc -l) )) && RMAX=120

combine -M AsymptoticLimits "$INPUT_ROOT" --rMin $RMIN --rMax $RMAX \
        --getLimitFromGrid limits_from_grid_${LABEL}.root \
        -n "_${LABEL}${FIT_TAG_LABEL}" -v 3

# Copy final limit results to plot directory
mkdir -p "$PLOT_DIR/$LABEL/M$MASS"
cp "fitAsymptotic_${LABEL}${FIT_TAG_LABEL}.log"            "higgsCombine_${LABEL}${FIT_TAG_LABEL}.AsymptoticLimits.mH120.root"            "$PLOT_DIR/$LABEL/M$MASS/"
[ -f combine_logger.out ] && cp combine_logger.out "$PLOT_DIR/$LABEL/M$MASS/combine_logger_${LABEL}${FIT_TAG_LABEL}.out"

echo "Results copied to $PLOT_DIR/$LABEL/M$MASS/"
