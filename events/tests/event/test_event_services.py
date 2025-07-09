import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from events.models import Event, EventImage
from events.services.events_services import EventService
from decimal import Decimal
from django.utils import timezone

@pytest.fixture
def event():
    date = timezone.now() + timezone.timedelta(days=30)
    return Event.objects.create(
        title="TestEvent",
        description="Desc of test event",
        category="music",
        date=date,
        location="Minsk",
        price=Decimal('180.00'),
        available_tickets=100
    )

@pytest.fixture
def event_with_image(event):
    image_file = SimpleUploadedFile(
        "test_image.jpg",
        b"fake image content",
        content_type="image/jpeg"
    )
    EventImage.objects.create(event=event, image=image_file)
    return event

@pytest.mark.django_db
class TestEventService:
    
    def test_get_event_images_existing_event(self, event_with_image):
        images = EventService.get_event_images(event_with_image.id)
        assert images is not None
        assert images.count() == 1
        assert images.first() == event_with_image.images.first()

    def test_get_event_images_nonexistent_event(self):
        images = EventService.get_event_images(99999)
        assert images is None

    @pytest.mark.parametrize("quantity, expected_result", [
        (50, True),
        (150, False),
        (100, True),
    ])
    def test_check_ticket_availability(self, event, quantity, expected_result):
        result = EventService.check_ticket_availability(event, quantity)
        assert result is expected_result

    def test_reduce_available_tickets(self, event):
        initial_tickets = event.available_tickets
        quantity_to_reduce = 20
        
        updated_event = EventService.reduce_available_tickets(event, quantity_to_reduce)
        
        assert updated_event.available_tickets == initial_tickets - quantity_to_reduce
        event.refresh_from_db()
        assert event.available_tickets == initial_tickets - quantity_to_reduce

    def test_increase_available_tickets(self, event):
        initial_tickets = event.available_tickets
        quantity_to_add = 30
        
        updated_event = EventService.increase_available_tickets(event, quantity_to_add)
        
        assert updated_event.available_tickets == initial_tickets + quantity_to_add
        event.refresh_from_db()
        assert event.available_tickets == initial_tickets + quantity_to_add

    def test_reduce_tickets_to_zero(self, event):
        updated_event = EventService.reduce_available_tickets(event, 100)
        assert updated_event.available_tickets == 0