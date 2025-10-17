import functools

from django.utils.deprecation import MiddlewareMixin
from django.http import HttpResponse
from fastcore.xml import FT
import fastcore.xml

REGISTRY = {}


class FastTagMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        if isinstance(response, FT):
            rendered_xml = fastcore.xml.to_xml(response)
            return HttpResponse(rendered_xml, content_type='text/html')
        return response


def ft(path=None, *decorator_args, **decorator_kwargs):
    def decorator(view_func):
        # Handle potential previous wrapping
        original_func = view_func
        while hasattr(original_func, '__wrapped__'):
            original_func = original_func.__wrapped__
        
        # Determine path
        final_path = path or '/' + original_func.__name__.lower() + '/'
        
        # Register the view
        REGISTRY[final_path] = original_func
        
        # Preserve metadata and support chaining
        @functools.wraps(original_func)
        def wrapper(*args, **kwargs):
            return original_func(*args, **kwargs)
        
        wrapper.__wrapped__ = original_func
        wrapper.ft_path = final_path
        
        return wrapper
    
    return decorator

