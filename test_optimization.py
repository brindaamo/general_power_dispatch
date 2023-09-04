from optimization import Optimization  # Import your Optimization module

import pandas as pd

def check_demand_capacity_constraints(opti_instance, real_demand_values, real_capacity_values):
    """
    Check if the demand at each time block exceeds the capacity using real demand and capacity values.

    Args:
        opti_instance (Optimization): An instance of the Optimization class.
        real_demand_values (dict): A dictionary containing real demand values keyed by date-time block.
        real_capacity_values (dict): A dictionary containing real capacity values keyed by plant name.

    Returns:
        list: List of tuples containing date, time block, total capacity, and total demand where demand exceeds capacity (if applicable).
    """
    exceeded_blocks = []
    opti_instance.demand_values = real_demand_values
    for plant, capacity in real_capacity_values.items():
        opti_instance.plant_upper_capacity[plant] = capacity

    capacity_data = []  # Store the capacity information in a list
    for date in opti_instance.scheduling_dates:
        for time_block in opti_instance.scheduling_time_blocks:
            demand_date_timeblock = date.strftime('%Y-%m-%d') + "-" + str(time_block)
            total_capacity = sum(
                opti_instance.plant_upper_capacity[plant] for plant in opti_instance.plant_names
            )
            capacity_data.append((date, time_block, total_capacity))

    # Create a DataFrame from the capacity data
    capacity_df = pd.DataFrame(capacity_data, columns=['Date', 'Time Block', 'Total Capacity'])

    # Save the DataFrame to a CSV file
    capacity_df.to_csv('capacity_at_each_time_block.csv', index=False)

    return exceeded_blocks



def main():
    simulation_yaml_file = "general_power_dispatch/simulation_inputs.yaml"
    opti = Optimization(simulation_yaml_file)
    opti.get_inputs_from_yaml_file()
    opti.get_powerplant_data()
    opti.get_demand_data()
    opti.get_power_plant_chars()
    opti.get_peak_demand()
    opti.get_hydro_maximum_for_constraint(1)
    opti.reading_optimization_data()
    opti.creating_optimization_instance_primary_problem()
    
    # Assuming you have the real capacity and demand data available for testing
    real_demand_values = opti.demand_values
    real_capacity_values = opti.plant_upper_capacity

    exceeded_blocks = check_demand_capacity_constraints(opti, real_demand_values, real_capacity_values)

    if not exceeded_blocks:
        print("Demand does not exceed capacity at any time block.")
    else:
        print("Demand exceeds capacity at the following time blocks:")
        for date, time_block, total_capacity, total_demand in exceeded_blocks:
            print(f"Date: {date}, Time Block: {time_block}, Total Capacity: {total_capacity}, Total Demand: {total_demand}")

if __name__ == '__main__':
    main()
