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


    scheduling_hours = list(range(0,24))
    scheduling_dates =  demand_UP['date'].unique()

    return scheduling_hours, scheduling_dates, plant_names, plant_production_costs, plant_capacity

def creating_optimization_instance(demand_of_UP_bydate_byhour_units,scheduling_hours, scheduling_dates, plant_names, plant_production_costs, plant_capacity):
    
    #creating the LP problem instance
    prob = LpProblem("production_cost_minimization", LpMinimize)

    #Creating the production variables
    production_vars = LpVariable.dicts(name = "production_units",indices = [(i,j,k) for i in plant_names for j in scheduling_dates for k in scheduling_hours],lowBound=0)

    #LP Objective function 
    prob += lpSum([plant_production_costs[i]*production_vars[(i,j,k)] for i in plant_names for j in scheduling_dates for k in scheduling_hours]), "Sum of production costs"

    #Adding constraints to the model
    #Demand constraints
    #for every date, every hour, demand[date][hour] has to be satisfied
    demand_values = {} 
    for item in demand_of_UP_bydate_byhour_units:
        demand_key = str(item.date) + "-" +str(item.hour)
        demand_values[demand_key] = item.demand_val

    for date in scheduling_dates:
        for hour in scheduling_hours:
            demand_date_hour = str(date) + "-"+str(hour)
            prob+= (lpSum(production_vars[(plant,date,hour)] for plant in plant_names) >= demand_values[demand_date_hour])


    # capacity constraint 
    # capacity of the power plant cannot be exceeded at any hour

    for plant in plant_names:
        for date in scheduling_dates:
            for hour in scheduling_hours:
                prob += production_vars[(plant,date,hour)] <= plant_capacity[plant]

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


