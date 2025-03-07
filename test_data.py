import os
import pytest
import pandas as pd
from data import (
    initialize_stations_data,
    download_station_data,
    clean_station_data,
    create_monthly_averages,
    create_yearly_averages
)

# Test stations from different continents
TEST_STATIONS = {
    'Europe': 'GME00102380',      # Germany - Nürnberg
    'Africa': 'SFM00068816',      # South Africa - Cape Town Intl
    'North_America': 'USC00047916',  # USA - Santa Cruz
    'Asia_Korea': 'KSM00047108',   # South Korea - Seoul City
    'Australia': 'ASN00066037',    # Australia - Sydney Airport
    'Asia_China': 'CHM00058362'    # China - Shanghai
}

@pytest.fixture(scope="session", autouse=True)
def cleanup_before_all():
    """Clean up any existing test data before tests start"""
    print("\nCleaning up existing test data...")
    for station_id in TEST_STATIONS.values():
        test_files = [
            f'./data/stations/{station_id}.csv',
            f'./data/stations/{station_id}_monthly.csv',
            f'./data/stations/{station_id}_yearly.csv'
        ]
        for file in test_files:
            if os.path.exists(file):
                os.remove(file)
                print(f"Removed: {file}")

@pytest.fixture
def setup_test_environment():
    """Setup test environment and cleanup after each test"""
    initialize_stations_data()
    
    yield
    
    # Cleanup after tests
    for station_id in TEST_STATIONS.values():
        test_files = [
            f'./data/stations/{station_id}.csv',
            f'./data/stations/{station_id}_monthly.csv',
            f'./data/stations/{station_id}_yearly.csv'
        ]
        for file in test_files:
            if os.path.exists(file):
                os.remove(file)

@pytest.mark.parametrize("continent,station_id", TEST_STATIONS.items())
def test_station_data_processing(setup_test_environment, continent, station_id):
    """Test complete data processing for stations from different continents"""
    print(f"\nTesting {continent} station: {station_id}")
    
    # Download and process data
    assert download_station_data(station_id) == True
    assert clean_station_data(station_id) == True
    assert create_monthly_averages(station_id) == True
    assert create_yearly_averages(station_id) == True
    
    # Verify file creation and structure
    assert os.path.exists(f'./data/stations/{station_id}.csv')
    assert os.path.exists(f'./data/stations/{station_id}_monthly.csv')
    assert os.path.exists(f'./data/stations/{station_id}_yearly.csv')
    
    # Check data continuity and missing values
    monthly_df = pd.read_csv(f'./data/stations/{station_id}_monthly.csv')
    yearly_df = pd.read_csv(f'./data/stations/{station_id}_yearly.csv')
    
    # Verify year continuity
    assert len(yearly_df['Year'].unique()) == (yearly_df['Year'].max() - yearly_df['Year'].min() + 1)
    
    # Verify correct columns
    monthly_columns = ['Station_ID', 'Year', 'Month', 'TMAX', 'TMIN']
    yearly_columns = ['Station_ID', 'Year', 'TMAX', 'TMIN']
    
    assert all(col in monthly_df.columns for col in monthly_columns)
    assert all(col in yearly_df.columns for col in yearly_columns)
    
    # Print some basic statistics
    print(f"Data range: {yearly_df['Year'].min()} - {yearly_df['Year'].max()}")
    print(f"Total years: {len(yearly_df)}")
    print(f"Missing values (yearly): TMAX={yearly_df['TMAX'].isna().sum()}, TMIN={yearly_df['TMIN'].isna().sum()}")

def test_initialize_stations_data():
    """Test if station initialization works"""
    initialize_stations_data()
    assert os.path.exists('./data/stations.csv')
    
    # Check if the file has the correct columns
    df = pd.read_csv('./data/stations.csv')
    expected_columns = ['Station_ID', 'Latitude', 'Longitude', 'FirstYear', 'LastYear', 'Station_Name']
    assert all(col in df.columns for col in expected_columns)

@pytest.mark.parametrize("continent,station_id", TEST_STATIONS.items())
def test_download_station_data(setup_test_environment, continent, station_id):
    """Test if station data download works for all test stations"""
    print(f"\nTesting download for {continent} station: {station_id}")
    
    result = download_station_data(station_id)
    assert result == True
    assert os.path.exists(f'./data/stations/{station_id}.csv')
    
    # Check if file has correct columns - added low_memory=False to suppress warning
    df = pd.read_csv(f'./data/stations/{station_id}.csv', low_memory=False)
    expected_columns = ['Station_ID', 'Year', 'Month', 'Day', 'Element', 'Value', 
                       'Quality_Flag', 'Measurement_Flag', 'Source_Flag']
    assert all(col in df.columns for col in expected_columns)

