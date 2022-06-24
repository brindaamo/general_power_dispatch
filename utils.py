from datetime import datetime
from plant_model import PlantUnits
import pandas as pd
from demand_model import Demand
import numpy as np
import csv
import re

raw_data = pd.read_csv("RawData/upsldc_plant_unit_time_block.csv")
raw_data['date'] = pd.to_datetime(raw_data['data_capture_time_block_start']).dt.date

#this function is to get the inputs needed for running the model. 
#accepted values are 'cost' and 'effeciency'
OBJECTIVE_FUCTION = 'cost'
COAL_RAMP_UP_PERCENT = 0.13
COAL_RAMP_DOWN_PERCENT = 0.13
COAL_EFFICIENCY_RATE = 1
BASE_OR_PEAK_COST_CUT_OFF = 3
MINIMUM_BASE_PLANT_CAPACITY = 0.70
MAXIMUM_BASE_PLANT_CAPACITY = 1
MINIMUM_PEAK_PLANT_CAPACITY = 0.45
MAXIMUM_PEAK_PLANT_CAPACITY = 1
OBJECTIVE = 'cost'

# start and end date of developmental window
DEVELOPMENT_PERIOD_START_TIME = datetime(2021, 3, 1)
DEVELOPMENT_PERIOD_END_TIME = datetime(2021, 4, 1)

#start and end of testing window 
MODEL_PERIOD_START_TIME = datetime(2021, 4, 1)
MODEL_PERIOD_END_TIME = datetime(2021, 5, 1)
INFINITE_CAPACITY = 10000
MINIMUM_UP_DRAWAL = 0
#values accepted are 'high','base' and 'low'
DEMAND_PROFILE = 'base'
HIGH_PROFILE_FACTOR = 1.2
LOW_PROFILE_FACTOR = 0.75
BASE_PROFILE_FACTOR = 1

TIME_LEVEL = ['date','hour_of_day','time_block_of_day']
DEMAND_LEVEL = ['date','hour_of_day','time_block_of_day','avg_unit_current_load']

#------------------CHANGE THIS INPUT-------------------------
#-----------------name of the month--------------------------
MONTH = "april_2021"

#------------------input file locations------------------------
INPUT_RAW_FILE_NAME = "RawData/upsldc_plant_unit_time_block.csv"
INPUT_MAPPING_TIMEBLOCKS_TO_HOURS = "RawData/hours_timeblock_mapping.csv"
INPUT_THERMAL_EFFECIENCY_FILE_NAME = "RawData/thermal_effeciencies.csv"

#-------------------output_file_locations-----------------------
OUTPUT_SOLUTION_FOLDER = "output_files"
OUTPUT_ACTUALS_FOLDER = "output_files"




#this function will read the UPSLDC input file from the location (this is the data for the whole time period.)
def reading_input_data(file_name):
    raw_data = pd.read_csv(file_name)
    raw_data['date'] = pd.to_datetime(raw_data['data_capture_time_block_start']).dt.date
    return raw_data


#this function is used to get data in the respective time blocks. The demand calculations 
#are at a different period (one period later from the parameters calculation period)
#the parameters are calculated at developmental window and demand at testing window
def get_raw_data_by_time(raw_data,start_time, end_time):
    start_time_str = start_time.strftime("%Y-%m-%d %H:%M:%S")
    end_time_str = end_time.strftime("%Y-%m-%d %H:%M:%S")
    return raw_data[
        (raw_data["data_capture_time_block_start"] >= start_time_str)
        & (raw_data["data_capture_time_block_start"] < end_time_str)
    ]
    

#this function is used to get the plant characteristics
def get_plant_characteristics(plant_unit_timeblocks):
    plant_units = []
    unique_names = (plant_unit_timeblocks['plant_name'] + " unit:" + plant_unit_timeblocks['actual_plant_unit'].astype(str)).unique()
    for name in unique_names:
        splitter = name.split(" unit:")
        plant_name = splitter[0]
        if plant_name != "OTHER RENEWABLE":
            plant_unit_num = int(splitter[1])
            plant_data = plant_unit_timeblocks[(plant_unit_timeblocks['plant_name'] == plant_name) & (plant_unit_timeblocks['actual_plant_unit'] == plant_unit_num)]
            plant_ramp_up_delta = np.percentile(plant_data['upsldc_unit_capacity'],75)*COAL_EFFICIENCY_RATE*COAL_RAMP_UP_PERCENT
            plant_ramp_down_delta = np.percentile(plant_data['upsldc_unit_capacity'],75)*COAL_EFFICIENCY_RATE*COAL_RAMP_DOWN_PERCENT
            plant_data_row = plant_data.iloc[0]
            average_cost = plant_data['variable_cost'].mean()
            if plant_name == 'UP DRAWAL':
                upper_capacity = INFINITE_CAPACITY
                lower_capacity = MINIMUM_UP_DRAWAL
                base_or_peak = 'peak'
                plant_ramp_up_delta = upper_capacity*COAL_EFFICIENCY_RATE*COAL_RAMP_UP_PERCENT
                plant_ramp_down_delta = upper_capacity*COAL_EFFICIENCY_RATE*COAL_RAMP_DOWN_PERCENT

            else:
                if average_cost<3:
                    upper_capacity = MAXIMUM_BASE_PLANT_CAPACITY*plant_data_row['upsldc_unit_capacity']
                    lower_capacity = MINIMUM_BASE_PLANT_CAPACITY*plant_data_row['upsldc_unit_capacity']
                    base_or_peak = 'base'
                else:
                    upper_capacity = MAXIMUM_PEAK_PLANT_CAPACITY*plant_data_row['upsldc_unit_capacity']
                    lower_capacity = MINIMUM_PEAK_PLANT_CAPACITY*plant_data_row['upsldc_unit_capacity']
                    base_or_peak = 'peak'


            
            plant_units.append(PlantUnits(name, plant_data_row["plant_ownership"], plant_data_row["plant_fuel_type"], plant_data_row['upsldc_unit_capacity'],lower_capacity,upper_capacity,plant_ramp_up_delta, plant_ramp_down_delta, average_cost,base_or_peak,None))
           
            
    return plant_units

