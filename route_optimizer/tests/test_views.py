import json
from unittest.mock import patch
from django.test import TestCase


MOCK_ROUTE = {
    'distance_meters': 4488000,
    'distance_miles': 2789.4,
    'duration_seconds': 144720,
    'polyline_coords': [(40.71, -74.00), (39.00, -94.00), (34.05, -118.24)],
    'encoded_polyline': 'a~l~Fjk~uOwHJy@P',
}

MOCK_OPTIMIZER_RESULT = {
    'fuel_stops': [
        {
            'stop_number': 1,
            'mile_marker': 500,
            'truckstop_name': 'PILOT #492',
            'city': 'Seymour',
            'state': 'IN',
            'retail_price_per_gallon': 3.149,
            'gallons_purchased': 50.0,
            'stop_cost': 157.45,
            'lat': 38.958,
            'lng': -85.889,
        }
    ],
    'total_fuel_cost': 824.65,
    'total_gallons': 250.0,
    'num_stops': 5,
}


class TestRouteOptimizerView(TestCase):
    @patch('route_optimizer.views.find_optimal_fuel_stops', return_value=MOCK_OPTIMIZER_RESULT)
    @patch('route_optimizer.views.get_route', return_value=MOCK_ROUTE)
    @patch('route_optimizer.views.geocode_location', side_effect=[(40.71, -74.00), (34.05, -118.24)])
    def test_happy_path_returns_200(self, mock_geo, mock_route, mock_opt):
        response = self.client.post(
            '/api/route/',
            data=json.dumps({'start': 'New York, NY', 'end': 'Los Angeles, CA'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('fuel_stops', data)
        self.assertIn('total_fuel_cost', data)
        self.assertIn('route_polyline', data)
        self.assertEqual(data['start'], 'New York, NY')
        self.assertEqual(data['end'], 'Los Angeles, CA')

    def test_missing_start_returns_400(self):
        response = self.client.post(
            '/api/route/',
            data=json.dumps({'end': 'Los Angeles, CA'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('start', response.json())

    def test_missing_end_returns_400(self):
        response = self.client.post(
            '/api/route/',
            data=json.dumps({'start': 'New York, NY'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('end', response.json())

    @patch('route_optimizer.views.geocode_location', side_effect=ValueError("Could not geocode location: 'Fake City, ZZ'"))
    def test_geocoding_failure_returns_400(self, mock_geo):
        response = self.client.post(
            '/api/route/',
            data=json.dumps({'start': 'Fake City, ZZ', 'end': 'Los Angeles, CA'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())

    @patch('route_optimizer.views.geocode_location', side_effect=Exception("Network error"))
    def test_internal_error_returns_500(self, mock_geo):
        response = self.client.post(
            '/api/route/',
            data=json.dumps({'start': 'New York, NY', 'end': 'Los Angeles, CA'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 500)
        self.assertIn('error', response.json())
