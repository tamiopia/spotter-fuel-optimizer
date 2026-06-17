from unittest.mock import patch
from django.test import TestCase
from route_optimizer.services.fuel_optimizer import find_cheapest_station_near, find_optimal_fuel_stops


MOCK_STATIONS = [
    {'id': 1, 'name': 'Cheap Stop', 'city': 'Columbus', 'state': 'OH',
     'retail_price': 2.90, 'lat': 39.96, 'lng': -82.99},
    {'id': 2, 'name': 'Expensive Stop', 'city': 'Springfield', 'state': 'OH',
     'retail_price': 3.80, 'lat': 39.92, 'lng': -83.81},
    {'id': 3, 'name': 'Medium Stop', 'city': 'Dayton', 'state': 'OH',
     'retail_price': 3.20, 'lat': 39.76, 'lng': -84.19},
    {'id': 4, 'name': 'Far Away Stop', 'city': 'Cincinnati', 'state': 'OH',
     'retail_price': 2.50, 'lat': 39.10, 'lng': -84.51},  # ~60 miles from Columbus
    {'id': 5, 'name': 'Kansas Stop', 'city': 'Wichita', 'state': 'KS',
     'retail_price': 3.10, 'lat': 37.69, 'lng': -97.34},
]


class TestFindCheapestStationNear(TestCase):
    @patch('route_optimizer.services.fuel_optimizer.STATIONS', MOCK_STATIONS)
    def test_returns_cheapest_within_radius(self):
        waypoint = (39.96, -83.00)
        result = find_cheapest_station_near(waypoint, 50)
        self.assertIsNotNone(result)
        self.assertEqual(result['retail_price'], 2.90)
        self.assertEqual(result['name'], 'Cheap Stop')

    @patch('route_optimizer.services.fuel_optimizer.STATIONS', MOCK_STATIONS)
    def test_returns_none_when_nothing_in_radius(self):
        waypoint = (45.0, -110.0)
        result = find_cheapest_station_near(waypoint, 10)
        self.assertIsNone(result)

    @patch('route_optimizer.services.fuel_optimizer.STATIONS', MOCK_STATIONS)
    def test_ignores_stations_outside_radius(self):
        # Far Away Stop (Cincinnati) is ~60 miles from Columbus — outside 50mi radius
        waypoint = (39.96, -82.99)
        result = find_cheapest_station_near(waypoint, 50)
        self.assertNotEqual(result['name'], 'Far Away Stop')

    @patch('route_optimizer.services.fuel_optimizer.STATIONS', MOCK_STATIONS)
    def test_price_beats_distance_as_primary_sort(self):
        # Standing right next to Expensive Stop but Cheap Stop is still cheaper
        waypoint = (39.92, -83.81)
        result = find_cheapest_station_near(waypoint, 100)
        self.assertEqual(result['retail_price'], 2.90)


class TestFindOptimalFuelStops(TestCase):
    @patch('route_optimizer.services.fuel_optimizer.STATIONS', MOCK_STATIONS)
    def test_2500_mile_route_produces_five_stops(self):
        coords = [(40.0, -74.0), (40.0, -97.0), (40.0, -120.0)]
        result = find_optimal_fuel_stops(coords, 2500, search_radius_miles=500)
        self.assertEqual(result['num_stops'], 5)
        self.assertEqual(len(result['fuel_stops']), 5)

    @patch('route_optimizer.services.fuel_optimizer.STATIONS', MOCK_STATIONS)
    def test_total_cost_matches_sum_of_stop_costs(self):
        coords = [(40.0, -74.0), (40.0, -97.0), (40.0, -120.0)]
        result = find_optimal_fuel_stops(coords, 2500, search_radius_miles=500)
        expected_total = sum(s['stop_cost'] for s in result['fuel_stops'])
        self.assertAlmostEqual(result['total_fuel_cost'], round(expected_total, 2), places=2)

    @patch('route_optimizer.services.fuel_optimizer.STATIONS', MOCK_STATIONS)
    def test_stop_numbers_are_sequential(self):
        coords = [(40.0, -74.0), (40.0, -97.0)]
        result = find_optimal_fuel_stops(coords, 1000, search_radius_miles=500)
        for i, stop in enumerate(result['fuel_stops']):
            self.assertEqual(stop['stop_number'], i + 1)

    @patch('route_optimizer.services.fuel_optimizer.STATIONS', MOCK_STATIONS)
    def test_gallons_per_stop_is_50(self):
        coords = [(40.0, -74.0), (40.0, -97.0)]
        result = find_optimal_fuel_stops(coords, 1000, search_radius_miles=500)
        for stop in result['fuel_stops']:
            self.assertEqual(stop['gallons_purchased'], 50.0)
