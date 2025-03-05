import requests 
import os
import pandas as pd

def initialize_stations_data():
    """
    Downloads and processes the initial stations data to create a clean stations.csv file
    containing all stations with TMAX and TMIN data.
    """
    
    # Create data directory and stations subfolder if they don't exist
    os.makedirs('./data', exist_ok=True)
    os.makedirs('./data/stations', exist_ok=True)    

    # Check if stations.csv already exists and is not empty
    if os.path.exists('./data/stations.csv') and os.path.getsize('./data/stations.csv') > 0:
        print("Stations data already exists. Skipping initialization.")
        return

    # Download stations file
    file_url_stations = "https://www1.ncdc.noaa.gov/pub/data/ghcn/daily/ghcnd-stations.csv"
    r = requests.get(file_url_stations)
    with open("./data/stations.csv", "wb") as stations_txt:
        stations_txt.write(r.content)
    print("File 'stations.csv' successfully downloaded")

    # Download inventory file
    file_url_inventory = "https://www1.ncdc.noaa.gov/pub/data/ghcn/daily/ghcnd-inventory.txt"
    r = requests.get(file_url_inventory)
    with open("./data/inventory.txt", "wb") as inventory_txt:
        inventory_txt.write(r.content)
    print("File 'inventory.txt' successfully downloaded")

    # Process the files
    # Read the inventory file using space separator (.txt file)
    inventory_df = pd.read_csv('./data/inventory.txt', 
                              sep=r'\s+',            # Using raw string for whitespace separator
                              usecols=[0, 1, 2, 3, 4, 5],
                              names=['Station_ID', 'Latitude', 'Longitude', 'Element', 'FirstYear', 'LastYear'])

    # Filter rows to keep only TMAX and TMIN elements
    inventory_df = inventory_df[inventory_df['Element'].isin(['TMAX', 'TMIN'])]

    # Read the stations file
    stations_names_df = pd.read_csv('./data/stations.csv', 
                                   usecols=[0, 5],  # Only need Station_ID and Station_Name (column 5)
                                   names=['Station_ID', 'Station_Name'])

    # Merge the dataframes on Station_ID
    stations_merge_df = pd.merge(stations_names_df, 
                               inventory_df, 
                               on='Station_ID', 
                               how='left')

    # Group by Station_ID and aggregate the data
    stations_df = stations_merge_df.groupby('Station_ID').agg({
        'Latitude': 'first',      # Take first value since it is the same for each station
        'Longitude': 'first',     # Take first value since it is the same for each station
        'FirstYear': 'max',       # Take the highest FirstYear
        'LastYear': 'min',        # Take the lowest LastYear
        'Station_Name': 'first'   # Take first value since it is the same for each station
    }).reset_index()

    # Fill any NaN values with 0
    stations_df['FirstYear'] = stations_df['FirstYear'].fillna(0).astype(int)
    stations_df['LastYear'] = stations_df['LastYear'].fillna(0).astype(int)

    # Save the final processed data
    stations_df.to_csv('./data/stations.csv', index=False)
    print("\nSaved processed station data to stations.csv")

    # Clean up temporary files
    os.remove('./data/inventory.txt')
    print("Removed temporary file inventory.txt")

def download_station_data(station_id):
    """
    Downloads and converts a station's .dly file to CSV format.
    
    Args:
        station_id (str): The station ID from the stations.csv file
        
    Returns:
        bool: True if successful, False if failed
    """
    base_url = "https://www.ncei.noaa.gov/pub/data/ghcn/daily/all/"
    file_url = f"{base_url}{station_id}.dly"
    
    try:
        # Download the .dly file
        r = requests.get(file_url)
        r.raise_for_status()  # Raises an HTTPError if the status is 4xx, 5xx
        
        # Parse the fixed-width format .dly file
        data = []
        content = r.content.decode('utf-8').split('\n')
        
        for line in content:
            if len(line) < 269:  # Skip incomplete lines
                continue
                
            station = line[0:11]
            year = int(line[11:15])
            month = int(line[15:17])
            element = line[17:21]
            
            # Process daily values (including flags)
            for day in range(31):
                pos = 21 + (day * 8)  # Each daily value takes 8 characters
                value = line[pos:pos+5]
                qflag = line[pos+5:pos+6]
                mflag = line[pos+6:pos+7]
                sflag = line[pos+7:pos+8]
                
                try:
                    value = int(value)
                    if value == -9999:  # Missing value in GHCN-Daily
                        value = None
                except ValueError:
                    value = None
                
                if value is not None:  # Only add non-missing values
                    data.append({
                        'Station_ID': station,
                        'Year': year,
                        'Month': month,
                        'Day': day + 1,
                        'Element': element,
                        'Value': value,
                        'Quality_Flag': qflag,
                        'Measurement_Flag': mflag,
                        'Source_Flag': sflag
                    })
        
        # Convert to DataFrame and save as CSV
        df = pd.DataFrame(data)
        output_file = f"./data/stations/{station_id}.csv"
        df.to_csv(output_file, index=False)
        print(f"Successfully downloaded and converted {station_id} data to CSV")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"Error downloading data for station {station_id}: {e}")
        return False
    except Exception as e:
        print(f"Error processing data for station {station_id}: {e}")
        return False

