"""
Production settings for PythonAnywhere deployment.
Username: auditorium
"""

from .settings import *

# SECURITY: Set to False in production
DEBUG = False

# PythonAnywhere domain
ALLOWED_HOSTS = ['auditorium.pythonanywhere.com']

# Static files - for collectstatic command
STATIC_ROOT = '/home/auditorium/auditorium-management/staticfiles'

# Media files
MEDIA_ROOT = '/home/auditorium/auditorium-management/media'

# Security settings for production
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
