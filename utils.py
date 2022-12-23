from datetime import datetime,timedelta
from typing import OrderedDict
from plant_model import PlantUnits
import pandas as pd
from demand_model import Demand
import numpy as np
import csv
import re
import glob
import os


# raw_data = pd.read_csv("RawData/upsldc_plant_unit_time_block.csv")
# raw_data['date'] = pd.to_datetime(raw_data['data_capture_time_block_start']).dt.date

#this function is to get the inputs needed for running the model. 
#accepted values are 'cost' and 'effeciency'
OBJECTIVE_FUNCTION = 'cost'
COAL_RAMP_UP_PERCENT = 0.15
COAL_RAMP_DOWN_PERCENT = 0.15
HYDRO_RAMP_UP_PERCENT = 0.4
HYDRO_RAMP_DOWN_PERCENT = 0.4
COAL_EFFICIENCY_RATE = 1
BASE_OR_PEAK_COST_CUT_OFF = 3
MINIMUM_BASE_PLANT_CAPACITY = 0.70
MAXIMUM_BASE_PLANT_CAPACITY = 1
MINIMUM_PEAK_PLANT_CAPACITY = 0.45
MAXIMUM_PEAK_PLANT_CAPACITY = 1
OBJECTIVE = 'cost'

# start and end date of developmental window
DEVELOPMENT_PERIOD_START_TIME = datetime(2021, 11, 1)
DEVELOPMENT_PERIOD_END_TIME = datetime(2021, 12,31)

#start and end of testing window 
MODEL_PERIOD_START_TIME = datetime(2021, 12,31)
MODEL_PERIOD_END_TIME = datetime(2022, 1,1)
MONTH = "dec_31st_2021"
INFINITE_CAPACITY = 14000
MINIMUM_UP_DRAWAL = 0
#values accepted are 'high','base', 'low' and 'stress_testing'
#if 'stress_testing' run the stress_testing.py file
DEMAND_PROFILE = 'stress_testing'
HIGH_PROFILE_FACTOR = 1.2
LOW_PROFILE_FACTOR = 0.75
BASE_PROFILE_FACTOR = 1

PLANT_UNIT_LEVEL = ['plant_name','actual_plant_unit']
TIME_LEVEL = ['date','hour_of_day','time_block_of_day']
DEMAND_LEVEL = ['date','hour_of_day','time_block_of_day','avg_unit_current_load']



#------------------input file locations------------------------
INPUT_FILE_LOCATION = "RawData/upsldc_data"
INPUT_MAPPING_TIMEBLOCKS_TO_HOURS = "RawData/hours_timeblock_mapping.csv"
INPUT_THERMAL_EFFECIENCY_FILE_NAME = "RawData/thermal_effeciencies.csv"
INPUT_FIXED_COSTS_DATA = "RawData/fixed_costs.csv"
#for stress testing
DEMAND_DATA_FILE_LOCATION = "RawData/stress_testing_demand_file_dec.csv"


#-------------------output_file_locations-----------------------
OUTPUT_SOLUTION_FOLDER = "output_files"
OUTPUT_ACTUALS_FOLDER = "output_files"

#this function will combine the input files in the folder to create a single upsldc file 
def combine_inputs_into_a_single_file(input_location):
    input_files = os.path.join(input_location,"upsldc_plant_unit_time_block*.csv")
    input_files = glob.glob(input_files)
    input_upsldc_final_csv = pd.concat(map(pd.read_csv,input_files),ignore_index=True)
    input_upsldc_final_csv.drop_duplicates(inplace=True)
    return input_upsldc_final_csv


#this function will read the UPSLDC input file from the location (this is the data for the whole time period.)
def converting_to_datetime(input_files):
    # raw_data = pd.read_csv(file_name)
    input_files['data_capture_time_block_start'] = pd.to_datetime(input_files['data_capture_time_block_start'])
    input_files['date'] = pd.to_datetime(input_files['data_capture_time_block_start']).dt.date
    return input_files


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

