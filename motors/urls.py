from django.urls import path
from django.views.generic import TemplateView

from .views import (
    MotorListCreateView,
    MotorRetrieveUpdateDestroyView,
    ValveListView,
    ValveControlView,
    ValveStatusView,
    MotorStatusToggleView,
    MotorStatusSetView,
)

urlpatterns = [
    # Motor endpoints (API)
    path('api/motors/', MotorListCreateView.as_view(), name='motor-list-create'),
    path('api/motors/<int:pk>/', MotorRetrieveUpdateDestroyView.as_view(), name='motor-detail'),

    # Valve endpoints (API)
    path('api/motors/<int:motor_id>/valves/', ValveListView.as_view(), name='valve-list'),
    path('api/motors/<int:motor_id>/control-valve/<int:valve_number>/',
         ValveControlView.as_view(), name='control-valve'),
    path('api/motors/<int:motor_id>/valve-status/',
         ValveStatusView.as_view(), name='valve-status'),

    # Motor status endpoints (API)
    path('api/motors/<int:motor_id>/toggle-status/',
         MotorStatusToggleView.as_view(), name='motor-toggle-status'),
    path('api/motors/<int:motor_id>/set-status/',
         MotorStatusSetView.as_view(), name='motor-set-status'),

    # Frontend template
    path('motor-management/',
         TemplateView.as_view(template_name="motor_managment.html"),
         name='motor_management'),]