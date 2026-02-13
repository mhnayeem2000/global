from django.db import models
from django.conf import settings
from ecommerce.models import Order
from services.models import Plan

class Review(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='review')
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField()
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('plan', 'user')

    def __str__(self):
        return f"Review for {self.plan.name} by {self.user.email}"

class FAQ(models.Model):
    plan = models.ForeignKey(Plan, related_name='faqs', on_delete=models.CASCADE)
    question = models.CharField(max_length=255)
    answer = models.TextField()

    def __str__(self):
        return f"FAQ for {self.plan.name}: {self.question}"