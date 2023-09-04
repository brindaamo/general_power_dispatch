#this function will connect to the database and give access to the tables in the database
import pandas as pd 
from datetime import datetime,timedelta,date

from sqlalchemy import create_engine,text
from config import connection_string

COAL_RAMP_UP_PERCENT = 0.15
COAL_RAMP_DOWN_PERCENT = 0.15
HYDRO_RAMP_UP_PERCENT = 0.4
HYDRO_RAMP_DOWN_PERCENT = 0.4
COAL_EFFICIENCY_RATE = 1.12
BASE_OR_PEAK_COST_CUT_OFF = 3
MINIMUM_BASE_PLANT_CAPACITY = 0.70
MAXIMUM_BASE_PLANT_CAPACITY = 1
MINIMUM_PEAK_PLANT_CAPACITY = 0.45
MAXIMUM_PEAK_PLANT_CAPACITY = 1
INFINITE_CAPACITY = 10000

MASTER_DEMAND_TABLE_NAME = 'input_data.demand_data_for_gridpath'
DATE_IN_DEMAND_TABLE = 'time_step_start'
INPUT_MAPPING_TIMEBLOCKS_TO_HOURS = "RawData/hours_timeblock_mapping.csv"
MASTER_PLANNING_ENTITIES_TABLE = 'input_data.planning_entities'
MASTER_GENERATING_ASSETS_TABLE = 'input_data.generating_assets_list'
MASTER_PRICING_TABLE = 'input_data.electricity_purchase_prices'
MASTER_HISTORICAL_DATA = 'general_power_dispatch/RawData/rjsldc.csv'
MASTER_THERMAL_START_UP_COSTS = 'input_data.thermal_plant_startup_costs'

def connecting_to_server():
    
    engine = create_engine(connection_string)
    conn = engine.connect()

    return conn

def get_data(table_name,conn):
    """
    Retrieves data from the database 

    Args:
        table_name (str): The name of the table to retrieve data from.
        conn (sqlite3.Connection): The database connection object.

    Returns:
        df (pandas.DataFrame): A DataFrame containing the retrieved data.
    """
    query = f"SELECT * FROM {table_name}"
    result = conn.execute(text(query))
    rows = result.fetchall()
    if rows is None:
        raise ValueError("No rows found in the query result")

    df = pd.DataFrame(rows, columns=result.keys())
    
    return df


def get_data_between_dates(start_date, end_date,date_column_name, table_name, conn):
    """
    Retrieves data from the database for a specified date range and table name.

    Args:
        start_date (str): The start date of the date range in 'YYYY-MM-DD' format.
        end_date (str): The end date of the date range in 'YYYY-MM-DD' format.
        date_column_name(str): the name of the date column in the table 
        table_name (str): The name of the table to retrieve data from.
        conn (sqlalchemy connection): The database connection object.

    Returns:
        df (pandas.DataFrame): A DataFrame containing the retrieved data.
    """
    query = f"SELECT * FROM {table_name} WHERE {date_column_name} BETWEEN '{start_date}' AND '{end_date}'"
    result = conn.execute(text(query))
    rows = result.fetchall()
    if rows is None:
        raise ValueError("No rows found in the query result")

    df = pd.DataFrame(rows, columns=result.keys())
    
    return df

def read_csv_file_between_dates(file_path, start_date, end_date):
    """
    Reads a CSV file between two dates and creates a DataFrame.

    Args:
        file_path (str): The path to the CSV file.
        start_date (str): The start date in 'YYYY-MM-DD' format.
        end_date (str): The end date in 'YYYY-MM-DD' format.

    Returns:
        pandas.DataFrame: The created DataFrame.
    """
    try:
        df = pd.read_csv(file_path)
        df['time_block_start_time'] = pd.to_datetime(df['time_block_start_time'])  # Replace 'date_column' with the actual column name
        filtered_df = df.loc[(df['time_block_start_time'] >= start_date) & (df['time_block_start_time'] < end_date)]
        return filtered_df
    
    except FileNotFoundError:
        print(f"File not found at path: {file_path}")
    
    except pd.errors.ParserError:
        print(f"Error parsing CSV file at path: {file_path}")


# Function to select columns from a DataFrame
def select_columns(df, columns):
    """
    Selects specified columns from a DataFrame.

    Args:
        df_name (str): The name of the DataFrame to select columns from.
        columns (list): A list of column names to select from the DataFrame.

    Returns:
        new_df (pandas.DataFrame): A new DataFrame containing only the selected columns.
    """

    new_df = df[columns]
    return new_df


