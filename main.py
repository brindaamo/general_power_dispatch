from utils import get_plant_characteristics, get_raw_data_by_time,reading_input_data,get_demand_data
from utils import FILE_NAME,DEVELOPMENT_PERIOD_END_TIME,DEVELOPMENT_PERIOD_START_TIME,MODEL_PERIOD_END_TIME,MODEL_PERIOD_START_TIME
from optimization import reading_optimization_data,creating_optimization_instance,solving_optimization_instance
from data_validations import capacity_checks_of_plants,cost_checks_of_plant
#---------------------data preprocessing-------------------------
#reading the raw data 
raw_data = reading_input_data(file_name=FILE_NAME)

#getting development and model data from raw data by time
development_data = get_raw_data_by_time(raw_data,DEVELOPMENT_PERIOD_START_TIME, DEVELOPMENT_PERIOD_END_TIME)
model_data = get_raw_data_by_time(raw_data,MODEL_PERIOD_START_TIME,MODEL_PERIOD_END_TIME)

#getting plant characteristics from development data 
plant_units = get_plant_characteristics(raw_data)

#getting demand data 
demand_of_UP_bydate_byhour_units,demand_UP = get_demand_data(model_data)

#run the data validations 
print(capacity_checks_of_plants(plant_units))
print(cost_checks_of_plant(plant_units))


#reading optimization data 
scheduling_hours, scheduling_dates, plant_names, plant_production_costs, plant_capacity = reading_optimization_data(plant_units,demand_UP)


#------------------optimization-----------------
#creating optimization instance 
prob = creating_optimization_instance(demand_of_UP_bydate_byhour_units,scheduling_hours, scheduling_dates, plant_names, plant_production_costs, plant_capacity)

#solving and writing outputs in a file 
solving_optimization_instance(prob)








