# from django.db import models
# from django.core.validators import MinValueValidator, MaxValueValidator
#
# from accounts.authentication import User
#
#
# class Motor(models.Model):
#     TYPE_CHOICES = [
#         ('REQ', 'Required'),
#         ('OPT', 'Optional'),
#     ]
#
#     STATUS_CHOICES = [
#         ('1', 'Working'),

#         ('0', 'Idle'),
#     ]
#
#     # Colors for status
#     STATUS_COLORS = {
#         '1': 'green',  # Working status color
#         '0': 'gray',  # Idle status color
#     }
#     owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='motors',null=True)
#     name = models.CharField(max_length=100)
#     UIN = models.CharField(max_length=15, unique=True)
#     TYPE = models.CharField(max_length=3, choices=TYPE_CHOICES, default='REQ')
#     VCOUNT = models.PositiveIntegerField(validators=[MinValueValidator(0), MaxValueValidator(10)])
#     STATUS = models.CharField(max_length=1, choices=STATUS_CHOICES, default='1')
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
#
#     def __str__(self):
#         return f"{self.name} - {self.UIN}"
#
#     @property
#     def status_color(self):
#         """Return the color associated with the current status"""
#         return self.STATUS_COLORS.get(self.STATUS, 'gray')
#
#     class Meta:
#         ordering = ['-created_at']
#
#
# class Valve(models.Model):
#     VALVE_STATUS_CHOICES = [
#         ('0', 'Off'),
#         ('1', 'On'),
#     ]
#
#     motor = models.ForeignKey(Motor, related_name='valves', on_delete=models.CASCADE)
#     valve_number = models.PositiveIntegerField()
#     value = models.CharField(max_length=10, choices=VALVE_STATUS_CHOICES, default="0")
#     last_operated_at = models.DateTimeField(auto_now=True)
#
#     class Meta:
#         unique_together = ('motor', 'valve_number')
#         ordering = ['valve_number']
#
#     def __str__(self):
#         return f"Valve {self.valve_number} of Motor {self.motor.name}"
#
#     def turn_on(self):
#         """Turn the valve on"""
#         self.value = "1"
#         self.save()
#         return True
#
#     def turn_off(self):
#         """Turn the valve off"""
#         self.value = "0"
#         self.save()
#         return True