from pulp import *
from datetime import timedelta

from utils import MONTH

def reading_optimization_data(plant_units,demand_UP):
    
    plant_names = []
    plant_production_costs = {}
    plant_capacity = {}
    plant_ramp_up_deltas = {}
    plant_ramp_down_deltas = {}
    for plant in plant_units:
        if(plant.average_variable_cost>0):
            plant_names.append(plant.name)
            plant_production_costs[plant.name] = plant.average_variable_cost
            plant_capacity[plant.name] = plant.capacity
            plant_ramp_up_deltas[plant.name] = plant.ramp_up_delta
            plant_ramp_down_deltas[plant.name] = plant.ramp_down_delta

    scheduling_time_blocks = list(range(1,97))
    scheduling_dates =  sorted(demand_UP['date'].unique())

    return scheduling_time_blocks, scheduling_dates, plant_names, plant_production_costs, plant_capacity,plant_ramp_up_deltas,plant_ramp_down_deltas

def creating_optimization_instance(demand_values,scheduling_time_blocks, scheduling_dates, plant_names, plant_production_costs, plant_capacity,plant_ramp_up_deltas,plant_ramp_down_deltas):
    
    #creating the LP problem instance
    prob = LpProblem("production_cost_minimization", LpMinimize)

    #Creating the production variables
    production_vars = LpVariable.dicts(name = "production_units",indices = [(i,j,k) for i in plant_names for j in scheduling_dates for k in scheduling_time_blocks],lowBound=0)

    #LP Objective function 
    prob += lpSum([plant_production_costs[i]*production_vars[(i,j,k)] for i in plant_names for j in scheduling_dates for k in scheduling_time_blocks]), "Sum of production costs"

    #Adding constraints to the model
    #Demand constraints
    #for every date, every hour, demand[date][hour] has to be satisfied
    

    for date in scheduling_dates:
        for time_block in scheduling_time_blocks:
            demand_date_timeblock = str(date) + "-"+str(time_block)
            prob+= (lpSum(production_vars[(plant,date,time_block)] for plant in plant_names) >= demand_values[demand_date_timeblock])


    # capacity constraint 
    # capacity of the power plant cannot be exceeded at any hour

    for plant in plant_names:
        for date in scheduling_dates:
            for time_block in scheduling_time_blocks:
                prob += production_vars[(plant,date,time_block)] <= plant_capacity[plant]

    #ramp up constraints 
    for plant in plant_names:
        if plant != 'UP DRAWAL unit:0':
            for date in scheduling_dates:
                for time_block in scheduling_time_blocks[:-1]:
                    prob += production_vars[(plant,date,time_block+1)] - production_vars[(plant,date,time_block)]<= plant_ramp_up_deltas[plant]

    #ramp up constraints for the last time block connecting to the next day
    for plant in plant_names:
        if plant != 'UP DRAWAL unit:0':
            for today in scheduling_dates[:-1]:
                tomorrow = today+timedelta(1)
                prob += production_vars[(plant,tomorrow,1)] - production_vars[(plant,today,96)]<= plant_ramp_up_deltas[plant]

    #ramp down constraints 
    for plant in plant_names:
        if plant != 'UP DRAWAL unit:0':
            for date in scheduling_dates:
                for time_block in scheduling_time_blocks[:-1]:
                    prob +=  production_vars[(plant,date,time_block)] - production_vars[(plant,date,time_block+1)]<= plant_ramp_down_deltas[plant]

    #ramp down constraints for the last time block connecting to the next day
    for plant in plant_names:
        if plant != 'UP DRAWAL unit:0':
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


