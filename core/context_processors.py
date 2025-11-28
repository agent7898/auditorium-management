import os
import random
from pathlib import Path
from django.conf import settings
from django.templatetags.static import static


def user_profile_role(request):
    """Context processor that exposes `user_profile_role` safely.

    Returns the profile role string when available, otherwise None. Use in
    templates as `user_profile_role` to avoid accessing `user.profile` directly.
    """
    role = None
    user = getattr(request, 'user', None)
    if user and user.is_authenticated:
        try:
            role = user.profile.role
        except Exception:
            role = None
    return {'user_profile_role': role}


def page_background(request):
    """Return `page_bg_url` pointing to a static image for page backgrounds.

    Behavior:
    - Looks for images inside `core/static/images/page_bgs/`.
    - If a file matches the first path segment (e.g. 'events.jpg' for '/events/'),
      it will be preferred.
    - Otherwise a random image from the folder is chosen.
    - If the folder is missing or empty, returns None.

    The returned `page_bg_url` is a fully-resolved static URL (via `static()`).
    Templates can then set a CSS variable like `--page-bg-url` using it.
    """
    try:
        imgs_dir = Path(settings.BASE_DIR) / 'core' / 'static' / 'images' / 'page_bgs'
        if not imgs_dir.exists() or not imgs_dir.is_dir():
            return {'page_bg_url': None}

        # Gather image files (common extensions) but exclude booking.jpg (unclear for pages)
        files = [p.name for p in imgs_dir.iterdir() if p.suffix.lower() in ('.png', '.jpg', '.jpeg', '.webp', '.svg') and not p.name.lower().startswith('booking')]
        if not files:
            return {'page_bg_url': None}

        # Prefer explicit mapping for common pages, then fall back to the
        # first URL segment heuristic, then a random file.
        path = (request.path or '').strip('/')
        path_segment = path.split('/')[0] if path else ''

        # explicit mapping: route -> filename (if present)
        mapping = {
            '': 'home',              # root -> home.jpg
            'events': 'events',      # /events/ -> events.jpg
            'auditorium': 'home',    # /auditorium/ -> use home.jpg for clarity
        }

        candidate = None

        # Special case: event detail pages like /events/123/ -> prefer event_detail
        import re
        if re.match(r'^events/\d+/?$', path):
            if 'event_detail' in [f.rsplit('.',1)[0] for f in files]:
                candidate = next((f for f in files if f.rsplit('.',1)[0] == 'event_detail'), None)

        # Try mapping (home/events/auditorium)
        if not candidate and path_segment in mapping:
            name = mapping[path_segment]
            candidate = next((f for f in files if f.rsplit('.',1)[0].lower() == name.lower()), None)

        # If no mapped candidate, fall back to the first-segment heuristic
        if not candidate and path_segment:
            candidate = next((f for f in files if f.lower().startswith(path_segment.lower())), None)

        # final fallback: random available image
        if not candidate:
            candidate = random.choice(files)

        # determine overlay opacity per image to ensure text contrast
        basename = candidate.rsplit('.', 1)[0].lower()
        overlay_map = {
            'home': 0.12,
            'events': 0.14,
            'event_detail': 0.18,
            'booking': 0.22,
        }
        overlay = overlay_map.get(basename, 0.14)

        # force a stronger overlay for auditorium pages to improve contrast
        if path_segment and 'auditorium' in path_segment:
            overlay = max(overlay, 0.22)

        # resolve to static URL relative to STATICFILES_DIRS (images stored under 'images/page_bgs/')
        return {'page_bg_url': static(f'images/page_bgs/{candidate}'), 'page_bg_overlay': overlay}
    except Exception:
        return {'page_bg_url': None, 'page_bg_overlay': 0.12}
