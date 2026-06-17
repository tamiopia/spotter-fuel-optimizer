import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .serializers import RouteRequestSerializer
from .services.routing import geocode_location, get_route
from .services.fuel_optimizer import find_optimal_fuel_stops
import route_optimizer.services.data_loader as _dl

logger = logging.getLogger(__name__)


class RouteOptimizerView(APIView):
    """
    POST /api/route/

    Accepts start and end US locations.
    Returns optimal fuel stops and total trip cost.
    """

    def post(self, request):
        if not _dl.STATIONS_READY:
            return Response(
                {'error': 'Station data is still loading. Please retry in a few minutes.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        serializer = RouteRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        start = serializer.validated_data['start']
        end = serializer.validated_data['end']

        try:
            start_coords = geocode_location(start)
            end_coords = geocode_location(end)

            route = get_route(start_coords, end_coords)

            optimizer_result = find_optimal_fuel_stops(
                polyline_coords=route['polyline_coords'],
                total_miles=route['distance_miles'],
            )

            response_data = {
                'start': start,
                'end': end,
                'total_distance_miles': route['distance_miles'],
                'total_duration_hours': round(route['duration_seconds'] / 3600, 2),
                'num_fuel_stops': optimizer_result['num_stops'],
                'total_gallons': optimizer_result['total_gallons'],
                'total_fuel_cost': optimizer_result['total_fuel_cost'],
                'fuel_stops': optimizer_result['fuel_stops'],
                'route_polyline': route['encoded_polyline'],
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Route optimization failed: {e}", exc_info=True)
            return Response(
                {'error': 'Internal server error. Check logs for details.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
