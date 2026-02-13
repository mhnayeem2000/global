from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Milestone

@receiver(post_save, sender=Milestone)
def update_order_status_on_milestone_change(sender, instance, **kwargs):

    if instance.order:
        instance.order.update_status_based_on_milestones()