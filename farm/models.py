
from django.db import models
from accounts.models import User
from django.core.exceptions import ValidationError

class Farm(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=200)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='farms')
    def __str__(self):
        return self.name


# models.py
class Motor(models.Model):
    MOTOR_TYPES = (
        ('single_phase', 'Single Phase'),
        ('double_phase', 'Double Phase'),
        ('triple_phase', 'Triple Phase'),
    )

    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='motors')
    motor_type = models.CharField(max_length=20, choices=MOTOR_TYPES)
    valve_count = models.PositiveIntegerField()
    UIN = models.PositiveIntegerField(null=True)
    is_active = models.BooleanField(default=False)  # New field

    def clean(self):
        max_valves = {
            'single_phase': 4,
            'double_phase': 6,
            'triple_phase': 10
        }
        if self.valve_count > max_valves[self.motor_type]:
            raise ValidationError(f"{self.motor_type} cannot have more than {max_valves[self.motor_type]} valves")

        # Check if motor is being turned on with no active valves
        if self.is_active and not self.valves.filter(is_active=True).exists():
            raise ValidationError("Motor cannot be turned on unless at least one valve is active.")

    def save(self, *args, **kwargs):
        self.clean()  # Ensure validation runs on save
        super().save(*args, **kwargs)
        current_valve_count = self.valves.count()
        if current_valve_count < self.valve_count:
            for i in range(current_valve_count, self.valve_count):
                Valve.objects.create(
                    motor=self,
                    name=f"Valve {i + 1}"
                )
        elif current_valve_count > self.valve_count:
            excess_valves = self.valves.order_by('id')[self.valve_count:]
            for valve in excess_valves:
                valve.delete()

    def __str__(self):
        return f"{self.motor_type} Motor - {self.farm.name}"

class Valve(models.Model):
    motor = models.ForeignKey(Motor, on_delete=models.CASCADE, related_name='valves')
    name = models.CharField(max_length=50)
    is_active = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} - {self.motor}"