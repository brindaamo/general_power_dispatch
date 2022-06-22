from datetime import datetime
import pandas as pd
from utils import get_plant_characteristics, get_raw_data_by_time,reading_input_data,get_demand_data,assign_hydro_as_peak,get_demand_based_on_profile,add_new_plants
from utils import INPUT_RAW_FILE_NAME,DEVELOPMENT_PERIOD_END_TIME,DEVELOPMENT_PERIOD_START_TIME,MODEL_PERIOD_END_TIME,MODEL_PERIOD_START_TIME,OUTPUT_ACTUALS_FOLDER,OUTPUT_SOLUTION_FOLDER,MONTH,DEMAND_PROFILE
from optimization import reading_optimization_data,creating_optimization_instance,solving_optimization_instance
from data_validations_preprocessing import capacity_checks_of_plants,cost_checks_of_plant,filling_missing_demand_withmean,missing_demand_at_timeblock_level_and_filling
from output_validations import output_formatting,output_plant_chars
#---------------------data preprocessing-------------------------
#reading the raw data 
raw_data = reading_input_data(file_name=INPUT_RAW_FILE_NAME)

#getting development and model data from raw data by time
development_data = get_raw_data_by_time(raw_data,DEVELOPMENT_PERIOD_START_TIME, DEVELOPMENT_PERIOD_END_TIME)
model_data = get_raw_data_by_time(raw_data,MODEL_PERIOD_START_TIME,MODEL_PERIOD_END_TIME)


#getting plant characteristics from development data 
plant_units = get_plant_characteristics(raw_data)
assign_hydro_as_peak(plant_units)

#RUN THIS FUNCTION TO ADD NEW PLANTS UNITS WITH THE RIGHT VALUES 
#name, ownership, fuel_type, capacity,average_variable_cost - THIS IS THE INFORMATION THAT IS NEEDED 
#adding new plant units into the model

# plant_units = add_new_plants(plant_units,name='something', ownership='something', fuel_type='something', capacity=100,average_variable_cost=2)


#getting demand data 
demand_of_UP_bydate_byhour_units,demand_UP = get_demand_data(model_data)
demand_of_UP_bydate_byhour_units,demand_UP = get_demand_based_on_profile(demand_of_UP_bydate_byhour_units,demand_UP,DEMAND_PROFILE)

#run the data validations 
print(capacity_checks_of_plants(plant_units))
print(cost_checks_of_plant(plant_units))
average_demand_dict=filling_missing_demand_withmean(demand_of_UP_bydate_byhour_units)
demand_of_UP_bydate_byhour_units_filled,demand_values_filled = missing_demand_at_timeblock_level_and_filling(demand_of_UP_bydate_byhour_units,average_demand_dict)


#reading optimization data 
scheduling_hours, scheduling_dates, plant_names, plant_production_costs,plant_thermal_effeciencies, plant_upper_capacity,plant_lower_capacity,plant_ramp_up_deltas,plant_ramp_down_deltas = reading_optimization_data(plant_units,demand_UP)



# ------------------optimization-----------------
# creating optimization instance 
prob = creating_optimization_instance(demand_values_filled,scheduling_hours, scheduling_dates, plant_names, plant_production_costs,plant_thermal_effeciencies, plant_upper_capacity,plant_lower_capacity,plant_ramp_up_deltas,plant_ramp_down_deltas)

#------------------checking the output validations----------------

#solving and writing outputs in a file 
solution_status,output = solving_optimization_instance(prob)

#writing the output and solution status into a file 
location_and_name_of_solution_status = OUTPUT_SOLUTION_FOLDER + "/" + MONTH + "_solution_status.txt"
with open(location_and_name_of_solution_status, "w") as text_file:
        text_file.write(solution_status)

with open("optimization_solution_with_new_constraints.txt", "w") as text_file:
        text_file.write(output)


#checking if the output follows the constraints and getting the capacities utilized 
opti_solution_json = output_formatting(optimization_solution='optimization_solution_with_new_constraints.txt')
output_plant_chars_added = output_plant_chars(opti_solution_json,plant_units)
# adding_ramp_up_down = add_plant_percent_ramp_up_or_down(capacity_constraint_checks)
output_plant_chars_added_to_json = pd.read_json(output_plant_chars_added)


opti_solution_location = OUTPUT_SOLUTION_FOLDER +"/"+ MONTH + "__opti_solution_"+DEMAND_PROFILE+"_"+str(datetime.now().date())+".csv"
output_plant_chars_added_to_json.to_csv(opti_solution_location,index=False)

# # # #output of actuals in a csv for comparison with model 
# # # # actuals_location = OUTPUT_ACTUALS_FOLDER +"/"+ MONTH +"_actuals"+ ".csv"
# # # # model_data.to_csv(actuals_location)







