from utils import get_demand_data,get_plant_characteristics

def output_formatting(optimization_solution):
    #output should be a json file with plant_name, date, timeblock and production_units
    return None

def demand_satisfaction_constraint_check(optimization_solution,demand_of_UP_bydate_byhour_units):
    #first input parameter needs to be changed to optimization output formatted 
    #demand of UP by hour needs to be satisfied summed across plant units 
    return None

def capacity_constraint_check():
    #every plant needs to run at a capacity that is not exceeding the maximum capacity of the plant
    #the percentage at which the plant is working at 
    return None
