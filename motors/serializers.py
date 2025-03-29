from rest_framework import serializers
from .models import Motor, Valve


class ValveSerializer(serializers.ModelSerializer):
    status_display = serializers.SerializerMethodField()

    class Meta:
        model = Valve
        fields = ['valve_number', 'value', 'status_display', 'last_operated_at']

    def get_status_display(self, obj):
        return "On" if obj.value == "1" else "Off"


class MotorSerializer(serializers.ModelSerializer):
    valves = ValveSerializer(many=True, read_only=True)
    status_display = serializers.SerializerMethodField()
    status_color = serializers.SerializerMethodField()
    owner = serializers.PrimaryKeyRelatedField(
        read_only=True,
        default=serializers.CurrentUserDefault()
    )

    # Only keeping V1-V4 since we only need 4 valves
    V1 = serializers.CharField(write_only=True, required=False, default="0")
    V2 = serializers.CharField(write_only=True, required=False, default="0")
    V3 = serializers.CharField(write_only=True, required=False, default="0")
    V4 = serializers.CharField(write_only=True, required=False, default="0")

    class Meta:
        model = Motor
        fields = ['id', 'owner', 'name', 'UIN', 'TYPE', 'VCOUNT', 'STATUS',
                  'status_display', 'status_color', 'V1', 'V2', 'V3', 'V4',
                  'valves', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_status_display(self, obj):
        return "Working" if obj.STATUS == "1" else "Idle"

    def get_status_color(self, obj):
        return obj.status_color

    def validate_VCOUNT(self, value):
        """Ensure VCOUNT doesn't exceed 4"""
        if value > 4:
            raise serializers.ValidationError("Maximum 4 valves allowed")
        return value

    def create(self, validated_data):
        # Set the owner to the current user
        validated_data['owner'] = self.context['request'].user

        # Extract valve data (only V1-V4)
        valve_data = {}
        for i in range(1, 5):
            key = f'V{i}'
            if key in validated_data:
                valve_data[i] = validated_data.pop(key)

        # Create the motor
        motor = Motor.objects.create(**validated_data)

        # Create valves based on VCOUNT (max 4)
        vcount = min(int(validated_data.get('VCOUNT', 0)), 4)

        for i in range(1, vcount + 1):
            value = valve_data.get(i, "0")
            Valve.objects.create(
                motor=motor,
                valve_number=i,
                value=value
            )

        return motor

    def update(self, instance, validated_data):
        # Extract valve data (only V1-V4)
        valve_data = {}
        for i in range(1, 5):
            key = f'V{i}'
            if key in validated_data:
                valve_data[i] = validated_data.pop(key)

        # Update the motor instance
        old_vcount = instance.VCOUNT
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Get the new VCOUNT (capped at 4)
        new_vcount = min(int(instance.VCOUNT), 4)

        # Update existing valves or create new ones
        for i in range(1, new_vcount + 1):
            if i in valve_data:
                valve, created = Valve.objects.update_or_create(
                    motor=instance,
                    valve_number=i,
                    defaults={'value': valve_data[i]}
                )

        # Create any missing valves if VCOUNT was increased
        existing_valve_numbers = set(Valve.objects.filter(motor=instance).values_list('valve_number', flat=True))
        for i in range(1, new_vcount + 1):
            if i not in existing_valve_numbers:
                value = valve_data.get(i, "0")
                Valve.objects.create(
                    motor=instance,
                    valve_number=i,
                    value=value
                )

        # Remove extra valves if VCOUNT was reduced
        if new_vcount < old_vcount:
            Valve.objects.filter(motor=instance, valve_number__gt=new_vcount).delete()

        return instance