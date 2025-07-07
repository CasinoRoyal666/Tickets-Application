from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from events.models import Event, EventImage
from events.serializers.events_serializers import EventSerializer, EventImageSerializer, EventListSerializer
from events.services.events_services import EventService


class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.prefetch_related('images').all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['title', 'description', 'location']
    ordering_fields = ['date', 'price', 'created_at']
    ordering = ['date']
    permission_classes = [AllowAny]

    def get_serializer_class(self):
        if self.action == 'list':
            return EventListSerializer
        return EventSerializer

    @action(detail=True, methods=['get'])
    def images(self, request, pk=None):
        images = EventService.get_event_images(pk)
        if images is None:
            return Response(
                {'error': 'Event not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = EventImageSerializer(images, many=True)
        return Response(serializer.data)


class EventImageViewSet(viewsets.ModelViewSet):
    queryset = EventImage.objects.select_related('event').all()
    serializer_class = EventImageSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['event']
    permission_classes = [AllowAny]