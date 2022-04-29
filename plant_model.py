class PlantUnits:
    def __init__(self, name, ownership, fuel_type, capacity,lower_capacity,upper_capacity,ramp_up_delta,ramp_down_delta, average_variable_cost):
        self.name = name
        self.ownership = ownership
        self.fuel_type = fuel_type
        self.capacity = capacity
        self.lower_capacity = lower_capacity
        self.upper_capacity = upper_capacity
        self.ramp_up_delta = ramp_up_delta
        self.ramp_down_delta = ramp_down_delta
        self.average_variable_cost = average_variable_cost
