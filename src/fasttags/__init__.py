from .core import *
from .elements import FT, ft, HTML_TAGS, VOID_ELEMENTS
from .attributes import keymap, attrmap, to_attr, to_attrs
from .rendering import to_xml, to_html, tidy, highlight, showtags
from .utilities import flatten, as_json, add_quotes
from .validation import warn_void_override
from .parsing import html2ft
from .config import config

# Do NOT import HTML tags here to avoid namespace pollution

__all__ = [
    'FastTag', 'SafeHtml', 'FT', 'ft', 'HTML_TAGS', 'VOID_ELEMENTS',
    'keymap', 'attrmap', 'to_attr', 'to_attrs',
    'to_xml', 'to_html', 'tidy', 'highlight', 'showtags',
    'flatten', 'as_json', 'add_quotes',
    'warn_void_override', 'html2ft', 'config',
]
