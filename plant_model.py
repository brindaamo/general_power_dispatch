class PlantFeatures:
    def __init__(self, name, ownership, fuel_type, capacity,lower_capacity,upper_capacity, average_variable_cost,fixed_cost,base_or_peak,ramp_up_delta=None,ramp_down_delta=None,hydro_limit=None):
        self.name = name
        self.ownership = ownership
        self.fuel_type = fuel_type
        self.capacity = capacity
        self.lower_capacity = lower_capacity
        self.upper_capacity = upper_capacity
        self.average_variable_cost = average_variable_cost
        self.fixed_cost = fixed_cost
        self.base_or_peak_plant = base_or_peak
        self.ramp_up_delta = ramp_up_delta
        self.ramp_down_delta = ramp_down_delta
        self.hydro_limit = hydro_limit
        
    
    def __repr__(self):
        return self.name
    


