from django.test import TestCase
from route_optimizer.services.geo_utils import haversine_miles, interpolate_along_polyline, decode_polyline


class TestHaversineMiles(TestCase):
    def test_nyc_to_la(self):
        nyc = (40.7128, -74.0060)
        la = (34.0522, -118.2437)
        distance = haversine_miles(nyc, la)
        self.assertAlmostEqual(distance, 2445, delta=50)

    def test_same_point(self):
        coord = (40.7128, -74.0060)
        self.assertAlmostEqual(haversine_miles(coord, coord), 0.0, places=5)

    def test_known_distance(self):
        # Chicago to Detroit: ~238 miles
        chicago = (41.8781, -87.6298)
        detroit = (42.3314, -83.0458)
        distance = haversine_miles(chicago, detroit)
        self.assertAlmostEqual(distance, 238, delta=15)


class TestInterpolateAlongPolyline(TestCase):
    def setUp(self):
        self.coords = [
            (40.0, -100.0),
            (40.0, -95.0),
            (40.0, -90.0),
            (40.0, -85.0),
        ]

    def test_fraction_zero_returns_first(self):
        result = interpolate_along_polyline(self.coords, 0.0)
        self.assertEqual(result, self.coords[0])

    def test_fraction_one_returns_last(self):
        result = interpolate_along_polyline(self.coords, 1.0)
        self.assertEqual(result, self.coords[-1])

    def test_midpoint(self):
        result = interpolate_along_polyline(self.coords, 0.5)
        self.assertAlmostEqual(result[0], 40.0, places=1)
        self.assertAlmostEqual(result[1], -92.5, delta=1.0)

    def test_raises_on_empty(self):
        with self.assertRaises(ValueError):
            interpolate_along_polyline([], 0.5)


class TestDecodePolyline(TestCase):
    def test_known_encoded(self):
        # Standard encoded polyline test vector
        encoded = "_p~iF~ps|U_ulLnnqC_mqNvxq`@"
        coords = decode_polyline(encoded)
        self.assertEqual(len(coords), 3)
        self.assertAlmostEqual(coords[0][0], 38.5, places=4)
        self.assertAlmostEqual(coords[0][1], -120.2, places=4)

    def test_returns_list_of_tuples(self):
        encoded = "_p~iF~ps|U_ulLnnqC_mqNvxq`@"
        coords = decode_polyline(encoded)
        for c in coords:
            self.assertIsInstance(c, tuple)
            self.assertEqual(len(c), 2)
