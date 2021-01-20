To run the program

cd data/colombia
gzip -d MPM_FuenteCensal_2018.json.gz

cd ../../src

python3 download_img.py --geo_json_file ../data/colombia/MPM_FuenteCensal_2018.json --state HUILA --municipal "SALADOBLANCO"

python3 download_img.py --geo_json_file ../data/colombia/MPM_FuenteCensal_2018.json --state TOLIMA --municipal "ALPUJARRA,ALVARADO,AMBALEMA,ANZOÁTEGUI,ARM
