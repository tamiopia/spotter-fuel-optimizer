from django.urls import path
from .views import RouteOptimizerView

urlpatterns = [
    path('route/', RouteOptimizerView.as_view(), name='route-optimizer'),
]
