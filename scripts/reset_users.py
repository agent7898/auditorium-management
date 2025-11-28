"""
Reset auth users in the SQLite DB and create one admin + one student account.

WARNING: This script will DELETE ALL rows in `auth_user` and related `Profile`
models. Run only when you are sure. It is intended to be executed from the
project root with the project's Python environment active.

Usage (PowerShell):
.\.venv\Scripts\Activate.ps1; python .\scripts\reset_users.py

The script prints the created credentials to stdout.
"""
import os
import sys

PROJECT_SETTINGS = 'college_event_mgmt.settings'

os.environ.setdefault('DJANGO_SETTINGS_MODULE', PROJECT_SETTINGS)

# Ensure project root is on sys.path (when script is executed from scripts/)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

try:
    import django
    django.setup()
except Exception as e:
    print('Failed to setup Django. Are you running this from the project root and is Django installed?')
    print('Error:', e)
    sys.exit(1)

from django.contrib.auth.models import User
from core.models import Profile
from django.db import transaction

ADMIN_CREDENTIALS = {
    'username': 'admin',
    'email': 'admin@example.com',
    'password': 'AdminPass123!'
}

STUDENT_CREDENTIALS = {
    'username': 'student',
    'email': 'student@example.com',
    'password': 'StudentPass123!'
}

def reset_users():
    with transaction.atomic():
        # Delete profiles first (Profile has FK to User)
        print('Deleting all Profile objects...')
        Profile.objects.all().delete()

        # Delete all users
        print('Deleting all User accounts...')
        User.objects.all().delete()

        # Create admin
        print('Creating admin account...')
        admin = User.objects.create_user(username=ADMIN_CREDENTIALS['username'],
                                         email=ADMIN_CREDENTIALS['email'],
                                         password=ADMIN_CREDENTIALS['password'])
        admin.is_staff = True
        admin.is_superuser = True
        admin.save()
        Profile.objects.create(user=admin, role='auditorium_manager')

        # Create student
        print('Creating student account...')
        student = User.objects.create_user(username=STUDENT_CREDENTIALS['username'],
                                           email=STUDENT_CREDENTIALS['email'],
                                           password=STUDENT_CREDENTIALS['password'])
        Profile.objects.create(user=student, role='student')

        print('\nDone. Created accounts:')
        print('ADMIN -> username: {username}  password: {password}'.format(**ADMIN_CREDENTIALS))
        print('STUDENT -> username: {username}  password: {password}'.format(**STUDENT_CREDENTIALS))

if __name__ == '__main__':
    reset_users()
