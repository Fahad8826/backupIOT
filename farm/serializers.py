from rest_framework import serializers
from .models import Farm, Motor, Valve
from accounts.models import User


class ValveSerializer(serializers.ModelSerializer):
    is_active = serializers.IntegerField(default=0)

    class Meta:
        model = Valve
        fields = ['id', 'name', 'is_active']
        extra_kwargs = {'name': {'required': False}}

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['is_active'] = 1 if instance.is_active else 0
        return ret

    def to_internal_value(self, data):
        data = super().to_internal_value(data)
        if 'is_active' in data:
            data['is_active'] = bool(data['is_active'])
        return data


# serializers.py
class MotorSerializer(serializers.ModelSerializer):
    valves = ValveSerializer(many=True, read_only=True)

    class Meta:
        model = Motor
        fields = ['id', 'motor_type', 'valve_count', 'valves', 'farm', 'UIN', 'is_active']
        extra_kwargs = {
            'farm': {'required': False}
        }

    def validate_UIN(self, value):
        if value is not None:  # Only validate if UIN is provided
            if Motor.objects.filter(UIN=value).exclude(id=self.instance.id if self.instance else None).exists():
                raise serializers.ValidationError("A motor with this UIN already exists.")
        return value

    def validate(self, data):
        motor_type = data.get('motor_type', self.instance.motor_type if self.instance else None)
        valve_count = data.get('valve_count', self.instance.valve_count if self.instance else None)
        is_active = data.get('is_active', self.instance.is_active if self.instance else False)

        max_valves = {
            'single_phase': 4,
            'double_phase': 6,
            'triple_phase': 10
        }

        if motor_type and valve_count and valve_count > max_valves.get(motor_type, 0):
            raise serializers.ValidationError(
                f"{motor_type} cannot have more than {max_valves[motor_type]} valves"
            )

        # If updating and turning on motor, check valve status
        if self.instance and is_active and not self.instance.valves.filter(is_active=True).exists():
            raise serializers.ValidationError(
                "Motor cannot be turned on unless at least one valve is active."
            )

        return data

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['is_active'] = 1 if instance.is_active else 0
        return ret

    def to_internal_value(self, data):
        data = super().to_internal_value(data)
        if 'is_active' in data:
            data['is_active'] = bool(data['is_active'])
        return data


class FarmSerializer(serializers.ModelSerializer):
    motors = MotorSerializer(many=True, required=False)
    owner = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = Farm
        fields = ['id', 'name', 'location', 'owner', 'motors']

    def create(self, validated_data):
        # Extract motors data if provided
        motors_data = validated_data.pop('motors', [])

        # Create the farm
        farm = Farm.objects.create(**validated_data)

        # Create associated motors
        for motor_data in motors_data:
            # Add the farm to motor data before creating
            motor_data['farm'] = farm
            Motor.objects.create(**motor_data)

        return farm

    def update(self, instance, validated_data):
        # Handle motors during update
        motors_data = validated_data.pop('motors', None)

        # Update farm fields
        instance.name = validated_data.get('name', instance.name)
        instance.location = validated_data.get('location', instance.location)
        instance.owner = validated_data.get('owner', instance.owner)
        instance.save()

        # If motors are provided, update them
        if motors_data is not None:
            # First, remove existing motors
            instance.motors.all().delete()

            # Create new motors
            for motor_data in motors_data:
                motor_data['farm'] = instance
                Motor.objects.create(**motor_data)

        return instance