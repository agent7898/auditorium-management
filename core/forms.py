from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Event, AuditoriumBooking, Profile

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['title', 'description', 'department', 'event_date',
                  'start_time', 'end_time', 'venue', 'total_seats', 'status']

    def clean(self):
        cleaned = super().clean()
        event_date = cleaned.get('event_date')
        start_time = cleaned.get('start_time')
        end_time = cleaned.get('end_time')
        venue = cleaned.get('venue')

        # prevent overlapping events at the same venue and date/time
        if event_date and start_time and end_time and venue:
            overlapping = Event.objects.filter(event_date=event_date, venue=venue)
            # exclude self when editing (instance)
            if self.instance and self.instance.pk:
                overlapping = overlapping.exclude(pk=self.instance.pk)
            for ev in overlapping:
                # check time overlap: events conflict if NOT (end <= other.start OR start >= other.end)
                if not (end_time <= ev.start_time or start_time >= ev.end_time):
                    raise forms.ValidationError(f'Event times overlap with another event "{ev.title}" at {venue} on {event_date}. Please choose a different time or venue.')
        return cleaned


class AuditoriumBookingForm(forms.ModelForm):
    class Meta:
        model = AuditoriumBooking
        # include expected_audience so user can request an expected audience size
        fields = ['department', 'purpose', 'event_date', 'start_time',
                  'end_time', 'expected_audience']

    def clean_expected_audience(self):
        from django.conf import settings
        cap = getattr(settings, 'AUDITORIUM_CAPACITY', 500)
        val = self.cleaned_data.get('expected_audience')
        if val is None:
            return val
        if val > cap:
            raise forms.ValidationError(f"Maximum auditorium capacity is {cap} seats. Please request {cap} or fewer.")
        if val <= 0:
            raise forms.ValidationError("Expected audience must be a positive number.")
        return val


class SignUpForm(UserCreationForm):
    # Allow user to choose a role at signup (student or admin)
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('admin', 'Admin'),
    ]
    role = forms.ChoiceField(choices=ROLE_CHOICES, initial='student', required=True, label='Role')
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2', 'role']
