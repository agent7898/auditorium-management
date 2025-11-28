from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),

    # Events
    path('events/', views.event_list, name='event_list'),
    path('events/<int:pk>/', views.event_detail, name='event_detail'),
    path('events/create/', views.event_create, name='event_create'),
    path('events/<int:pk>/edit/', views.event_update, name='event_update'),
    path('events/<int:pk>/register/', views.event_register, name='event_register'),
    path('events/<int:pk>/register/', views.event_register, name='event_register'),
    path('my-events/', views.my_events, name='my_events'),
    path('my-activities/', views.my_events, name='my_activities'),

    # Auditorium bookings
    path('auditorium/book/', views.booking_create, name='booking_create'),
    path('auditorium/my-bookings/', views.my_bookings, name='my_bookings'),
    path('auditorium/requests/', views.booking_list_admin, name='booking_list_admin'),
    path('auditorium/requests/<int:pk>/update/', views.booking_update_status, name='booking_update_status'),
    # Organizer booking views
    path('auditorium/organizer/requests/', views.booking_list_organizer, name='booking_list_organizer'),
    path('auditorium/organizer/requests/<int:pk>/update/', views.booking_update_status_organizer, name='booking_update_status_organizer'),

    # Admin user management
    path('admin/users/', views.admin_user_list, name='admin_user_list'),
    path('admin/users/<int:pk>/delete/', views.admin_user_delete, name='admin_user_delete'),

    # Simple signup (for students)
    path('signup/', views.signup, name='signup'),
]
