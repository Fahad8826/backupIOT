
# from django.shortcuts import get_object_or_404
# from rest_framework import generics, status, permissions
# from rest_framework.views import APIView
# from rest_framework.response import Response
# from .models import Farm, Motor, Valve
# from .serializers import FarmSerializer, MotorSerializer, ValveSerializer
#
#
# # ---------------- Farm Views ----------------
# class FarmListCreateView(generics.ListCreateAPIView):
#     queryset = Farm.objects.all()
#     serializer_class = FarmSerializer
#
#
# class FarmDetailView(generics.RetrieveUpdateDestroyAPIView):
#     queryset = Farm.objects.all()
#     serializer_class = FarmSerializer
#
#
# # ---------------- Motor Views ----------------
# class MotorListCreateView(generics.ListCreateAPIView):
#     queryset = Motor.objects.all()
#     serializer_class = MotorSerializer
#
#
# class MotorDetailView(generics.RetrieveUpdateDestroyAPIView):
#     queryset = Motor.objects.all()
#     serializer_class = MotorSerializer
#
#     def patch(self, request, *args, **kwargs):
#         """Handle partial updates, including toggling is_active"""
#         instance = self.get_object()
#         serializer = self.get_serializer(instance, data=request.data, partial=True)
#         serializer.is_valid(raise_exception=True)
#
#         # Additional check before saving
#         if 'is_active' in request.data and request.data['is_active']:
#             if not instance.valves.filter(is_active=True).exists():
#                 return Response(
#                     {"detail": "Motor cannot be turned on unless at least one valve is active."},
#                     status=status.HTTP_400_BAD_REQUEST
#                 )
#
#         self.perform_update(serializer)
#         return Response(serializer.data)
#
#
# # ---------------- Valve Views ----------------
# class ValveListCreateView(generics.ListCreateAPIView):
#     queryset = Valve.objects.all()
#     serializer_class = ValveSerializer
#
#
# class ValveDetailView(generics.RetrieveUpdateDestroyAPIView):
#     queryset = Valve.objects.all()
#     serializer_class = ValveSerializer
#
#
# # ---------------- Motor Toggle View ----------------
# # class MotorToggleView(APIView):
# #     permission_classes = [permissions.IsAuthenticated]
# #
# #     def post(self, request, motor_id):
# #         try:
# #             motor = Motor.objects.get(id=motor_id, farm__owner=request.user)
# #             new_state = request.data.get('is_active', not motor.is_active)
# #
# #             if new_state and not motor.valves.filter(is_active=True).exists():
# #                 return Response(
# #                     {"detail": "Motor cannot be turned on unless at least one valve is active."},
# #                     status=status.HTTP_400_BAD_REQUEST
# #                 )
# #
# #             motor.is_active = new_state
# #             motor.save()
# #             serializer = MotorSerializer(motor)
# #             return Response(serializer.data)
# #
# #         except Motor.DoesNotExist:
# #             return Response(
# #                 {"detail": "Motor not found or you do not have permission to access this motor."},
# #                 status=status.HTTP_404_NOT_FOUND
# #             )
#
#
# # ---------------- User's Farms View ----------------
# class UserFarmsView(APIView):
#     # permission_classes = [permissions.IsAuthenticated]
#
#     def get(self, request):
#         farms = Farm.objects.filter(owner=request.user)
#         serializer = FarmSerializer(farms, many=True)
#         return Response(serializer.data)
#
#
# class FarmMotorsListView(generics.ListAPIView):
#     """Lists all motors belonging to a specific farm"""
#     serializer_class = MotorSerializer
#     # permission_classes = [permissions.IsAuthenticated]
#
#     def get_queryset(self):
#         farm_id = self.kwargs.get('farm_id')  # Correct way to fetch farm_id
#         return Motor.objects.filter(farm_id=farm_id)
#
#
#
#
# # ---------------- Motor Update View ----------------

