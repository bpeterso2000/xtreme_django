"""
FastHTML Extensions and Component Library
=========================================

This module provides a lightweight framework for building HTML pages using FastHTML (via fastcore.xml),
with support for extensions (loaded from TOML), a global component catalog, and Django-like view registration.
It's designed for web development, allowing composition of UI components and dynamic HTML generation.

Key Features:
- **Extensions Library**: Load scripts/stylesheets from a TOML file (e.g., for Bootstrap, jQuery).
- **Component Catalog**: Register and reuse static/dynamic UI components (FT objects, tuples, or callables).
- **View Registration**: Decorate functions as web views with automatic path registration.
- **HTML Builder**: Dataclass for composing HTML pages with headers, body, and extensions.

Dependencies:
- Python 3.11+ (for tomllib; use 'pip install tomli' for older versions).
- fastcore.xml (for FT and HTML tags).
- Django (for HttpResponse and MiddlewareMixin, if used in a Django context).

Usage Overview:
1. Define extensions in 'extensions.toml' (e.g., [bootstrap] html = ["css_url", "js_url"]).
2. Register components globally (static or dynamic/callable).
3. Use the @ft decorator for views.
4. Build HTML with the HTML dataclass, incorporating extensions and components.

Example:
    # Register a component
    @register_component('alert')
    def alert(msg: str, level: str = 'info'):
        return Div(msg, cls=f'alert alert-{level}')
    
    # Build HTML
    html_builder = HTML()
    html_builder.contents = COMPONENT_REGISTRY['alert']('Hello!', level='success')
    html_builder.extensions = ['bootstrap']
    result = html_builder.to_html()  # Generates full HTML FT

Notes:
- Components are global and in-memory; import COMPONENT_REGISTRY to access from other modules.
- Extensions are loaded at import time; invalid/missing TOML files are ignored.
- Callables in components must return FT or tuple; invoke manually when assigning to HTML fields.
- Assumes fastcore.xml provides tags like Div, Meta, etc. (extend as needed).
- For production, consider error handling, persistence, or namespacing components.

Classes and Functions:
"""

from dataclasses import dataclass, field
from functools import partial
from typing import Any, Callable
import functools
import tomllib  # Use 'import tomli as tomllib' if on Python < 3.11

from django.utils.deprecation import MiddlewareMixin
from django.http import HttpResponse
from fastcore.xml import FT, Body, Div, Head, Html, Link, Meta, Script, to_xml

# Load extensions from TOML file (defaults to empty dict if file missing/invalid)
EXTENSIONS = {}
try:
    with open('extensions.toml', 'rb') as f:
        EXTENSIONS = tomllib.load(f)
except (FileNotFoundError, tomllib.TOMLKitError):
    pass  # Silently ignore; extensions will be empty

# Global component catalog
COMPONENT_REGISTRY = {}

def register_component(name: str, component: Any = None):
    """
    Register a component in the global catalog for reuse across modules.
    
    Args:
        name (str): Unique key for the component.
        component (Any, optional): The component to register. Can be:
            - Static: FT object or tuple (e.g., Div('text')).
            - Dynamic: Callable (function/lambda) returning FT or tuple. Supports any arguments/parameters
              (positional, keyword, *args, **kwargs).
    
    Returns:
        The registered component (for chaining).
    
    Usage:
        # Static
        register_component('footer', Div('© 2023'))
        
        # Dynamic (as decorator)
        @register_component('button')
        def button(text: str, href: str = '#', **attrs):
            return FT(tag='a', children=[text], href=href, **attrs)
        
        # Access and use
        COMPONENT_REGISTRY['footer']  # Static FT
        COMPONENT_REGISTRY['button']('Click', href='/url', cls='btn')  # Invoke callable
    """
    def decorator(comp):
        COMPONENT_REGISTRY[name] = comp
        return comp
    if component is not None:
        COMPONENT_REGISTRY[name] = component
        return component
    return decorator

REGISTRY = {}

