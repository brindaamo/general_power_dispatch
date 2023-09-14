from pickle import OBJ
from pulp import *
from datetime import timedelta,datetime
from input_module import InputModels

from utils import get_dates_between

class Optimization(InputModels):
    
    #this function reads the optimization data
    def reading_optimization_data(self):
        """
        This function reads the optimization data from the input models and stores it in class variables.
        
        Returns:
            tuple: A tuple containing the following data in order:
                - list: Plant names.
                - dict: Plant production costs, keyed by plant name.
                - dict: Plant lower capacities, keyed by plant name.
                - dict: Plant upper capacities, keyed by plant name.
                - dict: Plant ramp-up deltas, keyed by plant name.
                - dict: Plant ramp-down deltas, keyed by plant name.
                - dict: Demand values, keyed by date and time block.
        """
        
        self.plant_names = []
        self.plant_production_costs = {}
        self.plant_upper_capacity = {}
        self.plant_lower_capacity ={}
        self.plant_ramp_up_deltas = {}
        self.plant_ramp_down_deltas = {}
        self.demand_values = {}
        self.startup_costs = {}
        self.hydro_forecasts = {}


        for plant in self.power_plants:
            if(plant.average_variable_cost>0):
                self.plant_names.append(plant.name)
                self.plant_production_costs[plant.name] = plant.average_variable_cost
                self.plant_upper_capacity[plant.name] = plant.upper_capacity
                self.plant_lower_capacity[plant.name] = plant.lower_capacity
                self.plant_ramp_up_deltas[plant.name] = plant.ramp_up_delta
                self.plant_ramp_down_deltas[plant.name] = plant.ramp_down_delta
                self.startup_costs[plant.name] = plant.startup_cost
                self.hydro_forecasts[plant.name] = plant.hydro_limit

            self.scheduling_time_blocks = list(range(1,97))
            self.scheduling_dates =  sorted(get_dates_between(self.start_date,self.end_date))
        
        for demand in self.demand_data:
            self.demand_values[demand.date_time_block] = demand.demand_val
            
        return self.plant_names,self.plant_production_costs,self.plant_lower_capacity,self.plant_upper_capacity,self.plant_ramp_up_deltas,self.plant_ramp_down_deltas,self.demand_values
        
    def creating_optimization_instance_primary_problem(self):

        """
        Creates and returns the primary optimization problem instance for production cost minimization.
        
        Returns:
            LpProblem: The primary optimization problem instance.
        """
        
        #creating the objective function 
        self.primary_opti_prob = LpProblem("production_cost_minimization", LpMinimize)

        #creating the vatiables 
        production_vars = LpVariable.dicts(name = "productionUnits,",indices = [i for i in self.plant_names if i != 'excess plant'],lowBound=0)
        plant_off_or_on = LpVariable.dict(name="powerOnOff,",indices = [i for i in self.plant_names if i != 'excess plant'],cat='Binary')

        #demand_satisfaction_constraints
        total_capacity = 0
        for plant in self.power_plants:
            if plant.name != 'excess plant':
                total_capacity += plant.upper_capacity
        demand_considered = min(self.peak_demand,total_capacity)
        
        self.primary_opti_prob+= (lpSum(production_vars[plant] for plant in self.plant_names if plant != 'excess plant') >= 1
        
        )
        #capacity constraints 
        normalized_upper_capacity = {}
        for plant in self.power_plants:
            if(plant.average_variable_cost>0):
                if plant.name != 'excess plant':
                    normalized_upper_capacity[plant.name] = plant.upper_capacity/demand_considered
        
        for plant in self.plant_names:
            if plant != 'excess plant':
                self.primary_opti_prob += production_vars[plant] <= normalized_upper_capacity[plant]
        
        #this constraint ensures that the a plant is on only when there is production
        #other constraints 
        for plant in self.plant_names:
            if plant != 'excess plant':
                self.primary_opti_prob += plant_off_or_on[plant] >= production_vars[plant]

        #objective function
        self.primary_opti_prob += lpSum(self.startup_costs[plant] * plant_off_or_on[plant] for plant in self.plant_names if plant != 'excess plant') + lpSum(self.plant_production_costs[plant] for plant in self.plant_names if plant != 'excess plant')

        with open("lp_problem.txt", "w") as file:
            file.write(str(self.primary_opti_prob))


        return self.primary_opti_prob
    
    def solving_primary_optimization(self):

        """
        Solves the primary optimization problem and returns the solution status and output.

        Returns:
            tuple: A tuple containing the following data in order:
                - str: The status of solving the optimization problem.
                - str: The output containing the variable values with non-zero production.
        """
        self.primary_opti_prob.solve()
        
        self.primary_status = ""
        #status of solving the optimization problem
        self.primary_status += "Status:" + LpStatus[self.primary_opti_prob.status] + "\n"

        #optimal objective value
        self.primary_status += "Total cost of production = " + str(value(self.primary_opti_prob.objective)) + "\n"

        self.primary_output = ''
        for v in self.primary_opti_prob.variables():
            if v.varValue>0:
                self.primary_output += v.name + "=" + str(v.varValue) + "\n" 

        return self.primary_status,self.primary_output
        

    def creating_optimization_instance(self):

        """
        Creates and returns the secondary optimization problem instance for production cost minimization.

        Returns:
            LpProblem: The secondary optimization problem instance.
        """

        #chosen plants names list from the primary optimization problem 
        self.chosen_plant_names = list(self.primarysolution_output_dictionary.keys())
        self.chosen_plant_names.append('excess plant')

        #chosen plants list from the names 
        self.chosen_plants = [plant for plant in self.power_plants if plant.name in self.chosen_plant_names]
        
        self.prob = LpProblem("production_cost_minimization", LpMinimize)
      

        #Creating the production variables
        production_vars = LpVariable.dicts(name = "production_units",indices = [(i,j,k) for i in self.chosen_plant_names for j in self.scheduling_dates for k in self.scheduling_time_blocks],lowBound=0)

        #LP Objective function 
        self.prob += lpSum([self.plant_production_costs[i]*production_vars[(i,j,k)] for i in self.chosen_plant_names for j in self.scheduling_dates for k in self.scheduling_time_blocks]), "Sum of production costs"
        
        
        #Adding constraints to the model
        #Demand constraints
        #for every date, every hour, demand[date][hour] has to be satisfied
        
        for date in self.scheduling_dates:
            for time_block in self.scheduling_time_blocks:
                demand_date_timeblock = date.strftime('%Y-%m-%d') + "-"+str(time_block)
                self.prob+= (lpSum(production_vars[(plant,date,time_block)] for plant in self.chosen_plant_names) >= self.demand_values[demand_date_timeblock])


        # capacity constraint 
        # capacity of the power plant cannot be exceeded at any time block

        for plant in self.chosen_plant_names:
            for date in self.scheduling_dates:
                for time_block in self.scheduling_time_blocks:
                    self.prob += production_vars[(plant,date,time_block)] <= self.plant_upper_capacity[plant]
                          
        for plant in self.chosen_plants:
            for date in self.scheduling_dates:
                for time_block in self.scheduling_time_blocks:
                    if plant.fuel_type != "HYDRO":
                        self.prob += production_vars[(plant.name,date,time_block)] >= plant.lower_capacity
        

        #ramp up constraints 
        for plant in self.chosen_plant_names:
            if plant not in 'excess plant':
                for date in self.scheduling_dates:
                    for time_block in self.scheduling_time_blocks[:-1]:
                        self.prob += production_vars[(plant,date,time_block+1)] - production_vars[(plant,date,time_block)]<= self.plant_ramp_up_deltas[plant]

        #ramp up constraints for the last time block connecting to the next day
        for plant in self.chosen_plant_names:
            if plant not in 'excess plant':
                for today in self.scheduling_dates[:-1]:
                    tomorrow = today+timedelta(1)
                    self.prob += production_vars[(plant,tomorrow,1)] - production_vars[(plant,today,96)]<= self.plant_ramp_up_deltas[plant]

        #ramp down constraints 
        for plant in self.chosen_plant_names:
            if plant not in 'excess plant':
                for date in self.scheduling_dates:
                    for time_block in self.scheduling_time_blocks[:-1]:
                        self.prob +=  production_vars[(plant,date,time_block)] - production_vars[(plant,date,time_block+1)]<= self.plant_ramp_down_deltas[plant]

        #ramp down constraints for the last time block connecting to the next day
        for plant in self.chosen_plant_names:
            if plant not in 'excess plant':
                for today in self.scheduling_dates[:-1]:
                    tomorrow = today+timedelta(1)
                    self.prob += production_vars[(plant,today,96)] - production_vars[(plant,tomorrow,1)]<= self.plant_ramp_down_deltas[plant]

        # day level hydro constraint
        for plant in self.chosen_plants:
            if plant.fuel_type == 'HYDRO':
                for date in self.scheduling_dates:
                    # Assuming you have a forecasted DataFrame called forecasted_df
                    if plant.hydro_limit:
                        self.prob += (lpSum(production_vars[(plant.name,date,time_block)] for time_block in self.scheduling_time_blocks) <= plant.hydro_limit[date],f"hydro_constraint{date}{plant.name}")

        return self.prob

    def solving_optimization_instance(self):

        """
        Solves the secondary optimization problem and returns the solution status and output.

        Returns:
            tuple: A tuple containing the following data in order:
                - str: The status of solving the optimization problem.
                - str: The output containing the optimal objective value and variable values with non-zero production.
        """
        self.prob.solve()
        
        self.solution_status = ""
        #status of solving the optimization problem
        self.solution_status += "Status:" + LpStatus[self.prob.status] + "\n"

        #optimal objective value
        self.solution_status += "Total cost of production = " + str(value(self.prob.objective)) + "\n"

        self.output = ''
        self.output += str(value(self.prob.objective)) + "\n"
        for v in self.prob.variables():
            if v.varValue>0:
                self.output += v.name + "=" + str(v.varValue) + "\n" 
                
        with open("optimization_solution_with_new_constraints.txt", "w") as text_file:
            text_file.write(self.output)
        
        return self.solution_status,self.output
    



