# First do new routes freight cost analysis
# python code/get_cost_matrix.py -o data/csv/cm_baseline.csv   -r 'data/geojson/Networks/Baseline.geojson'
# python code/get_cost_matrix.py -o data/csv/cm_guinea_50.csv  -r 'data/geojson/Networks/Baseline.geojson' -b 'parameters/border_costs_guinea_50p.csv'
# python code/get_cost_matrix.py -o data/csv/cm_bamako_conakry.csv         -r 'data/geojson/Networks/Bamako_Conakry.geojson'
# python code/get_cost_matrix.py -o data/csv/cm_bamako_monrovia.csv        -r 'data/geojson/Networks/Bamako_Monrovia.geojson'
# python code/get_cost_matrix.py -o data/csv/cm_conakry_bissau.csv         -r 'data/geojson/Networks/Conakry_Bissau.geojson'
# python code/get_cost_matrix.py -o data/csv/cm_conakry_kankan_abidjan.csv -r 'data/geojson/Networks/Conakry_Kankan_Abidjan.geojson'
# python code/get_cost_matrix.py -o data/csv/cm_conakry_monrovia.csv       -r 'data/geojson/Networks/Conakry_Monrovia.geojson'
# python code/get_cost_matrix.py -o data/csv/cm_conakry_nze_abidjan.csv    -r 'data/geojson/Networks/Conakry_Nzé_Abidjan.geojson'
# python code/get_cost_matrix.py -o data/csv/cm_dakar_conakry.csv          -r 'data/geojson/Networks/Dakar_Conakry.geojson'
# python code/get_cost_matrix.py -o data/csv/cm_tah7.csv                   -r 'data/geojson/Networks/TAH7.geojson'

# python code/get_ma.py -i data/csv/cm_baseline.csv               -o output/ma_baseline.csv
# python code/get_ma.py -i data/csv/cm_guinea_50.csv              -o output/ma_guinea_50.csv
# python code/get_ma.py -i data/csv/cm_bamako_conakry.csv         -o output/ma_bamako_conakry.csv
# python code/get_ma.py -i data/csv/cm_bamako_monrovia.csv        -o output/ma_bamako_monrovia.csv
# python code/get_ma.py -i data/csv/cm_conakry_bissau.csv         -o output/ma_conakry_bissau.csv
# python code/get_ma.py -i data/csv/cm_conakry_kankan_abidjan.csv -o output/ma_conakry_kankan_abidjan.csv
# python code/get_ma.py -i data/csv/cm_conakry_monrovia.csv       -o output/ma_conakry_monrovia.csv
# python code/get_ma.py -i data/csv/cm_conakry_nze_abidjan.csv    -o output/ma_conakry_nze_abidjan.csv
# python code/get_ma.py -i data/csv/cm_dakar_conakry.csv          -o output/ma_dakar_conakry.csv
# python code/get_ma.py -i data/csv/cm_tah7.csv                   -o output/ma_tah7.csv

# python code/compare_outputs.py -a output/ma_baseline.csv -b output/ma_guinea_50.csv
# python code/compare_outputs.py -a output/ma_baseline.csv -b output/ma_bamako_conakry.csv
# python code/compare_outputs.py -a output/ma_baseline.csv -b output/ma_bamako_monrovia.csv
# python code/compare_outputs.py -a output/ma_baseline.csv -b output/ma_conakry_bissau.csv
# python code/compare_outputs.py -a output/ma_baseline.csv -b output/ma_conakry_kankan_abidjan.csv
# python code/compare_outputs.py -a output/ma_baseline.csv -b output/ma_conakry_monrovia.csv
# python code/compare_outputs.py -a output/ma_baseline.csv -b output/ma_conakry_nze_abidjan.csv
# python code/compare_outputs.py -a output/ma_baseline.csv -b output/ma_dakar_conakry.csv
# python code/compare_outputs.py -a output/ma_baseline.csv -b output/ma_tah7.csv



# Then do time analysis borders
# python code/get_cost_matrix.py -o data/csv/cmt_baseline.csv   -b 'parameters/border_costs.csv' -t
python code/get_cost_matrix.py -o data/csv/cmt_guinea_10.csv  -b 'parameters/border_costs_guinea_10p.csv' -t
# python code/get_cost_matrix.py -o data/csv/cmt_guinea_30.csv  -b 'parameters/border_costs_guinea_30p.csv' -t
# python code/get_cost_matrix.py -o data/csv/cmt_guinea_50.csv  -b 'parameters/border_costs_guinea_50p.csv' -t
# python code/get_cost_matrix.py -o data/csv/cmt_inf.csv  -b 'parameters/border_costs_infinite.csv' -t
# python code/get_cost_matrix.py -o data/csv/cm_guinea_100.csv -b 'parameters/border_costs_guinea_100p.csv' -t

# python code/get_cost_matrix.py -o data/csv/cm_baseline_th1.csv -b 'parameters/border_costs.csv' -t -harris
# python code/get_cost_matrix.py -o data/csv/cm_guinea_30_th1.csv  -b 'parameters/border_costs_guinea_30p.csv' -t -harris
# python code/get_cost_matrix.py -o data/csv/cm_guinea_50_th1.csv  -b 'parameters/border_costs_guinea_50p.csv' -t -harris
# python code/get_cost_matrix.py -o data/csv/cm_guinea_100_th1.csv -b 'parameters/border_costs_guinea_100p.csv' -t -harris


# python code/get_ma.py     -i data/csv/cmt_baseline.csv     -o output/mat_baseline.csv
python code/get_ma.py     -i data/csv/cmt_guinea_10.csv    -o output/mat_guinea_10.csv
# python code/get_ma.py     -i data/csv/cmt_guinea_30.csv    -o output/mat_guinea_30.csv
# python code/get_ma.py     -i data/csv/cmt_guinea_50.csv    -o output/mat_guinea_50.csv
# python code/get_ma.py     -i data/csv/cmt_baseline_ports_shut.csv    -o output/mat_baseline_ports_shut.csv
# python code/get_ma.py     -i data/csv/cmt_inf.csv    -o output/mat_inf.csv
# python code/get_ma.py     -i data/csv/cm_guinea_100.csv   -o output/ma_guinea_100.csv

# python code/get_ma.py     -i data/csv/cm_baseline_th1.csv     -o output/ma_baseline_th1.csv   -harris
# python code/get_ma.py     -i data/csv/cm_guinea_30_th1.csv    -o output/ma_guinea_30_th1.csv  -harris
# python code/get_ma.py     -i data/csv/cm_guinea_50_th1.csv    -o output/ma_guinea_50_th1.csv  -harris
# python code/get_ma.py     -i data/csv/cm_guinea_100_th1.csv   -o output/ma_guinea_100_th1.csv -harris


python code/compare_outputs.py -a output/mat_baseline.csv -b output/mat_guinea_10.csv
# python code/compare_outputs.py -a output/mat_baseline.csv -b output/mat_guinea_30.csv
# python code/compare_outputs.py -a output/mat_baseline.csv -b output/mat_baseline_ports_shut.csv
# python code/compare_outputs.py -a output/mat_baseline.csv -b output/mat_inf.csv
# python code/compare_outputs.py -a output/ma_baseline.csv -b output/ma_guinea_100.csv

# python code/compare_outputs.py -a output/ma_baseline_th1.csv -b output/ma_guinea_30_th1.csv
# python code/compare_outputs.py -a output/ma_baseline_th1.csv -b output/ma_guinea_50_th1.csv
# python code/compare_outputs.py -a output/ma_baseline_th1.csv -b output/ma_guinea_100_th1.csv
