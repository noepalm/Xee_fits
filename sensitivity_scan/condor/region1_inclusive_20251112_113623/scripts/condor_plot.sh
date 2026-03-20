#!/bin/bash
# DAGMan POST script to generate summary plots after all limit calculations complete

set -e

BASEDIR="/eos/home-n/npalmeri/DiEleAnalyzer/Xee_fits/sensitivity_scan"
OUTFOLDER="/eos/home-n/npalmeri/www/DiElectron/sensitivity/fitDiagnostics_grid_condortest_data_condor/mu0"
INPUT_FOLDER="/eos/home-n/npalmeri/DiEleAnalyzer/Xee_fits/sensitivity_scan/cards/cards_region1_data_condor"
REGION="region1"
FIT_TAG=""
FIT_TAG_LABEL=""
if [[ -n "$FIT_TAG" ]]; then
    FIT_TAG_LABEL="_$FIT_TAG"
fi

echo "=========================================="
echo "Generating summary plots..."
echo "=========================================="

echo "Creating summary plots for category inclusive"
python3 "$BASEDIR/scripts/plot_limits_result.py" -o "$OUTFOLDER/inclusive" -i "$INPUT_FOLDER" -c inclusive -r "$REGION" &> "$OUTFOLDER/inclusive/limits_summary_${REGION}${FIT_TAG_LABEL}.log"

echo "=========================================="
echo "Summary plots complete!"
echo "=========================================="
