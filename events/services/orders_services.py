from django.db import transaction
from events.models import Order, OrderItem
from .events_services import EventService


class OrderService:
    @staticmethod
    def create_order_with_items(validated_data):
        items_data = validated_data.pop('items', [])
        
        with transaction.atomic():
            order = Order.objects.create(**validated_data)
            
            for item_data in items_data:
                OrderItem.objects.create(
                    order=order,
                    event=item_data['event'],
                    quantity=item_data['quantity']
                )
                
                EventService.reduce_available_tickets(
                    item_data['event'], 
                    item_data['quantity']
                )
        
        return order

    @staticmethod
    def confirm_order(order):
        if order.status != 'pending':
            raise ValueError('Order cannot be confirmed')
        
        order.status = 'confirmed'
        order.save()
        return order

    @staticmethod
    def cancel_order(order):
        if order.status not in ['pending', 'confirmed']:
            raise ValueError('Order cannot be cancelled because of status')
        
        with transaction.atomic():
            for item in order.items.all():
                EventService.increase_available_tickets(item.event, item.quantity)
            
            order.status = 'cancelled'
            order.save()
        
        return order

    @staticmethod
    def complete_order(order):
        if order.status != 'confirmed':
            raise ValueError('Order must be confirmed to complete')
        
        order.status = 'completed'
        order.save()
        return order