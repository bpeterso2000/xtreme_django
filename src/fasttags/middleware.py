# fasttags_middleware.py (place this in your Django app or project)

from django.http import HttpResponse
from fasttags import FT, to_xml  # Import FastTag class and renderer

class FastTagsMiddleware:
    """
    Django middleware for prototyping with FastTags.
    
    This middleware allows views to return FastTag objects (e.g., Div(H1('Hello'))) 
    instead of HttpResponse. It automatically renders them to HTML.
    
    Usage:
    - Add to MIDDLEWARE in settings.py: 'path.to.FastTagsMiddleware'
    - In views, return FastTag instances for quick prototyping.
    - For production, migrate to templates (as per FastTags docs).

    # settings.py
    MIDDLEWARE = [
        # ... other middleware ...
        'yourapp.fasttags_middleware.FastTagsMiddleware',  # Adjust path
    ]
   
    Note: For safety, this is intended for development/prototyping only.
    
    Notes:

    Security/Prototyping Only: This allows returning non-HttpResponse objects, which bypasses some Django safeguards. Use for development/pilots; migrate to templates for production as per FastTags docs.
    Error Handling: If rendering fails, Django's error handling kicks in. Add try-except in the wrapped_view if needed.
    Customization: Extend for validation (e.g., call to_xml with validate=True).
    Dependencies: Ensure fasttags is installed and imported correctly.
    This middleware enables quick prototyping with FastTags in Django, aligning with the migration path to production templates.
    
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        """
        Wrap the view function to check if it returns a FastTag and render it.
        """
        def wrapped_view(request, *args, **kwargs):
            response = view_func(request, *args, **kwargs)
            if isinstance(response, FT):
                # Render FastTag to HTML string
                html = to_xml(response)
                return HttpResponse(html, content_type='text/html; charset=utf-8')
            return response
        return wrapped_view

# fasttags_middleware.py

from django.conf import settings
from django.http import HttpResponse, HttpResponseServerError
from django.utils.decorators import decorator_from_middleware
from fasttags import FT, to_xml  # Import FastTag class and renderer
import logging

logger = logging.getLogger(__name__)

class FastTagsMiddleware:
    """
    Secure Django middleware for prototyping with FastTags.
    
    Allows views to return FastTag objects, rendering them to HTML.
    Security enhancements:
    - Restricted to DEBUG mode (disable in production).
    - Validates response type.
    - Adds security headers.
    - Catches exceptions with proper error responses.
    - Logs actions for auditing.
    
    Usage:
    - Add to MIDDLEWARE: 'path.to.FastTagsMiddleware'
    - In views, return FastTag for prototyping.
    - Migrate to templates for production.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        if not settings.DEBUG:
            logger.warning("FastTagsMiddleware is enabled but DEBUG=False. This is insecure for production; disabling rendering.")
            self.enabled = False
        else:
            self.enabled = True

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        if not self.enabled:
            return None  # Skip in non-DEBUG mode

        def wrapped_view(request, *args, **kwargs):
            try:
                response = view_func(request, *args, **kwargs)
                if isinstance(response, FT):
                    logger.info(f"Rendering FastTag from view: {view_func.__name__}")
                    html = to_xml(response)
                    resp = HttpResponse(html, content_type='text/html; charset=utf-8')
                    # Add security headers
                    resp['X-Content-Type-Options'] = 'nosniff'
                    resp['X-Frame-Options'] = 'SAMEORIGIN'  # Adjust as needed
                    # TODO: Add CSRF if request has forms (manual check)
                    return resp
                return response
            except Exception as e:
                logger.error(f"Error rendering FastTag: {e}")
                prescription = (
                    "1. Check your FastTag structure for errors.\n"
                    "2. Ensure all dependencies (e.g., html5lib) are installed if using validation.\n"
                    "3. For production, migrate to Django templates."
                )
                return HttpResponseServerError(f"Rendering error: {str(e)}\n\nPrescription:\n{prescription}")

        return wrapped_view

# fasttags_middleware.py (place in your Django app/project)

from django.conf import settings
from django.http import HttpResponse, HttpResponseServerError
from django.middleware.csrf import get_token as get_csrf_token
from django.utils.html import escape
import re
import logging
from fasttags import FT, to_xml, config  # Import FastTag class, renderer, and config

logger = logging.getLogger(__name__)

class FastTagsMiddleware:
    """
    Secure Django middleware for rendering FastTags in views.
    
    Allows views to return FastTag objects for prototyping/small prod.
    Security features:
    - Opt-in for production via FASTTAGS_PROD_ENABLED setting.
    - Auto-injects CSRF tokens into <form> tags.
    - Adds security headers (CSP, HSTS, etc.).
    - Enforces escaping and validation in prod.
    - Robust error handling with generic responses.
    - Logging for auditing.
    
    Usage:
    - Add to MIDDLEWARE: 'path.to.FastTagsMiddleware'
    - Set FASTTAGS_PROD_ENABLED = True in settings.py for prod (default False).
    - In views, return FastTag instances.
    - Migrate to templates for larger projects.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        self.enabled = settings.DEBUG or getattr(settings, 'FASTTAGS_PROD_ENABLED', False)
        if not self.enabled:
            logger.warning("FastTagsMiddleware disabled in production (set FASTTAGS_PROD_ENABLED=True to enable).")

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        if not self.enabled:
            return None

        def wrapped_view(request, *args, **kwargs):
            try:
                response = view_func(request, *args, **kwargs)
                if isinstance(response, FT):
                    logger.info(f"Rendering FastTag from view: {view_func.__name__}")

                    # Enforce security configs in prod
                    if not settings.DEBUG:
                        config.escape_by_default = True
                        config.enable_validation = True
                        config.validate_mode = config.validate_mode or 'static'  # Minimum validation

                    # Render to HTML
                    html = to_xml(response, validate=config.enable_validation)

                    # Auto-inject CSRF into forms (simple regex; improve if needed)
                    csrf_token = get_csrf_token(request)
                    html = re.sub(r'<form\b', f'<form method="post"><input type="hidden" name="csrfmiddlewaretoken" value="{escape(csrf_token)}"> <form', html, flags=re.IGNORECASE)

                    # Create response with security headers
                    resp = HttpResponse(html, content_type='text/html; charset=utf-8')
                    self.add_security_headers(resp)
                    return resp
                return response
            except Exception as e:
                logger.error(f"Error rendering FastTag: {e}", exc_info=True)
                prescription = (
                    "1. Check your FastTag for errors (e.g., invalid attributes).\n"
                    "2. Ensure dependencies are installed if using advanced validation.\n"
                    "3. For production, consider migrating to Django templates for better security."
                )
                return HttpResponseServerError("An internal error occurred.")  # Generic message; no leak

        return wrapped_view

    def add_security_headers(self, response):
        """Add standard security headers."""
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'SAMEORIGIN'
        response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'  # HSTS (1 year)
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        # CSP: Customize based on your app (this is restrictive default)
        response['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self';"
        # Permissions-Policy: Limit features
        response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
