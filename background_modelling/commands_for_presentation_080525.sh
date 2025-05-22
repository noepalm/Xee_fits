python3 bkg_test.py --fit_region="unblinded" --tag="signalModel" &> log
python3 bkg_test.py --fit_region="unblinded" --use_reduced_mass --tag="signalModel" &> log
python3 bkg_test.py --fit_region="unblinded" --floating_signal --freeze_bkg_sidebands --tag="frozenBkgOnSidebands" &> log
python3 bkg_test.py --fit_region="unblinded" --floating_signal --tag="allFree" &> log

python3 bkg_test.py --fit_region="bkg_left" &> log
python3 bkg_test.py --fit_region="bkg_right" &> log