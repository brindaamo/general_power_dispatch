def capacity_checks_of_plants(plant_units):
    for plant in plant_units:
        if plant.capacity <= 0:
            return 'This plant unit has wrong capacity' + plant.name 
        else:
            return 'capacity checks done'

def cost_checks_of_plant(plant_units):
    for plant in plant_units:
        if plant.average_variable_cost <= 0:
            return 'This plant unit has wrong capacity' + plant.name 
        else:
            return 'cost checks done'

def missing_demand_at_timeblock_level(demand_of_UP_bydate_byhour_units):
    return None
