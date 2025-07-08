import pytest
import json
from decimal import Decimal
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from events.models import Event, Order, OrderItem


@pytest.mark.django_db
class TestOrderViewSet:
    
    @pytest.fixture
    def api_client(self):
        client = APIClient()
        client.session.save()
        return client
    
    @pytest.fixture
    def sample_events(self):
        events = []
        for i in range(3):
            event = Event.objects.create(
                title=f"Event {i+1}",
                description=f"Description {i+1}",
                category="concert",
                date="2025-07-08T20:00:00Z",
                location=f"Location {i+1}",
                price=Decimal(f'{100 + i*50}.00'),
                available_tickets=50
            )
            events.append(event)
        return events
    
    @pytest.fixture
    def sample_orders(self, sample_events):
        orders = []
        for i in range(2):
            order = Order.objects.create(
                customer_email=f'customer{i+1}@example.com',
                customer_name=f'Customer {i+1}',
                customer_phone=f'+123456789{i}',
                status='pending'
            )
            OrderItem.objects.create(
                order=order,
                event=sample_events[i],
                quantity=2
            )
            orders.append(order)
        return orders
    
    def test_list_orders(self, api_client, sample_orders):
        url = reverse('order-list')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 2 
        
        first_order = response.data['results'][0] 
        assert 'id' in first_order
        assert 'customer_email' in first_order
        assert 'items' in first_order
        assert 'total_price' in first_order
    
    def test_full_info_order(self, api_client, sample_orders):
        order = sample_orders[0]
        url = reverse('order-detail', kwargs={'pk': order.id})
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == order.id
        assert response.data['customer_email'] == order.customer_email
        assert len(response.data['items']) == 1
    
    def test_create_order_success(self, api_client, sample_events):
        cart_url = reverse('cart-list')
        api_client.post(cart_url, {
            'event_id': sample_events[0].id,
            'quantity': 2
        }, format='json')
        api_client.post(cart_url, {
            'event_id': sample_events[1].id,
            'quantity': 1
        }, format='json')
        
        url = reverse('order-list')
        data = {
            'customer_email': 'newtestcustomer@example.com',
            'customer_name': 'New Test Customer',
            'customer_phone': '+375267661875',
            'items': [
                {'event': sample_events[0].id, 'quantity': 2},
                {'event': sample_events[1].id, 'quantity': 1}
            ]
        }
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['customer_email'] == 'newtestcustomer@example.com'
        assert len(response.data['items']) == 2
        
        assert Order.objects.filter(customer_email='newtestcustomer@example.com').exists()
        
        cart_response = api_client.get(cart_url)
        assert cart_response.data['items'] == []
    
    def test_create_order_invalid_data(self, api_client):
        url = reverse('order-list')
        data = {
            'customer_email': 'invalid-email',  
            'customer_name': '',  
            'items': []  
        }
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_create_order_not_enough_tickets(self, api_client, sample_events):
        url = reverse('order-list')
        data = {
            'customer_email': 'customer@example.com',
            'customer_name': 'Customer',
            'customer_phone': '+1234567890',
            'items': [
                {'event': sample_events[0].id, 'quantity': 100}  
            ]
        }
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'items' in response.data
        assert len(response.data['items']) > 0
        assert 'non_field_errors' in response.data['items'][0]
        assert 'Not enough tickets for event' in response.data['items'][0]['non_field_errors'][0]

    def test_confirm_order_success(self, api_client, sample_orders):
        order = sample_orders[0]
        url = reverse('order-confirm', kwargs={'pk': order.id})
        response = api_client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'confirmed'
        
        order.refresh_from_db()
        assert order.status == 'confirmed'
    
    def test_confirm_order_wrong_status(self, api_client, sample_orders):
        order = sample_orders[0]
        order.status = 'completed'
        order.save()
        
        url = reverse('order-confirm', kwargs={'pk': order.id})
        response = api_client.post(url)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.data
    
    def test_cancel_order_success(self, api_client, sample_orders, sample_events):
        order = sample_orders[0]
        initial_tickets = sample_events[0].available_tickets
        
        url = reverse('order-cancel', kwargs={'pk': order.id})
        response = api_client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'cancelled'
        
        sample_events[0].refresh_from_db()
        assert sample_events[0].available_tickets == initial_tickets + 2
    
    def test_cancel_order_wrong_status(self, api_client, sample_orders):
        order = sample_orders[0]
        order.status = 'completed'
        order.save()
        
        url = reverse('order-cancel', kwargs={'pk': order.id})
        response = api_client.post(url)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.data
    
    def test_complete_order_success(self, api_client, sample_orders):
        order = sample_orders[0]
        order.status = 'confirmed'
        order.save()
        
        url = reverse('order-complete', kwargs={'pk': order.id})
        response = api_client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'completed'
        
        order.refresh_from_db()
        assert order.status == 'completed'
    
    def test_complete_order_wrong_status(self, api_client, sample_orders):
        order = sample_orders[0]
        assert order.status == 'pending'
        
        url = reverse('order-complete', kwargs={'pk': order.id})
        response = api_client.post(url)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.data
    
    def test_filter_orders_by_status(self, api_client, sample_orders):
        sample_orders[0].status = 'confirmed'
        sample_orders[0].save()
        
        url = reverse('order-list')
        response = api_client.get(url, {'status': 'confirmed'})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1 
        assert response.data['results'][0]['status'] == 'confirmed' 
    
    def test_filter_orders_by_customer_email(self, api_client, sample_orders):
        url = reverse('order-list')
        response = api_client.get(url, {'customer_email': 'customer1@example.com'})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1 
        assert response.data['results'][0]['customer_email'] == 'customer1@example.com'
    def test_order_not_found(self, api_client):
        url = reverse('order-detail', kwargs={'pk': 999})
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND