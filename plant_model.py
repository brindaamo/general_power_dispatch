class PlantUnits:
    def __init__(self, name, ownership, fuel_type, capacity,lower_capacity,upper_capacity,ramp_up_delta,ramp_down_delta, average_variable_cost,base_or_peak,actuals=None,thermal_effeciency=None,status_of_plant=None,hours_switched_off=None,start_type=None,fixed_cost_capacity_bucket=None):
        self.name = name
        self.ownership = ownership
        self.fuel_type = fuel_type
        self.capacity = capacity
        self.lower_capacity = lower_capacity
        self.upper_capacity = upper_capacity
        self.ramp_up_delta = ramp_up_delta
        self.ramp_down_delta = ramp_down_delta
        self.average_variable_cost = average_variable_cost
        self.base_or_peak_plant = base_or_peak
        self.actuals = actuals
        self.plant_thermal_effeciency = thermal_effeciency
        self.status_of_plant = status_of_plant
        self.hours_switched_off = hours_switched_off
        self.start_type = start_type
        self.fixed_cost_capacity_bucket = fixed_cost_capacity_bucket
        
    
    def __repr__(self):
        return self.name
    


