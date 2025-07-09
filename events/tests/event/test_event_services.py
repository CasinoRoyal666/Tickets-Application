from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from events.models import Event, EventImage
from events.services.events_services import EventService
from decimal import Decimal
from django.utils import timezone

#To awoid warning messages, related to time zone 
date = timezone.now() + timezone.timedelta(days=30)

class EventServiceTestCase(TestCase):
    def setUp(self):
        self.event = Event.objects.create(
            title="TestEvent",
            description="Desc of test event",
            category="music",
            date=date,
            location="Minsk",
            price=Decimal('180.00'),
            available_tickets=100
        )
        
        image_file = SimpleUploadedFile(
            "test_image.jpg",
            b"fake image content",
            content_type="image/jpeg"
        )
        self.event_image = EventImage.objects.create(
            event=self.event,
            image=image_file
        )

    def test_get_event_images_existing_event(self):
        images = EventService.get_event_images(self.event.id)
        self.assertIsNotNone(images)
        self.assertEqual(images.count(), 1)
        self.assertEqual(images.first(), self.event_image)

    def test_get_event_images_nonexistent_event(self):
        images = EventService.get_event_images(99999)
        self.assertIsNone(images)

    def test_check_ticket_availability_sufficient_tickets(self):
        result = EventService.check_ticket_availability(self.event, 50)
        self.assertTrue(result)

    def test_check_ticket_availability_insufficient_tickets(self):
        result = EventService.check_ticket_availability(self.event, 150)
        self.assertFalse(result)

    def test_check_ticket_availability_exact_amount(self):
        result = EventService.check_ticket_availability(self.event, 100)
        self.assertTrue(result)

    def test_reduce_available_tickets(self):
        initial_tickets = self.event.available_tickets
        quantity_to_reduce = 20
        
        updated_event = EventService.reduce_available_tickets(self.event, quantity_to_reduce)
        
        self.assertEqual(updated_event.available_tickets, initial_tickets - quantity_to_reduce)
        self.event.refresh_from_db()
        self.assertEqual(self.event.available_tickets, initial_tickets - quantity_to_reduce)

    def test_increase_available_tickets(self):
        initial_tickets = self.event.available_tickets
        quantity_to_add = 30
        
        updated_event = EventService.increase_available_tickets(self.event, quantity_to_add)
        
        self.assertEqual(updated_event.available_tickets, initial_tickets + quantity_to_add)
        self.event.refresh_from_db()
        self.assertEqual(self.event.available_tickets, initial_tickets + quantity_to_add)

    def test_reduce_tickets_to_zero(self):
        updated_event = EventService.reduce_available_tickets(self.event, 100)
        self.assertEqual(updated_event.available_tickets, 0)
