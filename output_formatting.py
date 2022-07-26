import json

import pandas as pd
from utils import MODEL_PERIOD_END_TIME, MODEL_PERIOD_START_TIME, get_demand_data,get_plant_characteristics, get_raw_data_by_time,reading_input_data
from datetime import date, datetime
import re
from utils import INPUT_RAW_FILE_NAME,OBJECTIVE,DEMAND_PROFILE
from datetime import timedelta

def output_formatting(optimization_solution):
    #output should be a json file with plant_name, date, timeblock and production_units
    print('formatting optimization solution output')
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
                json_data['model_plant_name'] = plant_name
                json_data['date'] = formatted_date
                json_data['time_bucket'] = time_bucket
                json_data['model_production'] = float(production)
                optimization_solution_json_data.append(json_data)
        # output_file.write(json.dumps(optimization_solution_json_data, default = my_date_time_converter))
    return json.dumps(optimization_solution_json_data, default = my_date_time_converter)

def output_formatting_primary_opti_solution():
    #input will be a string of the format choose_plants 
    #output should be {'plant_unit_name':'plant_unit_production_units'}
    return None


def demand_satisfaction_constraint_check(optimization_solution_json,demand_of_UP_bydate_byhour_units):
    #first input parameter needs to be changed to optimization output formatted
    #demand of UP by hour needs to be satisfied summed across plant units
    print('Demand satisfaction constraint check')
    demand_satisfaction = []
    optimization_solution_obj = json.loads(optimization_solution_json,object_hook=date_hook)
    optimization_df = pd.DataFrame(optimization_solution_obj)
    for demand in demand_of_UP_bydate_byhour_units:
        sum_total_of_production = optimization_df.loc[(optimization_df['date'] == demand.date) & (optimization_df['time_bucket'] == str(demand.time_block)),'production'].sum()
        if int(sum_total_of_production)+1 >= int(demand.demand_val) :
                demand_satisfaction.append('Demand of '+ str(demand.demand_val) +' satisfied during ' 
                + str(demand.date) 
                + ' and block '+ str(demand.time_block)
                + ' with production units ' + str(sum_total_of_production))
        else:
            print('Demand of '+ str(demand.demand_val) +' not satisfied during ' 
            + str(demand.date) 
            + ' and block '+ str(demand.time_block)
            + ' with production units ' + str(sum_total_of_production))
            print(sum_total_of_production)
            demand_satisfaction.append('Demand of '+ str(demand.demand_val) +' not satisfied during ' 
            + str(demand.date) 
            + ' and block '+ str(demand.time_block)
            + ' with production units ' + str(sum_total_of_production))
    return demand_satisfaction



def output_plant_chars(optimization_solution_json,plant_units):
    optimization_solution_obj = json.loads(optimization_solution_json,object_hook=date_hook)
    for obj in optimization_solution_obj:
        for plant in plant_units:
            formatted_name = re.sub(r"(\s)|(-)", "_", plant.name)
            if(formatted_name == obj['model_plant_name']):
                obj['capacity'] = plant.capacity
                obj['plant_ownership'] = plant.ownership
                obj['fuel_type'] = plant.fuel_type
                obj['model_max_ramp_up_delta'] = plant.ramp_up_delta
                obj['model_max_ramp_down_delta'] = plant.ramp_down_delta
                obj['avg_variable_cost'] = plant.average_variable_cost 
                obj['model_production_cost'] = plant.average_variable_cost*obj['model_production']
                obj['model_PLF'] = (float(obj['model_production']) / float(plant.capacity)) 
                obj['model_base_or_peak_plant'] = plant.base_or_peak_plant
                obj['demand_profile'] = DEMAND_PROFILE
                obj['model_objective'] = OBJECTIVE
                obj['model_run_date'] = str(datetime.now().date())
    with open("optimization_solution_json.json","w") as output_file:
        output_file.write(json.dumps(optimization_solution_obj, default = my_date_converter))
    return json.dumps(optimization_solution_obj,  default = my_date_converter)
     

