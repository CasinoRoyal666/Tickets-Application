import pytest
from decimal import Decimal
from datetime import datetime, timezone
from events.models import Event
from events.serializers.events_serializers import EventSerializer

@pytest.fixture
def event():
    return Event.objects.create(
        title="TestConc",
        description="Test Concert Test",
        category="concert",
        date=datetime(2025, 8, 15, 20, 0, tzinfo=timezone.utc),
        location="location",
        price=Decimal('2500.00'),
        available_tickets=100
    )

@pytest.mark.django_db
def test_event_serialization(event):
    serializer = EventSerializer(event)
    data = serializer.data
    
    assert data['title'] == 'TestConc'
    assert data['category'] == 'concert'
    assert data['category_display'] == 'Concert'
    assert float(data['price']) == 2500.00
    assert data['available_tickets'] == 100

@pytest.mark.django_db
def test_event_deserialization_valid():
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
    assert serializer.is_valid()
    
    event = serializer.save()
    assert event.title == 'TestConc'
    assert event.category == 'sports'

@pytest.mark.django_db
def test_event_deserialization_invalid():
    data = {
        'title': '',  
        'price': '-100',  
    }
    
    serializer = EventSerializer(data=data)
    assert not serializer.is_valid()
    assert 'title' in serializer.errors