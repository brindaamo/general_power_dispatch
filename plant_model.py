class PlantFeatures:
    def __init__(self, name, ownership, fuel_type, capacity,lower_capacity,upper_capacity, average_variable_cost,fixed_cost,type_of_plant,ramp_up_delta=None,ramp_down_delta=None,hydro_limit=None, fixed_cost_capacity_bucket=None, hours_switched_off=None, status_of_plant=None, start_type=None, startup_cost=None):
        self.name = name
        self.ownership = ownership
        self.fuel_type = fuel_type
        self.capacity = capacity
        self.lower_capacity = lower_capacity
        self.upper_capacity = upper_capacity
        self.average_variable_cost = average_variable_cost
        self.fixed_cost = fixed_cost
        self.type_of_plant = type_of_plant
        self.ramp_up_delta = ramp_up_delta
        self.ramp_down_delta = ramp_down_delta
        self.hydro_limit = hydro_limit
        self.fixed_cost_capacity_bucket = fixed_cost_capacity_bucket
        self.hours_switched_off = hours_switched_off 
        self.status_of_plant = status_of_plant
        self.start_type = start_type
        self.startup_cost = startup_cost
        
    
    def __repr__(self):
        return self.name
    


