from events.models import Event, EventImage

class EventService:
    @staticmethod
    def get_event_images(event_id):
        try:
            event = Event.objects.get(id=event_id)
            return event.images.all()
        except Event.DoesNotExist:
            return None

    @staticmethod
    def check_ticket_availability(event, quantity):
        return event.available_tickets >= quantity

    @staticmethod
    def reduce_available_tickets(event, quantity):
        event.available_tickets -= quantity
        event.save()
        return event

    @staticmethod
    def increase_available_tickets(event, quantity):
        event.available_tickets += quantity
        event.save()
        return event