from rest_framework import serializers
from events.models import Event


class CartItemSerializer(serializers.Serializer):
    """Serializer for cart items.

    Attributes:
        event_id (Integer): The ID of event;
        quantity (Integer): Numbers of tickets for the event.
    """
    event_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)

    def validate_event_id(self, value):
        """Validate that event with given ID exists.

        Args:
            value (int):The ID of the event.

        Raises:
            serializers.ValidationError: If the event with the given ID does not exists.

        Returns:
            int: The validated event ID.
        """
        try:
            Event.objects.get(id=value)
        except Event.DoesNotExist:
            raise serializers.ValidationError("Event does not exist")
        return value

    def validate(self, attrs):
        """Validate event_id and quntity combination.

        Checks if the event exists and has enough available tickets for the requested quantity.

        Args:
            attrs (dict): Dictionary containing 'event_id' and 'quantity' keys.

        Raises:
            serializers.ValidationError: If there are not enough tickets available for the event.

        Returns:
            dict: Validated dictionary
        """
        event_id = attrs.get('event_id')
        quantity = attrs.get('quantity')
        
        try:
            event = Event.objects.get(id=event_id)
            if event.available_tickets < quantity:
                raise serializers.ValidationError(
                    f'Not enough tickets. Available: {event.available_tickets}'
                )
        except Event.DoesNotExist:
            pass  
            
        return attrs