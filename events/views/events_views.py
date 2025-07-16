from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from ..filters import EventFilter
from events.models import Event, EventImage, EventCategory
from events.serializers.events_serializers import EventImageSerializer, EventListSerializer, EventSerializer
from events.services.events_services import EventService


class EventViewSet(viewsets.ModelViewSet):
    """Viewset for managing events

    Provides full CRUD functionality for events and event-images
   
    Supported filters:
        Search by fields: title, description, location
        Ordering by fields: date, price, created_at
        Filtering via django-filter
    
    Permissions:
        AllowAny
    """
    queryset = Event.objects.prefetch_related('images').all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['title', 'description', 'location']
    ordering_fields = ['date', 'price', 'created_at']
    ordering = ['date']
    permission_classes = [AllowAny]
    filterset_class = EventFilter

    def get_serializer_class(self):
        """Function that returns serializer based on action

        Returns:
            EventListSerializer: For list action (light info version)
            EventSerializer: For all other actions (full info version)
        """
        if self.action == 'list':
            return EventListSerializer
        return EventSerializer
  
    @action(detail=True, methods=['get', 'post'])
    def images(self, request, pk=None):
        """
        Get all images for event or add new image.
        
        GET: Returns list of event images
        POST: Creates new image for the event
        
        Attributes:
            request: HTTP request
            pk (int): Event ID
            
        Returns:
            Response: List of images (GET) or created image (POST)
            
        Raises:
            404: If event not found
            400: If image data is invalid (POST)
        """
        event = self.get_object()
        
        if request.method == 'GET':
            images = event.images.all()
            serializer = EventImageSerializer(images, many=True)
            return Response(serializer.data)

        elif request.method == 'POST':
            serializer = EventImageSerializer(data=request.data, context={'event': event})
            if serializer.is_valid():
                serializer.save(event=event)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # @action(detail=True, methods=['put', 'patch'], url_path='images/(?P<image_id>[^/.]+)')
    # def update_image(self, request, pk=None, image_id=None):
    #     event = self.get_object()
        
    #     try:
    #         image = EventImage.objects.get(id=image_id, event=event)
    #     except EventImage.DoesNotExist:
    #         return Response(
    #             {'error': 'Image not found'}, 
    #             status=status.HTTP_404_NOT_FOUND
    #         )
        
    #     partial = request.method == 'PATCH'
    #     serializer = EventImageSerializer(image, data=request.data, partial=partial)
        
    #     if serializer.is_valid():
    #         serializer.save()
    #         return Response(serializer.data)
        
    #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['delete'], url_path='images/(?P<image_id>[^/.]+)')
    def delete_image(self, request, pk=None, image_id=None):
        """
        Delete specific image from the event.
        
        Attributes:
            request: HTTP request
            pk (int): Event ID
            image_id (int): Image ID
            
        Returns:
            Response: Empty response with 204 status
            
        Raises:
            404: If event or image not found
        """
        event = self.get_object()
        
        try:
            image = EventImage.objects.get(id=image_id, event=event)
        except EventImage.DoesNotExist:
            return Response(
                {'error': 'Image not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        image.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    #get list of categories for transfer
    @action(detail=False, methods=['get'])
    def categories(self, request):
        categories_data = [{'value': value, 'label': label} for value, label in EventCategory.choices]
        return Response(categories_data)