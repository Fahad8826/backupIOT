
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
    # permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """Retrieve a specific motor belonging to a farm"""
        farm_id = self.kwargs['farm_id']
        motor_id = self.kwargs['motor_id']
        return get_object_or_404(Motor, id=motor_id, farm_id=farm_id)

    def update(self, request, *args, **kwargs):
        """Allows users to update only the status field"""
        motor = self.get_object()
        motor.status = request.data.get('status', motor.status)
        motor.save()
        return Response({"message": "Motor status updated successfully", "status": motor.status})


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
        """Allows users to update only the status field"""
        valve = self.get_object()
        valve.status = request.data.get('status', valve.status)
        valve.save()
        return Response({"message": "Valve status updated successfully", "status": valve.status})


class CheckUINView(APIView):
    def get(self, request):
        uin = request.query_params.get('uin')
        exclude_id = request.query_params.get('exclude')

        query = Motor.objects.filter(UIN=uin)
        if exclude_id:
            query = query.exclude(id=exclude_id)

        exists = query.exists()
        return Response({"exists": exists})