from django.contrib import admin
from .models import Event, EventImage, Order, OrderItem
from django.utils.html import format_html

class EventImageInline(admin.StackedInline):
    model = EventImage
    extra = 1
    readonly_fields = ('image_preview',)

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="100" height="100" style="object-fit: cover;" />',
                obj.image.url
            )
        return "No Image"
    image_preview.short_description = "Preview"

class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'date', 'price', 'available_tickets', 'tickets_status')
    search_fields = ('title', 'description')
    list_filter = ('date', 'category')
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Basic Information', {
            'fields' : ('title', 'description', 'category')
        }),
        ('Details', {
            'fields' : ('date', 'location', 'price', 'available_tickets') 
        }),
        ('System Information', {
            'fields' : ('created_at', 'updated_at')
        })
    )

    inlines = [EventImageInline]

    def tickets_status(self,obj):
        if obj.available_tickets == 0:
            color = 'red'
            status = 'Sold Out'
        elif obj.available_tickets < 50:
            color = 'yellow'
            status = 'Few tickets left'
        else:
            color = 'green'
            status = 'In Stock'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, status
        )
    tickets_status.short_description = "Ticket Status"


class OrderitemInline(admin.TabularInline):
    model = OrderItem
    extra = 1
    readonly_fields = ('amount_total_price',)

    def amount_total_price(self,obj):
        if obj.pk:
            return f"{obj.total_price}"
        return "-"
    amount_total_price.short_description = "Amount"

class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer_name', 'customer_email', 'total_price', 'status', 'order_status_color', 'created_at')
    search_fields = ('customer_name', 'customer_email', 'customer_phone')
    list_filter = ('status', 'created_at')
    readonly_fields = ('created_at', 'updated_at', 'total_price')

    fieldsets = (
        ('Customer Information', {
            'fields' : ('customer_name', 'customer_email', 'customer_phone')
        }),
        ('Order Information', {
            'fields' : ('total_price', 'status')
        }),
        ('System Information', {
            'fields' : ('created_at', 'updated_at')
        })
    )

    def order_status_color(self,obj):
       colors = {
            'pending' : 'yellow',
            'cancelled': 'red',
            'confirmed' : 'lightblue',
            'completed' : 'green'
       } 
       color = colors.get(obj.status, 'gray')
       return format_html(
           '<span style="background-color: {}; color: black; padding: 3px 8px; '
           'border-radius: 3px; font-size: 12px;">{}</span>',
           color, obj.get_status_display()
       )
    order_status_color.short_description = "Status"
    inlines = [OrderitemInline]

admin.site.register(Event, EventAdmin)
admin.site.register(Order, OrderAdmin)