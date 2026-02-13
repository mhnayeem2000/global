
from django.db import models
from django.conf import settings
from ecommerce.models import Order

def order_update_path(instance, filename):
    return f'order_updates/{instance.order.id}/{filename}'

class WorkUpdate(models.Model):

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='work_updates')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    title = models.CharField(max_length=255)
    description = models.TextField()
    attachment = models.FileField(upload_to=order_update_path, blank=True, null=True)
    link = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        author_email = self.author.email if self.author else "a Deleted User"
        return f"Update for Order #{self.order.id} by {author_email}"

class ChatMessage(models.Model):

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='chat_messages')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        author_email = self.author.email if self.author else "a Deleted User"
        return f"Message by {author_email} on Order #{self.order.id}"
