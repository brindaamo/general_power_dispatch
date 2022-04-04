from pulp import *

def reading_optimization_data(plant_units,demand_UP):
    
    plant_names = []
    plant_production_costs = {}
    plant_capacity = {}
    for plant in plant_units:
        if(plant.average_variable_cost>0):

            plant_names.append(plant.name)
            plant_production_costs[plant.name] = plant.average_variable_cost
            plant_capacity[plant.name] = plant.capacity


    scheduling_time_blocks = list(range(1,97))
    scheduling_dates =  demand_UP['date'].unique()

    return scheduling_time_blocks, scheduling_dates, plant_names, plant_production_costs, plant_capacity

def creating_optimization_instance(demand_values,scheduling_time_blocks, scheduling_dates, plant_names, plant_production_costs, plant_capacity):
    
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

    return prob

def solving_optimization_instance(prob):
    prob.solve()
    
    #status of solving the optimization problem
    print("Status:", LpStatus[prob.status])

    #optimal objective value
    print("Total cost of production = ", value(prob.objective))

    output = ''
    output += str(value(prob.objective)) + "\n"
    for v in prob.variables():
        if v.varValue>0:
            output += v.name + "=" + str(v.varValue) + "\n" 

    with open("optimization_solution.txt", "w") as text_file:
        text_file.write(output)

    return None


