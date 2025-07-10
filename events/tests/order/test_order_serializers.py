import pytest
from decimal import Decimal
from datetime import datetime, timezone
from events.models import Event, Order, OrderItem
from events.serializers.orders_serializers import OrderSerializer, OrderCreateSerializer
from events.services.orders_services import OrderService
from events.services.events_services import EventService


@pytest.fixture
def events(db):
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
def order_with_item(db, events):
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

@pytest.mark.django_db
@pytest.mark.parametrize("initial_status,expected_status", [
    ('pending', 'confirmed'),
])
def test_confirm_order_success(order_with_item, initial_status, expected_status):
    order = order_with_item
    order.status = initial_status
    order.save()

    confirmed_order = OrderService.confirm_order(order)
    assert confirmed_order.status == expected_status
    order.refresh_from_db() 
    assert order.status == expected_status

@pytest.mark.django_db
@pytest.mark.parametrize("invalid_status,expected_error", [
    ('completed', 'Order cannot be confirmed'),
    ('confirmed', 'Order cannot be confirmed'),
    ('cancelled', 'Order cannot be confirmed'),
])
def test_confirm_order_invalid_status(order_with_item, invalid_status, expected_error):
    order = order_with_item
    order.status = invalid_status
    order.save()

    with pytest.raises(ValueError, match=expected_error):
        OrderService.confirm_order(order)
    order.refresh_from_db()
    assert order.status == invalid_status

@pytest.mark.django_db
@pytest.mark.parametrize("initial_status,expected_status", [
    ('pending', 'cancelled'),
    ('confirmed', 'cancelled'),
])
def test_cancel_order_success(order_with_item, initial_status, expected_status):
    order = order_with_item
    order.status = initial_status
    order.save()
    
    event = order.items.first().event 
    initial_tickets = event.available_tickets
    order_quantity = order.items.first().quantity

    cancelled_order = OrderService.cancel_order(order)
    assert cancelled_order.status == expected_status
    order.refresh_from_db()
    assert order.status == expected_status

    event.refresh_from_db()
    assert event.available_tickets == initial_tickets + order_quantity

@pytest.mark.django_db
@pytest.mark.parametrize("invalid_status,expected_error", [
    ('completed', 'Order cannot be cancelled because of status'),
    ('cancelled', 'Order cannot be cancelled because of status'),
])
def test_cancel_order_invalid_status(order_with_item, invalid_status, expected_error):
    order = order_with_item
    order.status = invalid_status
    order.save()

    with pytest.raises(ValueError, match=expected_error):
        OrderService.cancel_order(order)
    order.refresh_from_db()
    assert order.status == invalid_status

@pytest.mark.django_db
@pytest.mark.parametrize("initial_status,expected_status", [
    ('confirmed', 'completed'),
])
def test_complete_order_success(order_with_item, initial_status, expected_status):
    order = order_with_item
    order.status = initial_status
    order.save()

    completed_order = OrderService.complete_order(order)
    assert completed_order.status == expected_status
    order.refresh_from_db()
    assert order.status == expected_status

@pytest.mark.django_db
@pytest.mark.parametrize("invalid_status,expected_error", [
    ('pending', 'Order must be confirmed to complete'),
    ('cancelled', 'Order must be confirmed to complete'),
    ('completed', 'Order must be confirmed to complete'),
])
def test_complete_order_invalid_status(order_with_item, invalid_status, expected_error):
    order = order_with_item
    order.status = invalid_status
    order.save()

    with pytest.raises(ValueError, match=expected_error):
        OrderService.complete_order(order)
    order.refresh_from_db()
    assert order.status == invalid_status