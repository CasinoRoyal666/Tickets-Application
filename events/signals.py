from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags
from django.db import transaction
from events.models import Order
import logging

logger = logging.getLogger(__name__)

def send_order_created_email(order):
    order.refresh_from_db()

    subject = f'Order #{order.id} registered successfully'

    context = {
        'order': order,
        'customer_name': order.customer_name,
        'total_price': order.total_price,
        'items': order.items.select_related('event').all(),
    }

    #deploy data from html template 
    html_message = render_to_string('emails/order_created.html', context)

    #delete all html tags
    plain_message = strip_tags(html_message)

    send_mail(
        subject=subject,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[order.customer_email],
        html_message=html_message,
        fail_silently=False,
    )

    logger.info(f"Create order {order.id} message sended to {order.customer_email}")

def send_order_status_changed_email(order):
    status_subjects={
        'pending': f'Order #{order.id} pending',
        'confirmed': f'Order #{order.id} confirmed',
        'cancelled': f'Order #{order.id} cancelled',
        'completed': f'Order #{order.id} completed',
    }

    subject = status_subjects.get(order.status, f'Order status #{order.id} changed')

    context = {
        'order': order,
        'customer_name': order.customer_name,
        'status': order.get_status_display(),
        'status_code': order.status,
        'total_price': order.total_price,
        'items': order.items.select_related('event').all(),
    }

    html_message = render_to_string('emails/order_status_changed.html', context)
    plain_message = strip_tags(html_message)

    send_mail(
        subject=subject,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[order.customer_email],
        html_message=html_message,
        fail_silently=False,
    )

    logger.info(f"Send email about order status {order.id} changed to {order.customer_email}")


@receiver(post_save, sender=Order)
def send_order_notification(sender, instance, created, **kwargs):
    def send_email():
        try:
            if created:
                send_order_created_email(instance)
            else:
                send_order_status_changed_email(instance)
        except Exception as e:
            logger.error(f"Error while sending email for order {instance.id}: {str(e)}")
    
    if created:
        transaction.on_commit(send_email)
    else:
        send_email()