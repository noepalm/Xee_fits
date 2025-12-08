# python3 main_oo.py --full --delete_ws --use_reco_mass \
#                    --copy_eos --tag="withReweight_Categories" &> logs/log_reco_triggerReweight_Categories.log

python3 main_oo.py --full --delete_ws --use_reco_mass \
                   --copy_eos --tag="withReweight_Categories_nanov15" &> logs/log_reco_triggerReweight_Categories_nanov15.log

python3 main_oo.py --plots --use_reco_mass \
                   --copy_eos --tag="withReweight_Categories_nanov15"