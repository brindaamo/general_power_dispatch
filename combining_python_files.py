import os
import glob
import pandas as pd
input_location = "output_files/output_to_db"

def combine_inputs_into_a_single_file(input_location):
    input_files = os.path.join(input_location,"*.csv")
    input_files = glob.glob(input_files)
    input_upsldc_final_csv = pd.concat(map(pd.read_csv,input_files),ignore_index=True)
    input_upsldc_final_csv = input_upsldc_final_csv.drop_duplicates()
    return input_upsldc_final_csv


final_csv = combine_inputs_into_a_single_file(input_location)
final_csv = final_csv[['model_plant_name', 'date', 'time_bucket', 'model_production',
       'capacity', 'plant_ownership', 'fuel_type', 'model_max_ramp_up_delta',
       'model_max_ramp_down_delta', 'avg_variable_cost',
       'model_production_cost', 'model_PLF', 'model_base_or_peak_plant',
       'demand_profile', 'model_objective', 'model_run_date','ramp_rate', 'actuals',
       'demand']]
print(final_csv.columns)
final_csv.to_csv('output_files/output_to_db/final.csv',index=False)