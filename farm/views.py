from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import generics, status, permissions
from rest_framework.exceptions import ValidationError, NotFound
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Farm, Motor, Valve
from .serializers import FarmSerializer, MotorSerializer, ValveSerializer, MotorValveSerializer


# ---------------- Farm Views ----------------
class FarmListCreateView(generics.ListCreateAPIView):
    queryset = Farm.objects.all().order_by('-created_at')
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


# class MotorValveUpdate(generics.RetrieveUpdateAPIView):
#     queryset = Valve.objects.all()
#     serializer_class = ValveSerializer

#     # permission_classes = [permissions.IsAuthenticated]

#     def get_object(self):
#         """Retrieve a specific valve belonging to a motor identified by UIN"""
#         motor_uin = self.kwargs['UIN']  # Using UIN as the parameter name to match the model
#         valve_id = self.kwargs['valve_id']

#         # First get the motor by UIN
#         motor = get_object_or_404(Motor, UIN=motor_uin)

#         # Then get the valve associated with that motor
#         return get_object_or_404(Valve, valve_id=valve_id, motor=motor)

#     def update(self, request, *args, **kwargs):
#         """Update the valve properties (primarily is_active)"""
#         valve = self.get_object()

#         if 'is_active' in request.data:
#             try:
#                 # Convert to boolean for consistent handling
#                 is_active = bool(int(request.data.get('is_active')))
#                 valve.is_active = is_active
#             except (ValueError, TypeError):
#                 return Response(
#                     {'detail': 'is_active must be 0 or 1'},
#                     status=status.HTTP_400_BAD_REQUEST
#                 )

#         # Update other fields if needed
#         if 'name' in request.data:
#             valve.name = request.data.get('name')

#         if 'valve_id' in request.data:
#             valve.valve_id = request.data.get('valve_id')

#         valve.save()

#         # If valve was deactivated and it was the only active valve, deactivate the motor as well
#         motor = valve.motor
#         if not valve.is_active and not motor.valves.filter(is_active=True).exists() and motor.is_active:
#             motor.is_active = False
#             motor.save()

#         return Response({
#             "message": "Valve updated successfully",
#             "valve": self.serializer_class(valve).data
#         })


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



#----------------------nandhu json-------------------

# ---------------- Valve Update View ----------------
class FarmMotorValveUpdateView(generics.RetrieveUpdateAPIView):
    queryset = Valve.objects.all()
    serializer_class = ValveSerializer


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


class MotorDetailView1(generics.RetrieveUpdateDestroyAPIView):
    queryset = Motor.objects.all()
    serializer_class = MotorSerializer
    lookup_field = 'UIN'  # Change the lookup field to UIN

    def get_queryset(self):
        # Optional: Add optimized query
        return Motor.objects.all().select_related('farm').prefetch_related('valves')

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

# class MotorValveUpdate(generics.RetrieveUpdateAPIView):
#     queryset = Valve.objects.all()
#     serializer_class = ValveSerializer

#     # permission_classes = [permissions.IsAuthenticated]

#     def get_object(self):
#         """Retrieve a specific valve belonging to a motor identified by UIN"""
#         motor_uin = self.kwargs['UIN']  # Using UIN as the parameter name to match the model
#         valve_id = self.kwargs['valve_id']

#         # First get the motor by UIN
#         motor = get_object_or_404(Motor, UIN=motor_uin)

#         # Then get the valve associated with that motor
#         return get_object_or_404(Valve, valve_id=valve_id, motor=motor)

#     def update(self, request, *args, **kwargs):
#         """Update the valve properties (primarily is_active)"""
#         valve = self.get_object()

#         if 'is_active' in request.data:
#             try:
#                 # Convert to boolean for consistent handling
#                 is_active = bool(int(request.data.get('is_active')))
#                 valve.is_active = is_active
#             except (ValueError, TypeError):
#                 return Response(
#                     {'detail': 'is_active must be 0 or 1'},
#                     status=status.HTTP_400_BAD_REQUEST
#                 )

#         # Update other fields if needed
#         if 'name' in request.data:
#             valve.name = request.data.get('name')

#         if 'valve_id' in request.data:
#             valve.valve_id = request.data.get('valve_id')

#         valve.save()

#         # If valve was deactivated and it was the only active valve, deactivate the motor as well
#         motor = valve.motor
#         if not valve.is_active and not motor.valves.filter(is_active=True).exists() and motor.is_active:
#             motor.is_active = False
#             motor.save()

