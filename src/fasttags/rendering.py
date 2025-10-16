from html import escape as html_escape
from collections.abc import Iterable, Mapping
from typing import Generator
import logging
from .core import FastTag, SafeHtml, Element, CurativeError
from .utilities import as_json
from .attributes import to_attr
from .config import config
from .validation import HTMLValidator

def _to_xml(el: Element, escape=html_escape) -> Generator[str, None, None]:
    try:
        match el:
            case FastTag():
                tag = el.tag
                yield f'<{tag}'
                attrs = el.attrs
                if attrs:
                    yield ' '
                    yield ' '.join(filter(None, (to_attr(k, v) for k, v in attrs.items())))
                if el.void:
                    yield ' />'
                else:
                    yield '>'
                    for child in el.children:
                        yield from _to_xml(child, escape)
                    yield f'</{tag}>'
            case SafeHtml():
                yield el.__html__()
            case str():
                yield escape(el) if config.escape_by_default else el
            case bytes():
                yield el.decode('utf-8')
            case Mapping():
                yield as_json(el)
            case Iterable():
                for item in el:
                    yield from _to_xml(item, escape)
            case _:
                yield escape(str(el)) if config.escape_by_default else str(el)
    except Exception as e:
        logging.error(f"Rendering error: {e}")
        if config.auto_heal:
            logging.info("Healing: Skipping unrenderable element.")
            return  # Skip and continue
        else:
            raise

def to_xml(*contents: Element, escape=html_escape, newline='\n', validate: bool = False) -> str:
    validator = HTMLValidator()
    processed = contents
    if validate:
        processed = []
        for el in contents:
            mode = getattr(el, 'validate_mode', config.validate_mode)  # Use per-element or global
            healed = validator.validate_and_heal(el, mode)
            if healed is not None:
                processed.append(healed)

    parts = []
    for content in processed:
        parts.extend(_to_xml(content, escape))
    return newline.join(parts)

to_html = to_xml  # Alias

def tidy(html: str) -> str:
    try:
        # First, try to use lxml if installed
        from lxml.html import fromstring
        import lxml.etree
        
        # Parse and pretty print using lxml
        tree = fromstring(html)
        pretty_html = lxml.etree.tostring(tree, pretty_print=True, method="html").decode('utf-8')
        logging.info("Successfully used lxml for tidying HTML.")
        return pretty_html
    except ImportError:
        # lxml is not installed, fallback to Beautiful Soup
        try:
            from bs4 import BeautifulSoup
            logging.info("lxml not available; falling back to Beautiful Soup for tidying HTML.")
            return BeautifulSoup(html, 'html.parser').prettify()
        except ImportError:
            prescription = (
                "1. Install lxml: pip install lxml\n"
                "2. Or install beautifulsoup4: pip install beautifulsoup4\n"
                "3. Restart your Python environment.\n"
                "4. Alternatively, set config.auto_heal=True for a basic fallback indenter."
            )
            if config.auto_heal:
                logging.info("Healing: Using basic fallback tidy due to missing dependencies.")
                return '\n'.join(f"  {line}" for line in html.split('\n'))  # Simple indent fallback
            else:
                raise CurativeError("Missing modules: lxml or beautifulsoup4 for tidy functionality.", prescription)
    except Exception as e:  # Catch any other errors (e.g., parsing errors with lxml)
        logging.error(f"Error in tidy: {e}")
        if config.auto_heal:
            logging.info("Healing: Returning original HTML due to error.")
            return html  # Fallback to original HTML
        else:
            raise CurativeError(f"Error during tidy operation: {e}", "Ensure HTML is valid or dependencies are correctly installed.")

def highlight(html: str) -> str:
    try:
        import pygments
        from pygments.lexers import HtmlLexer
        from pygments.formatters import HtmlFormatter
        return pygments.highlight(html, HtmlLexer(), HtmlFormatter())
    except ModuleNotFoundError:
        prescription = (
            "1. Install pygments: pip install pygments\n"
            "2. Restart your Python environment.\n"
            "3. Alternatively, disable highlighting or use a fallback (no auto-heal available)."
        )
        if config.auto_heal:
            logging.info("Healing: Returning raw HTML due to missing pygments.")
            return html  # Fallback to plain HTML
        else:
            raise CurativeError("Missing module: pygments for highlight functionality.", prescription)

def showtags(html: str) -> str:
    # Simple placeholder to show tags, can be improved
    return html
