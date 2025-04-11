
from rest_framework import serializers
from .models import Farm, Motor, Valve
from accounts.models import User
from django.core.exceptions import ValidationError as DjangoValidationError


class ValveSerializer(serializers.ModelSerializer):
    class Meta:
        model = Valve
        fields = ['id', 'name', 'is_active','valve_id']
        extra_kwargs = {
            'name': {'required': False},
            'is_active': {'required': True}
        }

    def validate(self, attrs):
        """Validate valve-specific rules"""
        try:
            name = attrs.get('name', '')
            if name and len(name.strip()) < 1:
                raise serializers.ValidationError({
                    'name': 'Valve name cannot be empty if provided'
                })
            return attrs
        except Exception as e:
            raise serializers.ValidationError({
                'detail': f'Error validating valve: {str(e)}'
            })

    def to_representation(self, instance):
        """Convert boolean to integer for API response"""
        try:
            ret = super().to_representation(instance)
            ret['is_active'] = 1 if instance.is_active else 0
            return ret
        except Exception as e:
            raise serializers.ValidationError({
                'detail': f'Error in representation: {str(e)}'
            })

    def to_internal_value(self, data):
        """Convert incoming integer to boolean"""
        try:
            if not isinstance(data, dict):
                raise serializers.ValidationError({
                    'detail': 'Invalid valve data format'
                })

            data = data.copy()
            if 'is_active' in data:
                try:
                    data['is_active'] = bool(int(data['is_active']))
                except (ValueError, TypeError):
                    raise serializers.ValidationError({
                        'is_active': 'Must be 0 or 1'
                    })
            return super().to_internal_value(data)
        except Exception as e:
            raise serializers.ValidationError({
                'detail': f'Error processing valve data: {str(e)}'
            })


class MotorSerializer(serializers.ModelSerializer):
    valves = ValveSerializer(many=True, required=False)

    class Meta:
        model = Motor
        fields = ['id', 'motor_type', 'valve_count', 'valves', 'farm', 'UIN', 'is_active']
        extra_kwargs = {
            'farm': {'required': False},
            'UIN': {'allow_null': True},
            'valve_count': {'required': True},
            'motor_type': {'required': True}
        }

    def validate(self, data):
        """Validate motor-specific rules"""
        try:
            instance = getattr(self, 'instance', None)
            motor_type = data.get('motor_type', instance.motor_type if instance else None)
            valve_count = data.get('valve_count', instance.valve_count if instance else None)
            is_active = data.get('is_active', instance.is_active if instance else False)

            # Validate motor type
            if motor_type not in dict(Motor.MOTOR_TYPES):
                raise serializers.ValidationError({
                    'motor_type': f'Invalid motor type. Must be one of: {", ".join(k for k, _ in Motor.MOTOR_TYPES)}'
                })

            # Validate valve count against motor type
            if motor_type and valve_count is not None:
                max_valves = {
                    'single_phase': 4,
                    'double_phase': 6,
                    'triple_phase': 10
                }
                if valve_count < 0:
                    raise serializers.ValidationError({
                        'valve_count': 'Valve count cannot be negative'
                    })
                if valve_count > max_valves.get(motor_type, 0):
                    raise serializers.ValidationError({
                        'valve_count': f'{motor_type} cannot have more than {max_valves[motor_type]} valves'
                    })

            # Validate is_active with valves
            if is_active:
                valves_data = data.get('valves')
                if instance:
                    active_valves = instance.valves.filter(is_active=True).exists()
                    if valves_data is not None:
                        active_valves = any(v.get('is_active', False) for v in valves_data)
                    if not active_valves:
                        raise serializers.ValidationError({
                            'is_active': 'Motor cannot be active without at least one active valve'
                        })
                elif valves_data and not any(v.get('is_active', False) for v in valves_data):
                    data['_check_valves_on_create'] = True

            return data
        except Exception as e:
            raise serializers.ValidationError({
                'detail': f'Error validating motor: {str(e)}'
            })

    def to_representation(self, instance):
        """Convert boolean to integer for API response"""
        try:
            ret = super().to_representation(instance)
            ret['is_active'] = 1 if instance.is_active else 0
            return ret
        except Exception as e:
            raise serializers.ValidationError({
                'detail': f'Error in motor representation: {str(e)}'
            })

    def to_internal_value(self, data):
        """Convert incoming data to internal format"""
        try:
            if not isinstance(data, dict):
                raise serializers.ValidationError({
                    'detail': 'Invalid motor data format'
                })

            data = data.copy()
            if 'is_active' in data:
                try:
                    data['is_active'] = bool(int(data['is_active']))
                except (ValueError, TypeError):
                    raise serializers.ValidationError({
                        'is_active': 'Must be 0 or 1'
                    })
            return super().to_internal_value(data)
        except Exception as e:
            raise serializers.ValidationError({
                'detail': f'Error processing motor data: {str(e)}'
            })

    def create(self, validated_data):
        """Create a new motor with valves"""
        try:
            valves_data = validated_data.pop('valves', [])
            check_valves = validated_data.pop('_check_valves_on_create', False)

            motor = Motor.objects.create(**validated_data)

            for valve_data in valves_data:
                Valve.objects.create(motor=motor, **valve_data)

            if check_valves and motor.is_active and not motor.valves.filter(is_active=True).exists():
                if motor.valves.exists():
                    first_valve = motor.valves.first()
                    first_valve.is_active = True
                    first_valve.save()
                else:
                    motor.is_active = False
                    motor.save(update_fields=['is_active'])

            return motor
        except DjangoValidationError as e:
            raise serializers.ValidationError({
                'detail': str(e)
            })
        except Exception as e:
            raise serializers.ValidationError({
                'detail': f'Error creating motor: {str(e)}'
            })

    def update(self, instance, validated_data):
        """Update existing motor"""
        try:
            valves_data = validated_data.pop('valves', None)

            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()

            if valves_data is not None:
                existing_valves = {valve.id: valve for valve in instance.valves.all()}
                for valve_data in valves_data:
                    valve_id = valve_data.get('id')
                    if valve_id and valve_id in existing_valves:
                        valve = existing_valves.pop(valve_id)
                        for attr, value in valve_data.items():
                            setattr(valve, attr, value)
                        valve.save()
                    else:
                        Valve.objects.create(motor=instance, **valve_data)
                for valve in existing_valves.values():
                    valve.delete()

            return instance
        except DjangoValidationError as e:
            raise serializers.ValidationError({
                'detail': str(e)
            })
        except Exception as e:
            raise serializers.ValidationError({
                'detail': f'Error updating motor: {str(e)}'
            })


