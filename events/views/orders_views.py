from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter

from events.models import Order, OrderItem
from events.serializers.orders_serializers import OrderSerializer, OrderCreateSerializer
from events.services.orders_services import OrderService
from events.services.cart_services import CartService


class OrderViewSet(viewsets.ModelViewSet):
    """"ViewSet for managing orders objects

    Provides full CRUD operations for orders

    Supported filters:
        Ordering by fields: created_at, total_price
        Filtering by fields: status,  customer_email
        Default ordering (-created_at).

    Permissions:
        AllowAny
    """
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['status', 'customer_email']
    ordering_fields = ['created_at', 'total_price']
    ordering = ['-created_at']
    permission_classes = [AllowAny]

    def get_queryset(self):
        if self.request.session and self.request.session.session_key:
            return Order.objects.filter(session_key=self.request.session.session_key).prefetch_related('items__event')
        return Order.objects.none()
    
    def get_serializer_class(self):
        """Function that returns serializer based on action

        Returns:
            OrderCreateSerializer: For action  "create"
            OrderSerializer: Otherwise, for getting orders
        """
        if self.action == 'create':
            return OrderCreateSerializer
        return OrderSerializer

    def create(self, request, *args, **kwargs):
        """Create a new order with associated items and clear the cart

        Attributes:
            request : HTTP request
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments

        Returns:
            Response: Serialized order data with status 201 on success
        
        Raises:
            error: error message with status 400 on failure.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            if not request.session.session_key:
                request.session.create()
            session_key = request.session.session_key

            order = OrderService.create_order_with_items(serializer.validated_data, session_key)
            
            if 'cart' in request.session:
                del request.session['cart']
                request.session.modified = True
            
            order_serializer = OrderSerializer(order)
            return Response(order_serializer.data, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """Confirm an existing order

        Attributes:
            request: HTTP request
            pk: Primary Key of the order to confirm

        Returns:
            Response: Serialized order data on success

        Raises:
            error: Error message with status 400
        """
        order = self.get_object()
        
        try:
            OrderService.confirm_order(order)
            serializer = self.get_serializer(order)
            return Response(serializer.data)
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel an existing order

        Attributes:
            request: HTTP request
            pk: Primary Key of the order to cancel

        Returns:
            Responce: Serialized order data on success
        
        Raises:
            error: Error message with status 400
        """
        order = self.get_object()
        
        try:
            OrderService.cancel_order(order)
            serializer = self.get_serializer(order)
            return Response(serializer.data)
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Complete the existing order

        Attributes:
            request: HTTP request
            pk: Primary Key of the order to complete

        Returns:
            Responce: Serialized order data on success
        
        Raises:
            error: Error message with status 400
        """
        order = self.get_object()
        
        try:
            OrderService.complete_order(order)
            serializer = self.get_serializer(order)
            return Response(serializer.data)
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


