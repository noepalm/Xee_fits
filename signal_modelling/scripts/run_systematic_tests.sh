# FIRST TEST WITH NUISANCE PARAMETERS
time python3 main_oo.py --full --delete_ws --use_reco_mass \
                   --no_categories --syst \
                   --copy_eos --tag="nanov15_withSyst_nuisanceTest" &> logs/log_reco_nanov15_withSyst_nuisanceTest.log
time python3 main_oo.py --plots --use_reco_mass \
                   --no_categories --syst \
                   --copy_eos --tag="nanov15_withSyst_nuisanceTest" &> logs/log_reco_nanov15_withSyst_nuisanceTest_plotting.log

# NUISANCE TEST WITH FULL UNCERTAINTY
time python3 main_oo.py --full --delete_ws --use_reco_mass \
                   --no_categories --syst \
                   --copy_eos --tag="nanov15_withSyst_nuisanceTest_final" &> logs/log_reco_nanov15_withSyst_nuisanceTest_final.log
time python3 main_oo.py --plots --use_reco_mass \
                   --no_categories --syst \
                   --copy_eos --tag="nanov15_withSyst_nuisanceTest_final" &> logs/log_reco_nanov15_withSyst_nuisanceTest_final_plotting.log

# NUISANCE TEST WITH M10, w/o inflated uncertainty
time python3 main_oo.py --full --delete_ws --use_reco_mass \
                   --no_categories --syst \
                   --copy_eos --tag="nanov15_withSyst_nuisanceTest" &> logs/log_reco_nanov15_withSyst_nuisanceTest_withM10.log
time python3 main_oo.py --plots --use_reco_mass \
                   --no_categories --syst \
                   --copy_eos --tag="nanov15_withSyst_nuisanceTest" &> logs/log_reco_nanov15_withSyst_nuisanceTest_withM10_plotting.log

# NUISANCE TEST WITH FULL UNCERTAINTY WITH M10
time python3 main_oo.py --full --delete_ws --use_reco_mass \
                   --no_categories --syst \
                   --copy_eos --tag="nanov15_withSyst_nuisanceTest_final_withM10" &> logs/log_reco_nanov15_withSyst_nuisanceTest_final_withM10.log
time python3 main_oo.py --plots --use_reco_mass \
                   --no_categories --syst \
                   --copy_eos --tag="nanov15_withSyst_nuisanceTest_final_withM10" &> logs/log_reco_nanov15_withSyst_nuisanceTest_final_withM10_plotting.log

# NUISANCE TEST WITH FULL UNCERTAINTY WITH M10, SIGMA ONLY
time python3 main_oo.py --full --delete_ws --use_reco_mass \
                   --no_categories --syst \
                   --copy_eos --tag="nanov15_withSyst_nuisanceTest_final_withM10_sigmaonly" &> logs/log_reco_nanov15_withSyst_nuisanceTest_final_withM10_sigmaonly.log
time python3 main_oo.py --plots --use_reco_mass \
                   --no_categories --syst \
                   --copy_eos --tag="nanov15_withSyst_nuisanceTest_final_withM10_sigmaonly" &> logs/log_reco_nanov15_withSyst_nuisanceTest_final_withM10_sigmaonly_plotting.log

## NO M10
time python3 main_oo.py --full --delete_ws --use_reco_mass \
                   --no_categories --syst \
                   --copy_eos --tag="nanov15_withSyst_noM10" &> logs/log_reco_nanov15_withSyst_noM10.log

time python3 main_oo.py --plots --use_reco_mass \
                   --no_categories --syst \
                   --copy_eos --tag="nanov15_withSyst" &> logs/log_reco_nanov15_withSyst_plotting.log

python3 main_oo.py --plots --use_reco_mass \
                   --copy_eos --tag="nanov15_withSyst"
