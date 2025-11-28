#!/usr/bin/env python
"""
Script to seed the database with fresh test events.
Run from project root: python scripts/seed_events.py
"""
import os
import sys
import django
from datetime import datetime, timedelta

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_event_mgmt.settings')
django.setup()

from django.contrib.auth.models import User
from core.models import Event

# Get or create an admin/organizer user for created_by field
admin_user, _ = User.objects.get_or_create(
    username='admin',
    defaults={'first_name': 'Admin', 'is_staff': True}
)

# Define events to create (all OPEN status so they're visible)
events_data = [
    {
        'title': 'Python Workshop',
        'description': 'Learn Python basics and advanced concepts',
        'department': 'CSE',
        'venue': 'Lab A',
        'total_seats': 50,
        'event_date': datetime.now().date() + timedelta(days=1),
        'start_time': '10:00',
        'end_time': '12:00',
        'status': 'OPEN'
    },
    {
        'title': 'Web Development Seminar',
        'description': 'Introduction to modern web frameworks',
        'department': 'CSE',
        'venue': 'Auditorium',
        'total_seats': 200,
        'event_date': datetime.now().date() + timedelta(days=2),
        'start_time': '14:00',
        'end_time': '16:00',
        'status': 'OPEN'
    },
    {
        'title': 'Data Science Bootcamp',
        'description': 'Hands-on data science with Python and ML',
        'department': 'CSE',
        'venue': 'Lab B',
        'total_seats': 40,
        'event_date': datetime.now().date() + timedelta(days=3),
        'start_time': '09:00',
        'end_time': '11:30',
        'status': 'OPEN'
    },
    {
        'title': 'Cloud Computing Basics',
        'description': 'Introduction to AWS and cloud platforms',
        'department': 'IT',
        'venue': 'Classroom 101',
        'total_seats': 60,
        'event_date': datetime.now().date() + timedelta(days=5),
        'start_time': '11:00',
        'end_time': '13:00',
        'status': 'OPEN'
    },
    {
        'title': 'AI & Machine Learning Workshop',
        'description': 'Deep learning and neural networks',
        'department': 'CSE',
        'venue': 'Auditorium',
        'total_seats': 250,
        'event_date': datetime.now().date() + timedelta(days=7),
        'start_time': '15:00',
        'end_time': '17:30',
        'status': 'OPEN'
    }
]

created_count = 0
for event_data in events_data:
    event, created = Event.objects.get_or_create(
        title=event_data['title'],
        event_date=event_data['event_date'],
        start_time=event_data['start_time'],
        defaults={
            **event_data,
            'created_by': admin_user
        }
    )
    if created:
        created_count += 1
        print(f"✓ Created: {event.title} on {event.event_date} at {event.start_time}")
    else:
        print(f"~ Already exists: {event.title}")

print(f"\n✓ Total created: {created_count} new events")
print("Events are now ready for registration!")
