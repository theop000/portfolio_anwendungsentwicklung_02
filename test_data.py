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

@pytest.fixture(scope="session")
def processed_station_data():
    """Setup test data once for all tests"""
    print("\nProcessing station data for all tests...")
    initialize_stations_data()
    
    # Process all stations once
    for station_id in TEST_STATIONS.values():
        download_station_data(station_id)
        clean_station_data(station_id)
        create_monthly_averages(station_id)
        create_yearly_averages(station_id)
    
    yield
    
    # Cleanup after all tests are done
    print("\nCleaning up test data...")
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

@pytest.mark.parametrize("continent,station_id", TEST_STATIONS.items())
def test_file_existence(processed_station_data, continent, station_id):
    """Test if all required files exist"""
    assert os.path.exists(f'./data/stations/{station_id}.csv')
    assert os.path.exists(f'./data/stations/{station_id}_monthly.csv')
    assert os.path.exists(f'./data/stations/{station_id}_yearly.csv')

@pytest.mark.parametrize("continent,station_id", TEST_STATIONS.items())
def test_data_structure(processed_station_data, continent, station_id):
    """Test data structure and column existence"""
    df = pd.read_csv(f'./data/stations/{station_id}.csv', low_memory=False)
    monthly_df = pd.read_csv(f'./data/stations/{station_id}_monthly.csv')
    yearly_df = pd.read_csv(f'./data/stations/{station_id}_yearly.csv')
    
    # Check columns
    assert all(col in df.columns for col in ['Station_ID', 'Year', 'Month', 'Day', 'Element', 'Value'])
    assert all(col in monthly_df.columns for col in ['Station_ID', 'Year', 'Month', 'TMAX', 'TMIN'])
    assert all(col in yearly_df.columns for col in ['Station_ID', 'Year', 'TMAX', 'TMIN'])
    
    # Check data types
    assert yearly_df['TMAX'].dtype == 'float64'
    assert yearly_df['TMIN'].dtype == 'float64'
    assert monthly_df['TMAX'].dtype == 'float64'
    assert monthly_df['TMIN'].dtype == 'float64'

@pytest.mark.parametrize("continent,station_id", TEST_STATIONS.items())
def test_data_continuity(processed_station_data, continent, station_id):
    """Test data continuity and relationships"""
    print(f"\nTesting data continuity for {continent} station: {station_id}")
    
    monthly_df = pd.read_csv(f'./data/stations/{station_id}_monthly.csv')
    yearly_df = pd.read_csv(f'./data/stations/{station_id}_yearly.csv')
    
    # Check year continuity and relationships
    yearly_years = set(yearly_df['Year'].unique())
    monthly_years = set(monthly_df['Year'].unique())
    assert yearly_years == monthly_years
    assert yearly_df['Year'].is_monotonic_increasing
    assert monthly_df['Month'].between(1, 12).all()
    
    # Print statistics
    print(f"Data range: {yearly_df['Year'].min()} - {yearly_df['Year'].max()}")
    print(f"Total years: {len(yearly_df)}")
    print(f"Monthly records per year: {len(monthly_df)/len(yearly_df):.1f}")
    print(f"Missing values (yearly): TMAX={yearly_df['TMAX'].isna().sum()}, TMIN={yearly_df['TMIN'].isna().sum()}")
    print(f"Missing values (monthly): TMAX={monthly_df['TMAX'].isna().sum()}, TMIN={monthly_df['TMIN'].isna().sum()}")