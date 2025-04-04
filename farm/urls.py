# # farm/urls.py
# from django.urls import path
# from django.views.generic import TemplateView
#
# from .views import (
#     FarmListCreateView, FarmDetailView,
#     MotorListCreateView, MotorDetailView,
#     ValveListCreateView, ValveDetailView,
#     UserFarmsView, MotorToggleView, FarmMotorUpdateView, FarmMotorValveUpdateView,
# )
#
# urlpatterns = [
#     # Farm endpoints
#     path('farms/', FarmListCreateView.as_view(), name='farm-list-create'),
#     path('farms/<int:pk>/', FarmDetailView.as_view(), name='farm-detail'),
#
#     # Motor endpoints
#     path('motors/', MotorListCreateView.as_view(), name='motor-list-create'),
#     path('motors/<int:pk>/', MotorDetailView.as_view(), name='motor-detail'),
#
#     # Valve endpoints
#     path('valves/', ValveListCreateView.as_view(), name='valve-list-create'),
#     path('valves/<int:pk>/', ValveDetailView.as_view(), name='valve-detail'),
#     path("farm-management/", TemplateView.as_view(template_name ='create_farm.html'), name='create_farm_page'),
#     #userfarmview
#     path('my-farms/', UserFarmsView.as_view(), name='user-farms'),
#     path('motors/<int:motor_id>/toggle/', MotorToggleView.as_view(), name='motor-toggle'),
#     path('farms/<int:farm_id>/motors/', FarmMotorUpdateView.as_view(), name='farm-motors'),
#
#     path('farms/<int:farm_id>/motors/<int:motor_id>/valves/', FarmMotorValveUpdateView.as_view(), name='farm-motor-valves'),
#
# ]
from django.urls import path
from django.views.generic import TemplateView
from .views import (
    FarmListCreateView, FarmDetailView,
    MotorListCreateView, MotorDetailView,
    ValveListCreateView, ValveDetailView,
    UserFarmsView, FarmMotorUpdateView, FarmMotorValveUpdateView,
    FarmMotorsListView, CheckUINView  # ✅ Add this new view for listing motors in a farm
)

urlpatterns = [
    # Farm endpoints
    path('farms/', FarmListCreateView.as_view(), name='farm-list-create'),
    path('farms/<int:pk>/', FarmDetailView.as_view(), name='farm-detail'),

    # Motor endpoints
    path('motors/', MotorListCreateView.as_view(), name='motor-list-create'),
    path('motors/<int:pk>/', MotorDetailView.as_view(), name='motor-detail'),

    # Valve endpoints
    path('valves/', ValveListCreateView.as_view(), name='valve-list-create'),
    path('valves/<int:pk>/', ValveDetailView.as_view(), name='valve-detail'),

    # Farm management page (HTML template view)
    path("farm-management/", TemplateView.as_view(template_name='create_farm.html'), name='create_farm_page'),

    # User Farms
    path('my-farms/', UserFarmsView.as_view(), name='user-farms'),

    # Motor toggle
    # path('motors/<int:motor_id>/toggle/', MotorToggleView.as_view(), name='motor-toggle'),

    # ✅ List motors of a specific farm
    path('farms/<int:farm_id>/motors/', FarmMotorsListView.as_view(), name='farm-motors-list'),

    # ✅ Update a specific motor's status
    path('farms/<int:farm_id>/motors/<int:motor_id>/update/', FarmMotorUpdateView.as_view(), name='farm-motor-update'),

    # ✅ Update a specific valve's status
    path('farms/<int:farm_id>/motors/<int:motor_id>/valves/<int:valve_id>/update/', FarmMotorValveUpdateView.as_view(), name='farm-motor-valve-update'),

path('check-uin/', CheckUINView.as_view(), name='check-uin'),
]

