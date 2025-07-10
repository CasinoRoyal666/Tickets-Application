import pytest
from django.utils import timezone
from decimal import Decimal
from events.models import Event
from events.serializers.cart_serializers import CartItemSerializer

@pytest.fixture
def event():

    #To awoid warning messages, related to time zone 
    event_date = timezone.now() + timezone.timedelta(days=30)

    return Event.objects.create(
        title="Test Event",
        description="Test Description",
        category="concert",
        date=event_date,
        location="Test Location",
        price=Decimal('100.00'),
        available_tickets=50
    )

@pytest.mark.django_db
def test_valid_cart_item(event):
    data = {'event_id': event.id, 'quantity': 2}
    serializer = CartItemSerializer(data=data)
    assert serializer.is_valid()
    assert serializer.validated_data['event_id'] == event.id
    assert serializer.validated_data['quantity'] == 2

@pytest.mark.django_db
@pytest.mark.parametrize("quantity, event_id_modifier, expected_error_key, expected_error_message", [
    (2, lambda e_id: 99999, 'event_id', "Event does not exist"),
    (0, lambda e_id: e_id, 'quantity', None),
    (-5, lambda e_id: e_id, 'quantity', None),
    (100, lambda e_id: e_id, 'non_field_errors', "Not enough tickets. Available: 50"),
])
def test_cart_item_invalid_data(event, quantity, event_id_modifier, expected_error_key, expected_error_message):
    data = {'event_id': event_id_modifier(event.id), 'quantity': quantity}
    serializer = CartItemSerializer(data=data)
    assert not serializer.is_valid()
    assert expected_error_key in serializer.errors
    if expected_error_message:
        assert expected_error_message in str(serializer.errors[expected_error_key][0])

@pytest.mark.django_db
def test_quantity_equals_available(event):
    data = {'event_id': event.id, 'quantity': 50}
    serializer = CartItemSerializer(data=data)
    assert serializer.is_valid()
    assert serializer.validated_data['quantity'] == 50

@pytest.mark.django_db
@pytest.mark.parametrize("input_data, expected_error_key", [
    ({'quantity': 2}, 'event_id'),
    ({'event_id': 'not_int', 'quantity': 'not_int'}, 'event_id'),
    ({'event_id':1, 'quantity': 'not_int'}, 'quantity'),
])
def test_missing_or_invalid_fields(event, input_data, expected_error_key):
    test_data = input_data.copy()
    if 'event_id' not in test_data and 'event_id' == expected_error_key:
        pass
    elif 'event_id' not in test_data:
        test_data['event_id'] = event.id
    
    serializer = CartItemSerializer(data=test_data)
    assert not serializer.is_valid()
    assert expected_error_key in serializer.errors
