import json

import pandas as pd
from utils import MODEL_PERIOD_END_TIME, MODEL_PERIOD_START_TIME, get_demand_data,get_plant_characteristics, get_raw_data_by_time,reading_input_data
from datetime import datetime
import re
from utils import FILE_NAME

def output_formatting(optimization_solution):
    #output should be a json file with plant_name, date, timeblock and production_units
    print('Fromating optimization solution output')
    optimization_solution_json_data = []
    with open(optimization_solution,"r") as file, open("optimization_solution_json.json","w") as output_file:
        for line in file:
            first_chunk = line.rsplit("production_units_(")
            if len(first_chunk) > 1:
                json_data = {}
                plant_name = re.search('%s(.*)%s' % ("'", "'"), first_chunk[1]).group(1)
                second_chunk = first_chunk[1].replace("'"+plant_name+"'", "").replace("_","")
                extracted_date = re.search('%s(.*)%s' % ("datetime.date(", "),"), second_chunk).group(1).replace("(","").replace(")","")
                temp_date = datetime.strptime(extracted_date, '%Y,%m,%d')
                formatted_date = temp_date.strftime('%Y-%m-%d')
                third_chunk = second_chunk.rsplit("),")[1].rsplit(")=")
                time_bucket = third_chunk[0]
                production = third_chunk[1].strip()
                json_data['plant_name'] = plant_name
                json_data['date'] = formatted_date
                json_data['time_bucket'] = time_bucket
                json_data['production'] = float(production)
                optimization_solution_json_data.append(json_data);
        output_file.write(json.dumps(optimization_solution_json_data, default = my_date_time_converter))
    return json.dumps(optimization_solution_json_data, default = my_date_time_converter)


def demand_satisfaction_constraint_check(optimization_solution_json,demand_of_UP_bydate_byhour_units):
    #first input parameter needs to be changed to optimization output formatted
    #demand of UP by hour needs to be satisfied summed across plant units
    print('Demand satisfaction constraint check')
    demand_satisfaction = [];
    optimization_solution_obj = json.loads(optimization_solution_json,object_hook=date_hook)
    optimization_df = pd.DataFrame(optimization_solution_obj)
    for demand in demand_of_UP_bydate_byhour_units:
        sum_total_of_production = optimization_df.loc[(optimization_df['date'] == demand.date) & (optimization_df['time_bucket'] == str(demand.time_block)),'production'].sum()
        if float(sum_total_of_production) >= demand.demand_val :
                demand_satisfaction.append('Demand of '+ str(demand.demand_val) +' satisfied during ' 
                + str(demand.date) 
                + ' and block '+ str(demand.time_block)
                + ' with production units ' + str(sum_total_of_production))
        else:
            demand_satisfaction.append('Demand of '+ str(demand.demand_val) +' not satisfied during ' 
            + str(demand.date) 
            + ' and block '+ str(demand.time_block)
            + ' with production units ' + str(sum_total_of_production))
    return demand_satisfaction

def capacity_constraint_check(optimization_solution_json,plant_units):
    #every plant needs to run at a capacity that is not exceeding the maximum capacity of the plant
    #the percentage at which the plant is working at
    print('Capacity satisfaction constraint check')
    optimization_solution_obj = json.loads(optimization_solution_json,object_hook=date_hook)
    for obj in optimization_solution_obj:
        for plant in plant_units:
            if(plant.name.replace(" ", "_") == obj['plant_name']):
                obj['high_capacity_flag'] = float(obj['production']) >= float(plant.capacity)
                obj['capacity_percent'] = (float(obj['production']) / float(plant.capacity)) * 100
    with open("optimization_solution_json.json","w") as output_file:
        output_file.write(json.dumps(optimization_solution_obj, default = my_date_time_converter))
    return json.dumps(optimization_solution_obj, default = my_date_time_converter)

#This method is used to convert datetime to string while parsing to json in code
def my_date_time_converter(o):
    if isinstance(o, datetime):
        return o.__str__()

#This method is used to convert string to date for formatting json to string
def date_hook(json_dict):
    for (key, value) in json_dict.items():
        try:
            json_dict[key] = datetime.strptime(value, "%Y-%m-%d").date()
        except:
            pass
    return json_dict


##Testing code starts
#raw_data = reading_input_data(file_name=FILE_NAME)
#plant_units = get_plant_characteristics(raw_data)

#model_data = get_raw_data_by_time(raw_data,MODEL_PERIOD_START_TIME,MODEL_PERIOD_END_TIME)
#demand_of_UP_bydate_byhour_units,demand_UP = get_demand_data(model_data)

#optimization_solution_json = output_formatting("optimization_solution.txt")
#capacity_constraint_check(optimization_solution_json,plant_units)
#demand_satisfaction_constraint_check(optimization_solution_json,demand_of_UP_bydate_byhour_units)
##Testing code ends