#         return Response({
#             "message": "Valve updated successfully",
#             "valve": self.serializer_class(valve).data
#         })



    
# class MotorValveUpdate(generics.RetrieveUpdateAPIView):
#     queryset = Valve.objects.all()
#     serializer_class = ValveSerializer
#     # permission_classes = [permissions.IsAuthenticated]
#
#     def get_object(self):
#         """Retrieve a specific valve belonging to a motor identified by UIN"""
#         motor_uin = self.kwargs.get('UIN')
#         valve_id = self.kwargs.get('valve_id')
#
#         # Validate motor
#         motor = get_object_or_404(Motor, UIN=motor_uin)
#
#         # Validate valve under that motor
#         return get_object_or_404(Valve, valve_id=valve_id, motor=motor)
#
#     def update(self, request, *args, **kwargs):
#         """Update the valve properties with error handling"""
#         try:
#             valve = self.get_object()
#             motor = valve.motor
#
#             data = request.data
#
#             # Validate and update `is_active` if provided
#             if 'is_active' in data:
#                 try:
#                     is_active = bool(int(data['is_active']))
#                     valve.is_active = is_active
#                 except (ValueError, TypeError):
#                     raise ValidationError({'is_active': 'Value must be 0 or 1 (interpreted as boolean).'})
#
#             # Update `name` if provided
#             if 'name' in data:
#                 if not isinstance(data['name'], str) or not data['name'].strip():
#                     raise ValidationError({'name': 'Name must be a non-empty string.'})
#                 valve.name = data['name']
#
#             # Update `valve_id` if provided
#             if 'valve_id' in data:
#                 new_valve_id = data['valve_id']
#                 if Valve.objects.filter(valve_id=new_valve_id).exclude(pk=valve.pk).exists():
#                     raise ValidationError({'valve_id': 'This valve ID is already in use.'})
#                 valve.valve_id = new_valve_id
#
#             valve.save()
#
#             # Deactivate the motor if no valves are active
#             if not valve.is_active and not motor.valves.filter(is_active=True).exists() and motor.is_active:
#                 motor.is_active = False
#                 motor.save()
#
#             return Response({
#                 "message": "Valve updated successfully",
#                 "valve": self.serializer_class(valve).data
#             }, status=status.HTTP_200_OK)
#
#         except ValidationError as e:
#             return Response({'errors': e.detail}, status=status.HTTP_400_BAD_REQUEST)
#
#         except Exception as e:
#             return Response(
#                 {"error": "An unexpected error occurred", "details": str(e)},
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )


class MotorValveUpdate(generics.RetrieveUpdateAPIView):
    queryset = Valve.objects.all()
    serializer_class = ValveSerializer
    # permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """Retrieve a specific valve belonging to a motor identified by UIN"""
        motor_uin = self.kwargs.get('UIN')
        valve_id = self.kwargs.get('valve_id')

        motor = get_object_or_404(Motor, UIN=motor_uin)
        return get_object_or_404(Valve, valve_id=valve_id, motor=motor)

    def update(self, request, *args, **kwargs):
        try:
            valve = self.get_object()
            motor = valve.motor
            data = request.data.copy()

            # Helper: convert to boolean or raise error
            def parse_bool(field_name):
                try:
                    return bool(int(data[field_name]))
                except (ValueError, TypeError):
                    raise ValidationError({field_name: "Must be 0 or 1 (interpreted as boolean)."})

            # Validate and update 'is_active'
            if 'is_active' in data:
                valve.is_active = parse_bool('is_active')

            # Validate and update 'status'
            if 'status' in data:
                valve.status = parse_bool('status')

            # Validate and update 'name'
            if 'name' in data:
                name = data['name'].strip()
                if not name:
                    raise ValidationError({'name': 'Name must be a non-empty string.'})
                valve.name = name

            # Validate and update 'valve_id'
            if 'valve_id' in data:
                new_valve_id = data['valve_id']
                if Valve.objects.filter(valve_id=new_valve_id).exclude(pk=valve.pk).exists():
                    raise ValidationError({'valve_id': 'This valve ID is already in use.'})
                valve.valve_id = new_valve_id

            valve.save()

            # Auto-deactivate motor if no active valves
            if not valve.is_active and not motor.valves.filter(is_active=True).exists() and motor.is_active:
                motor.is_active = False
                motor.save()

            return Response({
                "message": "Valve updated successfully",
                "valve": self.serializer_class(valve).data
            }, status=status.HTTP_200_OK)

        except ValidationError as e:
            return Response({'errors': e.detail}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"error": "An unexpected error occurred", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )