from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter

from events.models import Order, OrderItem
from events.serializers.orders_serializers import OrderSerializer, OrderItemSerializer, OrderCreateSerializer
from events.services.orders_services import OrderService
from events.services.cart_services import CartService


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.prefetch_related('items__event').all()
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['status', 'customer_email']
    ordering_fields = ['created_at', 'total_price']
    ordering = ['-created_at']
    permission_classes = [AllowAny]

    def get_serializer_class(self):
        if self.action == 'create':
            return OrderCreateSerializer
        return OrderSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            order = OrderService.create_order_with_items(serializer.validated_data)
            request.session['cart'] = CartService.clear_cart()
            order_serializer = OrderSerializer(order)
            return Response(order_serializer.data, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
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


class OrderItemViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = OrderItem.objects.select_related('event', 'order').all()
    serializer_class = OrderItemSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['order', 'event']
    permission_classes = [AllowAny]