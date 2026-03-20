#!/bin/bash

OUTFOLDER="/eos/home-n/npalmeri/www/DiElectron/sensitivity/fitDiagnostics_reweight/mu10"
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
        echo "Running FitDiagnostics with injected signal on Xee_ee_0_2023.txt"
        text2workspace.py Xee_ee_0_2023.txt

        # inject signal into the workspace
        python3 $BASEDIR/scripts/inject_signal.py -i Xee_ee_0_2023.root -m $mass --mu 10 -o Xee_ee_0_2023_injected_mu10.root

        combine -M FitDiagnostics Xee_ee_0_2023_injected_mu10.root \
            --saveNormalizations \
            --saveShapes \
            --setParameterRanges mass=2,4.2 \
            --keepFailures \
            --skipBOnlyFit \
            -n .injectedSignal_mu10 \
            -v 1 &> fitDiagnostics_injectedSignal_mu10.log;
            # --preFitValue 1 \

        # make output folder
        mkdir -p $OUTFOLDER/M$mass
        cp $OUTFOLDER/index.php $OUTFOLDER/M$mass/

        # copy output
        # cp fitDiagnostics_injectedSignal_mu10.log fitDiagnostics.injectedSignal_mu10.root higgsCombine.injectedSignal_mu10.FitDiagnostics.mH120.123456.root $OUTFOLDER/M$mass/
        cp fitDiagnostics_injectedSignal_mu10.log fitDiagnostics.injectedSignal_mu10.root higgsCombine.injectedSignal_mu10.FitDiagnostics.mH120.root $OUTFOLDER/M$mass/
        cp combine_logger.out $OUTFOLDER/M$mass/combine_logger_fitDiagnostics_injectedSignal_mu10.out

        python3 $BASEDIR/scripts/draw_mu1_fit.py -i Xee_ee_0_2023_injected_mu10.root -d Xee_ee_0_2023.root -f fitDiagnostics.injectedSignal_mu10.root -o $OUTFOLDER -m $mass 
        # python3 $BASEDIR/scripts/draw_mu1_fit.py -i higgsCombine.injectedSignal.FitDiagnostics.mH120.123456.root -d Xee_ee_0_2023.root -f fitDiagnostics.injectedSignal.root -o $OUTFOLDER -m $mass 
    else
        echo "Xee_ee_0_2023.txt not found in $dir"
    fi
    cd - || exit
}

export -f process_dir
export OUTFOLDER BASEDIR

find cards/ee -mindepth 1 -maxdepth 1 -type d | parallel --will-cite -j 8 process_dir {}

# produce summary plots
python3 $BASEDIR/scripts/plot_diagnostics_result.py -o $OUTFOLDER -m 10