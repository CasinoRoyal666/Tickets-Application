from decimal import Decimal
from events.models import Event
from events.serializers.events_serializers import EventListSerializer


class CartService:
    """Service class for managing shopping cart operations

    Provides static methods for handling cart contents, adding/removing items,
    clearing the cart, and validating cart items for a ticket purchasing system.
    Cart data is stored as a dictionary in the user's session.
    """
    @staticmethod
    def get_cart_contents(cart_data):
        """Retrieve and serialize the contents of the cart

        Attributes:
            cart_data (dict): Dictionary containing event IDs as keys and quantities as values

        Returns:
            dict: Dictionary with items and total_price (sum of all item totals)
        """
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
        """Add an item to the cart

        Attributes:
            cart_data (dict): Current cart dictionary
            event_id (int): ID of the event to add
            quantity (int): Quantity of tickets to add for the event

        Returns:
            dict: Updated cart dictionary
        """
        cart_data[str(event_id)] = quantity
        return cart_data

    @staticmethod
    def remove_from_cart(cart_data, event_id):
        """Remove an item from the cart

        Attributes:
            cart_data (dict): Current cart dictionary
            event_id (int): ID of the event to remove

        Returns:
            _type_: tuple: (updated cart dictionary, boolean if removal was successful)
        """
        event_id_str = str(event_id)
        if event_id_str in cart_data:
            del cart_data[event_id_str]
            return cart_data, True
        return cart_data, False

    @staticmethod
    def clear_cart():
        """"Clear all items from the cart

        Returns:
            dict: Empty dictionary representing an empty cart
        """
        return {}

    @staticmethod
    def validate_cart_item(event_id, quantity):
        """Validate a cart item before adding it to the cart

        Attributes:
            event_id (int): ID of the event to validate
            quantity (int): Quantity of tickets requested

        Returns:
            tuple: (Boolean indicating if valid, Error message if invalid or None if valid)

         Raises:
            Event.DoesNotExist: If the event with the given ID does not exist
        """
        try:
            event = Event.objects.get(id=event_id)
            if event.available_tickets < quantity:
                return False, f'Not enough tickets. Available: {event.available_tickets}'
            return True, None
        except Event.DoesNotExist:
            return False, 'Event does not exist'