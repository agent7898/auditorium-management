#!/usr/bin/env python
"""
Script to reset student and admin passwords to S123.
Run from project root: python scripts/reset_passwords.py
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_event_mgmt.settings')
django.setup()

from django.contrib.auth.models import User

# Reset student password
try:
    student = User.objects.get(username='student')
    student.set_password('S123')
    student.save()
    print("✓ Student password reset to: S123")
except User.DoesNotExist:
    print("✗ Student user not found")

# Reset admin password
try:
    admin = User.objects.get(username='admin')
    admin.set_password('S123')
    admin.save()
    print("✓ Admin password reset to: S123")
except User.DoesNotExist:
    print("✗ Admin user not found")

print("\nDone! You can now login with:")
print("  Student: username=student, password=S123")
print("  Admin:   username=admin, password=S123")