#this function is used to get the hourly up drawal capacity 
def get_up_drawal_plant_capacity(plant_unit_timeblocks,plant_name):
    plant_data = plant_unit_timeblocks[plant_unit_timeblocks['plant_name'] == plant_name]
    plant_data['avg_unit_current_load'] = plant_data['avg_unit_current_load']*1.1
    plant_data = plant_data.groupby('time_block_of_day').max('avg_unit_current_load').reset_index()[['time_block_of_day','avg_unit_current_load']].set_index('time_block_of_day').to_dict('dict')['avg_unit_current_load']
    return plant_data

#this function is used to get the plant characteristics
def get_plant_characteristics(plant_unit_timeblocks,up_drawal):
    plant_units = []
    unique_names = (plant_unit_timeblocks['plant_name'] + " unit:" + plant_unit_timeblocks['actual_plant_unit'].astype(str)).unique()
    for name in unique_names:
        splitter = name.split(" unit:")
        plant_name = splitter[0]
        if plant_name != "OTHER RENEWABLE":
            plant_unit_num = int(splitter[1])
            plant_data = plant_unit_timeblocks[(plant_unit_timeblocks['plant_name'] == plant_name) & (plant_unit_timeblocks['actual_plant_unit'] == plant_unit_num)]
            plant_data_row = plant_data.iloc[0]
            average_cost = plant_data['variable_cost'].mean()

            #identifying the thermal and hydro ramp rates independantly 
            if plant_data_row["plant_fuel_type"] == 'THERMAL':
                plant_ramp_up_delta = np.percentile(plant_data['upsldc_unit_capacity'],75)*COAL_EFFICIENCY_RATE*COAL_RAMP_UP_PERCENT
                plant_ramp_down_delta = np.percentile(plant_data['upsldc_unit_capacity'],75)*COAL_EFFICIENCY_RATE*COAL_RAMP_DOWN_PERCENT
            else:
                plant_ramp_up_delta = np.percentile(plant_data['upsldc_unit_capacity'],75)*HYDRO_RAMP_UP_PERCENT
                plant_ramp_down_delta = np.percentile(plant_data['upsldc_unit_capacity'],75)*HYDRO_RAMP_DOWN_PERCENT
            
            #getting the lower capacities 
            lower_capacity = plant_data.groupby('date').agg({'avg_unit_current_load':'min'}).reset_index()['avg_unit_current_load'].median()

            #setting UP Drawal's values 
            if plant_name == 'UP DRAWAL':
                upper_capacity = max(up_drawal.values())
                lower_capacity = MINIMUM_UP_DRAWAL
                base_or_peak = 'peak'
                up_drawal_ramp_up_delta = {key: value * COAL_EFFICIENCY_RATE*COAL_RAMP_UP_PERCENT for key, value in up_drawal.items()}
                up_drawal_max_ramp_up_delta = max(up_drawal_ramp_up_delta.values())
                up_drawal_ramp_down_delta = {key: value * COAL_EFFICIENCY_RATE*COAL_RAMP_DOWN_PERCENT for key, value in up_drawal.items()}
                up_drawal_max_ramp_down_delta = max(up_drawal_ramp_down_delta.values())
                plant_units.append(PlantUnits(name, plant_data_row["plant_ownership"], plant_data_row["plant_fuel_type"], plant_data_row['upsldc_unit_capacity'],lower_capacity,upper_capacity,plant_ramp_up_delta, plant_ramp_down_delta, average_cost,base_or_peak,up_drawal=up_drawal,up_drawal_ramp_up_delta=up_drawal_max_ramp_up_delta,up_drawal_ramp_down_delta = up_drawal_max_ramp_down_delta))

            else:
                if average_cost<3:
                    upper_capacity = MAXIMUM_BASE_PLANT_CAPACITY*plant_data_row['upsldc_unit_capacity']
                    base_or_peak = 'base'
                else:
                    upper_capacity = MAXIMUM_PEAK_PLANT_CAPACITY*plant_data_row['upsldc_unit_capacity']
                    base_or_peak = 'peak'
            


            if plant_name != 'UP DRAWAL':
                plant_units.append(PlantUnits(name, plant_data_row["plant_ownership"], plant_data_row["plant_fuel_type"], plant_data_row['upsldc_unit_capacity'],lower_capacity,upper_capacity,plant_ramp_up_delta, plant_ramp_down_delta, average_cost,base_or_peak,up_drawal=up_drawal))
           
            
    return 

