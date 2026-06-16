"""
Core fuel stop optimization algorithm.
No external API calls — pure computation against in-memory station data.
"""
import logging
from typing import Dict, Any, Optional
from django.conf import settings
from .data_loader import STATIONS
from .geo_utils import haversine_miles, interpolate_along_polyline

logger = logging.getLogger(__name__)

TANK_RANGE_MILES = 500
MPG = 10
GALLONS_PER_FILL = TANK_RANGE_MILES / MPG  # 50 gallons


def find_optimal_fuel_stops(
    polyline_coords: list,
    total_miles: float,
    search_radius_miles: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Main algorithm entry point.

    Args:
        polyline_coords: List of (lat, lng) tuples forming the route
        total_miles: Total route distance in miles
        search_radius_miles: How far from route waypoint to search (default from settings)

    Returns:
        {
            'fuel_stops': [...],
            'total_fuel_cost': float,
            'total_gallons': float,
            'num_stops': int,
        }
    """
    if search_radius_miles is None:
        search_radius_miles = getattr(settings, 'SEARCH_RADIUS_MILES', 50)

    num_stops = int(total_miles // TANK_RANGE_MILES)

    fuel_stops = []
    total_cost = 0.0

    for stop_index in range(num_stops):
        target_mile = (stop_index + 1) * TANK_RANGE_MILES
        target_fraction = target_mile / total_miles

        waypoint = interpolate_along_polyline(polyline_coords, target_fraction)

        station = find_cheapest_station_near(waypoint, search_radius_miles)

        if not station:
            station = find_cheapest_station_near(waypoint, search_radius_miles * 2)

        if not station:
            logger.warning(f"No station found near mile {target_mile}, waypoint {waypoint}")
            continue

        stop_cost = GALLONS_PER_FILL * station['retail_price']
        total_cost += stop_cost

        fuel_stops.append({
            'stop_number': stop_index + 1,
            'mile_marker': target_mile,
            'truckstop_name': station['name'],
            'city': station['city'],
            'state': station['state'],
            'retail_price_per_gallon': station['retail_price'],
            'gallons_purchased': GALLONS_PER_FILL,
            'stop_cost': round(stop_cost, 2),
            'lat': station['lat'],
            'lng': station['lng'],
        })

    total_gallons = sum(s['gallons_purchased'] for s in fuel_stops)

    return {
        'fuel_stops': fuel_stops,
        'total_fuel_cost': round(total_cost, 2),
        'total_gallons': total_gallons,
        'num_stops': len(fuel_stops),
    }


def find_cheapest_station_near(waypoint: tuple, radius_miles: float) -> Optional[Dict]:
    """
    Find the cheapest fuel station within radius_miles of waypoint.

    Args:
        waypoint: (lat, lng) tuple
        radius_miles: search radius in miles

    Returns:
        Station dict (with distance_from_route key added) or None if nothing found
    """
    candidates = []

    for station in STATIONS:
        station_coord = (station['lat'], station['lng'])
        distance = haversine_miles(waypoint, station_coord)

        if distance <= radius_miles:
            candidates.append({**station, 'distance_from_route': round(distance, 1)})

    if not candidates:
        return None

    candidates.sort(key=lambda s: (s['retail_price'], s['distance_from_route']))
    return candidates[0]
