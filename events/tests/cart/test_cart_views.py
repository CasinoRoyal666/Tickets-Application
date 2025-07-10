import pytest
import json
from decimal import Decimal
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from events.models import Event

@pytest.mark.django_db
class TestCartViewSet:
    
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
                date="2025-12-31T20:00:00Z",
                location=f"Location {i+1}",
                price=Decimal(f'{100 + i*50}.00'),
                available_tickets=50
            )
            events.append(event)
        return events

    @pytest.fixture
    def cart_with_items(self, api_client, sample_events):
        url = reverse('cart-list')
        api_client.post(url, {
            'event_id': sample_events[0].id,
            'quantity': 2
        }, format='json')
        api_client.post(url, {
            'event_id': sample_events[1].id,
            'quantity': 1
        }, format='json')
        return api_client

    def test_get_empty_cart(self, api_client):
        url = reverse('cart-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['items'] == []
        assert response.data['total_price'] == 0

    def test_add_item_to_cart(self, api_client, sample_events):
        url = reverse('cart-list')
        data = {
            'event_id': sample_events[0].id,
            'quantity': 3
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['items']) == 1
        assert response.data['items'][0]['quantity'] == 3
        assert response.data['total_price'] == Decimal('300.00')

    @pytest.mark.parametrize("payload_data, expected_error_message", [
        ({'event_id': 999, 'quantity': 1}, 'Event does not exist'),
        ({'event_id': 'use_event_0', 'quantity': 0}, 'Ensure this value is greater than or equal to 1'),
        ({'event_id': 'use_event_0', 'quantity': 100}, 'Not enough tickets'),
    ])
    def test_add_item_invalid_data(self, api_client, sample_events, payload_data, expected_error_message):
        if payload_data.get('event_id') == 'use_event_0':
            payload_data['event_id'] = sample_events[0].id

        url = reverse('cart-list')
        response = api_client.post(url, payload_data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert expected_error_message in str(response.data)

    def test_replace_item_in_cart(self, api_client, sample_events):
        url = reverse('cart-list')
        event_id = sample_events[0].id
        api_client.post(url, {'event_id': event_id, 'quantity': 2}, format='json')
        response = api_client.post(url, {'event_id': event_id, 'quantity': 5}, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['items']) == 1
        assert response.data['items'][0]['quantity'] == 5

    def test_get_cart_with_items(self, cart_with_items, sample_events):
        url = reverse('cart-list')
        response = cart_with_items.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['items']) == 2
        assert response.data['total_price'] == Decimal('350.00')

    def test_remove_item_from_cart(self, cart_with_items, sample_events):
        event_id = sample_events[0].id
        url = reverse('cart-detail', kwargs={'pk': event_id})
        response = cart_with_items.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        cart_url = reverse('cart-list')
        cart_response = cart_with_items.get(cart_url)
        assert len(cart_response.data['items']) == 1

    def test_remove_non_existing_item(self, cart_with_items):
        url = reverse('cart-detail', kwargs={'pk': 999})
        response = cart_with_items.delete(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert 'Item not found in cart' in response.data['error']

    def test_clear_cart(self, cart_with_items):
        url = reverse('cart-clear')
        response = cart_with_items.post(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['message'] == 'Cart cleared'
        cart_url = reverse('cart-list')
        cart_response = cart_with_items.get(cart_url)
        assert cart_response.data['items'] == []
        assert cart_response.data['total_price'] == 0

    def test_cart_persistence_across_requests(self, api_client, sample_events):
        add_url = reverse('cart-list')
        api_client.post(add_url, {
            'event_id': sample_events[0].id,
            'quantity': 2
        }, format='json')
        get_url = reverse('cart-list')
        response = api_client.get(get_url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['items']) == 1
        assert response.data['items'][0]['quantity'] == 2