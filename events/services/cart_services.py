from decimal import Decimal
from events.models import Event
from events.serializers.events_serializers import EventListSerializer


class CartService:
    @staticmethod
    def get_cart_contents(cart_data):
        if not cart_data:
            return {'items': [], 'total_price': 0}
        
        event_ids = cart_data.keys()
        events = Event.objects.filter(id__in=event_ids)
        
        total_price = Decimal('0.00')
        cart_items = []
        
        for event in events:
            quantity = cart_data[str(event.id)]
            item_total = event.price * quantity
            total_price += item_total
            
            cart_items.append({
                'event': EventListSerializer(event).data,
                'quantity': quantity,
                'item_total_price': item_total
            })
        
        return {
            'items': cart_items,
            'total_price': total_price
        }

    @staticmethod
    def add_to_cart(cart_data, event_id, quantity):
        cart_data[str(event_id)] = quantity
        return cart_data

    @staticmethod
    def remove_from_cart(cart_data, event_id):
        event_id_str = str(event_id)
        if event_id_str in cart_data:
            del cart_data[event_id_str]
            return cart_data, True
        return cart_data, False

    @staticmethod
    def clear_cart():
        return {}

    @staticmethod
    def validate_cart_item(event_id, quantity):
        try:
            event = Event.objects.get(id=event_id)
            if event.available_tickets < quantity:
                return False, f'Not enough tickets. Available: {event.available_tickets}'
            return True, None
        except Event.DoesNotExist:
            return False, 'Event does not exist'