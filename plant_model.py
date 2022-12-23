class PlantUnits:
    def __init__(self, name, ownership, fuel_type, capacity,lower_capacity,upper_capacity,ramp_up_delta,ramp_down_delta, average_variable_cost,base_or_peak,actuals=None,thermal_effeciency=None,status_of_plant=None,hours_switched_off=None,start_type=None,fixed_cost_capacity_bucket=None,up_drawal = None,up_drawal_ramp_up_delta=None,up_drawal_ramp_down_delta=None,hydro_limit=None):
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
        self.up_drawal = up_drawal
        self.up_drawal_ramp_up_delta = up_drawal_ramp_up_delta
        self.up_drawal_ramp_down_delta = up_drawal_ramp_down_delta
        self.hydro_limit = hydro_limit
        
    
    def __repr__(self):
        return self.name
    


