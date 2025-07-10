#!/bin/bash

OUTFOLDER="/eos/home-n/npalmeri/www/DiElectron/sensitivity/fitDiagnostics_reweight/mu0"
BASEDIR=$PWD

# take optional bool argument to only do plots
PLOT_ONLY=false
if [ "$1" == "--plots-only" ]; then
    PLOT_ONLY=true
    echo "Only generating plots, skipping FitDiagnostics runs."
fi

mkdir -p $OUTFOLDER/s
mkdir -p $OUTFOLDER/b
cp $OUTFOLDER/index.php $OUTFOLDER/s/
cp $OUTFOLDER/index.php $OUTFOLDER/b/

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
    if (( $(echo "$mass < 2" | bc -l) )) || (( $(echo "$mass > 4.2" | bc -l) )); then
        echo "Skipping $dir, mass $mass is out of range (2 to 4.2)"
        return
    fi

    echo "Processing directory: $dir"
    cd "$dir" || return
    if [ -f Xee_ee_0_2023.txt ]; then
        echo "Running FitDiagnostics on Xee_ee_0_2023.txt"
        echo "   Running combine"
        text2workspace.py Xee_ee_0_2023.txt
        combine -M FitDiagnostics Xee_ee_0_2023.root \
            --saveNormalizations \
            --saveShapes \
            --setParameterRanges mass=2,4.2 \
            --keepFailures \
            -v 1 &> fitDiagnostics.log
            # --preFitValue 0 \
        tail -n 10 fitDiagnostics.log

        mkdir -p $OUTFOLDER/M$mass
        cp $OUTFOLDER/index.php $OUTFOLDER/M$mass/
        cp fitDiagnostics.log Xee_ee_0_2023.txt fitDiagnosticsTest.root higgsCombineTest.FitDiagnostics.mH120.root $OUTFOLDER/M$mass/
        cp combine_logger.out $OUTFOLDER/M$mass/combine_logger_fitDiagnostics.out

        echo "   Plotting"
        python3 $BASEDIR/scripts/draw_mu0_fit.py -i Xee_ee_0_2023.root -f fitDiagnosticsTest.root -o $OUTFOLDER -m $mass 
    else
        echo "Xee_ee_0_2023.txt not found in $dir"
    fi
    cd - || exit
}

export -f process_dir
export OUTFOLDER BASEDIR

find cards/ee -mindepth 1 -maxdepth 1 -type d | parallel -j 8 process_dir {}

# produce summary plots
python3 $BASEDIR/scripts/plot_diagnostics_result.py -o $OUTFOLDER