def filter_dataframe(df, column, value):
    """
    Filter a Pandas DataFrame based on a certain column's value.

    Args:
        df (pd.DataFrame): The input DataFrame.
        column (str): The name of the column to filter on.
        value: The value to filter on.

    Returns:
        pd.DataFrame: The filtered DataFrame.
    """
    filtered_df = df[df[column] == value]
    if filtered_df.empty:
        raise ValueError("state data does not exist")
    return filtered_df

def get_year_from_date(date_str):
    """
    Get the year from a date string in the format "YYYY-MM-DD".

    Args:
        date_str (str): Date string in the format "YYYY-MM-DD".

    Returns:
        int: Year extracted from the date string.
    """
    # Extract the year from the date string
    date = datetime.strptime(date_str, '%Y-%m-%d')
    year = date.year

    return year

def create_time_blocks():
    """
    Create a dictionary mapping time to time blocks.

    Returns:
        dict: A dictionary where the keys are time strings in the format "HH:MM"
              and the values are the corresponding time blocks.

    Example:
        {
            '00:00': 1,
            '00:15': 2,
            '00:30': 3,
            ...
            '23:45': 96
        }
    """
    time_blocks = {}
    time_block_counter = 1

    for hour in range(24):
        for minute in range(0, 60, 15):
            time = f"{hour:02d}:{minute:02d}"
            time_blocks[time] = time_block_counter
            time_block_counter += 1

    return time_blocks

def assign_base_or_peak(cost: float) -> str:
    """
    Assigns base or peak status based on the cost.

    Args:
        cost (float): The cost value used to determine base or peak.

    Returns:
        str: The assigned base or peak status.
    """
    if cost > 3:
        base_or_peak = 'peak'
    else:
        base_or_peak = 'base'

    return base_or_peak


def get_lower_and_higher_capacities(capacity: float, base_or_peak: str):
    """
    Calculates lower and higher capacities based on the given capacity and base or peak status.

    Args:
        capacity (float): The capacity value used for calculations.
        base_or_peak (str): The base or peak status.

    Returns:
        Tuple[float, float]: The lower and higher capacities.
    """
    if base_or_peak == 'base':
        lower_capacity, higher_capacity = capacity * MINIMUM_BASE_PLANT_CAPACITY, capacity * MAXIMUM_BASE_PLANT_CAPACITY
    else:
        lower_capacity, higher_capacity = capacity * MINIMUM_PEAK_PLANT_CAPACITY, capacity * MAXIMUM_PEAK_PLANT_CAPACITY

    return lower_capacity, higher_capacity


def get_ramp_up_and_ramp_down_deltas(capacity: float, energy_source: str):
    """
    Calculates ramp-up and ramp-down deltas based on the given capacity and energy source.

    Args:
        capacity (float): The capacity value used for calculations.
        energy_source (str): The energy source.

    Returns:
        Tuple[float, float]: The ramp-up and ramp-down deltas.
    """
    if energy_source == "HYDRO":
        ramp_up_delta = capacity * 0.7 * HYDRO_RAMP_UP_PERCENT
        ramp_down_delta = capacity * 0.7 * HYDRO_RAMP_DOWN_PERCENT
    else:
        ramp_up_delta = capacity * 0.7 * COAL_RAMP_UP_PERCENT
        ramp_down_delta = capacity * 0.7 * COAL_RAMP_DOWN_PERCENT

    return ramp_up_delta, ramp_down_delta


def get_dates_between(start_date_str: datetime, end_date_str: datetime):
    """
    Retrieves all dates between the given start and end dates.

    Args:
        start_date_str (datetime): The start date in the format 'YYYY-MM-DD'.
        end_date_str (datetime): The end date in the format 'YYYY-MM-DD'.

    Returns:
        List[datetime]: A list of dates in the format 'YYYY-MM-DD' between the start and end dates.
    """
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
    
    dates = []
    current_date = start_date

    while current_date < end_date:
        dates.append(current_date)
        current_date += timedelta(days=1)

    return dates

#This method is used to convert datetime to string while parsing to json in code
def my_date_time_converter(o):
    if isinstance(o, datetime):
        return o.__str__()

#This method is used to convert datetime.date to string while parsing to json in code
def my_date_converter(o):
    if isinstance(o, date):
        return o.__str__()

#This method is used to convert string to date for formatting json to string
def date_hook(json_dict):
    for (key, value) in json_dict.items():
        try:
            json_dict[key] = datetime.strptime(value, "%Y-%m-%d").date()
        except:
            pass
    return json_dict

