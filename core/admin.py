from django.contrib import admin
from .models import Profile, Event, Ticket, AuditoriumBooking

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'department')
    list_filter = ('role', 'department')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'department')


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'event_date', 'venue', 'department', 'total_seats', 'status')
    list_filter = ('department', 'status', 'event_date')
    search_fields = ('title', 'department', 'venue')


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('event', 'user', 'status', 'booked_at')
    list_filter = ('status', 'event__event_date')
    search_fields = ('event__title', 'user__username')


@admin.register(AuditoriumBooking)
class AuditoriumBookingAdmin(admin.ModelAdmin):
    list_display = ('purpose', 'event_date', 'start_time', 'end_time',
                    'requested_by', 'department', 'expected_audience', 'status')
    list_filter = ('status', 'department', 'event_date')
    search_fields = ('purpose', 'requested_by__username', 'department')
