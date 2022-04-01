from statistics import mean
from demand_model import Demand
from utils import MODEL_PERIOD_END_TIME, MODEL_PERIOD_START_TIME
from datetime import date,timedelta


def capacity_checks_of_plants(plant_units):
    for plant in plant_units:
        if plant.capacity <= 0:
            return 'This plant unit has wrong capacity' + plant.name 
     
    return 'capacity checks done'

def cost_checks_of_plant(plant_units):
    for plant in plant_units:
        if plant.average_variable_cost <= 0:
            return 'This plant unit has wrong capacity' + plant.name 
    return 'cost checks done'

def filling_missing_demand_withmean(demand_of_UP_bydate_byhour_units):
    average_demand_list = []
    average_demand_dict = {}

    for hour in range(0,24):
        for demand_block in demand_of_UP_bydate_byhour_units:
            if demand_block.hour == hour:
                average_demand_list.append(demand_block.demand_val)
    return average_demand_dict
    
 
def missing_demand_at_timeblock_level(demand_values,average_demand_dict):
    unique_time_blocks = []

    def daterange(start_date, end_date):
        for n in range(int((end_date - start_date).days)):
            yield start_date + timedelta(n)

    start_date = MODEL_PERIOD_START_TIME
    end_date = MODEL_PERIOD_END_TIME
    for single_date in daterange(start_date, end_date):
        for time_block in range(1,97):
            unique_time_blocks.append(single_date.strftime("%Y-%m-%d") + str('-') + str(time_block))


    for time_block in unique_time_blocks:
        if time_block not in demand_values.keys():
            print(time_block)
    return None