def ft(path=None, *decorator_args, **decorator_kwargs):
    """
    Decorator to register a function as a web view for Django URL routing.
    
    Args:
        path (str, optional): Custom URL path. Defaults to '/<function_name>/'.
        *decorator_args, **decorator_kwargs: Passed to the decorator (for extensibility).
    
    Returns:
        Decorated function that registers the view and handles FT/tuple responses.
    
    Usage:
        @ft('/home/')
        def home_view(request):
            return Div('Welcome!')
        
        # Access registered views
        view_func = REGISTRY['/home/']
    """
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
            result = original_func(*args, **kwargs)
            if isinstance(result, (FT, tuple)):
                rendered_xml = to_xml(result)
                return HttpResponse(rendered_xml, content_type='text/html')
            return result
        
        wrapper.__wrapped__ = original_func
        wrapper.ft_path = final_path
        
        return wrapper
    
    return decorator

@dataclass
class HTML:
    """
    Dataclass for building HTML pages with headers, body, and extensions.
    
    Attributes:
        language (str): HTML lang attribute (default: 'en').
        encoding (FT): Meta charset tag.
        viewport (FT): Meta viewport tag.
        body (FT): Body tag (default: empty Body()).
        hdrs (list[Any]): Additional header elements (e.g., Meta tags).
        contents (FT): Main content (default: empty Div; can be FT, tuple, or component).
        ftrs (list[Any]): Footer elements (e.g., components).
        extensions (list[str]): List of extension names from TOML to load (e.g., ['bootstrap']).
    
    Methods:
        add_hdrs(): Builds the <head> with encoding, viewport, hdrs, and extensions (CSS/JS links).
        to_html(): Wraps content in full HTML structure, handling FT/tuple nesting.
    
    Usage:
        html_builder = HTML()
        html_builder.contents = COMPONENT_REGISTRY['alert']('Message')
        html_builder.extensions = ['jquery']
        html = html_builder.to_html()  # FT object for rendering
    """
    language: str = 'en'
    encoding: FT = Meta(charset='utf-8')
    viewport: FT = Meta(content='width=device-width, initial-scale=1.0')
    body: FT = Body()
    hdrs: list[Any] = field(default_factory=list)
    contents: FT = Div()  # Default to an empty div if not set; can be overridden
    ftrs: list[Any] = field(default_factory=list)
    extensions: list[str] = field(default_factory=list)  # List of shortcut names from TOML

    def add_hdrs(self) -> FT:
        headers = [self.encoding, self.viewport, *self.hdrs]  # Standard + user headers first
        
        # Add extensions at the end
        for ext in self.extensions:
            if ext in EXTENSIONS:
                for url in EXTENSIONS[ext]['html']:
                    if url.endswith('.css'):
                        headers.append(Link(rel='stylesheet', href=url))
                    elif url.endswith('.js'):
                        headers.append(Script(src=url))
                    # Skip if not .css or .js
        
        return Head(*headers)

    def to_html(self) -> FT:
        '''Wrap a Fast Tag in HTML, Head, and/or Body tags if not provided.'''
        if isinstance(self.contents, FT):
            match self.contents.tag:
                case 'html':
                    return self.contents
                case 'head':
                    return Html(self.contents, lang=self.language)
                case 'body':
                    return Html(
                        self.add_hdrs(),
                        self.contents,
                        lang=self.language
                    )

        # Default: wrap in Html with Head and Body
        return Html(
            self.add_hdrs(),
            self.body(self.contents, *self.ftrs),
            lang=self.language
        )

if __name__ == '__main__':
    # Example: Register components
    register_component('footer', Div('© 2023 My Site'))  # Static component
    @register_component('alert')  # Dynamic component
    def alert(msg: str):
        return Div(msg, cls='alert')
    
    # Example: Use in HTML builder
    html_builder = HTML()
    html_builder.contents = COMPONENT_REGISTRY['alert']('Hello World')
    html_builder.hdrs.append(Meta(name='author', content='Me'))
    html_builder.extensions = ['bootstrap']  # Load extensions
    result = html_builder.to_html()
    print(result)  # Outputs the full HTML FT structure
