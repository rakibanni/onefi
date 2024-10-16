from django.db.models.signals import post_save
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Payment, Customer, Expense

@receiver(post_save, sender=Payment)
@receiver(post_save, sender=Customer)
@receiver(post_save, sender=Expense)
def update_dashboard(sender, instance, **kwargs):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "dashboard",
        {
            "type": "send_dashboard_update",
        },
    )
