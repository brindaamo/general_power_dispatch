import json
import pandas as pd
from datetime import date, datetime
import re
import csv
from utils import my_date_converter,my_date_time_converter,date_hook
from utils import BIG_QUERY_CREDENTIALS, BIG_QUERY_RESULTS_TABLE
from datetime import timedelta
from optimization import Optimization
from google.cloud import bigquery



class output_formatting(Optimization):

    def output_formatting_primary_opti_solution(self):
        #output should be {'plant_unit_name':'plant_unit_production_units'}
        self.primarysolution_output_dictionary = {}  
        #input will be a string of the format choose_plants 
        splitData = self.primary_output.split("\n")
        for arrayLength in range(len(splitData)):
            if(splitData[arrayLength].find("productionUnits")!=-1):
                outputDataSplitArray = splitData[arrayLength].rsplit(",_")[1].rsplit("=")
                outputDataSplitArray[0]=outputDataSplitArray[0].replace("_"," ")
                self.primarysolution_output_dictionary[outputDataSplitArray[0]] = outputDataSplitArray[1]
        #output should be {'plant_unit_name':'plant_unit_production_units'}     
        return self.primarysolution_output_dictionary
    
    def extract_data_from_text_file(self,input_file_path, output_csv_file_path):
        self.optimization_solution_csv_data = []

        with open(input_file_path, "r") as file:
            for line in file:
                first_chunk = line.rsplit("production_units_(")
                if len(first_chunk) > 1:
                    self.solution_json_file = {}
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

                    self.solution_json_file["model_run_date"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    self.solution_json_file["state"] = self.state
                    self.solution_json_file["model_plant_name"] = plant_name
                    self.solution_json_file["generation_date"] = formatted_date
                    self.solution_json_file["time_bucket"] = time_bucket
                    self.solution_json_file["model_production"] = float(production)

                    self.optimization_solution_csv_data.append(self.solution_json_file)

        # Write the data to the CSV file
        field_names = ["model_run_date","state","generation_date","model_plant_name", "time_bucket", "model_production"]
        with open(output_csv_file_path, "w", newline="") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=field_names)
            writer.writeheader()
            writer.writerows(self.optimization_solution_csv_data)
        
        return None 
    
    def data_into_big_query_table(self):
      
        # Create a BigQuery client using your credentials
        client = bigquery.Client.from_service_account_json(BIG_QUERY_CREDENTIALS)

    

        # Insert the rows into BigQuery
        errors = client.insert_rows_json(BIG_QUERY_RESULTS_TABLE, self.optimization_solution_csv_data)

        if errors:
            print(f"Errors: {errors}")
        else:
            print("Data inserted successfully.")
    
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
    opti.create_excess_plant()
    opti.get_final_historical_df()
    opti.get_hydro_maximum_for_constraint(2)
    opti.get_plant_fixed_cost_capacity_bucket()
    opti.get_plant_status()
    opti.get_plant_start_type()
    opti.get_start_up_costs()
    opti.reading_optimization_data()
    opti.creating_optimization_instance_primary_problem()
    opti.solving_primary_optimization()
    opti.output_formatting_primary_opti_solution()
    opti.creating_optimization_instance()
    opti.solving_optimization_instance()
    opti.extract_data_from_text_file(input_file_path,output_csv_file_path)
    opti.data_into_big_query_table()

    
    
    
    
if __name__ == "__main__":
    main()

import os
os.remove('optimization_solution_with_new_constraints.txt')

        

    


    


