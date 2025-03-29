# # farm/models.py
# from django.db import models
# from accounts.models import User
# from django.core.exceptions import ValidationError
#
#
# class Farm(models.Model):
#     name = models.CharField(max_length=100)
#     location = models.CharField(max_length=200)
#     owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='farms')
#     def __str__(self):
#         return self.name
#
#
# class Motor(models.Model):
#     MOTOR_TYPES = (
#         ('single_phase', 'Single Phase'),
#         ('double_phase', 'Double Phase'),
#         ('triple_phase', 'Triple Phase'),
#     )
#
#     farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='motors')
#     motor_type = models.CharField(max_length=20, choices=MOTOR_TYPES)
#     valve_count = models.PositiveIntegerField()
#
#     def clean(self):
#         max_valves = {
#             'single_phase': 4,
#             'double_phase': 6,
#             'triple_phase': 10
#         }
#         if self.valve_count > max_valves[self.motor_type]:
#             raise ValidationError(f"{self.motor_type} cannot have more than {max_valves[self.motor_type]} valves")
#
#     def save(self, *args, **kwargs):
#         super().save(*args, **kwargs)
#         current_valve_count = self.valves.count()
#         if current_valve_count < self.valve_count:
#             for i in range(self.valve_count - current_valve_count):
#                 Valve.objects.create(
#                     motor=self,
#                     name=f"Valve {current_valve_count + i + 1}"
#                 )
#
#     def __str__(self):
#         return f"{self.motor_type} Motor - {self.farm.name}"
#
#
# class Valve(models.Model):
#     motor = models.ForeignKey(Motor, on_delete=models.CASCADE, related_name='valves')
#     name = models.CharField(max_length=50)
#     is_active = models.BooleanField(default=False)
#
#     def __str__(self):
#         return f"{self.name} - {self.motor}"


from django.db import models
from accounts.models import User
from django.core.exceptions import ValidationError

class Farm(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=200)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='farms')
    def __str__(self):
        return self.name

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

    def clean(self):
        max_valves = {
            'single_phase': 4,
            'double_phase': 6,
            'triple_phase': 10
        }
        if self.valve_count > max_valves[self.motor_type]:
            raise ValidationError(f"{self.motor_type} cannot have more than {max_valves[self.motor_type]} valves")

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        current_valve_count = self.valves.count()
        if current_valve_count < self.valve_count:
            for i in range(current_valve_count, self.valve_count):
                Valve.objects.create(
                    motor=self,
                    name=f"Valve {i + 1}"
                )
        elif current_valve_count > self.valve_count:
            # Optional: Remove excess valves if valve_count decreases
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