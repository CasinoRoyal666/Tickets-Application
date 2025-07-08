import pytest
from decimal import Decimal
from events.models import Event
from events.services.cart_services import CartService


@pytest.mark.django_db
class TestCartService:
    
    @pytest.fixture
    def sample_events(self):
        events = []
        for i in range(3):
            event = Event.objects.create(
                title=f"Event {i+1}",
                description=f"Description {i+1}",
                category="concert",
                date="2025-12-31T20:00:00Z",
                location=f"Location {i+1}",
                price=Decimal(f'{100 + i*50}.00'),
                available_tickets=50
            )
            events.append(event)
        return events
    
    @pytest.fixture
    def sample_cart_data(self, sample_events):
        return {
            str(sample_events[0].id): 2,
            str(sample_events[1].id): 1,
        }
    
    def test_get_cart_contents_empty(self):
        result = CartService.get_cart_contents({})
        
        assert result['items'] == []
        assert result['total_price'] == 0
     
    def test_get_cart_contents_with_items(self, sample_events, sample_cart_data):
        result = CartService.get_cart_contents(sample_cart_data)
        
        assert len(result['items']) == 2
        assert result['total_price'] == Decimal('350.00')  # 2*100 + 1*150
        
        first_item = result['items'][0]
        assert 'event' in first_item
        assert 'quantity' in first_item
        assert 'item_total_price' in first_item
    
    def test_add_to_cart_new_item(self, sample_events):
        cart_data = {}
        event_id = sample_events[0].id
        quantity = 3
        
        updated_cart = CartService.add_to_cart(cart_data, event_id, quantity)
        
        assert str(event_id) in updated_cart
        assert updated_cart[str(event_id)] == quantity
    
    def test_add_to_cart_replace_existing(self, sample_events, sample_cart_data):
        event_id = sample_events[0].id
        new_quantity = 5
        
        updated_cart = CartService.add_to_cart(sample_cart_data, event_id, new_quantity)
        
        assert updated_cart[str(event_id)] == new_quantity
    
    def test_remove_from_cart_existing_item(self, sample_events, sample_cart_data):
        event_id = sample_events[0].id
        
        updated_cart, removed = CartService.remove_from_cart(sample_cart_data, event_id)
        
        assert removed is True
        assert str(event_id) not in updated_cart
        assert len(updated_cart) == 1
    
    def test_remove_from_cart_non_existing_item(self, sample_events, sample_cart_data):
        non_existing_event_id = 999
        
        updated_cart, removed = CartService.remove_from_cart(sample_cart_data, non_existing_event_id)
        
        assert removed is False
        assert len(updated_cart) == 2  
    
    def test_clear_cart(self):
        result = CartService.clear_cart()
        
        assert result == {}
    
    def test_validate_cart_item_valid(self, sample_events):
        event = sample_events[0]
        
        is_valid, error = CartService.validate_cart_item(event.id, 10)
        
        assert is_valid is True
        assert error is None
    
    def test_validate_cart_item_not_enough_tickets(self, sample_events):
        event = sample_events[0]
        
        is_valid, error = CartService.validate_cart_item(event.id, 100)
        
        assert is_valid is False
        assert 'Not enough tickets' in error
        assert str(event.available_tickets) in error
    
    def test_validate_cart_item_event_not_exists(self):
        non_existing_event_id = 999
        
        is_valid, error = CartService.validate_cart_item(non_existing_event_id, 1)
        
        assert is_valid is False
        assert error == 'Event does not exist'
    
    def test_cart_total_calculation_precision(self, sample_events):
        event = Event.objects.create(
            title="Precision Test Event",
            description="Test Description",
            category="workshop",
            date="2025-12-31T20:00:00Z",
            location="Test Location",
            price=Decimal('99.99'),
            available_tickets=10
        )
        
        cart_data = {str(event.id): 3}
        result = CartService.get_cart_contents(cart_data)
        
        expected_total = Decimal('299.97')  # 99.99 * 3
        assert result['total_price'] == expected_total