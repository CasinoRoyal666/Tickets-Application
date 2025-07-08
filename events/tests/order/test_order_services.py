import pytest
from decimal import Decimal
from django.db import transaction
from django.test import TransactionTestCase
from rest_framework.serializers import ValidationError
from events.models import Event, Order, OrderItem
from events.services.orders_services import OrderService

@pytest.mark.django_db
class TestOrderService:
    
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
    def valid_order_data(self, sample_events):
        return {
            'customer_email': 'test@example.com',
            'customer_name': 'Test Customer',
            'customer_phone': '+1234567890',
            'items': [
                {'event': sample_events[0], 'quantity': 2},
                {'event': sample_events[1], 'quantity': 1},
            ]
        }
    
    @pytest.fixture
    def sample_order(self, valid_order_data):
        return OrderService.create_order_with_items(valid_order_data)
    
    def test_create_order_with_items_success(self, valid_order_data, sample_events):
        initial_tickets_0 = sample_events[0].available_tickets
        initial_tickets_1 = sample_events[1].available_tickets
        
        order = OrderService.create_order_with_items(valid_order_data)
        
        assert order is not None
        assert order.customer_email == 'test@example.com'
        assert order.customer_name == 'Test Customer'
        assert order.status == 'pending'
        
        assert order.items.count() == 2
        
        sample_events[0].refresh_from_db()
        sample_events[1].refresh_from_db()
        assert sample_events[0].available_tickets == initial_tickets_0 - 2
        assert sample_events[1].available_tickets == initial_tickets_1 - 1
    
    def test_create_order_not_enough_tickets(self, sample_events):
        order_data = {
            'customer_email': 'test@example.com',
            'customer_name': 'Test Customer',
            'customer_phone': '+1234567890',
            'items': [
                {'event': sample_events[0], 'quantity': 100}, 
            ]
        }
        
        with pytest.raises(ValidationError) as exc_info:
            OrderService.create_order_with_items(order_data)
        
        assert 'Not enough tickets' in str(exc_info.value)
        assert sample_events[0].title in str(exc_info.value)
        
        assert Order.objects.count() == 0
        
        sample_events[0].refresh_from_db()
        assert sample_events[0].available_tickets == 50
    
    def test_create_order_empty_items(self, sample_events):
        order_data = {
            'customer_email': 'test@example.com',
            'customer_name': 'Test Customer',
            'customer_phone': '+1234567890',
            'items': []
        }
        
        order = OrderService.create_order_with_items(order_data)
        
        assert order is not None
        assert order.items.count() == 0
    
    def test_confirm_order_success(self, sample_order):
        assert sample_order.status == 'pending'
        
        confirmed_order = OrderService.confirm_order(sample_order)
        
        assert confirmed_order.status == 'confirmed'
        
        sample_order.refresh_from_db()
        assert sample_order.status == 'confirmed'
    
    def test_confirm_order_wrong_status(self, sample_order):
        sample_order.status = 'completed'
        sample_order.save()
        
        with pytest.raises(ValueError) as exc_info:
            OrderService.confirm_order(sample_order)
        
        assert 'Order cannot be confirmed' in str(exc_info.value)
        
        sample_order.refresh_from_db()
        assert sample_order.status == 'completed'
    
    def test_cancel_order_pending_status(self, sample_order, sample_events):
        initial_tickets_0 = sample_events[0].available_tickets
        initial_tickets_1 = sample_events[1].available_tickets
        
        cancelled_order = OrderService.cancel_order(sample_order)
        
        assert cancelled_order.status == 'cancelled'
        
        sample_events[0].refresh_from_db()
        sample_events[1].refresh_from_db()
        assert sample_events[0].available_tickets == initial_tickets_0 + 2
        assert sample_events[1].available_tickets == initial_tickets_1 + 1
    
    def test_cancel_order_confirmed_status(self, sample_order, sample_events):
        sample_order.status = 'confirmed'
        sample_order.save()
        
        initial_tickets_0 = sample_events[0].available_tickets
        initial_tickets_1 = sample_events[1].available_tickets
        
        cancelled_order = OrderService.cancel_order(sample_order)
        
        assert cancelled_order.status == 'cancelled'
        
        sample_events[0].refresh_from_db()
        sample_events[1].refresh_from_db()
        assert sample_events[0].available_tickets == initial_tickets_0 + 2
        assert sample_events[1].available_tickets == initial_tickets_1 + 1
    
    def test_cancel_order_wrong_status(self, sample_order):
        sample_order.status = 'completed'
        sample_order.save()
        
        with pytest.raises(ValueError) as exc_info:
            OrderService.cancel_order(sample_order)
        
        assert 'Order cannot be cancelled' in str(exc_info.value)
        
        sample_order.refresh_from_db()
        assert sample_order.status == 'completed'
    
    def test_complete_order_success(self, sample_order):
        sample_order.status = 'confirmed'
        sample_order.save()
        
        completed_order = OrderService.complete_order(sample_order)
        
        assert completed_order.status == 'completed'
        
        sample_order.refresh_from_db()
        assert sample_order.status == 'completed'
    
    def test_complete_order_wrong_status(self, sample_order):
        assert sample_order.status == 'pending'
        
        with pytest.raises(ValueError) as exc_info:
            OrderService.complete_order(sample_order)
        
        assert 'Order must be confirmed to complete' in str(exc_info.value)
        
        sample_order.refresh_from_db()
        assert sample_order.status == 'pending'
    
    def test_order_transaction_rollback_on_error(self, sample_events):
        event = Event.objects.create(
            title="Limited Event",
            description="Limited Description",
            category="workshop",
            date="2025-12-31T20:00:00Z",
            location="Limited Location",
            price=Decimal('200.00'),
            available_tickets=1
        )
        
        order_data = {
            'customer_email': 'test@example.com',
            'customer_name': 'Test Customer',
            'customer_phone': '+1234567890',
            'items': [
                {'event': event, 'quantity': 2},  
            ]
        }
        
        initial_order_count = Order.objects.count()
        initial_order_item_count = OrderItem.objects.count()
        
        with pytest.raises(ValidationError):
            OrderService.create_order_with_items(order_data)
        
        assert Order.objects.count() == initial_order_count
        assert OrderItem.objects.count() == initial_order_item_count
        
        event.refresh_from_db()
        assert event.available_tickets == 1