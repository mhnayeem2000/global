from django.db import models
from django.conf import settings
from services.models import Plan

class QuoteRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        CONTACTED = 'CONTACTED', 'Contacted'
        CONVERTED = 'CONVERTED', 'Converted'
        REJECTED = 'REJECTED', 'Rejected'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    plan = models.ForeignKey(Plan, on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=255)
    email = models.EmailField()
    company_name = models.CharField(max_length=255, blank=True, null=True)
    custom_requirements = models.TextField(blank=True, null=True, help_text="Customer's custom requirements")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Quote Request from {self.email} for {self.plan.name if self.plan else 'Custom Plan'}"
    