import pytest
from decimal import Decimal
from datetime import datetime, timezone
from events.models import Event, Order, OrderItem
from events.serializers import OrderSerializer, OrderCreateSerializer
from events.services import create_order


@pytest.fixture
def events():
    event1 = Event.objects.create(
        title="TestConc1",
        description="testdescr",
        category="concert",
        date=datetime(2025, 8, 15, 20, 0, tzinfo=timezone.utc),
        location="locationlocation",
        price=Decimal('2500.00'),
        available_tickets=100
    )
    
    event2 = Event.objects.create(
        title="TestConc2",
        description="blahblah",
        category="theater",
        date=datetime(2025, 9, 15, 19, 0, tzinfo=timezone.utc),
        location="location2",
        price=Decimal('1500.00'),
        available_tickets=50
    )
    return event1, event2

@pytest.fixture
def order_with_item(events):
    event = events[0]
    order = Order.objects.create(
        customer_email='test@example.com',
        customer_name='testusr',
        customer_phone='+375222222'
    )
    
    OrderItem.objects.create(
        order=order,
        event=event,
        quantity=2,
        unit_price=Decimal('2500.00')
    )
    return order

@pytest.mark.django_db
def test_create_order_with_items(events):
    event1, event2 = events
    data = {
        'customer_email': 'test@example.com',
        'customer_name': 'testusr',
        'customer_phone': '+3752266678',
        'items': [
            {
                'event': event1.id,
                'quantity': 2,
                'unit_price': '2500.00'
            },
            {
                'event': event2.id,
                'quantity': 1,
                'unit_price': '1500.00'
            }
        ]
    }
    
    serializer = OrderCreateSerializer(data=data)
    assert serializer.is_valid(), f"Errors: {serializer.errors}"
    
    order = create_order(serializer.validated_data)
    
    assert order.customer_email == 'test@example.com'
    assert order.customer_name == 'testusr'
    items = order.items.all()
    assert items.count() == 2
    expected_total = Decimal('2500.00') * 2 + Decimal('1500.00') * 1
    assert order.total_price == expected_total

@pytest.mark.django_db
def test_create_order_invalid_email():
    data = {
        'customer_email': 'invalid-email', 
        'customer_name': 'test',
        'customer_phone': '36465433454653',
        'items': []
    }
    
    serializer = OrderCreateSerializer(data=data)
    assert not serializer.is_valid()
    assert 'customer_email' in serializer.errors

@pytest.mark.django_db
def test_order_serialization_with_items(order_with_item):
    serializer = OrderSerializer(order_with_item)
    data = serializer.data
    
    assert data['customer_email'] == 'test@example.com'
    assert data['status'] == 'pending'
    assert data['status_display'] == 'Pending'
    
    assert len(data['items']) == 1
    item = data['items'][0]
    assert item['event_title'] == 'TestConc1'
    assert item['quantity'] == 2
    assert float(item['total_price']) == 5000.00