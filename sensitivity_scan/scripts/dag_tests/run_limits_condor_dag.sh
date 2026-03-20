#!/bin/bash

# HTCondor DAGMan-based parallelization for AsymptoticLimits grid computation
# This version uses DAGMan to properly handle job dependencies

BASEDIR=$PWD

# Parse command line arguments (same as before)
TAG=""
TAG_LABEL=""
FIT_TAG=""
FIT_TAG_LABEL=""
CATEGORY_TYPE="eta"
REGION="region1"
INPUT_FOLDER="cards"
USE_REWEIGHT=true
FREEZE_JPSI=false
RUN_COMBINATION=false
USE_SB_SNAPSHOT=false
USE_DATA=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --tag) TAG="$2"; TAG_LABEL="_$TAG"; shift 2 ;;
        --fit_tag) FIT_TAG="$2"; FIT_TAG_LABEL="_$FIT_TAG"; shift 2 ;;
        --category|--cat) CATEGORY_TYPE="$2"; shift 2 ;;
        --region) REGION="$2"; shift 2 ;;
        --no_reweight) INPUT_FOLDER="cards_noReweight"; USE_REWEIGHT=false; shift ;;
        --data) USE_DATA=true; shift ;;
        --freeze_jpsi) FREEZE_JPSI=true; shift ;;
        --use_sb_snapshot) USE_SB_SNAPSHOT=true; shift ;;
        --combination) RUN_COMBINATION=true; shift ;;
        *) echo "Unknown argument: $1"; exit 1 ;;
    esac
done

# Set input/output folders
INPUT_FOLDER="${INPUT_FOLDER}_${REGION}"
OUTFOLDER="/eos/home-n/npalmeri/www/DiElectron/sensitivity/fitDiagnostics_grid"

if [ "$USE_DATA" = true ]; then
    OUTFOLDER="${OUTFOLDER}_data"
    INPUT_FOLDER="${INPUT_FOLDER}_data"
elif [ "$USE_REWEIGHT" = true ]; then
    OUTFOLDER="${OUTFOLDER}_reweight_categories"
else
    OUTFOLDER="${OUTFOLDER}_noReweight"
fi

if [[ "$TAG" != "" ]]; then
    INPUT_FOLDER="${INPUT_FOLDER}_${TAG}"
    OUTFOLDER="${OUTFOLDER}_${TAG}"
fi

OUTFOLDER="${OUTFOLDER}/mu0"

# Create directories
CONDOR_LOGS="$OUTFOLDER/condor_logs"
CONDOR_DAGS="$OUTFOLDER/condor_dags"
mkdir -p "$CONDOR_LOGS" "$CONDOR_DAGS"

# Mass range
case "$REGION" in
    "region0") MIN_MASS_LIMIT=0.5; MAX_MASS_LIMIT=2.2 ;;
    "region1") MIN_MASS_LIMIT=1.8; MAX_MASS_LIMIT=4.4 ;;
    "region2") MIN_MASS_LIMIT=4.0; MAX_MASS_LIMIT=10.8 ;;
esac

echo "HTCondor DAGMan Submission"
echo "  Region: $REGION"
echo "  Input: $INPUT_FOLDER"
echo "  Output: $OUTFOLDER"
echo "  DAG files: $CONDOR_DAGS"

# Source helper functions
source $BASEDIR/scripts/run_limits_parallel.sh --help 2>/dev/null || true

# Create worker script (same as before)
WORKER_SCRIPT="$OUTFOLDER/condor_worker.sh"
cat > "$WORKER_SCRIPT" << 'EOF'
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
EOF
chmod +x "$WORKER_SCRIPT"

# Create merge script
MERGE_SCRIPT="$OUTFOLDER/condor_merge.sh"
cat > "$MERGE_SCRIPT" << 'EOF'
#!/bin/bash
set -e
MASS=$1; LABEL=$2; INPUT_ROOT=$3; REGION=$4; FIT_TAG_LABEL=$5; WORK_DIR=$6; POINTS="$7"

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
EOF
chmod +x "$MERGE_SCRIPT"

