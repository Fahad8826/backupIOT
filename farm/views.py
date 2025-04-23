from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import generics, status, permissions
from rest_framework.exceptions import ValidationError
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Farm, Motor, Valve
from .serializers import FarmSerializer, MotorSerializer, ValveSerializer, MotorValveSerializer


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
        """
        Handle partial updates for the motor.
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)

        # Validate and save
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def perform_update(self, serializer):
        """
        Save the updated motor instance.
        """
        serializer.save()


# ---------------- Valve Views ----------------
class ValveListCreateView(generics.ListCreateAPIView):
    queryset = Valve.objects.all()
    serializer_class = ValveSerializer


class ValveDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Valve.objects.all()
    serializer_class = ValveSerializer


class MotorValveView(generics.ListAPIView, generics.UpdateAPIView):
    queryset = Motor.objects.all()
    serializer_class = MotorValveSerializer
    authentication_classes = []  # No authentication
    permission_classes = []  # No permission checks
    lookup_field = 'id'  # For update by ID

    def get_queryset(self):
        # Optimize queries for all motors
        return Motor.objects.all().select_related('farm').prefetch_related('valves')

    def update(self, request, *args, **kwargs):
        """Update a motor and its valves"""
        try:
            data = request.data
            if not isinstance(data, dict):
                return Response(
                    {'detail': 'Invalid data format. Expected a JSON object'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get the motor to update
            motor = self.get_object()

            # Handle motor update
            if 'is_active' in data:
                try:
                    is_active = bool(int(data['is_active']))
                    # Check if motor is being activated without active valves
                    if is_active and not motor.valves.filter(is_active=True).exists():
                        if 'valves' in data and data['valves']:
                            any_valve_active = any(
                                bool(int(v.get('is_active', 0))) for v in data['valves'] if 'is_active' in v)
                            if not any_valve_active:
                                return Response(
                                    {'detail': 'Motor cannot be activated without at least one active valve'},
                                    status=status.HTTP_400_BAD_REQUEST
                                )
                        else:
                            return Response(
                                {'detail': 'Motor cannot be activated without at least one active valve'},
                                status=status.HTTP_400_BAD_REQUEST
                            )
                    motor.is_active = is_active
                except (ValueError, TypeError):
                    return Response(
                        {'detail': 'is_active must be 0 or 1'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            # Update other motor fields
            if 'UIN' in data:
                motor.UIN = data['UIN']
            if 'motor_type' in data:
                if data['motor_type'] not in dict(Motor.MOTOR_TYPES):
                    return Response(
                        {'detail': f"Invalid motor_type. Must be one of: {', '.join(dict(Motor.MOTOR_TYPES).keys())}"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                motor.motor_type = data['motor_type']
            if 'valve_count' in data:
                try:
                    motor.valve_count = int(data['valve_count'])
                except (ValueError, TypeError):
                    return Response(
                        {'detail': 'valve_count must be a positive integer'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            # Validate and save motor
            motor.full_clean()  # Run model validation (e.g., valve count limits)
            motor.save()

            # Handle valve updates
            if 'valves' in data and isinstance(data['valves'], list):
                existing_valves = {valve.id: valve for valve in motor.valves.all()}
                existing_by_valve_id = {valve.valve_id: valve for valve in motor.valves.all() if valve.valve_id}
                processed_valve_ids = []

                for valve_data in data['valves']:
                    if not isinstance(valve_data, dict):
                        continue

                    # Find valve by id or valve_id
                    valve = None
                    valve_id = valve_data.get('id')
                    external_valve_id = valve_data.get('valve_id')

                    if valve_id and valve_id in existing_valves:
                        valve = existing_valves[valve_id]
                    elif external_valve_id and external_valve_id in existing_by_valve_id:
                        valve = existing_by_valve_id[external_valve_id]

                    # Update existing valve or create new one
                    if valve:
                        if 'name' in valve_data:
                            valve.name = valve_data['name']
                        if 'is_active' in valve_data:
                            try:
                                valve.is_active = bool(int(valve_data['is_active']))
                            except (ValueError, TypeError):
                                return Response(
                                    {'detail': f'Valve is_active must be 0 or 1 for valve {valve.id}'},
                                    status=status.HTTP_400_BAD_REQUEST
                                )
                        if 'valve_id' in valve_data:
                            valve.valve_id = valve_data['valve_id']
                        valve.save()
                        processed_valve_ids.append(valve.id)
                    else:
                        # Create new valve
                        new_valve_data = valve_data.copy()
                        if 'id' in new_valve_data:
                            del new_valve_data['id']
                        if 'is_active' in new_valve_data:
                            try:
                                new_valve_data['is_active'] = bool(int(new_valve_data['is_active']))
                            except (ValueError, TypeError):
                                return Response(
                                    {'detail': 'Valve is_active must be 0 or 1 for new valve'},
                                    status=status.HTTP_400_BAD_REQUEST
                                )
                        new_valve = Valve.objects.create(motor=motor, **new_valve_data)
                        processed_valve_ids.append(new_valve.id)

            # Ensure consistency: deactivate motor if no active valves
            if motor.is_active and not motor.valves.filter(is_active=True).exists():
                motor.is_active = False
                motor.save()

            # Return updated motor data
            serializer = self.get_serializer(motor)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except ValidationError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {'detail': f'Error updating motor and valves: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )



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