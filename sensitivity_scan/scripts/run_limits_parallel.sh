#!/bin/bash

OUTFOLDER="/eos/home-n/npalmeri/www/DiElectron/sensitivity/fitDiagnostics_reweight/mu0"
BASEDIR=$PWD

mkdir -p $OUTFOLDER/s
mkdir -p $OUTFOLDER/b
cp $OUTFOLDER/index.php $OUTFOLDER/s/
cp $OUTFOLDER/index.php $OUTFOLDER/b/

process_dir() {
    dir="$1"

    # check folder format -- should be cards/ee/<mass>
    if [[ ! "$dir" =~ ^cards/ee/[0-9]+(\.[0-9]+)?$ ]]; then
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
    if [ -f Xee_ee_0_2023.txt ]; then
        echo "Running AsymptoticLimits on Xee_ee_0_2023.txt"
        text2workspace.py Xee_ee_0_2023.txt
        combine -M AsymptoticLimits Xee_ee_0_2023.root --rMin 0 --rMax 1 \
                -n .AsymptoticLimit \
                -v 3 &> fitAsymptotic.log
        tail -n 10 fitAsymptotic.log
        mkdir -p $OUTFOLDER/M$mass
        cp fitAsymptotic.log higgsCombine.AsymptoticLimit.AsymptoticLimits.mH120.root $OUTFOLDER/M$mass/
        [ -f combine_logger.out ] && cp combine_logger.out $OUTFOLDER/M$mass/combine_logger_AsymptoticLimit.out
    else
        echo "Xee_ee_0_2023.txt not found in $dir"
    fi
    cd - > /dev/null || exit
}

export -f process_dir
export OUTFOLDER BASEDIR

find cards/ee -mindepth 1 -maxdepth 1 -type d | \
    parallel --jobs 8 process_dir {}


# produce summary plots
python3 $BASEDIR/scripts/plot_limits_result.py -o $OUTFOLDER &> $OUTFOLDER/limits_summary.log