def add_plant_ramp_up_and_down(output_plant_chars_add,scheduling_time_blocks, scheduling_dates, plant_names):
    output_plant_chars_added = json.loads(output_plant_chars_add)
    plant_name_date_time_bucket = {}
    ramp_rates = {}
    for solution in  output_plant_chars_added:
        key_to_look = solution['model_plant_name']+","+solution['date']+","+solution['time_bucket']
        plant_name_date_time_bucket[key_to_look] = solution


    for plant in plant_names:
        formatted_name = plant.replace(" ","_").replace("-","_")
        for date in scheduling_dates:
                for time_block in scheduling_time_blocks[:-1]:
                    name_date_time_block = formatted_name+","+str(date)+","+str(time_block) 
                    name_date_time_block_plus_one = formatted_name+","+str(date)+","+str(time_block+1) 
                    if name_date_time_block in plant_name_date_time_bucket.keys():
                        if name_date_time_block_plus_one in plant_name_date_time_bucket.keys():
                            ramp_rates[name_date_time_block] = (plant_name_date_time_bucket[name_date_time_block_plus_one]['model_production'] - plant_name_date_time_bucket[name_date_time_block]['model_production'])/plant_name_date_time_bucket[name_date_time_block]['model_production']
            
    for plant in plant_names:
        formatted_name = plant.replace(" ","_").replace("-","_")
        for today in scheduling_dates[:-1]:
            tomorrow = today + timedelta(1)
            name_date_time_block = formatted_name+","+str(today)+","+str(96)
            name_date_time_block_plus_one = formatted_name+","+str(tomorrow)+","+str(1) 
            if name_date_time_block in plant_name_date_time_bucket.keys():
                if name_date_time_block_plus_one in plant_name_date_time_bucket.keys():
                  ramp_rates[name_date_time_block] = (plant_name_date_time_bucket[name_date_time_block_plus_one]['model_production'] - plant_name_date_time_bucket[name_date_time_block]['model_production'])/plant_name_date_time_bucket[name_date_time_block]['model_production']
    return ramp_rates
    
def converting_outputs_to_df(plant_units,scheduling_time_blocks,scheduling_dates,plant_names):
    opti_solution_json = output_formatting(optimization_solution='optimization_solution_with_new_constraints.txt')
    output_plant_chars_add = output_plant_chars(opti_solution_json,plant_units)
    output_plant_chars_added = pd.read_json(output_plant_chars_add)
    ramp_rates = add_plant_ramp_up_and_down(output_plant_chars_add,scheduling_time_blocks, scheduling_dates, plant_names)

    ramp_rates_in_a_df = pd.DataFrame(ramp_rates.items(),columns = ['plant_date_time','ramp_rate'])
    
    ramp_rates_in_a_df[['model_plant_name','date','time_bucket']]=ramp_rates_in_a_df['plant_date_time'].str.split(',', expand=True)
    ramp_rates_in_a_df['time_bucket'] = ramp_rates_in_a_df['time_bucket'].astype(int)
    ramp_rates_in_a_df['date'] = pd.to_datetime(ramp_rates_in_a_df['date'])
    ramp_rates_in_a_df = ramp_rates_in_a_df.drop(columns='plant_date_time')

    opti_output = output_plant_chars_added.merge(ramp_rates_in_a_df,on=['model_plant_name','date','time_bucket'],how='left')
    return opti_output


#This method is used to convert datetime to string while parsing to json in code
def my_date_time_converter(o):
    if isinstance(o, datetime):
        return o.__str__()

#This method is used to convert datetime.date to string while parsing to json in code
def my_date_converter(o):
    if isinstance(o, date):
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
#FILE_NAME = "RawData/upsldc_plant_unit_time_block.csv"
#raw_data = reading_input_data(file_name=FILE_NAME)
#plant_units = get_plant_characteristics(raw_data)

#model_data = get_raw_data_by_time(raw_data,MODEL_PERIOD_START_TIME,MODEL_PERIOD_END_TIME)
#demand_of_UP_bydate_byhour_units,demand_UP = get_demand_data(model_data)

#optimization_solution_json = output_formatting("optimization_solution.txt")
#add_plant_percent_ramp_up_or_down(optimization_solution_json,plant_units)
# capacity_constraint_check(optimization_solution_json,plant_units)
# demand_satisfaction_constraint_check(optimization_solution_json,demand_of_UP_bydate_byhour_units)
##Testing code ends