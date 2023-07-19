import json
import pandas as pd
from datetime import date, datetime
import re
import csv
from utils import my_date_converter,my_date_time_converter,date_hook
from datetime import timedelta
from optimization import Optimization


class output_formatting(Optimization):
    
    def extract_data_from_text_file(self,input_file_path, output_csv_file_path):
        optimization_solution_csv_data = []

        with open(input_file_path, "r") as file:
            for line in file:
                first_chunk = line.rsplit("production_units_(")
                if len(first_chunk) > 1:
                    json_data = {}
                    plant_name = re.search(r"'(.*?)'", first_chunk[1]).group(1)
                    second_chunk = first_chunk[1].replace("'" + plant_name + "'", "").replace("_", "")

                    date_match = re.search(r"datetime\.datetime\((.*?)\)", second_chunk)
                    if date_match:
                        date_str = date_match.group(1)
                        date_components = [int(comp.strip()) for comp in date_str.split(",")]
                        extracted_date = datetime(*date_components).date()
                        formatted_date = extracted_date.strftime('%Y-%m-%d')
                    else:
                        formatted_date = None

                    third_chunk = second_chunk.rsplit("),")[1].rsplit(")=")
                    time_bucket = third_chunk[0]
                    production = third_chunk[1].strip()

                    json_data["model_plant_name"] = plant_name
                    json_data["date"] = formatted_date
                    json_data["time_bucket"] = time_bucket
                    json_data["model_production"] = float(production)

                    optimization_solution_csv_data.append(json_data)

        # Write the data to the CSV file
        field_names = ["model_plant_name", "date", "time_bucket", "model_production"]
        with open(output_csv_file_path, "w", newline="") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=field_names)
            writer.writeheader()
            writer.writerows(optimization_solution_csv_data)
        
        return None 

    
   

        
def main():
    input_file_path = "optimization_solution_with_new_constraints.txt"
    output_csv_file_path = "optimization_solution.csv"

    simulation_yaml_file = "general_power_dispatch/simulation_inputs.yaml"
    opti = output_formatting(simulation_yaml_file)
    opti.get_inputs_from_yaml_file()
    opti.get_powerplant_data()
    opti.get_demand_data()
    opti.get_power_plant_chars()
    opti.get_peak_demand()
    opti.get_hydro_maximum_for_constraint(1)
    opti.reading_optimization_data()
    opti.creating_optimization_instance_primary_problem()
    opti.solving_primary_optimization()
    opti.creating_optimization_instance()
    opti.solving_optimization_instance()
    opti.extract_data_from_text_file(input_file_path,output_csv_file_path)
    
    
if __name__ == "__main__":
    main()

import os
os.remove('optimization_solution_with_new_constraints.txt')

        

    


    