#
# # ---------------- Valve Update View ----------------
# class FarmMotorValveUpdateView(generics.RetrieveUpdateAPIView):
#     queryset = Valve.objects.all()
#     serializer_class = ValveSerializer
#     # permission_classes = [permissions.IsAuthenticated]
#
#     def get_object(self):
#         """Retrieve a specific valve belonging to a motor and farm"""
#         farm_id = self.kwargs['farm_id']
#         motor_id = self.kwargs['motor_id']
#         valve_id = self.kwargs['valve_id']
#         return get_object_or_404(Valve, id=valve_id, motor_id=motor_id, motor__farm_id=farm_id)
#
#     def update(self, request, *args, **kwargs):
#         """Allows users to update only the status field"""
#         valve = self.get_object()
#         valve.status = request.data.get('status', valve.status)
#         valve.save()
#         return Response({"message": "Valve status updated successfully", "status": valve.status})


from django.shortcuts import get_object_or_404
from rest_framework import generics, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Farm, Motor, Valve
from .serializers import FarmSerializer, MotorSerializer, ValveSerializer


# ---------------- Farm Views ----------------
class FarmListCreateView(generics.ListCreateAPIView):
    queryset = Farm.objects.all()
    serializer_class = FarmSerializer


class FarmDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Farm.objects.all()
    serializer_class = FarmSerializer


# ---------------- Motor Views ----------------
class MotorListCreateView(generics.ListCreateAPIView):
    queryset = Motor.objects.all()
    serializer_class = MotorSerializer


class MotorDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Motor.objects.all()
    serializer_class = MotorSerializer

    def patch(self, request, *args, **kwargs):
        """Handle partial updates, including toggling is_active"""
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        # Additional check before saving
        if 'is_active' in request.data and request.data['is_active']:
            if not instance.valves.filter(is_active=True).exists():
                return Response(
                    {"detail": "Motor cannot be turned on unless at least one valve is active."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        self.perform_update(serializer)
        return Response(serializer.data)


# ---------------- Valve Views ----------------
class ValveListCreateView(generics.ListCreateAPIView):
    queryset = Valve.objects.all()
    serializer_class = ValveSerializer


class ValveDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Valve.objects.all()
    serializer_class = ValveSerializer


# ---------------- User's Farms View ----------------
class UserFarmsView(APIView):
    # permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        farms = Farm.objects.filter(owner=request.user)
        serializer = FarmSerializer(farms, many=True)
        return Response(serializer.data)


class FarmMotorsListView(generics.ListAPIView):
    """Lists all motors belonging to a specific farm"""
    serializer_class = MotorSerializer
    # permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        farm_id = self.kwargs.get('farm_id')  # Correct way to fetch farm_id
        return Motor.objects.filter(farm_id=farm_id)


# ---------------- Motor Update View ----------------
class FarmMotorUpdateView(generics.RetrieveUpdateAPIView):
    queryset = Motor.objects.all()
    serializer_class = MotorSerializer

    def get_object(self):
        """Retrieve a specific motor belonging to a farm"""
        farm_id = self.kwargs['farm_id']
        motor_id = self.kwargs['motor_id']
        return get_object_or_404(Motor, id=motor_id, farm_id=farm_id)

    def update(self, request, *args, **kwargs):
        """Allows users to update all fields of a motor"""
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(serializer.data)


# ---------------- Valve Update View ----------------
class FarmMotorValveUpdateView(generics.RetrieveUpdateAPIView):
    queryset = Valve.objects.all()
    serializer_class = ValveSerializer
    # permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """Retrieve a specific valve belonging to a motor and farm"""
        farm_id = self.kwargs['farm_id']
        motor_id = self.kwargs['motor_id']
        valve_id = self.kwargs['valve_id']
        return get_object_or_404(Valve, id=valve_id, motor_id=motor_id, motor__farm_id=farm_id)

    def update(self, request, *args, **kwargs):
        """Allows users to update only the is_active field"""
        valve = self.get_object()
        valve.is_active = request.data.get('is_active', valve.is_active)  # Use is_active instead of status
        valve.save()
        return Response({"message": "Valve active state updated successfully", "is_active": valve.is_active})