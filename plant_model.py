class PlantUnits:
    def __init__(self, name, ownership, fuel_type, capacity,fixed_cost_capacity_bucket,lower_capacity,upper_capacity,ramp_up_delta,ramp_down_delta, average_variable_cost,base_or_peak,thermal_effeciency,hours_switched_off,start_type):
        self.name = name
        self.ownership = ownership
        self.fuel_type = fuel_type
        self.capacity = capacity
        self.fixed_cost_capacity_bucket = fixed_cost_capacity_bucket
        self.lower_capacity = lower_capacity
        self.upper_capacity = upper_capacity
        self.ramp_up_delta = ramp_up_delta
        self.ramp_down_delta = ramp_down_delta
        self.average_variable_cost = average_variable_cost
        self.base_or_peak_plant = base_or_peak
        self.plant_thermal_effeciency = thermal_effeciency
        self.hours_switched_off = hours_switched_off
        self.start_type = start_type

 


