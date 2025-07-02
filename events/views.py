from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend

from .models import Event, EventImage, Order, OrderItem
from .serializers import ( EventSerializer, EventImageSerializer, EventListSerializer, OrderSerializer, OrderItemSerializer, OrderCreateSerializer)
from .services import create_order

class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.prefetch_related('images').all() #prefetch_related for get related data images (event have many images)
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['title', 'description', 'location']
    ordering_fields = ['date', 'price', 'created_at']
    ordering = ['date']
    permission_classes = [AllowAny]

    #if list requested return EventListRes else usual EventSer
    def get_serializer_class(self):
        if self.action == 'list':
            return EventListSerializer
        return EventSerializer
    
    #for the images get wiz mandatory field id (bc of detail=True)
    @action(detail=True,methods=['get'])
    def images(self, request, pk=None):
        event = self.get_object()
        images = event.images.all()
        serializer = EventImageSerializer(images, many=True)
        return Response(serializer.data)
    
class EventImageViewSet(viewsets.ModelViewSet):
    queryset = EventImage.objects.select_related('event').all() #like prefetch, but select_rltd betta for simple connections (many imgs = 1 evnt)
    serializer_class = EventImageSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['event']
    permission_classes = [AllowAny]

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.prefetch_related('items__event').all() #chain load i->e
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['status', 'customer_email']
    ordering_fields = ['created_at', 'total_price']
    ordering = ['-created_at']
    permission_classes = [AllowAny]

        #for create and read ser
    def get_serializer_class(self):
        if self.action == 'create':
             return OrderCreateSerializer
        return OrderSerializer
        
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        items_data = serializer.validated_data.get('items', [])

        for item_data in items_data:
            event = item_data['event']
            quantity = item_data['quantity']

            if event.available_tickets < quantity:
                return Response(
                    {
                        'error' : f'Not enough tickets for event "{event.title}".'
                                f"Available : {event.available_tickets}, Requested : {quantity}" 
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            order = create_order(serializer.validated_data)

            #reducing tickets after creating order
            for item_data in items_data:
                event = item_data['event']
                quantity = item_data['quantity']
                event.available_tickets -= quantity
                event.save()
                
            order_serializer = OrderSerializer(order)
            return Response(order_serializer.data, status=status.HTTP_201_CREATED)
            
    @action(detail=True,methods=['post'])
    def confirm(self, request, pk=None):
        order = self.get_object()
        if order.status != 'pending':
            return Response(
                {
                    'error' : 'Order cant be confirmed!'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        order.status = 'confirmed'
        order.save()

        serializer = self.get_serializer(order)
        return Response(serializer.data)
            
    @action(detail=True,methods=['post'])
    def cancel(self, request, pk=None):
        order = self.get_object()
        if order.status not in ['pending', 'confirmed']:
            return Response(
                {
                    'error' : 'Order can not be cancelled because of status!'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
                
        #else return tickets
        with transaction.atomic():
            for item in order.items.all():
                event = item.event
                event.available_tickets += item.quantity
                event.save()
            order.status = 'cancelled'
            order.save()
        serializer = self.get_serializer(order)
        return Response(serializer.data)
            
    @action(detail=True,methods=['post'])
    def complete(self, request, pk=None):
        order = self.get_object()
        if order.status != 'confirmed':
            return Response(
                {
                    'error' : 'Order must be confirmed for to complete'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        order.status = 'completed'
        order.save()
        serializer = self.get_serializer(order)
        return Response(serializer.data)
        
#viewset for reading orderitems
class OrderItemViewSet(viewsets.ReadOnlyModelViewSet):
        queryset = OrderItem.objects.select_related('event', 'order').all()
        serializer_class = OrderItemSerializer
        filter_backends = [DjangoFilterBackend]
        filterset_fields = ['order', 'event']
        permission_classes = [AllowAny]

class CartViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]

    def list(self, request):
        cart = request.session.get('cart', {})
        #for empty
        if not cart:
            return Response({'items': [], 'total_price': 0})
        
        event_ids = cart.keys()
        events = Event.objects.filter(id__in=event_ids) # for all events_ids
        
        total_price = 0
        cart_items = []
        #return list of all items in cart
        for event in events:
            quantity = cart[str(event.id)]
            item_total = event.price * quantity
            total_price += item_total
            cart_items.append({
                'event' : EventListSerializer(event).data,
                'quantity' : quantity,
                'item_total_price' : item_total 
            })
        return Response({'items' : cart_items, 'total_price' : total_price})
    
    #cart add
    def create(self,request):
        event_id = request.data.get('event_id')
        quantity = request.data.get('quantity')

        if not all([event_id, quantity]):
            return Response({'error' : 'event_id and quantity fields are required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            quantity = int(quantity)
            if quantity <= 0:
                return Response({'error' : 'Quantity must be > 0'}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError:
            return Response({'error' : 'Quantity must be a digit'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            event = Event.objects.get(id=event_id)
            if event.available_tickets < quantity:
                return Response({'error' : 'Not enough tickets. Available : {event.available_tickets}'}, status=status.HTTP_400_BAD_REQUEST)
        except Event.DoesNotExist:
            return Response({'error' : 'Event does not exist'}, status=status.HTTP_400_BAD_REQUEST)
        
        cart = request.session.get('cart', {})
        cart[str(event_id)] = quantity
        request.session['cart'] = cart

        return self.list(request)
    
def destroy(self,request, pk=None):
    cart = request.session.get('cart', {})
    event_id_remove = str(pk)

    if event_id_remove in cart:
        del cart[event_id_remove]
        request.session['cart'] = cart
        return Response(status=status.HTTP_204_NO_CONTENT)
    else:
        return Response({'error' : 'Item not found in cart'}, status=status.HTTP_400_BAD_REQUEST)
    
@action(detail=False,methods=['post'])
def clear(self, request):
    request.session['cart'] = {}
    return Response({'message' : 'Cart cleared'}, status=status.HTTP_200_OK)
