import logging
from django.apps import AppConfig

logger = logging.getLogger(__name__)


class RouteOptimizerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'route_optimizer'

    def ready(self):
        from .services.data_loader import load_station_data
        try:
            load_station_data()
        except Exception as e:
            logger.error(f"Failed to load station data at startup: {e}")
