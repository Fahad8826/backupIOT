# farm/views.py
from rest_framework import generics
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

class ValveListCreateView(generics.ListCreateAPIView):
    queryset = Valve.objects.all()
    serializer_class = ValveSerializer

class ValveDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Valve.objects.all()
    serializer_class = ValveSerializer

# New view for user's farms
class UserFarmsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        farms = Farm.objects.filter(owner=request.user)
        serializer = FarmSerializer(farms, many=True)
        return Response(serializer.data)
    

# Additional view in farm/views.py
class FarmMotorsView(APIView):
    # permission_classes = [IsAuthenticated]

    def get(self, request, farm_id):
        """
        Retrieve all motors associated with a specific farm.
        Ensures that the user can only access motors from farms they own.
        """
        try:
            # First, verify that the farm exists and belongs to the user
            farm = Farm.objects.get(id=farm_id, owner=request.user)
            
            # Get all motors associated with this farm
            motors = Motor.objects.filter(farm=farm)
            
            # Serialize the motors
            serializer = MotorSerializer(motors, many=True)
            
            return Response(serializer.data)
        
        except Farm.DoesNotExist:
            # Return a 404 if the farm doesn't exist or doesn't belong to the user
            return Response(
                {"detail": "Farm not found or you do not have permission to access this farm."},
                status=404
            )