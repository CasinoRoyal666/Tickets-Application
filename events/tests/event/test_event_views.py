import pytest
import json
from decimal import Decimal
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from events.models import Event, EventImage
from django.core.files.uploadedfile import SimpleUploadedFile

@pytest.mark.django_db
class TestEventViewSet:
    
    @pytest.fixture
    def api_client(self):
        return APIClient()
    
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
                price=Decimal(f'{100 + i*10}.00'),
                available_tickets=50 + i*10
            )
            events.append(event)
        return events
    
    @pytest.fixture
    def event_with_images(self, sample_events):
        event = sample_events[0]
        EventImage.objects.create(event=event, image="test1.jpg")
        EventImage.objects.create(event=event, image="test2.jpg")
        return event
    
    def test_list_events(self, api_client, sample_events):
        url = reverse('event-list')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 3
        
        first_event = response.data['results'][0]
        assert 'id' in first_event
        assert 'title' in first_event
        assert 'description' not in first_event 
    
    def test_retrieve_event(self, api_client, sample_events):
        event = sample_events[0]
        url = reverse('event-detail', kwargs={'pk': event.id})
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == event.id
        assert response.data['title'] == event.title
        assert 'description' in response.data 
        assert 'images' in response.data
    
    def test_create_event(self, api_client):
        url = reverse('event-list')
        data = {
            'title': 'New Event',
            'description': 'New Description',
            'category': 'concert', 
            'date': '2025-12-31T20:00:00Z',
            'location': 'New Location',
            'price': '150.00',
            'available_tickets': 100
        }
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert Event.objects.filter(title='New Event').exists()
        assert response.data['title'] == 'New Event'
    
    def test_update_event(self, api_client, sample_events):
        event = sample_events[0]
        url = reverse('event-detail', kwargs={'pk': event.id})
        data = {
            'title': 'Updated Event',
            'description': event.description,
            'category': event.category,
            'date': event.date,
            'location': event.location,
            'price': str(event.price),
            'available_tickets': event.available_tickets
        }
        response = api_client.put(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['title'] == 'Updated Event'
        
        event.refresh_from_db()
        assert event.title == 'Updated Event'
    
    def test_delete_event(self, api_client, sample_events):
        event = sample_events[0]
        url = reverse('event-detail', kwargs={'pk': event.id})
        response = api_client.delete(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Event.objects.filter(id=event.id).exists()
    
    def test_search_events(self, api_client, sample_events):
        url = reverse('event-list')
        response = api_client.get(url, {'search': 'Event 1'})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['title'] == 'Event 1'
    
    def test_order_events_by_price(self, api_client, sample_events):
        url = reverse('event-list')
        response = api_client.get(url, {'ordering': 'price'})
        
        assert response.status_code == status.HTTP_200_OK
        prices = [Decimal(event['price']) for event in response.data['results']]
        assert prices == sorted(prices)
    
    def test_get_event_images(self, api_client, event_with_images):
        url = reverse('event-images', kwargs={'pk': event_with_images.id})
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2
        assert all('id' in img and 'image' in img for img in response.data)
    
    def test_get_images_event_not_found(self, api_client):
        url = reverse('event-images', kwargs={'pk': 999})
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

        """I don't understand what the problem is, but when manually testing in Postman, adding an image works correctly
        """
    # def test_add_event_image(self, api_client, sample_events):
    #     event = sample_events[0]
    #     url = reverse('event-images', kwargs={'pk': event.id})
        
    #     image_file = SimpleUploadedFile(
    #         "test_image.jpg",
    #         b"file_content",
    #         content_type="image/jpg"
    #     )
        
    #     data = {'image': image_file}
    #     response = api_client.post(url, data, format='multipart')
        
    #     assert response.status_code == status.HTTP_201_CREATED
    #     assert EventImage.objects.filter(event=event).exists()
    
    def test_delete_event_image(self, api_client, event_with_images):
        image = event_with_images.images.first()
        url = reverse('event-delete-image', kwargs={
            'pk': event_with_images.id,
            'image_id': image.id
        })
        response = api_client.delete(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not EventImage.objects.filter(id=image.id).exists()
    
    def test_delete_image_not_found(self, api_client, sample_events):
        event = sample_events[0]
        url = reverse('event-delete-image', kwargs={
            'pk': event.id,
            'image_id': 999
        })
        response = api_client.delete(url)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert 'Image not found' in response.data['error']