import pytest
from main import haversine_distance


def test_haversine_distance():
    """Test distance calculation function"""
    test_cases = [
        # Known distances between cities
        ((52.5200, 13.4050, 48.8566, 2.3522), 878),  # Berlin to Paris
        ((51.5074, -0.1278, 40.7128, -74.0060), 5570),  # London to New York
        ((35.6762, 139.6503, 22.3193, 114.1694), 2892),  # Tokyo to Hong Kong
        
        # Special cases
        ((50.0, 8.0, 50.0, 8.0), 0),  # Same point
        ((0.0, 0.0, 0.0, 180.0), 20015),  # Half Earth circumference
    ]
    
    for (lat1, lon1, lat2, lon2), expected in test_cases:
        distance = haversine_distance(lat1, lon1, lat2, lon2)
        # Allow 1% margin of error due to rounding
        assert abs(distance - expected) < expected * 0.01, f"Distance calculation failed for coordinates: ({lat1}, {lon1}) to ({lat2}, {lon2})"