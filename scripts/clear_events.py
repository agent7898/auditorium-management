#!/usr/bin/env python
"""
Script to clear all events, tickets, and auditorium bookings from the database.
Run from project root: python scripts/clear_events.py
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_event_mgmt.settings')
django.setup()

from core.models import Event, Ticket, AuditoriumBooking

# Clear all events (cascades to tickets)
event_count = Event.objects.count()
Event.objects.all().delete()

# Clear tickets (if any orphaned)
ticket_count = Ticket.objects.count()
Ticket.objects.all().delete()

# Clear auditorium bookings
booking_count = AuditoriumBooking.objects.count()
AuditoriumBooking.objects.all().delete()

print(f"✓ Cleared {event_count} events")
print(f"✓ Cleared {ticket_count} tickets")
print(f"✓ Cleared {booking_count} auditorium bookings")
print("\nDatabase cleaned. You can now create fresh events!")