def clean_station_data(station_id):
    """
    Cleans the station data by:
    1. Filtering for TMAX and TMIN elements
    2. Converting temperature from tenths of °C to °C with 2 decimal places
    3. Removing flag columns
    
    Args:
        station_id (str): The station ID to clean data for
        
    Returns:
        bool: True if successful, False if failed
    """
    try:
        # Read the CSV file
        input_file = f"./data/stations/{station_id}.csv"
        df = pd.read_csv(input_file)
        
        # Filter for TMAX and TMIN elements
        df = df[df['Element'].isin(['TMAX', 'TMIN'])]
        
        # Convert temperature from tenths of degrees to degrees Celsius
        df['Value'] = df['Value'].apply(lambda x: round(x / 10.0, 2))
        
        # Remove flag columns
        df = df.drop(['Quality_Flag', 'Measurement_Flag', 'Source_Flag'], axis=1)
        
        # Save the cleaned data back to CSV
        df.to_csv(input_file, index=False)
        print(f"Successfully cleaned data for station {station_id}")
        return True
        
    except Exception as e:
        print(f"Error cleaning data for station {station_id}: {e}")
        return False

def create_monthly_averages(station_id):
    """
    Creates a new CSV file with monthly averages for TMAX and TMIN values.
    The new file will be named 'station_id_monthly.csv'.
    
    Args:
        station_id (str): The station ID to process
        
    Returns:
        bool: True if successful, False if failed
    """
    try:
        # Read the cleaned station data
        input_file = f"./data/stations/{station_id}.csv"
        df = pd.read_csv(input_file)
        
        # Group by Year, Month, and Element to calculate monthly averages
        monthly_df = df.groupby(['Year', 'Month', 'Element'])['Value'].mean().round(2).reset_index()
        
        # Pivot the data to have TMAX and TMIN as separate columns
        monthly_df = monthly_df.pivot(
            index=['Year', 'Month'],
            columns='Element',
            values='Value'
        ).reset_index()
        
        # Rename columns to be more descriptive
        monthly_df.columns.name = None
        
        # Add Station_ID column
        monthly_df['Station_ID'] = station_id
        
        # Reorder columns to put Station_ID first
        monthly_df = monthly_df[['Station_ID', 'Year', 'Month', 'TMAX', 'TMIN']]
        
        # Save to new CSV file
        output_file = f"./data/stations/{station_id}_monthly.csv"
        monthly_df.to_csv(output_file, index=False)
        print(f"Successfully created monthly averages for station {station_id}")
        return True
        
    except Exception as e:
        print(f"Error creating monthly averages for station {station_id}: {e}")
        return False

def create_yearly_averages(station_id):
    """
    Creates a new CSV file with yearly averages for TMAX and TMIN values,
    calculated from the monthly averages.
    The new file will be named 'station_id_yearly.csv'.
    
    Args:
        station_id (str): The station ID to process
        
    Returns:
        bool: True if successful, False if failed
    """
    try:
        # Read the monthly averages file
        input_file = f"./data/stations/{station_id}_monthly.csv"
        monthly_df = pd.read_csv(input_file)
        
        # Group by Year to calculate yearly averages
        yearly_df = monthly_df.groupby(['Year']).agg({
            'Station_ID': 'first',  # Keep the station ID
            'TMAX': 'mean',         # Average of monthly TMAX values
            'TMIN': 'mean'          # Average of monthly TMIN values
        }).round(2)
        
        # Reset index to make Year a column
        yearly_df = yearly_df.reset_index()
        
        # Reorder columns
        yearly_df = yearly_df[['Station_ID', 'Year', 'TMAX', 'TMIN']]
        
        # Save to new CSV file
        output_file = f"./data/stations/{station_id}_yearly.csv"
        yearly_df.to_csv(output_file, index=False)
        print(f"Successfully created yearly averages for station {station_id}")
        return True
        
    except Exception as e:
        print(f"Error creating yearly averages for station {station_id}: {e}")
        return False

# Keep the if __name__ == "__main__" block for direct script execution
if __name__ == "__main__":
    initialize_stations_data()