#this function is used to get the plant characteristics
def get_plant_characteristics(plant_unit_timeblocks,up_drawal):
    plant_units = []
    unique_names = (plant_unit_timeblocks['plant_name'] + " unit:" + plant_unit_timeblocks['actual_plant_unit'].astype(str)).unique()
    for name in unique_names:
        splitter = name.split(" unit:")
        plant_name = splitter[0]
        if plant_name != "OTHER RENEWABLE":
            plant_unit_num = int(splitter[1])
            plant_data = plant_unit_timeblocks[(plant_unit_timeblocks['plant_name'] == plant_name) & (plant_unit_timeblocks['actual_plant_unit'] == plant_unit_num)]
            plant_data_row = plant_data.iloc[0]
            average_cost = plant_data['variable_cost'].mean()

            #calculating thermal and hydro ramp rates independantly 
            if plant_data_row["plant_fuel_type"] == 'THERMAL':
                plant_ramp_up_delta = np.percentile(plant_data['upsldc_unit_capacity'],75)*COAL_EFFICIENCY_RATE*COAL_RAMP_UP_PERCENT
                plant_ramp_down_delta = np.percentile(plant_data['upsldc_unit_capacity'],75)*COAL_EFFICIENCY_RATE*COAL_RAMP_DOWN_PERCENT
            else:
                plant_ramp_up_delta = np.percentile(plant_data['upsldc_unit_capacity'],75)*HYDRO_RAMP_UP_PERCENT
                plant_ramp_down_delta = np.percentile(plant_data['upsldc_unit_capacity'],75)*HYDRO_RAMP_DOWN_PERCENT
            
            #getting the lower capacities 
            lower_capacity = plant_data.groupby('date').agg({'avg_unit_current_load':'min'}).reset_index()['avg_unit_current_load'].median()

            #setting UP Drawal's values 
            if plant_name == 'UP DRAWAL':
                upper_capacity = max(up_drawal.values())
                lower_capacity = MINIMUM_UP_DRAWAL
                base_or_peak = 'peak'
                plant_ramp_up_delta = {key: value * COAL_EFFICIENCY_RATE*COAL_RAMP_UP_PERCENT for key, value in up_drawal.items()}
                max_up_ramp_up_delta = max(plant_ramp_up_delta.values())
                plant_ramp_down_delta = {key: value * COAL_EFFICIENCY_RATE*COAL_RAMP_DOWN_PERCENT for key, value in up_drawal.items()}
                max_ramp_down_delta = max(plant_ramp_down_delta.values())
                plant_units.append(PlantUnits(name, plant_data_row["plant_ownership"], plant_data_row["plant_fuel_type"], plant_data_row['upsldc_unit_capacity'],lower_capacity,upper_capacity,plant_ramp_up_delta, plant_ramp_down_delta, average_cost,base_or_peak,up_drawal=up_drawal,up_drawal_ramp_up_delta=max_up_ramp_up_delta,up_drawal_ramp_down_delta = max_ramp_down_delta))

            else:
                if average_cost<3:
                    upper_capacity = MAXIMUM_BASE_PLANT_CAPACITY*plant_data_row['upsldc_unit_capacity']
                    base_or_peak = 'base'
                else:
                    upper_capacity = MAXIMUM_PEAK_PLANT_CAPACITY*plant_data_row['upsldc_unit_capacity']
                    base_or_peak = 'peak'
            


            if plant_name != 'UP DRAWAL':
                plant_units.append(PlantUnits(name, plant_data_row["plant_ownership"], plant_data_row["plant_fuel_type"], plant_data_row['upsldc_unit_capacity'],lower_capacity,upper_capacity,plant_ramp_up_delta, plant_ramp_down_delta, average_cost,base_or_peak,up_drawal=up_drawal))
           
            
    return plant_units

