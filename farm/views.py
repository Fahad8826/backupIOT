# farm/views.py
from symtable import Class

from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Farm, Motor, Valve
from .serializers import FarmSerializer, MotorSerializer, ValveSerializer

# Existing views
class FarmListCreateView(generics.ListCreateAPIView):
    queryset = Farm.objects.all()
    serializer_class = FarmSerializer

class FarmDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Farm.objects.all()
    serializer_class = FarmSerializer

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

class ValveListCreateView(generics.ListCreateAPIView):
    queryset = Valve.objects.all()
    serializer_class = ValveSerializer

class ValveDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Valve.objects.all()
    serializer_class = ValveSerializer


class MotorToggleView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, motor_id):
        try:
            motor = Motor.objects.get(id=motor_id, farm__owner=request.user)
            new_state = request.data.get('is_active', not motor.is_active)

            if new_state and not motor.valves.filter(is_active=True).exists():
                return Response(
                    {"detail": "Motor cannot be turned on unless at least one valve is active."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            motor.is_active = new_state
            motor.save()
            serializer = MotorSerializer(motor)
            return Response(serializer.data)

        except Motor.DoesNotExist:
            return Response(
                {"detail": "Motor not found or you do not have permission to access this motor."},
                status=status.HTTP_404_NOT_FOUND
            )


# New view for user's farms
class UserFarmsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        farms = Farm.objects.filter(owner=request.user)
        serializer = FarmSerializer(farms, many=True)
        return Response(serializer.data)


    

# Additional view in farm/views.py
# class FarmMotorsView(APIView):
#     # permission_classes = [IsAuthenticated]
#
#     def get(self, request, farm_id):
#         """
#         Retrieve all motors associated with a specific farm.
#         Ensures that the user can only access motors from farms they own.
#         """
#         try:
#             # First, verify that the farm exists and belongs to the user
#             farm = Farm.objects.get(id=farm_id, owner=request.user)
#
#             # Get all motors associated with this farm
#             motors = Motor.objects.filter(farm=farm)
#
#             # Serialize the motors
#             serializer = MotorSerializer(motors, many=True)
#
#             return Response(serializer.data)
#
#         except Farm.DoesNotExist:
#             # Return a 404 if the farm doesn't exist or doesn't belong to the user
#             return Response(
#                 {"detail": "Farm not found or you do not have permission to access this farm."},
#                 status=404
#             )

class FarmMotorsView(APIView):
    # permission_classes = [IsAuthenticated]  # Keep commented out as per your original code

    def get(self, request, farm_id):
        try:
            # Retrieve the farm by ID only, no owner check
            farm = Farm.objects.get(id=farm_id)
            # Get all motors associated with this farm
            motors = Motor.objects.filter(farm=farm)
            # Serialize the motors
            serializer = MotorSerializer(motors, many=True)
            return Response(serializer.data)
        except Farm.DoesNotExist:
            return Response(
                {"detail": "Farm not found."},
                status=404
            )


class FarmMotorValveView(APIView):
    # permission_classes = [IsAuthenticated]  # Commented out as per pattern in FarmMotorsView

    def get(self, request, farm_id, motor_id):
        try:
            # Retrieve the farm by ID
            farm = Farm.objects.get(id=farm_id)

            # Get the specific motor in this farm
            motor = Motor.objects.get(id=motor_id, farm=farm)

            # Get all valves associated with this motor
            valves = Valve.objects.filter(motor=motor)

            # Serialize the valves
            serializer = ValveSerializer(valves, many=True)

            return Response(serializer.data)
        except Farm.DoesNotExist:
            return Response(
                {"detail": "Farm not found."},
                status=404
            )
        except Motor.DoesNotExist:
            return Response(
                {"detail": "Motor not found in this farm."},
                status=404
            )
