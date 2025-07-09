from django.test import TestCase
from django.utils import timezone
from datetime import datetime
from decimal import Decimal
from events.models import Event
from events.serializers.cart_serializers import CartItemSerializer


class CartItemSerializerTestCase(TestCase):
    def setUp(self):
        
        #To awoid warning messages, related to time zone 
        event_date =  timezone.now() + timezone.timedelta(days=30)
        
        self.event = Event.objects.create(
            title="Test Event",
            description="Test Description",
            category="concert",
            date=event_date,
            location="Test Location",
            price=Decimal('100.00'),
            available_tickets=50
        )

    def test_valid_cart_item(self):
        data = {'event_id': self.event.id, 'quantity': 2}
        serializer = CartItemSerializer(data=data)
        
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['event_id'], self.event.id)
        self.assertEqual(serializer.validated_data['quantity'], 2)

    def test_nonexistent_event_id(self):
        data = {'event_id': 99999, 'quantity': 2}
        serializer = CartItemSerializer(data=data)
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('event_id', serializer.errors)
        self.assertEqual(serializer.errors['event_id'][0], "Event does not exist")

    def test_zero_quantity(self):
        data = {'event_id': self.event.id, 'quantity': 0}
        serializer = CartItemSerializer(data=data)
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('quantity', serializer.errors)

    def test_negative_quantity(self):
        data = {'event_id': self.event.id, 'quantity': -5}
        serializer = CartItemSerializer(data=data)
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('quantity', serializer.errors)

    def test_quantity_exceeds_available(self):
        data = {'event_id': self.event.id, 'quantity': 100}
        serializer = CartItemSerializer(data=data)
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)
        self.assertIn('Not enough tickets. Available: 50', str(serializer.errors['non_field_errors'][0]))

    def test_quantity_equals_available(self):
        data = {'event_id': self.event.id, 'quantity': 50}
        serializer = CartItemSerializer(data=data)
        
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['quantity'], 50)

    def test_missing_fields(self):
        data = {'quantity': 2}
        serializer = CartItemSerializer(data=data)
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('event_id', serializer.errors)

    def test_invalid_data_types(self):
        data = {'event_id': 'not_int', 'quantity': 'not_int'}
        serializer = CartItemSerializer(data=data)
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('event_id', serializer.errors)
        self.assertIn('quantity', serializer.errors)