def get_hydro_maximum_for_constraint(plant_unit_timeblocks,plant_units):
    from statsmodels.tsa.api import SimpleExpSmoothing
    hydro_plant_data = plant_unit_timeblocks[plant_unit_timeblocks['plant_fuel_type']=='HYDRO']
    unique_names = (hydro_plant_data['plant_name'] + " unit:" + hydro_plant_data['actual_plant_unit'].astype(str)).unique()
    hydro_limit_dict = {}
    for name in unique_names:
        splitter = name.split(" unit:")
        plant_name = splitter[0]
        plant_unit_num = int(splitter[1])
        plant_data = hydro_plant_data[(hydro_plant_data['plant_name'] == plant_name) & (hydro_plant_data['actual_plant_unit'] == plant_unit_num)]
        plant_wise_hydro = plant_data.groupby('date').agg({'avg_unit_current_load':'sum'}).reset_index()['avg_unit_current_load']
        fit3 = SimpleExpSmoothing(plant_wise_hydro, initialization_method="estimated").fit()
        modeling_day_hydro_limit = float(fit3.forecast(1))
        hydro_limit_dict[name] = float(modeling_day_hydro_limit)
    
    for plant in plant_units:
        if plant.fuel_type == "HYDRO":
            plant.hydro_limit = hydro_limit_dict[plant.name]

    return hydro_limit_dict

def get_actuals_for_reporting(plant_unit_timeblocks):
    actuals_df = pd.DataFrame()
    
    actuals_df = plant_unit_timeblocks[['plant_name','actual_plant_unit','date','time_block_of_day','avg_unit_current_load']]
    actuals_df['plant_unit_name'] = plant_unit_timeblocks['plant_name'] + " unit:" + plant_unit_timeblocks['actual_plant_unit'].astype(str)
    actuals_df = actuals_df.drop(['plant_name','actual_plant_unit'],axis=1)
    actuals_df.to_csv('actuals.csv')

    actuals_data = actuals_df.set_index(['plant_unit_name','date','time_block_of_day']).T.to_dict()
    actuals_data = {key: value['avg_unit_current_load'] for (key, value) in actuals_data.items()}
    with open('actuals_dict.csv', 'w') as f:
        for key in actuals_data.keys():
            f.write("%s,%s\n"%(key,actuals_data[key]))
    return actuals_data
    
def get_actuals_df_for_reporting(plant_unit_timeblocks):
    actuals_df = plant_unit_timeblocks.copy()
    actuals_df['model_plant_name'] = actuals_df['plant_name'] + " unit:" + actuals_df['actual_plant_unit'].astype(str)
    actuals_df['model_plant_name']=actuals_df['model_plant_name'].replace(' ','_',regex=True)
    actuals_df = actuals_df.rename(columns = {'avg_unit_current_load':'actuals','time_block_of_day':'time_bucket'})
    actuals_df.drop('plant_ownership',inplace=True,axis=1)
    return actuals_df
   

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
    plant_units.append(PlantUnits(name,ownership,fuel_type,capacity,None,lower_capacity,upper_capacity,plant_ramp_up_delta,plant_ramp_down_delta,average_variable_cost,base_or_peak,None,None,None))

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
    demand_UP.to_csv('demand_UP.csv')

    demand_of_UP_bydate_byhour_units = []
    for index,demand_row in demand_UP.iterrows():
        demand_of_UP_bydate_byhour_units.append(Demand(demand_row['date'],demand_row['hour_of_day'],demand_row['time_block_of_day'],demand_row['avg_unit_current_load'],str(demand_row['date'])+"-"+str(demand_row['time_block_of_day'])))
    
    return demand_of_UP_bydate_byhour_units,demand_UP

