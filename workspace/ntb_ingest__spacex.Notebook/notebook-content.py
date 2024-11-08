# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "8a011eb7-3604-46da-99df-99a06acb6726",
# META       "default_lakehouse_name": "lkh_bronze__space_x",
# META       "default_lakehouse_workspace_id": "6a582960-b57f-4a22-9753-1a7f7abfc235"
# META     }
# META   }
# META }

# CELL ********************

# Import libraries
import requests
import pandas as pd
from pyspark.sql import SparkSession
from datetime import datetime
import json
import concurrent.futures

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## Bronze layer - load raw data
# Dynamic loading pipeline, that can load data from multiple endpoints at the same time.

# CELL ********************

# Define data sources
data_sources = [
    {
        'name': 'Launches',
        'api_url': "https://api.spacexdata.com/v4/launches",
        'raw_data_base_path': "raw/launches"
        
    },
    {
        'name': 'Cores',
        'api_url': "https://api.spacexdata.com/v4/cores",
        'raw_data_base_path': "raw/cores"
    },
    # Add more data sources as needed
    # {
    #     'name': 'Payloads',
    #     'api_url': "https://api.spacexdata.com/v4/payloads",
    #     'raw_data_base_path': "raw/payloads"
    # },
]

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# Initialize Spark for easier data handling (saving in Fabric is easier this way)
spark = SparkSession.builder.getOrCreate()

# Generic fetch from unsecured endpoint
def fetch_data_from_api(api_url):
    """
    Fetches data from a given API endpoint.

    Parameters:
    - api_url (str): The API endpoint URL.

    Returns:
    - list/dict: The data fetched from the API.
    """
    try:
        response = requests.get(api_url)
        response.raise_for_status()  # Raise an exception for HTTP errors
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from {api_url}: {e}")
        raise

# Generic Raw Data Saving Function to Lakehouse Files
def save_raw_data(raw_data, raw_data_path):
    """
    Saves the raw data to the Lakehouse in the specified path.

    Parameters:
    - raw_data (list/dict): The raw data to save.
    - raw_data_path (str): The Lakehouse path where the data will be saved.
    """

    print(f"Started saving raw data to: {raw_data_path}")
    try:
        # Convert raw_data to JSON string
        json_data_str = json.dumps(raw_data)
        
        # Create an RDD with the JSON string
        rdd = spark.sparkContext.parallelize([json_data_str])
        
        # Write the RDD to the specified path
        rdd.saveAsTextFile(raw_data_path)
    except Exception as e:
        print(f"Error saving raw data to {raw_data_path}: {e}")
        raise

# Function to Handle Data Pipeline for Each Data Source
def handle_data_source(data_source):
    """
    Handles fetching, saving and writing data for a given data source.

    Parameters:
    - data_source (dict): A dictionary containing parameters for the data source.
    """
    try:
        # Fetch raw data
        raw_data = fetch_data_from_api(data_source['api_url'])

        # Generate raw data path with timestamp
        now = datetime.utcnow()
        year = now.strftime('%Y')
        month = now.strftime('%m')
        day = now.strftime('%d')
        timestamp = now.strftime('%H%M%S')
        raw_data_path = f"Files/{data_source['raw_data_base_path']}/{year}/{month}/{day}/{timestamp}.json"

        #print(raw_data)

        # Save raw data
        save_raw_data(raw_data, raw_data_path)


    except Exception as e:
        print(f"Error handling data source '{data_source['name']}': {e}")


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

#Main parallel loop to handle all data sources
try:
    # Use futures for parallel execution
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(handle_data_source, ds) for ds in data_sources]
        concurrent.futures.wait(futures)

    print("All data sources processing finished.")

except Exception as e:
    print(f"An error occurred during the pipeline execution: {e}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