@pytest.mark.parametrize("continent,station_id", TEST_STATIONS.items())
def test_clean_station_data(setup_test_environment, continent, station_id):
    """Test if data cleaning works for all test stations"""
    print(f"\nTesting cleaning for {continent} station: {station_id}")
    
    # First download the data
    download_station_data(station_id)
    
    # Then clean it
    result = clean_station_data(station_id)
    assert result == True
    
    # Check if cleaned file exists and has correct format
    df = pd.read_csv(f'./data/stations/{station_id}.csv')
    assert 'Quality_Flag' not in df.columns
    assert df['Element'].isin(['TMAX', 'TMIN']).all()

@pytest.mark.parametrize("continent,station_id", TEST_STATIONS.items())
def test_create_monthly_averages(setup_test_environment, continent, station_id):
    """Test if monthly average creation works for all test stations"""
    print(f"\nTesting monthly averages for {continent} station: {station_id}")
    
    # Setup: Download and clean data
    download_station_data(station_id)
    clean_station_data(station_id)
    
    # Create monthly averages
    result = create_monthly_averages(station_id)
    assert result == True
    
    # Check if file exists and has correct format
    df = pd.read_csv(f'./data/stations/{station_id}_monthly.csv')
    expected_columns = ['Station_ID', 'Year', 'Month', 'TMAX', 'TMIN']
    assert all(col in df.columns for col in expected_columns)
    assert df['Month'].between(1, 12).all()

@pytest.mark.parametrize("continent,station_id", TEST_STATIONS.items())
def test_create_yearly_averages(setup_test_environment, continent, station_id):
    """Test if yearly average creation works for all test stations"""
    print(f"\nTesting yearly averages for {continent} station: {station_id}")
    
    # Setup: Download and clean data
    download_station_data(station_id)
    clean_station_data(station_id)
    
    # Create yearly averages
    result = create_yearly_averages(station_id)
    assert result == True
    
    # Check if file exists and has correct format
    df = pd.read_csv(f'./data/stations/{station_id}_yearly.csv')
    expected_columns = ['Station_ID', 'Year', 'TMAX', 'TMIN']
    assert all(col in df.columns for col in expected_columns)

@pytest.mark.parametrize("continent,station_id", TEST_STATIONS.items())
def test_data_continuity(setup_test_environment, continent, station_id):
    """Test if data processing maintains continuity and handles missing values for all test stations"""
    print(f"\nTesting data continuity for {continent} station: {station_id}")
    
    # Setup: Process all data
    download_station_data(station_id)
    clean_station_data(station_id)
    create_monthly_averages(station_id)
    create_yearly_averages(station_id)
    
    # Read the processed files
    monthly_df = pd.read_csv(f'./data/stations/{station_id}_monthly.csv')
    yearly_df = pd.read_csv(f'./data/stations/{station_id}_yearly.csv')
    
    # Verify basic data structure
    assert 'Year' in yearly_df.columns, "Year column should exist in yearly data"
    assert 'Year' in monthly_df.columns, "Year column should exist in monthly data"
    assert yearly_df['Year'].is_monotonic_increasing, "Years should be in ascending order in yearly data"
    
    # Check year continuity in both datasets
    yearly_years = set(yearly_df['Year'].unique())
    monthly_years = set(monthly_df['Year'].unique())
    assert yearly_years == monthly_years, "Years in monthly and yearly data should match"
    
    # Verify data types and ranges
    assert yearly_df['TMAX'].dtype == 'float64', "TMAX should be float in yearly data"
    assert yearly_df['TMIN'].dtype == 'float64', "TMIN should be float in yearly data"
    assert monthly_df['TMAX'].dtype == 'float64', "TMAX should be float in monthly data"
    assert monthly_df['TMIN'].dtype == 'float64', "TMIN should be float in monthly data"
    
    # Print data statistics for information
    print(f"Data range: {yearly_df['Year'].min()} - {yearly_df['Year'].max()}")
    print(f"Total years with data: {len(yearly_df)}")
    print(f"Monthly records per year: {len(monthly_df)/len(yearly_df):.1f}")
    print(f"Missing values (yearly): TMAX={yearly_df['TMAX'].isna().sum()}, TMIN={yearly_df['TMIN'].isna().sum()}")
    print(f"Missing values (monthly): TMAX={monthly_df['TMAX'].isna().sum()}, TMIN={monthly_df['TMIN'].isna().sum()}")