# Create DAG file for each mass point
create_dag_for_mass() {
    local mass=$1
    local work_dir="$INPUT_FOLDER/ee/$mass"
    
    [ ! -d "$work_dir" ] && return
    (( $(echo "$mass < $MIN_MASS_LIMIT || $mass > $MAX_MASS_LIMIT" | bc -l) )) && return
    
    local dag_file="$CONDOR_DAGS/limits_M${mass}.dag"
    echo "# DAG for mass $mass" > "$dag_file"
    
    local points=$(get_points_for_mass "$mass" "$REGION")
    
    # Process categories
    local categories=()
    if [ "$RUN_COMBINATION" = true ]; then
        categories=("${CATEGORY_TYPE}Combination")
    else
        for cat_id in $(get_all_category_ids); do
            categories+=("$(get_category_name "$cat_id")")
        done
    fi
    
    for label in "${categories[@]}"; do
        local root_file="$work_dir/Xee_ee_${label}_2023.root"
        [ ! -f "$root_file" ] && continue
        
        local jdl_base="$CONDOR_DAGS/${label}_M${mass}"
        
        # Create JDL for grid point jobs
        cat > "${jdl_base}_grid.jdl" << JDL_EOF
executable = $WORKER_SCRIPT
arguments = $mass $label $root_file \$(Point) "" $REGION $USE_SB_SNAPSHOT $FIT_TAG_LABEL $work_dir
output = $CONDOR_LOGS/grid_${label}_M${mass}_\$(Point).out
error = $CONDOR_LOGS/grid_${label}_M${mass}_\$(Point).err
log = $CONDOR_LOGS/grid_${label}_M${mass}.log
+JobFlavour = "longlunch"
queue Point from (
JDL_EOF
        for point in $points; do
            echo "$point" >> "${jdl_base}_grid.jdl"
        done
        echo ")" >> "${jdl_base}_grid.jdl"
        
        # Create JDL for merge job
        cat > "${jdl_base}_merge.jdl" << MERGE_JDL_EOF
executable = $MERGE_SCRIPT
arguments = $mass $label $root_file $REGION $FIT_TAG_LABEL $work_dir "$points"
output = $CONDOR_LOGS/merge_${label}_M${mass}.out
error = $CONDOR_LOGS/merge_${label}_M${mass}.err
log = $CONDOR_LOGS/merge_${label}_M${mass}_merge.log
+JobFlavour = "espresso"
queue 1
MERGE_JDL_EOF
        
        # Add to DAG with dependencies
        echo "" >> "$dag_file"
        echo "# Category: $label" >> "$dag_file"
        
        # Define grid jobs
        for point in $points; do
            local job_name="grid_${label}_${point}"
            echo "JOB $job_name ${jdl_base}_grid.jdl" >> "$dag_file"
            echo "VARS $job_name Point=\"$point\"" >> "$dag_file"
        done
        
        # Define merge job
        local merge_job="merge_${label}"
        echo "JOB $merge_job ${jdl_base}_merge.jdl" >> "$dag_file"
        
        # Set up dependencies: merge depends on all grid jobs
        echo -n "PARENT " >> "$dag_file"
        for point in $points; do
            echo -n "grid_${label}_${point} " >> "$dag_file"
        done
        echo "CHILD $merge_job" >> "$dag_file"
    done
    
    echo "Created DAG: $dag_file"
    condor_submit_dag "$dag_file"
}

# Submit DAGs for all masses
for dir in $INPUT_FOLDER/ee/*; do
    if [ -d "$dir" ]; then
        mass=$(basename "$dir")
        create_dag_for_mass "$mass"
    fi
done

echo ""
echo "DAG submission complete!"
echo "Monitor with: condor_q"
echo "DAG files in: $CONDOR_DAGS"
echo "Logs in: $CONDOR_LOGS"
