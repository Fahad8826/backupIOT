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
            # Get IDs of motors in the form submission
            submitted_motor_ids = []
            new_motors = []

            # First, update existing motors and collect new ones
            for motor_data in motors_data:
                motor_id = motor_data.get('id')

                if motor_id and motor_id != '':
                    # This is an existing motor - update it
                    try:
                        motor = Motor.objects.get(id=motor_id, farm=instance)
                        for key, value in motor_data.items():
                            if key != 'id' and key != 'farm':
                                setattr(motor, key, value)
                        motor.save()
                        submitted_motor_ids.append(motor_id)
                    except Motor.DoesNotExist:
                        # Motor ID doesn't exist or doesn't belong to this farm
                        new_motors.append(motor_data)
                else:
                    # This is a new motor
                    new_motors.append(motor_data)

            # Now create any new motors
            for motor_data in new_motors:
                motor_data['farm'] = instance
                new_motor = Motor.objects.create(**motor_data)
                submitted_motor_ids.append(new_motor.id)

            # Delete motors that weren't in the submitted data
            if submitted_motor_ids:
                instance.motors.exclude(id__in=submitted_motor_ids).delete()

        return instance