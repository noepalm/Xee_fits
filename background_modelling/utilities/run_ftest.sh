# --------------------------------------------- #
# -------------- 10% DATA F-TEST -------------- #
# --------------------------------------------- #

# echo "######### F-test: bernstein #########"
# python3 utilities/plot_ftest_result.py \
#   --family bernstein \
#   --orders 4,5,6,7 \
#   --input-folder datasets/260327/2022 \
#   --output-folder /eos/home-n/npalmeri/www/DiElectron/background_model/260327/2022 \
#   --era 2022

# echo "######### F-test: chebyshev #########"
# python3 utilities/plot_ftest_result.py \
#   --family chebyshev \
#   --orders 4,5,6 \
#   --input-folder datasets/260327/2022 \
#   --output-folder /eos/home-n/npalmeri/www/DiElectron/background_model/260327/2022 \
#   --era 2022

# echo "######### F-test: polyexp #########"
# python3 utilities/plot_ftest_result.py \
#   --family polyexp \
#   --orders 4,5,6,7 \
#   --input-folder datasets/260327/2022 \
#   --output-folder /eos/home-n/npalmeri/www/DiElectron/background_model/260327/2022 \
#   --era 2022

# echo "######### F-test: bernstein #########"
# python3 utilities/plot_ftest_result.py \
#   --family bernstein \
#   --orders 4,5,6,7 \
#   --input-folder datasets/260603/2022 \
#   --output-folder /eos/home-n/npalmeri/www/DiElectron/background_model/260603/2022 \
#   --era 2022

# echo "######### F-test: chebyshev #########"
# python3 utilities/plot_ftest_result.py \
#   --family chebyshev \
#   --orders 4,5,6 \
#   --input-folder datasets/260603/2022 \
#   --output-folder /eos/home-n/npalmeri/www/DiElectron/background_model/260603/2022 \
#   --era 2022

# echo "######### F-test: polyexp #########"
# python3 utilities/plot_ftest_result.py \
#   --family polyexp \
#   --orders 4,5,6,7 \
#   --input-folder datasets/260603/2022 \
#   --output-folder /eos/home-n/npalmeri/www/DiElectron/background_model/260603/2022 \
#   --era 2022  

# ---------------------------------------------- #
# -------------- 100% DATA F-TEST -------------- #
# ---------------------------------------------- #

# echo "######### F-test: bernstein #########"
# for era in 2022 2023; do
#   python3 utilities/plot_ftest_result.py \
#     --family bernstein \
#     --orders 4,5,6,7,8,9,10,11,12,13,14,15 \
#     --input-folder datasets/260805/${era} \
#     --output-folder /eos/home-n/npalmeri/www/DiElectron/background_model/260805/${era} \
#     --workspace-template dataset_data_{region}_binned_data_altbkg_{family}{order}_allCorrections_{era}_full.root \
#     --era ${era}
# done

# echo "######### F-test: chebyshev #########"
# for era in 2022; do
#   python3 utilities/plot_ftest_result.py \
#     --family chebyshev \
#     --orders 3,4,5,6,7,8,9,10,11,12,13 \
#     --input-folder datasets/260805/${era} \
#     --output-folder /eos/home-n/npalmeri/www/DiElectron/background_model/260805/${era} \
#     --workspace-template dataset_data_{region}_binned_data_altbkg_{family}{order}_allCorrections_{era}_full.root \
#     --era ${era}
# done

echo "######### F-test: bernstein #########"
for era in 2022 2023; do
  python3 utilities/plot_ftest_result.py \
    --family bernstein \
    --orders 4,5,6,7,8,9,10,11,12,13,14,15 \
    --input-folder datasets/260929/${era} \
    --output-folder /eos/home-n/npalmeri/www/DiElectron/background_model/260929/${era} \
    --workspace-template dataset_data_{region}_binned_data_altbkg_{family}{order}_allCorrections_{era}_full.root \
    --era ${era}
done

echo "######### F-test: chebyshev #########"
for era in 2022 2023; do
  python3 utilities/plot_ftest_result.py \
    --family chebyshev \
    --orders 4,5,6,7,8,9,10,11,12,13 \
    --input-folder datasets/260929/${era} \
    --output-folder /eos/home-n/npalmeri/www/DiElectron/background_model/260929/${era} \
    --workspace-template dataset_data_{region}_binned_data_altbkg_{family}{order}_allCorrections_{era}_full.root \
    --era ${era}
done