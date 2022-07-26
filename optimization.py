from pickle import OBJ
from pulp import *
from datetime import timedelta

from utils import MONTH,OBJECTIVE

def reading_optimization_data(plant_units,demand_UP,fixed_costs):
    
    plant_names = []
    plant_production_costs = {}
    plant_thermal_effeciencies = {}
    plant_upper_capacity = {}
    plant_lower_capacity ={}
    plant_ramp_up_deltas = {}
    plant_ramp_down_deltas = {}
    plant_fixed_costs = {}
    for plant in plant_units:
        if(plant.average_variable_cost>0):
            plant_names.append(plant.name)
            plant_production_costs[plant.name] = plant.average_variable_cost
            plant_thermal_effeciencies[plant.name] = plant.plant_thermal_effeciency
            plant_upper_capacity[plant.name] = plant.upper_capacity
            plant_lower_capacity[plant.name] = plant.lower_capacity
            plant_ramp_up_deltas[plant.name] = plant.ramp_up_delta
            plant_ramp_down_deltas[plant.name] = plant.ramp_down_delta
            plant_fixed_costs[plant.name] = fixed_costs[(plant.fixed_cost_capacity_bucket,plant.start_type)]

    scheduling_time_blocks = list(range(1,97))
    scheduling_dates =  sorted(demand_UP['date'].unique())
    

    return scheduling_time_blocks, scheduling_dates, plant_names, plant_production_costs,plant_thermal_effeciencies, plant_upper_capacity,plant_lower_capacity,plant_ramp_up_deltas,plant_ramp_down_deltas

def creating_optimization_instance_primary_problem(plant_units,plant_names,plant_production_costs,peak_demand,plant_fixed_costs):
    
    #creating the objective function 
    primary_opti_prob = LpProblem("production_cost_minimization", LpMinimize)

    #creating the vatiables 
    production_vars = LpVariable.dicts(name = "productionUnits",indices = [i for i in plant_names],lowBound=0)
    plant_off_or_on = LpVariable.dict(name="powerOnOff",indices = [i for i in plant_names],cat='Binary')

    #demand_satisfaction_constraints
    for plant in plant_units:
        total_capacity += plant.upper_capacity
    demand_considered = min(peak_demand,total_capacity)
    
    primary_opti_prob+= (lpSum(production_vars[plant] for plant in plant_names) >= 1)
    
    
    #capacity constraints 
    normalized_upper_capacity = {}
    for plant in plant_units:
        if(plant.average_variable_cost>0):
            normalized_upper_capacity[plant.name] = plant.upper_capacity/demand_considered
    
    for plant in plant_names:
        primary_opti_prob += production_vars[plant] <= normalized_upper_capacity[plant]
    
    #this constraint ensures that the a plant is on only when there is production
    #other constraints 
    for plant in plant_names:
        primary_opti_prob += plant_off_or_on[plant] >= production_vars[plant]

    #objective function
    primary_opti_prob += lpSum(plant_fixed_costs[plant]*plant_off_or_on[plant] for plant in plant_names) + lpSum(plant_production_costs[plant] for plant in plant_names)
    
    return primary_opti_prob

def solving_optimization_instance(primary_opti_prob):
    primary_opti_prob.solve()
    
    solution_status = ""
    #status of solving the optimization problem
    solution_status += MONTH + "\n"
    solution_status += "Status:" + LpStatus[primary_opti_prob.status] + "\n"

    #optimal objective value
    solution_status += "Total cost of production = " + str(value(primary_opti_prob.objective)) + "\n"

    output = ''
    for v in primary_opti_prob.variables():
        if v.varValue>0:
            output += v.name + "=" + str(v.varValue) + "\n" 
    
    return solution_status,output
    

