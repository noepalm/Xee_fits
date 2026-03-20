#!/bin/bash
set -e
MASS=$1; LABEL=$2; INPUT_ROOT=$3; POINT=$4
FREEZE_PARAMS=$5; REGION=$6; USE_SB_SNAPSHOT=$7; FIT_TAG_LABEL=$8; WORK_DIR=$9

cd "$WORK_DIR"
source /cvmfs/cms.cern.ch/cmsset_default.sh
eval `scramv1 runtime -sh`

RMIN=0; RMAX=10
(( $(echo "$MASS > 9" | bc -l) )) && RMIN=1
(( $(echo "$MASS > 8.5" | bc -l) )) && RMAX=120

if [ "$USE_SB_SNAPSHOT" = "true" ]; then
    combine -M AsymptoticLimits "$INPUT_ROOT" --rMin $RMIN --rMax $RMAX \
            --snapshotName MultiDimFit --singlePoint "$POINT" \
            -n "_${LABEL}${FIT_TAG_LABEL}_point_${POINT}" -v 3
else
    combine -M AsymptoticLimits "$INPUT_ROOT" --rMin $RMIN --rMax $RMAX \
            --singlePoint "$POINT" -n "_${LABEL}${FIT_TAG_LABEL}_point_${POINT}" -v 3
fi
