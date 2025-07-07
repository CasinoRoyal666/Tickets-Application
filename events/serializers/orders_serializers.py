from rest_framework import serializers
from events.models import Order, OrderItem, Event


class OrderItemSerializer(serializers.ModelSerializer):
    """Serializer for order items

    Attributes:
        id (int): The ID of the order item;
        event (Event): The related even;
        event_title (str): The title of the associated event (read-only);
        event_date (DateTimeField): The date of the associated event (read-only);
        quantity (int): The number of items ordered;
        unit_price (DecimalField): The price per unit (read-only);
        total_price (DecimalField): The total price for the item (read-only).
    """
    event_title = serializers.CharField(source='event.title', read_only=True)
    event_date = serializers.DateTimeField(source='event.date', read_only=True)

    class Meta:
        model = OrderItem
        fields = [
            'id', 'event', 'event_title', 'event_date',
            'quantity', 'unit_price', 'total_price'
        ]


class OrderSerializer(serializers.ModelSerializer):
    """Serializer for detailde order data

    Attributes:
        id (int): The ID of the order;
        customer_email (EmailField): The email of the customer;
        customer_name (str): The name of the customer;
        customer_phone (str): The phone number of the customer;
        status (str): The current status of the order;
        status_display (str): The human-readable status name (read-only);
        total_price (DecimalField): The total price of the order (read-only);
        items (List[OrderItemSerializer]): Nested serializer for order items (read-only);
        created_at (DateTimeField): The timestamp when the order was created;
        updated_at (DateTimeField): The timestamp when the order was last updated.
    """
    items = OrderItemSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'customer_email', 'customer_name', 'customer_phone', 'status',
            'status_display', 'total_price', 'items', 'created_at', 'updated_at'
        ]


class OrderItemCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating order items.

    The serializer validates data for creating OrderItem instances.

    Attributes:
        event (PrimaryKeyRelatedField): The related event (referenced by ID).
        quantity (int): The number of items to order. 

    """
    event = serializers.PrimaryKeyRelatedField(queryset=Event.objects.all())

    class Meta:
        model = OrderItem
        fields = ['event', 'quantity']

    def validate_quantity(self, value):
        """Validate that the quantity is positive.

        Args:
            value (int): The quantity to validate.

        Raises:
            serializers.ValidationError: If quntity is less or equal to 0.

        Returns:
            int: Validated quantity.
        """
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than 0")
        return value

    def validate(self, attrs):
        """Validate the combination of event and quantity.

        Ensures the event has enough available tickets for the requested quantity.

        Args:
            attrs (dict): Dictionary containing 'event' and 'quantity' keys.

        Raises:
            serializers.ValidationError: If there are not enough tickets available.

        Returns:
            dict: Validated attributes dictionary.
        """
        event = attrs.get('event')
        quantity = attrs.get('quantity')
        
        if event and quantity:
            if event.available_tickets < quantity:
                raise serializers.ValidationError(
                    f'Not enough tickets for event "{event.title}". '
                    f'Available: {event.available_tickets}, Requested: {quantity}'
                )
        return attrs


class OrderCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating orders.

    This serializer validates and prepares data for creating Order instances.

    Attributes:
        customer_email (EmailField): The email of the customer.
        customer_name (str): The name of the customer.
        customer_phone (str): The phone number of the customer.
        items (List[OrderItemCreateSerializer]): Nested serializer for order items.
    """
    items = OrderItemCreateSerializer(many=True)

    class Meta:
        model = Order
        fields = ['customer_email', 'customer_name', 'customer_phone', 'items']

    def validate_items(self, value):
        """Validate that the order contains at least one item.

        Args:
            value (list): List of order items.

        Raises:
            serializers.ValidationError: If the list of items is empty.

        Returns:
            list: The validated list of items.
        """
        if not value:
            raise serializers.ValidationError("Order must contain at least one item")
        return value