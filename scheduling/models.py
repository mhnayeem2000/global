from django.db import models
from django.conf import settings
from datetime import time

class EmployeeAvailability(models.Model):

    class Weekday(models.IntegerChoices):
        MONDAY = 0, 'Monday'
        TUESDAY = 1, 'Tuesday'
        WEDNESDAY = 2, 'Wednesday'
        THURSDAY = 3, 'Thursday'
        FRIDAY = 4, 'Friday'
        SATURDAY = 5, 'Saturday'
        SUNDAY = 6, 'Sunday'

    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='availabilities',
        limit_choices_to={'role__in': ['EMPLOYEE', 'OWNER']}
    )
    weekday = models.IntegerField(choices=Weekday.choices)
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        unique_together = ('employee', 'weekday') 

    def __str__(self):
        return f"{self.employee.email}'s availability on {self.get_weekday_display()}"


class Appointment(models.Model):

    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        CONFIRMED = 'CONFIRMED', 'Confirmed'
        COMPLETED = 'COMPLETED', 'Completed'
        CANCELLED = 'CANCELLED', 'Cancelled'

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='customer_appointments',
        limit_choices_to={'role': 'CUSTOMER'}
    )
    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='employee_appointments',
        limit_choices_to={'role__in': ['EMPLOYEE', 'OWNER']}
    )
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    notes = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    meeting_link = models.URLField(blank=True, null=True)

    def __str__(self):
        return f"Appointment with {self.employee.email} and {self.customer.email} on {self.start_time.strftime('%Y-%m-%d %H:%M')}"
