To run the program

gzip -d data/colombia/MPM_FuenteCensal_2018.json.gz

python3 download_img.py --geo_json_file ../data/colombia/MPM_FuenteCensal_2018.json --state HUILA --municipal "SALADOBLANCO"
python3 download_img.py --geo_json_file ../data/colombia/MPM_FuenteCensal_2018.json --state TOLIMA --municipal "ALPUJARRA,ALVARADO,AMBALEMA,ANZOÁTEGUI,ARM