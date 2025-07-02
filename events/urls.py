from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .import views

router = DefaultRouter()
router.register(r'events', views.EventViewSet, basename='event')
router.register(r'event-images', views.EventImageViewSet, basename='eventimages')
router.register(r'orders', views.OrderViewSet, basename='order')
router.register(r'order-items', views.OrderItemViewSet, basename='orderitem')

urlpatterns = [
    path('', include(router.urls)),
]