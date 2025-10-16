import warnings
import logging
import difflib  # Built-in for fuzzy matching
from .core import FastTag, Element, HTML_TAGS, VOID_ELEMENTS, CurativeError
from .config import config
from .rendering import to_xml  # For dynamic validation rendering

# Global attributes allowed on all elements
GLOBAL_ATTRS = {
    'accesskey', 'class', 'contenteditable', 'dir', 'draggable', 'hidden', 'id',
    'lang', 'spellcheck', 'style', 'tabindex', 'title', 'translate'
}

# Expanded static allowlist (from MDN/WHATWG; add more as needed)
VALID_ATTRS = {
    'img': {'alt', 'crossorigin', 'decoding', 'height', 'ismap', 'loading', 'referrerpolicy', 'sizes', 'src', 'srcset', 'usemap', 'width'},
    'a': {'download', 'href', 'hreflang', 'ping', 'referrerpolicy', 'rel', 'target', 'type'},
    'div': set(),  # Only globals
    'input': {'accept', 'alt', 'autocomplete', 'autofocus', 'capture', 'checked', 'dirname', 'disabled', 'form', 'formaction', 'formenctype', 'formmethod', 'formnovalidate', 'formtarget', 'height', 'list', 'max', 'maxlength', 'min', 'minlength', 'multiple', 'name', 'pattern', 'placeholder', 'readonly', 'required', 'size', 'src', 'step', 'type', 'value', 'width'},
    'script': {'async', 'charset', 'crossorigin', 'defer', 'integrity', 'nomodule', 'nonce', 'referrerpolicy', 'src', 'type'},
    'link': {'as', 'crossorigin', 'href', 'hreflang', 'imagesizes', 'imagesrcset', 'integrity', 'media', 'prefetch', 'referrerpolicy', 'rel', 'sizes', 'title', 'type'},
    # Expand with more tags
}

def warn_void_override(tag: str, user_void: bool, expected_void: bool):
    if user_void != expected_void:
        warnings.warn(
            f"Tag '{tag}' is {'void' if expected_void else 'not void'}, "
            f"but void={user_void} was specified. This may produce invalid HTML.",
            UserWarning
        )

class HTMLValidator:
    def validate_and_heal(self, el: Element, mode: str = 'none') -> Element:
        """Validate and optionally heal based on mode: 'none', 'static', 'html5lib', 'w3c'."""
        if mode == 'none':
            return el

        match el:
            case FastTag():
                # Check invalid tag
                if el.tag.title() not in HTML_TAGS:
                    logging.warning(f"Invalid tag '{el.tag}' detected.")
                    if config.auto_heal:
                        logging.info(f"Healing: Dropping invalid tag '{el.tag}'.")
                        return None

                # Mode-specific attribute validation with fuzzy healing
                valid_attrs = {}
                for k, v in list(el.attrs.items()):  # Copy to avoid modification during iteration
                    if self.is_valid_attr(k, el.tag, mode):
                        valid_attrs[k] = v
                    else:
                        if config.auto_heal:
                            healed_key = self.fuzzy_heal_attr(k, el.tag, mode)
                            if healed_key:
                                valid_attrs[healed_key] = v
                                logging.info(f"Healing: Replaced '{k}' with fuzzy match '{healed_key}' in '{el.tag}'.")
                            else:
                                logging.info(f"Healing: Dropped invalid attribute '{k}' from '{el.tag}'.")
                        else:
                            logging.warning(f"Invalid attribute '{k}' in '{el.tag}'.")

                el.attrs = valid_attrs

                # Recurse on children
                healed_children = [self.validate_and_heal(child, mode) for child in el.children if child is not None]
                el.children = healed_children

                return el

            case _:
                return el

    def is_valid_attr(self, attr: str, tag: str, mode: str) -> bool:
        if attr.startswith('data-') or attr in GLOBAL_ATTRS:
            return True

        if mode == 'static':
            return tag in VALID_ATTRS and attr in VALID_ATTRS[tag]

        if mode == 'html5lib':
            try:
                import html5lib
                # Render minimal test HTML and parse strictly
                test_html = f'<{tag} {attr}="test"></{tag}>' if tag not in VOID_ELEMENTS else f'<{tag} {attr}="test">'
                parser = html5lib.HTMLParser(strict=True)
                parser.parseFragment(test_html)
                return True
            except ModuleNotFoundError:
                prescription = (
                    "1. Install html5lib: pip install html5lib\n"
                    "2. Restart your Python environment.\n"
                    "3. Alternatively, switch to 'static' mode or set config.auto_heal=True for fallback."
                )
                if config.auto_heal:
                    logging.warning("Healing: Falling back to static validation due to missing html5lib.")
                    return self.is_valid_attr(attr, tag, 'static')
                else:
                    raise CurativeError("Missing module: html5lib for 'html5lib' validation mode.", prescription)
            except html5lib.html5parser.ParseError:
                return False

        if mode == 'w3c':
            try:
                import requests
                # Render minimal test HTML
                test_html = f'<{tag} {attr}="test"></{tag}>' if tag not in VOID_ELEMENTS else f'<{tag} {attr}="test">'
                url = "https://validator.w3.org/nu/"
                params = {"out": "json"}
                headers = {"Content-Type": "text/html; charset=utf-8"}
                response = requests.post(url, params=params, data=test_html.encode('utf-8'), headers=headers)
                if response.status_code == 200:
                    results = response.json()
                    errors = [msg for msg in results.get('messages', []) if msg['type'] == 'error']
                    return not errors  # Valid if no errors
                return False
            except ModuleNotFoundError:
                prescription = (
                    "1. Install requests: pip install requests\n"
                    "2. Restart your Python environment.\n"
                    "3. Alternatively, switch to 'static' or 'html5lib' mode or set config.auto_heal=True for fallback.\n"
                    "See https://validator.w3.org/docs/api.html for more info."
                )
                if config.auto_heal:
                    logging.warning("Healing: Falling back to static validation due to missing requests.")
                    return self.is_valid_attr(attr, tag, 'static')
                else:
                    raise CurativeError("Missing module: requests for 'w3c' validation mode.", prescription)
            except Exception as e:
                logging.error(f"W3C validation error: {e}")
                return True  # Assume valid on failure to avoid false negatives

        return True  # Default to allow if mode invalid
