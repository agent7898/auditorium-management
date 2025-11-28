from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth import login
from django.utils import timezone
from django.db import IntegrityError
from io import BytesIO
from PIL import Image
from django.core.files.base import ContentFile
import qrcode

from .models import Event, Ticket, AuditoriumBooking, Profile
from .forms import EventForm, AuditoriumBookingForm, SignUpForm

# Helper checks
def is_organizer(user):
    try:
        return user.profile.role == 'organizer' or user.is_staff
    except Profile.DoesNotExist:
        return False

def is_auditorium_manager(user):
    try:
        return user.profile.role == 'auditorium_manager' or user.is_staff
    except Profile.DoesNotExist:
        return False


def generate_qr_code(ticket):
    """Generate a QR code image for a ticket and save it."""
    try:
        # QR code data: event ID + ticket ID + user username
        qr_data = f"Event:{ticket.event.id}|Ticket:{ticket.id}|User:{ticket.user.username}"
        qr = qrcode.QRCode(version=1, box_size=10, border=2)
        qr.add_data(qr_data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Save image to BytesIO buffer
        img_io = BytesIO()
        img.save(img_io, format='PNG')
        img_io.seek(0)
        
        # Save to ticket model
        filename = f'ticket_{ticket.id}_qr.png'
        ticket.qr_code.save(filename, ContentFile(img_io.getvalue()), save=True)
    except Exception as e:
        print(f"Error generating QR code: {e}")


def home(request):
    # If the user is not authenticated, redirect them to login first
    if not request.user.is_authenticated:
        return redirect('login')

    events = Event.objects.filter(event_date__gte=timezone.now().date()).order_by('event_date')[:5]
    return render(request, 'core/home.html', {'events': events})


def event_list(request):
    # Only show OPEN events (approved by admin); hide PENDING requests
    events = Event.objects.filter(status='OPEN').order_by('event_date')
    return render(request, 'core/event_list.html', {'events': events})


def event_detail(request, pk):
    # Only allow viewing OPEN events; PENDING requests are not visible to students
    event = get_object_or_404(Event, pk=pk, status='OPEN')
    ticket = None
    if request.user.is_authenticated:
        ticket = Ticket.objects.filter(event=event, user=request.user).first()
    # collect booked seats to render a seat map client-side
    booked_seats = list(Ticket.objects.filter(event=event, status='BOOKED').values_list('seat', flat=True))
    return render(request, 'core/event_detail.html', {
        'event': event,
        'ticket': ticket,
        'booked_seats': booked_seats,
    })


@login_required
@user_passes_test(is_organizer)
def event_create(request):
    if request.method == 'POST':
        form = EventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            event.created_by = request.user
            event.save()
            messages.success(request, "Event created successfully.")
            return redirect('event_detail', pk=event.pk)
    else:
        form = EventForm()
    return render(request, 'core/event_form.html', {'form': form, 'title': 'Create Event'})


@login_required
@user_passes_test(is_organizer)
def event_update(request, pk):
    event = get_object_or_404(Event, pk=pk)
    if event.created_by != request.user and not request.user.is_staff:
        messages.error(request, "You are not allowed to edit this event.")
        return redirect('event_detail', pk=pk)

    if request.method == 'POST':
        form = EventForm(request.POST, instance=event)
        if form.is_valid():
            form.save()
            messages.success(request, "Event updated successfully.")
            return redirect('event_detail', pk=pk)
    else:
        form = EventForm(instance=event)
    return render(request, 'core/event_form.html', {'form': form, 'title': 'Edit Event'})


@login_required
def event_register(request, pk):
    event = get_object_or_404(Event, pk=pk, status='OPEN')

    if event.available_seats() <= 0:
        event.status = 'CLOSED'
        event.save()
        messages.error(request, "No seats available.")
        return redirect('event_detail', pk=pk)

    existing = Ticket.objects.filter(event=event, user=request.user, status='BOOKED').first()
    if existing:
        messages.info(request, "You are already registered for this event.")
        return redirect('event_detail', pk=pk)

    # assign seat from POST if provided
    seat = request.POST.get('seat') if request.method == 'POST' else None
    # check seat uniqueness
    if seat:
        if Ticket.objects.filter(event=event, seat=seat, status='BOOKED').exists():
            messages.error(request, 'Selected seat is already taken. Choose a different seat.')
            return redirect('event_detail', pk=pk)

    Ticket.objects.create(event=event, user=request.user, status='BOOKED', seat=seat)
    ticket = Ticket.objects.get(event=event, user=request.user, status='BOOKED')
    
    # Generate and save QR code for the ticket
    generate_qr_code(ticket)
    
    if event.available_seats() <= 0:
        event.status = 'CLOSED'
        event.save()

    messages.success(request, "Registration successful.")
    return redirect('my_events')


@login_required
def my_events(request):
    tickets = Ticket.objects.filter(user=request.user, status='BOOKED').select_related('event').order_by('-booked_at')
    from django.conf import settings
    auditorium_capacity = getattr(settings, 'AUDITORIUM_CAPACITY', 500)

    bookings = AuditoriumBooking.objects.filter(requested_by=request.user).order_by('-created_at')
    # attach linked event info (if an Event was created from the booking)
    for b in bookings:
        ev = Event.objects.filter(title=b.purpose, event_date=b.event_date,
                                  start_time=b.start_time, end_time=b.end_time, venue='Auditorium').first()
        b.linked_event = ev
    return render(request, 'core/my_events.html', {'tickets': tickets, 'bookings': bookings, 'auditorium_capacity': auditorium_capacity})


@login_required
def booking_create(request):
    from django.conf import settings
    auditorium_capacity = getattr(settings, 'AUDITORIUM_CAPACITY', 500)

    if request.method == 'POST':
        form = AuditoriumBookingForm(request.POST)
        if form.is_valid():
            # create a booking record for tracking
            booking = form.save(commit=False)
            booking.requested_by = request.user
            # expected_audience is provided by user (validated in the form)
            booking.save()

            # also create a corresponding Event in PENDING state so organizers/users see it as a requested event
            title = booking.purpose or 'Auditorium Request'
            # check for existing events at the same venue/date/time (strict: prevent any overlaps at auditorium)
            overlapping = Event.objects.filter(
                event_date=booking.event_date,
                venue='Auditorium'
            )
            has_conflict = False
            for ev in overlapping:
                # check time overlap
                if not (booking.end_time <= ev.start_time or booking.start_time >= ev.end_time):
                    has_conflict = True
                    break
            
            if not has_conflict:
                Event.objects.create(
                    title=title,
                    description=f"Requested auditorium event by {request.user.username}",
                    department=booking.department,
                    event_date=booking.event_date,
                    start_time=booking.start_time,
                    end_time=booking.end_time,
                    venue='Auditorium',
                    total_seats=auditorium_capacity,
                    status='PENDING',
                    created_by=request.user
                )
                messages.success(request, "Auditorium booking request submitted.")
            else:
                # reject the booking if auditorium is already booked at that time
                booking.delete()
                messages.error(request, f"Auditorium booking request rejected: The auditorium is already booked during {booking.start_time} – {booking.end_time} on {booking.event_date}. Please choose a different time.")
                return render(request, 'core/booking_form.html', {'form': form, 'auditorium_capacity': auditorium_capacity})
            return redirect('my_bookings')
        else:
            # gather specific validation messages, prefer expected_audience validation
            if 'expected_audience' in form.errors:
                # show the field error as a prominent toast
                messages.error(request, f"Auditorium booking request rejected: {form.errors['expected_audience'][0]}")
            else:
                # generic form error
                # join non-field errors and field errors into one message
                errors = []
                for k, v in form.errors.items():
                    errors.append(f"{k}: {', '.join(v)}")
                messages.error(request, "Please correct the errors and resubmit: " + ' | '.join(errors))
    else:
        form = AuditoriumBookingForm()
    return render(request, 'core/booking_form.html', {'form': form, 'auditorium_capacity': auditorium_capacity})


@login_required
def my_bookings(request):
    from django.conf import settings
    auditorium_capacity = getattr(settings, 'AUDITORIUM_CAPACITY', 500)

    bookings = AuditoriumBooking.objects.filter(requested_by=request.user).order_by('-created_at')
    for b in bookings:
        ev = Event.objects.filter(title=b.purpose, event_date=b.event_date,
                                  start_time=b.start_time, end_time=b.end_time, venue='Auditorium').first()
        b.linked_event = ev
    return render(request, 'core/my_bookings.html', {'bookings': bookings, 'auditorium_capacity': auditorium_capacity})


@login_required
@user_passes_test(is_auditorium_manager)
def booking_list_admin(request):
    bookings = AuditoriumBooking.objects.all().order_by('-created_at')
    return render(request, 'core/booking_list.html', {'bookings': bookings})


@login_required
@user_passes_test(is_organizer)
def booking_list_organizer(request):
    # Organizers see only bookings for their department (if department set on profile)
    role = None
    try:
        role = request.user.profile.role
    except Profile.DoesNotExist:
        role = None

    if request.user.is_staff:
        bookings = AuditoriumBooking.objects.all().order_by('-created_at')
    else:
        # If organizer has department, filter by same department; otherwise show all
        dept = getattr(request.user.profile, 'department', None)
        if dept:
            bookings = AuditoriumBooking.objects.filter(department=dept).order_by('-created_at')
        else:
            bookings = AuditoriumBooking.objects.all().order_by('-created_at')

    return render(request, 'core/booking_list_organizer.html', {'bookings': bookings})


@login_required
@user_passes_test(is_organizer)
def booking_update_status_organizer(request, pk):
    booking = get_object_or_404(AuditoriumBooking, pk=pk)
    if request.method == 'POST':
        status = request.POST.get('status')
        remarks = request.POST.get('remarks', '')
        if status in ['PENDING', 'APPROVED', 'REJECTED']:
            booking.status = status
            booking.remarks = remarks
            booking.save()
            messages.success(request, "Booking updated.")
        # if approved, ensure a corresponding Event is OPEN so it appears in upcoming events
        if status == 'APPROVED':
            from django.conf import settings
            title = booking.purpose or 'Approved Auditorium Event'
            
            # check for time conflicts with other approved events
            overlapping = Event.objects.filter(
                event_date=booking.event_date,
                venue='Auditorium',
                status='OPEN'  # only check against approved/open events
            )
            has_conflict = False
            for ev in overlapping:
                if not (booking.end_time <= ev.start_time or booking.start_time >= ev.end_time):
                    has_conflict = True
                    break
            
            if has_conflict:
                booking.status = 'REJECTED'
                booking.remarks = 'Rejected: Auditorium already booked at this time.'
                booking.save()
                messages.error(request, f"Cannot approve: Auditorium is already booked during {booking.start_time} – {booking.end_time} on {booking.event_date}.")
            else:
                # prefer updating an existing PENDING event created at request time
                ev = Event.objects.filter(title=title, event_date=booking.event_date,
                                          start_time=booking.start_time, end_time=booking.end_time,
                                          venue='Auditorium').first()
                if ev:
                    ev.status = 'OPEN'
                    ev.total_seats = getattr(settings, 'AUDITORIUM_CAPACITY', ev.total_seats or 500)
                    ev.save()
                else:
                    Event.objects.create(title=title,
                                         description=f"Approved auditorium booking by {booking.requested_by.username}",
                                         department=booking.department,
                                         event_date=booking.event_date,
                                         start_time=booking.start_time,
                                         end_time=booking.end_time,
                                         venue='Auditorium',
                                         total_seats=getattr(settings, 'AUDITORIUM_CAPACITY', 500),
                                         status='OPEN',
                                         created_by=booking.requested_by)
        return redirect('booking_list_organizer')
    return render(request, 'core/booking_form.html', {'booking': booking, 'organizer_update': True})


@login_required
@user_passes_test(lambda u: u.is_staff)
def admin_user_list(request):
    users = Profile.objects.select_related('user').all()
    return render(request, 'core/admin_user_list.html', {'profiles': users})


@login_required
@user_passes_test(lambda u: u.is_staff)
def admin_user_delete(request, pk):
    # pk here is the User id
    from django.contrib.auth.models import User
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        user.delete()
        messages.success(request, 'User deleted.')
        return redirect('admin_user_list')
    return render(request, 'core/admin_user_confirm_delete.html', {'user_obj': user})


@login_required
@user_passes_test(is_auditorium_manager)
def booking_update_status(request, pk):
    booking = get_object_or_404(AuditoriumBooking, pk=pk)
    if request.method == 'POST':
        status = request.POST.get('status')
        remarks = request.POST.get('remarks', '')
        if status in ['PENDING', 'APPROVED', 'REJECTED']:
            booking.status = status
            booking.remarks = remarks
            booking.save()
            messages.success(request, "Booking updated.")
        # if approved by admin, ensure event is opened
        if status == 'APPROVED':
            from django.conf import settings
            title = booking.purpose or 'Approved Auditorium Event'
            
            # check for time conflicts with other approved events
            overlapping = Event.objects.filter(
                event_date=booking.event_date,
                venue='Auditorium',
                status='OPEN'  # only check against approved/open events
            )
            has_conflict = False
            for ev in overlapping:
                if not (booking.end_time <= ev.start_time or booking.start_time >= ev.end_time):
                    has_conflict = True
                    break
            
            if has_conflict:
                booking.status = 'REJECTED'
                booking.remarks = 'Rejected: Auditorium already booked at this time.'
                booking.save()
                messages.error(request, f"Cannot approve: Auditorium is already booked during {booking.start_time} – {booking.end_time} on {booking.event_date}.")
            else:
                ev = Event.objects.filter(title=title, event_date=booking.event_date,
                                          start_time=booking.start_time, end_time=booking.end_time,
                                          venue='Auditorium').first()
                if ev:
                    ev.status = 'OPEN'
                    ev.total_seats = getattr(settings, 'AUDITORIUM_CAPACITY', ev.total_seats or 500)
                    ev.save()
                else:
                    Event.objects.create(title=title,
                                         description=f"Approved auditorium booking by {booking.requested_by.username}",
                                         department=booking.department,
                                         event_date=booking.event_date,
                                         start_time=booking.start_time,
                                         end_time=booking.end_time,
                                         venue='Auditorium',
                                         total_seats=getattr(settings, 'AUDITORIUM_CAPACITY', 500),
                                         status='OPEN',
                                         created_by=booking.requested_by)

        return redirect('booking_list_admin')
    return render(request, 'core/booking_form.html', {'booking': booking, 'admin_update': True})

    


def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            try:
                # Save user
                user = form.save()
                # Determine role from form (default to student)
                role = form.cleaned_data.get('role', 'student')
                # Map 'admin' role to staff user privileges for simplicity
                if role == 'admin':
                    user.is_staff = True
                    user.save()
                    Profile.objects.create(user=user, role='organizer')
                else:
                    Profile.objects.create(user=user, role='student')
                login(request, user)
                messages.success(request, "Account created successfully.")
                return redirect('home')
            except IntegrityError:
                # This will catch "UNIQUE constraint failed: auth_user.username"
                form.add_error('username', "This username is already taken. Please choose another one.")
    else:
        form = SignUpForm()
    return render(request, 'registration/signup.html', {'form': form})