#this is alternate to get_demand_data function for stress testing. Use this when aggregate demand is available instead of regular one 
def get_demand_data_from_a_file(demand_data_file_location):

    demand_UP = pd.read_csv(demand_data_file_location)
    demand_UP['date'] = pd.to_datetime(demand_UP['date']).dt.date
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

def get_peak_demand(demand_UP):
    peak_demand_by_date = demand_UP.groupby(['date']).agg({'avg_unit_current_load':'max'}).reset_index().set_index('date').T.to_dict(orient='records')
    return peak_demand_by_date

def get_max_capacity(plant_units):
    total_capacity = 0
    for plant in plant_units:
        total_capacity += plant.upper_capacity
    return total_capacity

def get_plant_start_type(plant_unit):

    if plant_unit.status_of_plant == 1:
        start_type = None
    else:
        if plant_unit.hours_switched_off < 10:
            start_type = 'hot_start'
        elif (plant_unit.hours_switched_off >10 and plant_unit.hours_switched_off <72):
            start_type = 'warm_start'
        else:
            start_type = 'cold_start'
    return start_type

def get_fixed_costs(FIXED_COSTS_FILE):
    fixed_costs = pd.read_csv(FIXED_COSTS_FILE).set_index(['plant_capacity','start_type']).T.to_dict()
    return fixed_costs

def get_plant_status(development_data,plant_units):
    dev_dates = sorted(development_data['date'].unique(),reverse=True)


    development_data['plf'] = development_data['avg_unit_current_load']/development_data['upsldc_unit_capacity']
    status_data = development_data.groupby(['plant_name','actual_plant_unit','date','time_block_of_day']).agg({'plf':'sum'}).reset_index()
    status_data['plant_unit_name'] = status_data['plant_name']+" unit:"+status_data['actual_plant_unit'].astype(str)
    status_data = status_data.set_index(['plant_unit_name','date','time_block_of_day']).drop(['plant_name','actual_plant_unit'],axis=1).to_dict()
    

    #finding the last 3 days from the development data 
    last_date = dev_dates[0]
    last_three_dates = dev_dates[:3] 

    #if the plant was over 10% at the last hour of the last day it is deemed on else off 
    checked_plants = {}
    for plant in plant_units:
        for date in last_three_dates:
            if date == last_date:
                key_to_look = (plant.name,last_date,96) 
                if key_to_look in status_data['plf']:
                    if status_data['plf'][key_to_look]>=0.10:
                        plant.status_of_plant = 1
                        plant.hours_switched_off = 0
                        checked_plants[plant] = 1 
                    else:
                        plant.status_of_plant = 0
                        plant.hours_switched_off=1

        #identifying the number of hours switched off if off         
        for date in last_three_dates:
            time_block_counter = 96
            while(time_block_counter!=0):
                for plant in plant_units:
                    if plant.status_of_plant == 0:
                        key_to_look = (plant.name,date,time_block_counter) 
                        if key_to_look in status_data['plf']:
                            if status_data['plf'][key_to_look]<=0.1:
                                if date == last_date:
                                    plant.hours_switched_off = abs((time_block_counter//4)-24)
                                elif date == last_date-timedelta(1):
                                    plant.hours_switched_off = abs((time_block_counter//4)-48)
                                else:
                                    plant.hours_switched_off = abs((time_block_counter//4)-72)
                time_block_counter -= 1

        for plant in plant_units:
            if plant.status_of_plant==0:
                if plant.hours_switched_off is None:
                    plant.hours_switched_off = 72

        
    return None 

def get_plant_fixed_cost_capacity_bucket(plant_units):
    for plant in plant_units:
        if plant.capacity<200:
            plant.fixed_cost_capacity_bucket = 200
        else:
            plant.fixed_cost_capacity_bucket = 500
    return None

def get_plant_units_from_plant_names(plant_names,plant_units):
    needed_plant_units = []
    for plant in plant_units:
        if plant.name in plant_names:
            needed_plant_units.append(plant)
    return needed_plant_units







        












