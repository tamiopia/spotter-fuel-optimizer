"""
Pure Python geographic calculations. No API calls.
"""
import math
from typing import List, Tuple

Coord = Tuple[float, float]  # (lat, lng)


def haversine_miles(coord1: Coord, coord2: Coord) -> float:
    """
    Calculate great-circle distance between two points in miles.
    Uses the Haversine formula.
    """
    R = 3958.8  # Earth radius in miles
    lat1, lon1 = math.radians(coord1[0]), math.radians(coord1[1])
    lat2, lon2 = math.radians(coord2[0]), math.radians(coord2[1])

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))

    return R * c


def interpolate_along_polyline(coords: List[Coord], target_fraction: float) -> Coord:
    """
    Given a list of (lat, lng) coords forming a polyline,
    return the coordinate at `target_fraction` (0.0 to 1.0) of total length.
    """
    if not coords:
        raise ValueError("Empty coordinate list")
    if target_fraction <= 0:
        return coords[0]
    if target_fraction >= 1:
        return coords[-1]

    segment_lengths = []
    total_length = 0.0
    for i in range(len(coords) - 1):
        d = haversine_miles(coords[i], coords[i + 1])
        segment_lengths.append(d)
        total_length += d

    target_distance = target_fraction * total_length
    accumulated = 0.0

    for i, seg_len in enumerate(segment_lengths):
        if accumulated + seg_len >= target_distance:
            overshoot = target_distance - accumulated
            fraction_in_seg = overshoot / seg_len if seg_len > 0 else 0
            lat = coords[i][0] + fraction_in_seg * (coords[i + 1][0] - coords[i][0])
            lng = coords[i][1] + fraction_in_seg * (coords[i + 1][1] - coords[i][1])
            return (lat, lng)
        accumulated += seg_len

    return coords[-1]


def decode_polyline(encoded: str) -> List[Coord]:
    """
    Decode a Google-format encoded polyline string into list of (lat, lng) tuples.
    OpenRouteService returns encoded polylines in this format.
    """
    coords = []
    index, lat, lng = 0, 0, 0

    while index < len(encoded):
        for coord_ref in [0, 1]:  # lat then lng
            result, shift = 0, 0
            while True:
                b = ord(encoded[index]) - 63
                index += 1
                result |= (b & 0x1f) << shift
                shift += 5
                if b < 0x20:
                    break
            delta = ~(result >> 1) if result & 1 else result >> 1
            if coord_ref == 0:
                lat += delta
            else:
                lng += delta
        coords.append((lat / 1e5, lng / 1e5))

    return coords
