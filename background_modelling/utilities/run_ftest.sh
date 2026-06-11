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

echo "######### F-test: bernstein #########"
python3 utilities/plot_ftest_result.py \
  --family bernstein \
  --orders 4,5,6,7 \
  --input-folder datasets/260603/2022 \
  --output-folder /eos/home-n/npalmeri/www/DiElectron/background_model/260603/2022 \
  --era 2022

# echo "######### F-test: chebyshev #########"
# python3 utilities/plot_ftest_result.py \
#   --family chebyshev \
#   --orders 4,5,6 \
#   --input-folder datasets/260603/2022 \
#   --output-folder /eos/home-n/npalmeri/www/DiElectron/background_model/260603/2022 \
#   --era 2022

echo "######### F-test: polyexp #########"
python3 utilities/plot_ftest_result.py \
  --family polyexp \
  --orders 4,5,6,7 \
  --input-folder datasets/260603/2022 \
  --output-folder /eos/home-n/npalmeri/www/DiElectron/background_model/260603/2022 \
  --era 2022  