"""
Routing service.
- geocode_location: uses Nominatim (OpenStreetMap) — free, no API key, no quota
- get_route: uses OpenRouteService directions API — 1 call per request
"""
import logging
import requests
from django.conf import settings
from .geo_utils import decode_polyline

logger = logging.getLogger(__name__)

ORS_BASE = "https://api.openrouteservice.org"
_NOMINATIM_HEADERS = {'User-Agent': 'FuelRouteOptimizer/1.0 (be-assessment)'}


def geocode_location(query: str) -> tuple:
    """
    Convert a US location string to (lat, lng) using Nominatim (OpenStreetMap).
    Free, no API key, no daily quota. Only called twice per user request.
    Raises ValueError if location cannot be found.
    """
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        'q': query,
        'format': 'json',
        'limit': 1,
        'countrycodes': 'us',
    }
    response = requests.get(url, params=params, headers=_NOMINATIM_HEADERS, timeout=10)
    response.raise_for_status()

    results = response.json()
    if not results:
        raise ValueError(f"Could not geocode location: '{query}'")

    return (float(results[0]['lat']), float(results[0]['lon']))


def get_route(start_coords: tuple, end_coords: tuple) -> dict:
    """
    Get driving route between two coordinate pairs via ORS.

    Returns:
        {
            'distance_meters': int,
            'distance_miles': float,
            'duration_seconds': int,
            'polyline_coords': [(lat, lng), ...],
            'encoded_polyline': str,
        }
    """
    url = f"{ORS_BASE}/v2/directions/driving-car"
    headers = {
        'Authorization': settings.ORS_API_KEY,
        'Content-Type': 'application/json',
    }
    body = {
        "coordinates": [
            [start_coords[1], start_coords[0]],  # ORS uses [lng, lat]
            [end_coords[1], end_coords[0]],
        ],
        "format": "json",
        "geometry_simplify": False,
    }

    response = requests.post(url, json=body, headers=headers, timeout=30)
    response.raise_for_status()
    data = response.json()

    route = data['routes'][0]
    summary = route['summary']

    distance_meters = summary['distance']
    distance_miles = distance_meters * 0.000621371

    encoded = route['geometry']
    polyline_coords = decode_polyline(encoded)

    return {
        'distance_meters': distance_meters,
        'distance_miles': round(distance_miles, 2),
        'duration_seconds': summary['duration'],
        'polyline_coords': polyline_coords,
        'encoded_polyline': encoded,
    }
