from datetime import datetime
import pandas as pd
import time 
from utils import get_fixed_costs, get_hydro_maximum_for_constraint,get_max_capacity, get_only_thermal_power_plant, get_peak_demand, get_plant_start_type,get_thermal_effeciency,get_plant_characteristics, get_raw_data_by_time,converting_to_datetime,get_demand_data,assign_hydro_as_peak,get_demand_based_on_profile,add_new_plants,get_plant_status,get_plant_fixed_cost_capacity_bucket,get_plant_units_from_plant_names,combine_inputs_into_a_single_file,get_actuals_for_reporting,get_up_drawal_plant_capacity,get_actuals_df_for_reporting,get_demand_data_from_a_file
from utils import INPUT_THERMAL_EFFECIENCY_FILE_NAME,INPUT_FILE_LOCATION,DEVELOPMENT_PERIOD_END_TIME,DEVELOPMENT_PERIOD_START_TIME,MODEL_PERIOD_END_TIME,MODEL_PERIOD_START_TIME,OUTPUT_ACTUALS_FOLDER,OUTPUT_SOLUTION_FOLDER,MONTH,DEMAND_PROFILE,INPUT_FIXED_COSTS_DATA,DEMAND_DATA_FILE_LOCATION
from optimization import creating_optimization_instance_primary_problem, reading_optimization_data,creating_optimization_instance,solving_optimization_instance
from data_validations_preprocessing import capacity_checks_of_plants,cost_checks_of_plant,filling_missing_demand_withmean,missing_demand_at_timeblock_level_and_filling
from  output_formatting import converting_outputs_to_df,output_formatting_primary_opti_solution
#---------------------data preprocessing-------------------------
#reading the raw data 
t0=time.time()
input_files = combine_inputs_into_a_single_file(INPUT_FILE_LOCATION)
raw_data = converting_to_datetime(input_files)

#getting development and model data from raw data by time
development_data = get_raw_data_by_time(raw_data,DEVELOPMENT_PERIOD_START_TIME, DEVELOPMENT_PERIOD_END_TIME)
model_data = get_raw_data_by_time(raw_data,MODEL_PERIOD_START_TIME,MODEL_PERIOD_END_TIME)


#getting plant characteristics from development data 
up_drawal_capacity = get_up_drawal_plant_capacity(development_data,'UP DRAWAL')
plant_units = get_plant_characteristics(development_data,up_drawal_capacity)
actuals_data = get_actuals_for_reporting(model_data)
actuals_df = get_actuals_df_for_reporting(model_data)
get_plant_status(development_data,plant_units)
hydro_limits_dict=get_hydro_maximum_for_constraint(development_data,plant_units)
for plant in plant_units:
        plant.start_type = get_plant_start_type(plant)  
get_plant_fixed_cost_capacity_bucket(plant_units)      

#getting demand data 
# demand_of_UP_bydate_byhour_units,demand_UP = get_demand_data(model_data)
# demand_of_UP_bydate_byhour_units,demand_UP = get_demand_based_on_profile(demand_of_UP_bydate_byhour_units,demand_UP,DEMAND_PROFILE)

#use this when stress testing with the right file 
demand_of_UP_bydate_byhour_units,demand_UP = get_demand_data_from_a_file(DEMAND_DATA_FILE_LOCATION)

#run the data validations 
print(capacity_checks_of_plants(plant_units))
print(cost_checks_of_plant(plant_units))
average_demand_dict=filling_missing_demand_withmean(demand_of_UP_bydate_byhour_units)
demand_of_UP_bydate_byhour_units_filled,demand_values_filled = missing_demand_at_timeblock_level_and_filling(demand_of_UP_bydate_byhour_units,average_demand_dict)




#reading optimization data 
plant_fixed_costs = get_fixed_costs(INPUT_FIXED_COSTS_DATA)
total_capacity = get_max_capacity(plant_units)
peak_demand = 1.5*max(get_peak_demand(demand_UP)[0].values())
scheduling_time_blocks, scheduling_dates, plant_names, plant_production_costs,plant_thermal_effeciencies, plant_upper_capacity,plant_lower_capacity,plant_ramp_up_deltas,plant_ramp_down_deltas,fixed_costs,up_drawal_ramp_up,up_drawal_ramp_down = reading_optimization_data(plant_units,demand_UP,plant_fixed_costs)

# ------------------optimization-----------------
# creating and solving primary optimization instance for primary problem
primary_opti_prob = creating_optimization_instance_primary_problem(plant_units,plant_names,plant_production_costs,peak_demand,fixed_costs)
primary_solution_status,primary_output = solving_optimization_instance(primary_opti_prob)
chosen_plant_names = output_formatting_primary_opti_solution(primary_output)
pd.DataFrame(chosen_plant_names.items()).to_csv('chosen_plants.csv')

#solving the secondary problem
chosen_plant_units = get_plant_units_from_plant_names(chosen_plant_names.keys(),plant_units)
scheduling_time_blocks, scheduling_dates, plant_names, plant_production_costs,plant_thermal_effeciencies, plant_upper_capacity,plant_lower_capacity,plant_ramp_up_deltas,plant_ramp_down_deltas,fixed_costs,up_drawal_ramp_up,up_drawal_ramp_down = reading_optimization_data(chosen_plant_units,demand_UP,plant_fixed_costs)
prob = creating_optimization_instance(demand_values_filled,scheduling_time_blocks, scheduling_dates,chosen_plant_units,plant_names, plant_production_costs,plant_thermal_effeciencies, plant_upper_capacity,plant_lower_capacity,plant_ramp_up_deltas,plant_ramp_down_deltas,up_drawal_capacity,up_drawal_ramp_up,up_drawal_ramp_down,hydro_limits_dict)
solution_status,secondary_output = solving_optimization_instance(prob)
# #------------------checking the output validations----------------

# #writing outputs in a file 

# #writing the output and solution status into a file 
location_and_name_of_solution_status = OUTPUT_SOLUTION_FOLDER + "/" + MONTH + "_solution_status.txt"
with open(location_and_name_of_solution_status, "w") as text_file:
        text_file.write(solution_status)

with open("optimization_solution_with_new_constraints.txt", "w") as text_file:
        text_file.write(secondary_output)

actuals_df = get_actuals_df_for_reporting(model_data)
opti_output,opti_final_output_with_actuals = converting_outputs_to_df(plant_units,scheduling_time_blocks,scheduling_dates,plant_names,demand_of_UP_bydate_byhour_units,actuals_data,actuals_df)

opti_solution_location = OUTPUT_SOLUTION_FOLDER +"/"+ MONTH + "__opti_solution_"+DEMAND_PROFILE+"_"+str(datetime.now().date())+".csv"
opti_final_output_with_actuals.to_csv(opti_solution_location,index=False)
print(time.time() - t0)


# # output of actuals in a csv for comparison with model 
# actuals_location = OUTPUT_ACTUALS_FOLDER +"/"+ MONTH +"_actuals"+ ".csv"
# model_data.to_csv(actuals_location)








