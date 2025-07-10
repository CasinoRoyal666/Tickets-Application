from events.models import Event, EventImage

class EventService:
    """Service class for managing event-related operations
    
    Provides static methods for retrieving event images and managing ticket availability
    for events in a ticket purchasing system.
    """
    @staticmethod
    def get_event_images(event_id):
        """Getting all images related with event

        Attributes:
            event_id (int): ID of the event

        Returns:
            QuerySet: Collection of EventImage objects if the event exists, None otherwise
        """
        try:
            event = Event.objects.get(id=event_id)
            return event.images.all()
        except Event.DoesNotExist:
            return None

    @staticmethod
    def check_ticket_availability(event, quantity):
        """Check if enough tickets are available for an event

        Attributes:
            event (Event): Event object
            quantity (int): Number of tickets 

        Returns:
            bool: True if enough tickets are available, False otherwise
        """
        return event.available_tickets >= quantity

    @staticmethod
    def reduce_available_tickets(event, quantity):
        """Reduce the number of available tickets for an event

        Attributes:
            event (Object): Event object to update
            quantity (int): Number of tickets

        Returns:
            Event: Updated Event object
        """
        event.available_tickets -= quantity
        event.save()
        return event

    @staticmethod
    def increase_available_tickets(event, quantity):
        """Increase the number of available tickets for an event

        Attributes:
            event (Event): Event object to update
            quantity (int): Number of tickets

        Returns:
            Event: Updated Event object
        """
        event.available_tickets += quantity
        event.save()
        return event