def creating_optimization_instance(demand_values,scheduling_time_blocks, scheduling_dates, plant_names, plant_production_costs,plant_thermal_effeciencies, plant_upper_capacity,plant_lower_capacity,plant_ramp_up_deltas,plant_ramp_down_deltas):
    
    #creating the LP problem instance
    if OBJECTIVE == 'cost':
        prob = LpProblem("production_cost_minimization", LpMinimize)
    elif OBJECTIVE == 'effeciency':
        prob = LpProblem("effienciecy_maximization", LpMinimize)

    #Creating the production variables
    production_vars = LpVariable.dicts(name = "production_units",indices = [(i,j,k) for i in plant_names for j in scheduling_dates for k in scheduling_time_blocks],lowBound=0)

    #LP Objective function 
    if OBJECTIVE == 'cost':
        prob += lpSum([plant_production_costs[i]*production_vars[(i,j,k)] for i in plant_names for j in scheduling_dates for k in scheduling_time_blocks]), "Sum of production costs"
    elif OBJECTIVE == 'effeciency':
        prob += lpSum([plant_thermal_effeciencies[i]*production_vars[(i,j,k)] for i in plant_names for j in scheduling_dates for k in scheduling_time_blocks]), "Sum of production costs"


    #Adding constraints to the model
    #Demand constraints
    #for every date, every hour, demand[date][hour] has to be satisfied
    
    
    for date in scheduling_dates:
        for time_block in scheduling_time_blocks:
            demand_date_timeblock = str(date) + "-"+str(time_block)
            prob+= (lpSum(production_vars[(plant,date,time_block)] for plant in plant_names) >= demand_values[demand_date_timeblock])


    # capacity constraint 
    # capacity of the power plant cannot be exceeded at any time block

    for plant in plant_names:
        for date in scheduling_dates:
            for time_block in scheduling_time_blocks:
                prob += production_vars[(plant,date,time_block)] <= plant_upper_capacity[plant]
    
    for plant in plant_names:
        for date in scheduling_dates:
            for time_block in scheduling_time_blocks:
                prob += production_vars[(plant,date,time_block)] >= plant_lower_capacity[plant]

    #ramp up constraints 
    for plant in plant_names:
        # if plant != 'UP DRAWAL unit:0':
        for date in scheduling_dates:
            for time_block in scheduling_time_blocks[:-1]:
                prob += production_vars[(plant,date,time_block+1)] - production_vars[(plant,date,time_block)]<= plant_ramp_up_deltas[plant]

    #ramp up constraints for the last time block connecting to the next day
    for plant in plant_names:
        # if plant != 'UP DRAWAL unit:0':
        for today in scheduling_dates[:-1]:
            tomorrow = today+timedelta(1)
            prob += production_vars[(plant,tomorrow,1)] - production_vars[(plant,today,96)]<= plant_ramp_up_deltas[plant]

    #ramp down constraints 
    for plant in plant_names:
        # if plant != 'UP DRAWAL unit:0':
        for date in scheduling_dates:
            for time_block in scheduling_time_blocks[:-1]:
                prob +=  production_vars[(plant,date,time_block)] - production_vars[(plant,date,time_block+1)]<= plant_ramp_down_deltas[plant]

    #ramp down constraints for the last time block connecting to the next day
    for plant in plant_names:
        # if plant != 'UP DRAWAL unit:0':
        for today in scheduling_dates[:-1]:
            tomorrow = today+timedelta(1)
            prob += production_vars[(plant,today,96)] - production_vars[(plant,tomorrow,1)]<= plant_ramp_down_deltas[plant]

        return prob

def solving_optimization_instance(prob):
    prob.solve()
    
    solution_status = ""
    #status of solving the optimization problem
    solution_status += MONTH + "\n"
    solution_status += "Status:" + LpStatus[prob.status] + "\n"

    #optimal objective value
    solution_status += "Total cost of production = " + str(value(prob.objective)) + "\n"

    output = ''
    output += str(value(prob.objective)) + "\n"
    for v in prob.variables():
        if v.varValue>0:
            output += v.name + "=" + str(v.varValue) + "\n" 
    

    return solution_status,output


