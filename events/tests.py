from django.test import TestCase
from datetime import datetime, timezone
from decimal import Decimal
from .models import Event, Order, OrderItem
from .serializers import EventSerializer, OrderSerializer, OrderCreateSerializer


class EventSerializerTest(TestCase):    
    def setUp(self):
        self.event = Event.objects.create(
            title="TestConc",
            description="Test Concert Test",
            category="concert",
            date=datetime(2025, 8, 15, 20, 0, tzinfo=timezone.utc),
            location="location",
            price=Decimal('2500.00'),
            available_tickets=100
        )
    
    def test_event_serialization(self):
        serializer = EventSerializer(self.event)
        data = serializer.data
        
        self.assertEqual(data['title'], 'TestConc')
        self.assertEqual(data['category'], 'concert')
        self.assertEqual(data['category_display'], 'Concert')
        self.assertEqual(float(data['price']), 2500.00)
        self.assertEqual(data['available_tickets'], 100)
    
    def test_event_deserialization_valid(self):
        data = {
            'title': 'TestConc',
            'description': 'nono',
            'category': 'sports',
            'date': '2025-09-20T19:00:00Z',
            'location': 'newloc',
            'price': '3000.00',
            'available_tickets': 200
        }
        
        serializer = EventSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        event = serializer.save()
        self.assertEqual(event.title, 'TestConc')
        self.assertEqual(event.category, 'sports')
    
    def test_event_deserialization_invalid(self):
        data = {
            'title': '',  
            'price': '-100',  
        }
        
        serializer = EventSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('title', serializer.errors)


class OrderCreateSerializerTest(TestCase):
    
    def setUp(self):
        self.event1 = Event.objects.create(
            title="TestConc1",
            description="testdescr",
            category="concert",
            date=datetime(2025, 8, 15, 20, 0, tzinfo=timezone.utc),
            location="locationlocation",
            price=Decimal('2500.00'),
            available_tickets=100
        )
        
        self.event2 = Event.objects.create(
            title="TestConc2",
            description="blahblah",
            category="theater",
            date=datetime(2025, 9, 15, 19, 0, tzinfo=timezone.utc),
            location="location2",
            price=Decimal('1500.00'),
            available_tickets=50
        )
    
    def test_create_order_with_items(self):
        data = {
            'customer_email': 'test@example.com',
            'customer_name': 'testusr',
            'customer_phone': '+3752266678',
            'items': [
                {
                    'event': self.event1.id,
                    'quantity': 2,
                    'unit_price': '2500.00'
                },
                {
                    'event': self.event2.id,
                    'quantity': 1,
                    'unit_price': '1500.00'
                }
            ]
        }
        
        serializer = OrderCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid(), f"Errors: {serializer.errors}")
        
        order = serializer.save()
        
        self.assertEqual(order.customer_email, 'test@example.com')
        self.assertEqual(order.customer_name, 'testusr')
        items = order.items.all()
        self.assertEqual(items.count(), 2)
        expected_total = Decimal('2500.00') * 2 + Decimal('1500.00') * 1
        self.assertEqual(order.total_price, expected_total)
    
    def test_create_order_invalid_email(self):
        data = {
            'customer_email': 'invalid-email', 
            'customer_name': 'test',
            'customer_phone': '36465433454653',
            'items': []
        }
        
        serializer = OrderCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('customer_email', serializer.errors)


class OrderSerializerTest(TestCase):
    
    def setUp(self):
        self.event = Event.objects.create(
            title="TestConc",
            description="desc",
            category="concert",
            date=datetime(2025, 8, 15, 20, 0, tzinfo=timezone.utc),
            location="loc",
            price=Decimal('2500.00'),
            available_tickets=100
        )
        
        self.order = Order.objects.create(
            customer_email='test@example.com',
            customer_name='testusr',
            customer_phone='+375222222'
        )
        
        self.order_item = OrderItem.objects.create(
            order=self.order,
            event=self.event,
            quantity=2,
            unit_price=Decimal('2500.00')
        )
    
    def test_order_serialization_with_items(self):
        serializer = OrderSerializer(self.order)
        data = serializer.data
        
        self.assertEqual(data['customer_email'], 'test@example.com')
        self.assertEqual(data['status'], 'pending')
        self.assertEqual(data['status_display'], 'Pending')
        
        self.assertEqual(len(data['items']), 1)
        item = data['items'][0]
        self.assertEqual(item['event_title'], 'TestConc')
        self.assertEqual(item['quantity'], 2)
        self.assertEqual(float(item['total_price']), 5000.00)
