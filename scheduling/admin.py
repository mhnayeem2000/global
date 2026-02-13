from django.contrib import admin

from scheduling.models import Appointment, EmployeeAvailability

# Register your models here.

admin.site.register(EmployeeAvailability)
admin.site.register(Appointment)