from django.db import models

class Service(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    is_product = models.BooleanField(default=False, help_text="this service be purchased directly like a product")

    def __str__(self):
        return self.name

class Plan(models.Model):
    class BillingCycle(models.TextChoices):
        MONTHLY = 'MONTHLY', 'Monthly'
        QUARTERLY = 'QUARTERLY', 'Quarterly'
        YEARLY = 'YEARLY', 'Yearly'
        ONE_TIME = 'ONE_TIME', 'One Time'

    service = models.ForeignKey(Service, related_name='plans', on_delete=models.CASCADE)
    name = models.CharField(max_length=100) 
    slug = models.SlugField(unique=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    billing_cycle = models.CharField(max_length=20, choices=BillingCycle.choices, default=BillingCycle.MONTHLY)

    def __str__(self):
        return f"{self.service.name} - {self.name} Plan"

class Feature(models.Model):
    plan = models.ForeignKey(Plan, related_name='features', on_delete=models.CASCADE)
    description = models.CharField(max_length=255)

    def __str__(self):
        return self.description