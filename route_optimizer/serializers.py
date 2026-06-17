from rest_framework import serializers


class RouteRequestSerializer(serializers.Serializer):
    start = serializers.CharField(
        max_length=200,
        help_text="Start location, e.g. 'New York, NY'"
    )
    end = serializers.CharField(
        max_length=200,
        help_text="End location, e.g. 'Los Angeles, CA'"
    )


class FuelStopSerializer(serializers.Serializer):
    stop_number = serializers.IntegerField()
    mile_marker = serializers.FloatField()
    truckstop_name = serializers.CharField()
    city = serializers.CharField()
    state = serializers.CharField()
    retail_price_per_gallon = serializers.FloatField()
    gallons_purchased = serializers.FloatField()
    stop_cost = serializers.FloatField()
    lat = serializers.FloatField()
    lng = serializers.FloatField()


class RouteResponseSerializer(serializers.Serializer):
    start = serializers.CharField()
    end = serializers.CharField()
    total_distance_miles = serializers.FloatField()
    total_duration_hours = serializers.FloatField()
    num_fuel_stops = serializers.IntegerField()
    total_gallons = serializers.FloatField()
    total_fuel_cost = serializers.FloatField()
    fuel_stops = FuelStopSerializer(many=True)
    route_polyline = serializers.CharField(help_text="Encoded polyline for map rendering")