def get_only_thermal_power_plant(plant_units):
    thermal_plant_units = []
    for plant in plant_units:
        if plant.fuel_type == 'THERMAL' or plant.fuel_type == 'ALL CENTRAL':
            thermal_plant_units.append(plant)
    return thermal_plant_units
            

def assign_hydro_as_peak(plant_units):
    for plant in plant_units:
        if(plant.fuel_type=='HYDRO'):
            plant.base_or_peak_plant = 'peak'
            plant.upper_capacity = MAXIMUM_PEAK_PLANT_CAPACITY*plant.capacity
            plant.lower_capacity = MINIMUM_PEAK_PLANT_CAPACITY*plant.capacity
    return None

        
def add_new_plants(plant_units,name, ownership, fuel_type, capacity,average_variable_cost):
    if average_variable_cost<3:
        upper_capacity = MAXIMUM_BASE_PLANT_CAPACITY*capacity
        lower_capacity = MINIMUM_BASE_PLANT_CAPACITY*capacity
        base_or_peak = 'base'
    else:
        upper_capacity = MAXIMUM_PEAK_PLANT_CAPACITY*capacity
        lower_capacity = MINIMUM_PEAK_PLANT_CAPACITY*capacity
        base_or_peak = 'peak'

    plant_ramp_up_delta = capacity*COAL_EFFICIENCY_RATE*COAL_RAMP_UP_PERCENT
    plant_ramp_down_delta = capacity*COAL_EFFICIENCY_RATE*COAL_RAMP_DOWN_PERCENT
    plant_units.append(PlantUnits(name,ownership,fuel_type,capacity,lower_capacity,upper_capacity,plant_ramp_up_delta,plant_ramp_down_delta,average_variable_cost,base_or_peak,None))

    return plant_units 

def get_thermal_effeciency(thermal_effeciencies_in_a_csv,thermal_plants):
    with open(thermal_effeciencies_in_a_csv, mode='r',encoding='utf-8-sig') as infile:
        reader = csv.reader(infile)
        thermal_effeciency = dict((rows[0],float(rows[1])) for rows in reader)

    avg_thermal_effeciency = sum(thermal_effeciency.values())/len(thermal_effeciency)

    for plant in thermal_plants:
        splitter = plant.name.split(" unit:")
        formatted_name = re.sub(r"(\s)|(-)", "_", splitter[0])
        if formatted_name in thermal_effeciency.keys():
            plant.plant_thermal_effeciency = thermal_effeciency[formatted_name]
        else:
            plant.plant_thermal_effeciency = avg_thermal_effeciency

    return None





#This function is used to clean up the demand and get the demand units. Removing the demand satisfied by other renewables 

def get_demand_data(model_demand):
    demand= model_demand[~model_demand.plant_fuel_type.isin(["RENEWABLE"])]
    demand_without_other_ren = demand.groupby(TIME_LEVEL).sum().reset_index()
    demand_UP = demand_without_other_ren[DEMAND_LEVEL]

    demand_of_UP_bydate_byhour_units = []
    for index,demand_row in demand_UP.iterrows():
        demand_of_UP_bydate_byhour_units.append(Demand(demand_row['date'],demand_row['hour_of_day'],demand_row['time_block_of_day'],demand_row['avg_unit_current_load'],str(demand_row['date'])+"-"+str(demand_row['time_block_of_day'])))
    
    return demand_of_UP_bydate_byhour_units,demand_UP

   
def demand_with_only_thermal(model_demand):
    demand = model_demand[(model_demand['plant_fuel_type']=='THERMAL') | (model_demand['plant_fuel_type']=='ALL CENTRAL')]
    demand_without_hydro = demand.groupby(TIME_LEVEL).sum().reset_index()
    demand_without_hydro = demand_without_hydro[DEMAND_LEVEL]

    demand_of_UP_bydate_byhour_units = []
    for index,demand_row in demand_without_hydro.iterrows():
        demand_of_UP_bydate_byhour_units.append(Demand(demand_row['date'],demand_row['hour_of_day'],demand_row['time_block_of_day'],demand_row['avg_unit_current_load'],str(demand_row['date'])+"-"+str(demand_row['time_block_of_day'])))
    
    return demand_of_UP_bydate_byhour_units,demand_without_hydro


def get_demand_based_on_profile(demand_of_UP_bydate_byhour_units,demand_UP,demand_profile):

    if demand_profile == 'high':
        demand_UP['avg_unit_current_load'].multiply(HIGH_PROFILE_FACTOR)
        for demand_of_UP_by_timeblock in demand_of_UP_bydate_byhour_units:
          new_value = demand_of_UP_by_timeblock.demand_val*HIGH_PROFILE_FACTOR
          demand_of_UP_by_timeblock.demand_val = new_value 
    elif demand_profile == 'low':
        demand_UP['avg_unit_current_load'].multiply(LOW_PROFILE_FACTOR)
        for demand_of_UP_by_timeblock in demand_of_UP_bydate_byhour_units:
            new_value = demand_of_UP_by_timeblock.demand_val*LOW_PROFILE_FACTOR
            demand_of_UP_by_timeblock.demand_val = new_value 
    elif demand_profile == 'base':
        pass

    return demand_of_UP_bydate_byhour_units,demand_UP






