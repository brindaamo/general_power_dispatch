import yaml
from utils import connecting_to_server,get_data_between_dates,select_columns,create_time_blocks,get_data,assign_base_or_peak,get_lower_and_higher_capacities
from utils import get_ramp_up_and_ramp_down_deltas
from utils import read_csv_file_between_dates
from utils import MASTER_DEMAND_TABLE_NAME,DATE_IN_DEMAND_TABLE,MASTER_GENERATING_ASSETS_TABLE,MASTER_PRICING_TABLE,MASTER_HISTORICAL_DATA
from demand_model import Demand
from plant_model import PlantFeatures
from statsmodels.tsa.api import SimpleExpSmoothing
import pandas as pd
from datetime import timedelta,datetime,date

class InputModels():
    """constructor class for the input models. This should directly be fed into the optimization class.
    """
    def __init__(self,simulation_yaml_file):
        self.inputs = simulation_yaml_file
        self.connection = connecting_to_server()
    
    def get_inputs_from_yaml_file(self):
        """Gets inputs from a YAML file.

        Reads a YAML file and retrieves specific input data required for further processing.

        Returns:
            tuple: A tuple containing the following elements:
            - state (str): The state for which the gridpath tables need to be created.
            - start_date (str): The start date of the simulation run.
            - end_date (str): The end date of the simulation run.
            - demand_group (str): The demand group associated with the input data.
         """
        
        # Open the YAML file for reading
        with open(self.inputs, 'r') as file:
            # Load the YAML content
            input_data = yaml.load(file, Loader=yaml.FullLoader)

        # Access the input data as needed
        self.country = input_data['country']
        self.state = input_data['state']
        self.start_date = input_data['start_date']
        self.end_date = input_data['end_date']
        self.demand_group = input_data['demand_group']


        return self.state,self.start_date,self.end_date,self.demand_group
    
    
    def get_demand_data(self):
        """this will get the demand data in the form of dictionaries from the master demand file 

        Returns:
            demand data (list of dictionaries) : demand data with each column as a key and each row as a record
        """
        self.demand_data = []
        
        demand_dataframe = get_data_between_dates(self.start_date,self.end_date,DATE_IN_DEMAND_TABLE,MASTER_DEMAND_TABLE_NAME,self.connection)
        demand_input_state = demand_dataframe.loc[(demand_dataframe['demand_group']==self.demand_group) & (demand_dataframe['country_code'] == self.country) & (demand_dataframe['time_step_start'] >= self.start_date) & (demand_dataframe['time_step_end'] <= self.end_date) & (demand_dataframe['state_name'] == self.state)]
        demand_input_selected = select_columns(demand_input_state,['time_step_start','demand'])
        time_block_mapping = create_time_blocks()


        
        for dt,demand_val in zip(demand_input_selected['time_step_start'],demand_input_selected['demand']) :
            
            # Extract the date, hour, and time block
            date = dt.date()
            hour = dt.hour
            time_block = time_block_mapping[dt.strftime("%H:%M")]

            # Generate the formatted string
            date_timeblock = f"{date}-{time_block}"
            self.demand_data.append(Demand(date,hour,time_block,demand_val,date_timeblock))
    
        return self.demand_data
    
    #all powerplant related data 
    def get_powerplant_data(self):
        """
        Retrieve power plant data for the specified state.

        This method fetches the demand data from the master demand file
        based on the provided state. It merges the power plant pricing data
        and power plant generating assets data to obtain the complete power
        plant data for the state.

        Returns:
            list of dictionaries: Power plant data with each dictionary
            representing a record, where each key corresponds to a column.

        Note:
            This method assumes that the `MASTER_PRICING_TABLE` and
            `MASTER_GENERATING_ASSETS_TABLE` constants are correctly defined
            and accessible.

        """
        power_plant_pricing = get_data(MASTER_PRICING_TABLE, self.connection)
        power_plant_pricing_state = power_plant_pricing.loc[power_plant_pricing['purchaser_name'] == self.state]
        power_plant_generating_assets = get_data(MASTER_GENERATING_ASSETS_TABLE, self.connection)
        self.power_plant_data = power_plant_pricing_state.merge(power_plant_generating_assets, how='inner', on='virtual_asset_name')
        return self.power_plant_data
    
    


    def get_power_plant_chars(self):
        """
    Retrieves and processes power plant characteristics.

    Returns:
        List[PlantFeatures]: A list of PlantFeatures objects representing power plant characteristics.
    """
        power_plants_with_variable_costs = self.power_plant_data.loc[self.power_plant_data['variable_cost_per_unit']>0]
        unique_power_plant_names = power_plants_with_variable_costs['virtual_asset_name'].unique().tolist()
        self.power_plants = []
        for power_plant in unique_power_plant_names:
            plant_data = self.power_plant_data[self.power_plant_data['virtual_asset_name']==power_plant]
            plant_data_row = plant_data.iloc[0]
            base_or_peak = assign_base_or_peak(plant_data_row['variable_cost_per_unit'])
            lower_capacity,higher_capacity = get_lower_and_higher_capacities(plant_data_row['capacity_allocated_to_purchaser'],base_or_peak)
            ramp_up_delta,ramp_down_delta = get_ramp_up_and_ramp_down_deltas(plant_data_row['capacity_allocated_to_purchaser'],plant_data_row['energy_source'])
            fixed_costs = plant_data_row['fixed_cost_per_unit']*plant_data_row['capacity_allocated_to_purchaser']
            self.power_plants.append(PlantFeatures(plant_data_row['virtual_asset_name'],plant_data_row['asset_category'],plant_data_row['energy_source'],plant_data_row['capacity_allocated_to_purchaser'],lower_capacity,1.1*higher_capacity,plant_data_row['variable_cost_per_unit'],fixed_costs,base_or_peak,ramp_up_delta,ramp_down_delta))

        return self.power_plants
    
    def get_peak_demand(self):
        peak = 0
        for demand in self.demand_data:
            if demand.demand_val > peak:
                peak = demand.demand_val
        self.peak_demand = 1.5*peak
        return self.peak_demand
        

    def get_hydro_maximum_for_constraint(self, forecast_days):
        """
        Performs simple exponential smoothing on the summarized DataFrame and forecasts average load for the next few days.

        Args:
            forecast_days (int): The number of days to forecast.

        Returns:
            pandas.DataFrame: The DataFrame with average load forecasted for the next few days.
        """
        
        end_date = datetime.strptime(self.start_date + ' 00:00:00', "%Y-%m-%d %H:%M:%S")
        start_date = end_date - timedelta(days=30)
        summarized_df = read_csv_file_between_dates(MASTER_HISTORICAL_DATA, start_date, end_date)
        summarized_df_with_source = summarized_df.merge(self.power_plant_data[['virtual_asset_name', 'energy_source']], right_on='virtual_asset_name', left_on='cea_generator_name', how='left')
        df = summarized_df_with_source.copy()

        # Convert 'time_block_start_time' to datetime if it is not already in datetime format
        df['time_block_start_time'] = pd.to_datetime(df['time_block_start_time'])

        # Group by date and 'cea_generator_name' and sum the load
        df_grouped = df.groupby([df['time_block_start_time'].dt.date, 'cea_generator_name'])['on_load'].sum().reset_index()

        
        for plant in self.power_plants:
            if plant.fuel_type == 'HYDRO':
                filtered_group = df_grouped[df_grouped['cea_generator_name'] == plant.name]
                if not filtered_group.empty:
                    model = SimpleExpSmoothing(filtered_group['on_load'])
                    fitted_model = model.fit()
                    forecast = fitted_model.forecast(forecast_days)
                    forecast_dates = pd.date_range(end=end_date, periods=forecast_days, freq='D')
                    plant.hydro_limit = dict(zip(forecast_dates, forecast.values))
                
        return None








    
        
# def main():
#     # Initialize GridpathTables object with simulation YAML file
#     simulation_yaml_file = "general_power_dispatch/simulation_inputs.yaml"
#     input_models = InputModels(simulation_yaml_file)
#     input_models.get_inputs_from_yaml_file()
#     input_models.get_demand_data()
#     input_models.get_powerplant_data()
#     input_models.get_power_plant_chars()
   
    
# if __name__ == "__main__":
#     main()