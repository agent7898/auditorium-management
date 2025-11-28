# College Event Management System

Django 5.2 application for managing college events, ticket bookings, and auditorium reservations.

## Architecture

- **Project**: `college_event_mgmt/` (settings, root URLs)
- **App**: `core/` (all domain logic, models, views, templates)
- **Database**: SQLite (`db.sqlite3`)
- **Templates**: Global `templates/` (login/signup) + `core/templates/core/` (app views)

## Domain Models (`core/models.py`)

| Model | Purpose | Key Rules |
|-------|---------|-----------|
| `Profile` | Extends User with role | Roles: `student`, `organizer`, `auditorium_manager` |
| `Event` | Campus events | Status: `OPEN`, `CLOSED`, `PENDING`. Uses `available_seats()` / `booked_seats()` |
| `Ticket` | Event registrations | `unique_together = ('event', 'user')`. Has QR code generation |
| `AuditoriumBooking` | Venue requests | Status: `PENDING` → `APPROVED`/`REJECTED`. Links to Event on approval |

## Role-Based Access (`core/views.py`)

```python
# Use these helper functions for permission checks
def is_organizer(user):      # Can create/edit events, manage bookings
def is_auditorium_manager(user):  # Can approve/reject auditorium bookings

# Pattern: always guard profile access
try:
    role = request.user.profile.role
except Profile.DoesNotExist:
    role = None
```

## Key Workflows

**Event Registration Flow**: `event_detail` → `event_register` → creates `Ticket` + QR code → auto-closes event if full

**Auditorium Booking Flow**: `booking_create` → creates `AuditoriumBooking` + `PENDING` Event → organizer/manager approves → Event becomes `OPEN`

## URL Names (preserve these)

`home`, `event_list`, `event_detail`, `event_create`, `event_update`, `event_register`, `my_events`, `booking_create`, `my_bookings`, `booking_list_admin`, `booking_list_organizer`, `signup`, `login`, `logout`

## Dev Commands

```bash
# Setup
python -m venv .venv && source .venv/bin/activate
pip install Django==5.2.8 qrcode pillow

# Database
python manage.py migrate
python manage.py createsuperuser

# Run
python manage.py runserver

# Seed test data
python scripts/seed_events.py
```

## Project-Specific Settings (`settings.py`)

- `AUDITORIUM_CAPACITY = 500` — used when approving bookings
- Custom context processors: `user_profile_role`, `page_background` in `core/context_processors.py`
- Media uploads: `media/qr_codes/` for ticket QR images

## Editing Guidelines

1. **Model changes**: Always run `python manage.py makemigrations && python manage.py migrate`
2. **Permissions**: Reuse `is_organizer()` / `is_auditorium_manager()` helpers
3. **User feedback**: Use `messages.success()` / `messages.error()` framework
4. **Forms**: Extend `ModelForm` in `core/forms.py`; validation in `clean()` methods
5. **Signup**: Must create `Profile` after `User` save (see `views.signup`)

## Do NOT Change Without Review

- `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS` in settings
- Database backend (SQLite → other requires deployment changes)
- URL names (templates depend on `{% url 'name' %}` tags)