class FarmSerializer(serializers.ModelSerializer):
    motors = MotorSerializer(many=True, required=False)
    owner = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = Farm
        fields = ['id', 'name', 'location', 'owner', 'motors']
        extra_kwargs = {
            'name': {'required': True},
            'location': {'required': True},
            'owner': {'required': True}
        }

    def validate(self, attrs):
        """Validate farm-specific rules"""
        try:
            name = attrs.get('name')
            location = attrs.get('location')

            if name and len(name.strip()) < 1:
                raise serializers.ValidationError({
                    'name': 'Farm name cannot be empty'
                })
            if location and len(location.strip()) < 1:
                raise serializers.ValidationError({
                    'location': 'Location cannot be empty'
                })
            return attrs
        except Exception as e:
            raise serializers.ValidationError({
                'detail': f'Error validating farm: {str(e)}'
            })

    def create(self, validated_data):
        """Create a new farm with motors"""
        try:
            motors_data = validated_data.pop('motors', [])
            farm = Farm.objects.create(**validated_data)

            for motor_data in motors_data:
                motor_data['farm'] = farm
                valves_data = motor_data.pop('valves', [])
                motor = Motor.objects.create(**motor_data)
                for valve_data in valves_data:
                    Valve.objects.create(motor=motor, **valve_data)

            return farm
        except DjangoValidationError as e:
            raise serializers.ValidationError({
                'detail': str(e)
            })
        except Exception as e:
            raise serializers.ValidationError({
                'detail': f'Error creating farm: {str(e)}'
            })

    def update(self, instance, validated_data):
        """Update existing farm"""
        try:
            motors_data = validated_data.pop('motors', None)

            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()

            if motors_data is not None:
                existing_motors = {motor.id: motor for motor in instance.motors.all()}
                for motor_data in motors_data:
                    motor_id = motor_data.get('id')
                    if motor_id and motor_id in existing_motors:
                        motor = existing_motors.pop(motor_id)
                        valves_data = motor_data.pop('valves', None)

                        for attr, value in motor_data.items():
                            setattr(motor, attr, value)
                        motor.save()

                        if valves_data is not None:
                            existing_valves = {valve.id: valve for valve in motor.valves.all()}
                            for valve_data in valves_data:
                                valve_id = valve_data.get('id')
                                if valve_id and valve_id in existing_valves:
                                    valve = existing_valves.pop(valve_id)
                                    for attr, value in valve_data.items():
                                        setattr(valve, attr, value)
                                    valve.save()
                                else:
                                    Valve.objects.create(motor=motor, **valve_data)
                            for valve in existing_valves.values():
                                valve.delete()
                    else:
                        motor_data['farm'] = instance
                        valves_data = motor_data.pop('valves', [])
                        motor = Motor.objects.create(**motor_data)
                        for valve_data in valves_data:
                            Valve.objects.create(motor=motor, **valve_data)
                for motor in existing_motors.values():
                    motor.delete()

            return instance
        except DjangoValidationError as e:
            raise serializers.ValidationError({
                'detail': str(e)
            })
        except Exception as e:
            raise serializers.ValidationError({
                'detail': f'Error updating farm: {str(e)}'
            })