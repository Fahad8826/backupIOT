# views.py
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Motor, Valve
from .serializers import MotorSerializer, ValveSerializer
from django.shortcuts import get_object_or_404


class MotorListCreateView(generics.ListCreateAPIView):
    serializer_class = MotorSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return only motors owned by the current user"""
        return Motor.objects.filter(owner=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Set owner to current user
        motor = serializer.save(owner=request.user)

        # Create valves (max 4)
        vcount = min(motor.VCOUNT, 4)
        existing_valve_numbers = set(motor.valves.values_list('valve_number', flat=True))

        for i in range(1, vcount + 1):
            if i not in existing_valve_numbers:
                Valve.objects.create(
                    motor=motor,
                    valve_number=i,
                    value="0"
                )

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class MotorRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = MotorSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return only motors owned by the current user"""
        return Motor.objects.filter(owner=self.request.user)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        old_vcount = instance.VCOUNT

        serializer = self.get_serializer(instance, data=request.data, partial=kwargs.pop('partial', False))
        serializer.is_valid(raise_exception=True)
        motor = serializer.save()

        # Handle valve count changes (max 4)
        new_vcount = min(motor.VCOUNT, 4)
        existing_valve_numbers = set(motor.valves.values_list('valve_number', flat=True))

        # Create missing valves
        for i in range(1, new_vcount + 1):
            if i not in existing_valve_numbers:
                Valve.objects.create(
                    motor=motor,
                    valve_number=i,
                    value="0"
                )

        # Remove extra valves if VCOUNT was reduced
        if new_vcount < old_vcount:
            motor.valves.filter(valve_number__gt=new_vcount).delete()

        return Response(serializer.data)


class ValveListView(generics.ListAPIView):
    serializer_class = ValveSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        motor_id = self.kwargs.get('motor_id')
        motor = get_object_or_404(Motor, pk=motor_id, owner=self.request.user)
        return motor.valves.all()


class ValveControlView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, motor_id, valve_number):
        """Control (turn on/off) a specific valve of a motor"""
        motor = get_object_or_404(Motor, pk=motor_id, owner=self.request.user)

        try:
            valve = motor.valves.get(valve_number=valve_number)
        except Valve.DoesNotExist:
            return Response(
                {"error": f"Valve {valve_number} does not exist for motor {motor.name}"},
                status=status.HTTP_404_NOT_FOUND
            )

        action_type = request.data.get('action', '').lower()

        if action_type == 'on':
            valve.turn_on()
            return Response({"status": "success", "message": f"Valve {valve_number} turned ON"})
        elif action_type == 'off':
            valve.turn_off()
            return Response({"status": "success", "message": f"Valve {valve_number} turned OFF"})
        else:
            return Response(
                {"error": "Invalid action. Use 'on' or 'off'"},
                status=status.HTTP_400_BAD_REQUEST
            )


class ValveStatusView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, motor_id):
        """Get the status of all valves for a motor"""
        motor = get_object_or_404(Motor, pk=motor_id, owner=self.request.user)
        valves = motor.valves.all()

        status_data = {
            "motor_name": motor.name,
            "UIN": motor.UIN,
            "valve_count": min(motor.VCOUNT, 4),
            "valves": {
                f"V{valve.valve_number}": {
                    "status": "On" if valve.value == "1" else "Off",
                    "value": valve.value,
                    "last_operated": valve.last_operated_at
                } for valve in valves
            }
        }

        return Response(status_data)


class MotorStatusToggleView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, motor_id):
        """Toggle the status of a motor between Working (1) and Idle (0)"""
        motor = get_object_or_404(Motor, pk=motor_id, owner=self.request.user)

        motor.STATUS = "0" if motor.STATUS == "1" else "1"
        motor.save()

        status_display = "Working" if motor.STATUS == "1" else "Idle"

        return Response({
            "status": "success",
            "message": f"Motor {motor.name} status changed to {status_display}",
            "motor_status": motor.STATUS,
            "status_display": status_display,
            "status_color": motor.status_color
        })


class MotorStatusSetView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, motor_id):
        """Set the status of a motor to Working (1) or Idle (0)"""
        motor = get_object_or_404(Motor, pk=motor_id, owner=self.request.user)

        status_value = request.data.get('status')
        if status_value not in ["0", "1"]:
            return Response(
                {"error": "Invalid status. Use '0' for Idle or '1' for Working"},
                status=status.HTTP_400_BAD_REQUEST
            )

        motor.STATUS = status_value
        motor.save()

        status_display = "Working" if status_value == "1" else "Idle"

        return Response({
            "status": "success",
            "message": f"Motor {motor.name} status set to {status_display}",
            "motor_status": motor.STATUS,
            "status_display": status_display,
            "status_color": motor.status_color
        })