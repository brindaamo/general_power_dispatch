from utils import get_demand_data,get_plant_characteristics

def output_formatting(optimization_solution):
    #output should be a json file with plant_name, date, timeblock and production_units
    return None

def demand_satisfaction_constraint_check(optimization_solution,demand_values):
    #input of this function is from demand_values_filled missing_demand_at_timeblock_level_and_filling
    # this is a dictionary with key in the format of 'yyyy-mm-dd-time_block' and value is the demand value  
    # 
    return None

def capacity_constraint_check():
    #every plant needs to run at a capacity that is not exceeding the maximum capacity of the plant
    #the percentage at which the plant is working at 
    return None
