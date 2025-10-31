from dataclasses import dataclass
from typing import Callable, Any
import tomllib  # Use 'import tomli as tomllib' if on Python < 3.11
import logging
import types

from django.http import HttpResponse
from fastcore.xml import FT, Body, Head, Html, Link, Meta, Script, to_xml

logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(
        level=logging.WARNING, 
        format='%(levelname)s: %(message)s'
    )

# ============================================================================
# COMPONENT REGISTRY - Simple dict for reusable components
# ============================================================================

COMPONENTS = types.SimpleNamespace()

def component(func):
    """Decorator to register a component with its function name."""
    setattr(COMPONENTS, func.__name__, func)
    return func

# ============================================================================
# EXTENSIONS - Load CSS/JS from TOML config (immutable after load)
# ============================================================================

def load_extensions(config_path='extensions.toml'):
    try:
        with open(config_path, 'rb') as f:
            data = tomllib.load(f)
        
        extensions = {}
        for name, config in data.items():
            if isinstance(config, dict) and 'html' in config:
                extensions[name] = config['html']
            else:
                logger.warning(
                    f"Extension '{name}' missing 'html' key or invalid format"
                )
        
        return extensions
    
    except FileNotFoundError:
        logger.warning(f"Config file '{config_path}' not found. No extensions loaded.")
        return {}
    
    except tomllib.TOMLDecodeError as e:
        logger.error(f"Invalid TOML in '{config_path}': {e}")
        return {}


# Load extensions once at module import (immutable)
EXTENSIONS = load_extensions()


def list_extensions() -> dict[str, list[str]]:
    """Return available extensions and their URLs."""
    return dict(EXTENSIONS)  # Return copy to prevent mutation

def list_components() -> dict[str, str]:
    """Return available components and their descriptions."""
    descs = {}
    for name, comp in vars(COMPONENTS).items():
        desc = ''
        if callable(comp) and comp.__doc__:
            doc = comp.__doc__.strip()
            paragraphs = doc.split('\n\n')
            # Collapse first paragraph into a single line
            desc = ' '.join(line.strip() for line in paragraphs[0].splitlines() if line.strip())
        descs[name] = desc
    return descs

# ============================================================================
# HTML BUILDER - Stateless builder for constructing HTML documents
# ============================================================================

@dataclass
class HTMLBuilder:
    lang: str = 'en'

    def render(self, content, extensions=None, extra_head=None, body_attrs=None):
        # Validate content type
        if not isinstance(content, (FT, tuple)):
            raise TypeError(
                f"content must be FT or tuple, got {type(content).__name__}"
            )
        
        # if already wrapped in Html
        if isinstance(content, FT) and content.tag == 'html':
            return content

        # if already wrapped in Head
        if (
            content 
            and isinstance(content, tuple)
            and content[0].tag == 'head'
        ):
            return Html(content[0], Body(content[1:]), lang=self.lang)

        # Build head elements
        head_elements = [
            Meta(charset='utf-8'),
            Meta(name='viewport', content='width=device-width, initial-scale=1.0')
        ]
        
        # Add extensions (CSS/JS from TOML)
        if extensions:
            head_elements.extend(self._build_extension_tags(extensions))
        
        # Add custom head elements
        if extra_head:
            head_elements.extend(extra_head)

        if isinstance(content, FT) and content.tag == 'body':
            return Html(Head(*head_elements), content, lang=self.lang)
        
        # Return complete HTML
        return Html(
            Head(*head_elements),
            Body(content),
            lang=self.lang
        )

    def _build_extension_tags(self, extension_names):
        tags = []
        
        for name in extension_names:
            if name not in EXTENSIONS:
                logger.warning(f"Extension '{name}' not found in config")
                continue
            
            for url in EXTENSIONS[name]:
                if not isinstance(url, str):
                    logger.warning(f"Invalid URL in extension '{name}': {url}")
                    continue
                
                if url.endswith('.css'):
                    tags.append(Link(rel='stylesheet', href=url))
                elif url.endswith('.js'):
                    tags.append(Script(src=url))
                else:
                    logger.warning(
                        f"Unknown file type in extension '{name}': {url}"
                    )
        
        return tags

# ============================================================================
# VIEW DECORATOR - Auto-render FT objects in Django views
# ============================================================================

def view(func):
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        
        # Auto-render FT objects
        if isinstance(result, (FT, tuple)):
            html_string = to_xml(result)
            return HttpResponse(html_string, content_type='text/html')
        
        # Pass through other responses (HttpResponse, JsonResponse, etc.)
        return result
    
    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    return wrapper

# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == '__main__':
    from fastcore.xml import Div

    # 1. Register components
    component('Footer', Div('© 2023 My Site', cls='footer'))
    
    @component('alert')
    def Alert(message: str, alert_type: str = 'info'):
        return Div(message, cls=f'alert alert-{alert_type}')
    
    @component('button')
    def Button(text: str, href: str = '#', **attrs):
        return FT(tag='a', children=[text], href=href, **attrs)
    
    # 2. Build HTML
    builder = HTMLBuilder(lang='en')
    
    content = Div(
        Alert('Welcome to the site!', alert_type='success'),
        Button('Click me', href='/action', cls='btn btn-primary'),
        Footer
    )
    
    html = builder.render(
        content=content,
        extensions=['bootstrap', 'sortjs'],
        extra_head=[
            Meta(name='author', content='John Doe'),
            Meta(name='description', content='Example site')
        ]
    )
    
    # 3. Render to string
    print(to_xml(html))
    
    # 4. List available extensions
    print("\nAvailable extensions:")
    for name, urls in list_extensions().items():
        print(f"  {name}: {len(urls)} files")
