import json
from utils import MODEL_PERIOD_END_TIME, MODEL_PERIOD_START_TIME, get_demand_data,get_plant_characteristics, get_raw_data_by_time,reading_input_data
import datetime
import re
from utils import FILE_NAME

def output_formatting(optimization_solution):
    #output should be a json file with plant_name, date, timeblock and production_units
    optimization_solution_json_data = []
    with open(optimization_solution,"r") as file, open("optimization_solution_json.json","w") as output_file:
        for line in file:
            first_chunk = line.rsplit("production_units_(")
            if len(first_chunk) > 1:
                json_data = {};
                plant_name = re.search('%s(.*)%s' % ("'", "'"), first_chunk[1]).group(1)
                second_chunk = first_chunk[1].replace("'"+plant_name+"'", "").replace("_","")
                #print(second_chunk);
                extracted_date = re.search('%s(.*)%s' % ("datetime.date(", "),"), second_chunk).group(1).replace("(","").replace(")","")
                #print(extracted_date)
                date = datetime.datetime.strptime(extracted_date, '%Y,%m,%d')
                #print(date)
                third_chunk = second_chunk.rsplit("),")[1].rsplit(")=")
                time_bucket = third_chunk[0];
                production = third_chunk[1].strip();
                #print(time_bucket)
                #print(production)
                json_data['plant_name'] = plant_name
                json_data['date'] = date
                json_data['time_bucket'] = time_bucket
                json_data['production'] = production
                optimization_solution_json_data.append(json_data);  
        output_file.write(json.dumps(optimization_solution_json_data, default = my_date_time_converter))
    return json.dumps(optimization_solution_json_data, default = my_date_time_converter)


def demand_satisfaction_constraint_check(optimization_solution_json,demand_of_UP_bydate_byhour_units):
    #first input parameter needs to be changed to optimization output formatted 
    #demand of UP by hour needs to be satisfied summed across plant units 
    optimization_solution_obj = json.loads(optimization_solution_json)
    for demand_details in demand_of_UP_bydate_byhour_units:
       print(str(demand_details.date) + ' '+ str(demand_details.time_block) + ' '+ str(demand_details.demand_val))
    return None

def capacity_constraint_check(optimization_solution_json,plant_units):
    #every plant needs to run at a capacity that is not exceeding the maximum capacity of the plant
    #the percentage at which the plant is working at 
    optimization_solution_obj = json.loads(optimization_solution_json)
    
    for obj in optimization_solution_obj:
        for plant in plant_units:
            if(plant.name.replace(" ", "_") == obj['plant_name']):
                obj['high_capacity_flag'] = float(obj['production']) >= float(plant.capacity) 
                obj['capacity_percent'] = (float(obj['production']) / float(plant.capacity)) * 100
    with open("optimization_solution_json.json","w") as output_file:
        output_file.write(json.dumps(optimization_solution_obj, default = my_date_time_converter))
    return json.dumps(optimization_solution_obj, default = my_date_time_converter)


def my_date_time_converter(o):
    if isinstance(o, datetime.datetime):
        return o.__str__()

raw_data = reading_input_data(file_name=FILE_NAME)
plant_units = get_plant_characteristics(raw_data)

model_data = get_raw_data_by_time(raw_data,MODEL_PERIOD_START_TIME,MODEL_PERIOD_END_TIME)
demand_of_UP_bydate_byhour_units,demand_UP,demand_values = get_demand_data(model_data)

optimization_solution_json = output_formatting("optimization_solution.txt")
demand_satisfaction_constraint_check(optimization_solution_json,demand_of_UP_bydate_byhour_units)
capacity_constraint_check(optimization_solution_json,plant_units);