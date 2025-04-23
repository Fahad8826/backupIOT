

from rest_framework import serializers
from .models import Farm, Motor, Valve
from accounts.models import User
from django.core.exceptions import ValidationError as DjangoValidationError


class ValveSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)  # Make ID optional but pass it when present

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

    def update(self, instance, validated_data):
        """Update existing valve"""
        try:
            # Update valve attributes
            for attr, value in validated_data.items():
                if attr != 'id':  # Skip the ID field
                    setattr(instance, attr, value)
            instance.save()
            return instance
        except DjangoValidationError as e:
            raise serializers.ValidationError({
                'detail': str(e)
            })
        except Exception as e:
            raise serializers.ValidationError({
                'detail': f'Error updating valve: {str(e)}'
            })


class MotorSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)  # Make ID optional but pass it when present
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
                valve_id = valve_data.pop('id', None)  # Remove id if present for creation
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
        try:
            valves_data = validated_data.pop('valves', None)

            # Update motor attributes
            for attr, value in validated_data.items():
                if attr != 'id':  # Skip the ID field
                    setattr(instance, attr, value)
            instance.save()

            # Handle valves update if provided
            if valves_data is not None:
                # Create a dictionary of existing valves by ID
                existing_valves = {valve.id: valve for valve in instance.valves.all()}
                # Also track by valve_id for better matching
                existing_valves_by_valve_id = {valve.valve_id: valve for valve in instance.valves.all() if valve.valve_id}

                processed_valve_ids = []

                # Debug: Print existing valves
                print(f"DEBUG: Motor {instance.id} existing valves: {existing_valves}")

                # Process each valve in the update data
                for valve_data in valves_data:
                    valve_id = valve_data.get('id')
                    valve_external_id = valve_data.get('valve_id')

                    # Debug: Print valve data being processed
                    print(f"DEBUG: Processing valve data: {valve_data}")

                    # First try to find by ID exactly as provided
                    valve = None
                    if valve_id and valve_id in existing_valves:
                        valve = existing_valves[valve_id]
                        print(f"DEBUG: Found valve by ID {valve_id}")

                    # Then try to find by external ID if not found by primary ID
                    elif valve_external_id and valve_external_id in existing_valves_by_valve_id:
                        valve = existing_valves_by_valve_id[valve_external_id]
                        print(f"DEBUG: Found valve by external ID {valve_external_id}, actual DB ID: {valve.id}")

                    # If valve found by any method, update it
                    if valve:
                        processed_valve_ids.append(valve.id)
                        # Update the existing valve - exclude 'id' to avoid updating primary key
                        valve_update_data = {k: v for k, v in valve_data.items() if k != 'id'}
                        print(f"DEBUG: Updating valve {valve.id} with data: {valve_update_data}")
                        for attr, value in valve_update_data.items():
                            setattr(valve, attr, value)
                        valve.save()
                    else:
                        # Create new valve if not found
                        new_valve_data = valve_data.copy()
                        if 'id' in new_valve_data:
                            del new_valve_data['id']  # Remove id if present for creation
                        print(f"DEBUG: Creating new valve with data: {new_valve_data}")
                        new_valve = Valve.objects.create(motor=instance, **new_valve_data)
                        processed_valve_ids.append(new_valve.id)

                # Handle deletion of valves not in the update
                for valve_id, valve in existing_valves.items():
                    if valve_id not in processed_valve_ids:
                        print(f"DEBUG: Deleting valve {valve_id} as it's not in update data")
                        valve.delete()

            # Ensure motor state is consistent with valves
            if instance.is_active and not instance.valves.filter(is_active=True).exists():
                if instance.valves.exists():
                    first_valve = instance.valves.first()
                    first_valve.is_active = True
                    first_valve.save()
                else:
                    instance.is_active = False
                    instance.save(update_fields=['is_active'])

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
                motor_data = motor_data.copy()
                if 'id' in motor_data:
                    del motor_data['id']  # Remove id if present for creation

                motor_data['farm'] = farm
                valves_data = motor_data.pop('valves', [])
                motor = Motor.objects.create(**motor_data)

                for valve_data in valves_data:
                    valve_data = valve_data.copy()
                    if 'id' in valve_data:
                        del valve_data['id']  # Remove id if present for creation
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
        try:
            motors_data = validated_data.pop('motors', None)

            # Update farm attributes
            for attr, value in validated_data.items():
                if attr != 'id':  # Skip the ID field
                    setattr(instance, attr, value)
            instance.save()

            # Handle motors update if provided
            if motors_data is not None:
                # Create a dictionary of existing motors by ID
                existing_motors = {motor.id: motor for motor in instance.motors.all()}
                processed_motor_ids = []

                # Process each motor in the update data
                for motor_data in motors_data:
                    motor_id = motor_data.get('id')
                    valves_data = motor_data.pop('valves', None)

                    if motor_id and motor_id in existing_motors:
                        # Update existing motor
                        motor = existing_motors[motor_id]
                        processed_motor_ids.append(motor_id)

                        # Remove ID from data before updating
                        motor_update_data = {k: v for k, v in motor_data.items() if k != 'id'}

                        # Apply updates
                        for attr, value in motor_update_data.items():
                            setattr(motor, attr, value)
                        motor.save()

                        # Handle nested valves update
                        if valves_data is not None:
                            # Debug: Print existing valves
                            existing_valves_debug = list(motor.valves.all())
                            print(f"DEBUG: Existing valves for motor {motor.id}: {existing_valves_debug}")

                            # Get all existing valves for this motor
                            existing_valves = {valve.id: valve for valve in motor.valves.all()}
                            # Also track by valve_id for better matching
                            existing_valves_by_valve_id = {valve.valve_id: valve for valve in motor.valves.all() if valve.valve_id}

                            processed_valve_ids = []

                            for valve_data in valves_data:
                                valve_id = valve_data.get('id')
                                valve_external_id = valve_data.get('valve_id')

                                # Debug: Print valve data being processed
                                print(f"DEBUG: Processing valve data: {valve_data}")

                                # First check: Try to find by ID exactly as provided
                                valve = None
                                if valve_id and valve_id in existing_valves:
                                    valve = existing_valves[valve_id]
                                    print(f"DEBUG: Found valve by ID {valve_id}")

                                # Second check: If not found by ID and has external ID, try to match by external ID
                                elif valve_external_id and valve_external_id in existing_valves_by_valve_id:
                                    valve = existing_valves_by_valve_id[valve_external_id]
                                    print(f"DEBUG: Found valve by external ID {valve_external_id}, actual DB ID: {valve.id}")
                                    # Don't update the valve_data here - we want to keep using the provided ID

                                # If valve found by any method, update it
                                if valve:
                                    processed_valve_ids.append(valve.id)
                                    # Update the existing valve - exclude 'id' to avoid updating primary key
                                    valve_update_data = {k: v for k, v in valve_data.items() if k != 'id'}
                                    print(f"DEBUG: Updating valve {valve.id} with data: {valve_update_data}")
                                    for attr, value in valve_update_data.items():
                                        setattr(valve, attr, value)
                                    valve.save()
                                else:
                                    # Create new valve if not found
                                    new_valve_data = valve_data.copy()
                                    if 'id' in new_valve_data:
                                        del new_valve_data['id']  # Remove id if present for creation
                                    print(f"DEBUG: Creating new valve with data: {new_valve_data}")
                                    new_valve = Valve.objects.create(motor=motor, **new_valve_data)
                                    processed_valve_ids.append(new_valve.id)

                            # Handle deletion of valves not in the update
                            for valve_id, valve in existing_valves.items():
                                if valve_id not in processed_valve_ids:
                                    print(f"DEBUG: Deleting valve {valve_id} as it's not in update data")
                                    valve.delete()
                    else:
                        # Create new motor without ID from data
                        new_motor_data = motor_data.copy()
                        if 'id' in new_motor_data:
                            del new_motor_data['id']  # Remove id if present for creation

                        new_motor = Motor.objects.create(farm=instance, **new_motor_data)
                        processed_motor_ids.append(new_motor.id)

                        # Create valves for the new motor if provided
                        if valves_data:
                            for valve_data in valves_data:
                                valve_data = valve_data.copy()
                                if 'id' in valve_data:
                                    del valve_data['id']  # Remove id if present for creation
                                Valve.objects.create(motor=new_motor, **valve_data)

                # Handle deletion of motors not in the update
                for motor_id, motor in existing_motors.items():
                    if motor_id not in processed_motor_ids:
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


class MotorValveSerializer(serializers.ModelSerializer):
    """Serializer for Motor with nested Valves"""
    valves = serializers.SerializerMethodField()
    is_active = serializers.SerializerMethodField()
    farm_name = serializers.CharField(source='farm.name', read_only=True)

    class Meta:
        model = Motor
        fields = ['id', 'UIN', 'is_active', 'farm_name', 'motor_type', 'valve_count', 'valves']

    def get_valves(self, obj):
        return [{
            'id': valve.id,
            'valve_id': valve.valve_id,
            'name': valve.name,
            'is_active': 1 if valve.is_active else 0
        } for valve in obj.valves.all()]

    def get_is_active(self, obj):
        return 1 if obj.is_active else 0