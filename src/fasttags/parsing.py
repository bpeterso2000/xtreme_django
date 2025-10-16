"""Utilities for parsing and converting HTML to FastTag expressions or objects.

This module provides tools for one-time conversion of HTML strings to FastTag (FT) representations,
suitable for prototyping migration to production templates (e.g., Django). It integrates with FastTags'
validation and healing features for robustness.

Key Functions:
- normalize_coll: Unified utility for converting inputs to tuples or lists.
- html2ft: Convert HTML to FT expression string or object, with optional validation.
"""

from typing import Any, Union, List, Tuple, Optional
import re
from collections.abc import Iterable, Generator
from functools import partial
from html import escape
from .core import FastTag, Element, CurativeError, HTML_TAGS, ft
from .utilities import flatten
from .config import config
from .validation import HTMLValidator
from .attributes import attrmap, keymap  # Reused for attribute mapping
try:
    from bs4 import BeautifulSoup, Comment
except ModuleNotFoundError as e:
    raise CurativeError(
        "Missing module: beautifulsoup4 for HTML parsing.",
        "1. Install beautifulsoup4: pip install beautifulsoup4\n"
        "2. Restart your Python environment.\n"
        "3. If issues persist, check for conflicts in your virtualenv."
    ) from e

# Simplified predicates (no NumPy/PyTorch support)
def is_iter(obj: Any) -> bool:
    """Check if obj is iterable (e.g., list, generator, but not str/bytes)."""
    return isinstance(obj, (Iterable, Generator)) and not isinstance(obj, (str, bytes))

def is_coll(obj: Any) -> bool:
    """Check if obj is a collection with a usable len() (e.g., list, tuple)."""
    return hasattr(obj, '__len__')

# Unified conversion function (merges to_tuple, listify, tuplify for DRY)
def normalize_coll(input_obj: Any, to_type: str = 'tuple', match_len: Optional[int] = None) -> Union[Tuple[Any, ...], List[Any]]:
    """
    Normalize input_obj to a tuple or list, handling various types.

    Args:
        input_obj: Object to normalize (e.g., None, str, iterable).
        to_type: 'tuple' (default) or 'list'.
        match_len: If set, expand or assert length matches this value.

    Returns:
        Tuple or list based on to_type.

    Raises:
        TypeError: For unhandled types.
        CurativeError: If match_len mismatch and no healing.

    Examples:
        >>> normalize_coll(None)
        ()
        >>> normalize_coll('ab')
        ('ab',)
        >>> normalize_coll([1, 2], to_type='list')
        [1, 2]
        >>> normalize_coll(42, match_len=3)
        (42, 42, 42)
    """
    match input_obj:
        case None:
            result = []
        case str() | bytes():
            result = [input_obj]
        case _ if is_iter(input_obj):
            result = list(flatten(input_obj))  # Reuse FastTags' flatten for DRY
        case _:
            raise TypeError(f"Unhandled type: {type(input_obj).__name__}. Supported: None, str/bytes, iterables.")

    if match_len is not None:
        if len(result) == 1:
            result = result * match_len
        elif len(result) != match_len:
            prescription = (
                f"1. Adjust input to have exactly {match_len} elements.\n"
                "2. If intentional, remove match_len or set to None.\n"
                "3. Enable config.auto_heal for automatic truncation/extension (not recommended)."
            )
            if config.auto_heal:
                logging.warning(f"Healing: Truncating/extending collection to match length {match_len}.")
                if len(result) < match_len:
                    result += [None] * (match_len - len(result))  # Pad with None (safe default)
                else:
                    result = result[:match_len]
            else:
                raise CurativeError(f"Length mismatch: Got {len(result)}, expected {match_len}.", prescription)

    return tuple(result) if to_type == 'tuple' else result

# Simplified risinstance (curried isinstance with mro support for string types)
def risinstance(types: Union[str, type, Tuple[Union[str, type], ...]], obj: Any = None) -> bool:
    """Curried isinstance with support for string type names and mro checks."""
    types = normalize_coll(types, to_type='tuple')  # Use our normalizer for DRY
    def _check(o: Any) -> bool:
        if any(isinstance(t, str) for t in types):
            return any(t in (cls.__name__ for cls in type(o).__mro__))
        return isinstance(o, types)
    return _check(obj) if obj is not None else _check

# Regex for valid attribute keys
_re_h2x_attr_key = re.compile(r'^[A-Za-z_-][\w-]*$')

# Unsafe tags for warnings (common injection vectors)
_UNSAFE_TAGS = {'script', 'iframe', 'object', 'embed', 'link'}  # link for rel="import"

def html2ft(html: Union[str, bytes], attr1st: bool = False, validate: Optional[bool] = None, 
            heal_parsing: Optional[bool] = None, strict: str = 'warn', 
            raw_embedded: bool = False, quiet_unsafe: bool = False, 
            return_obj: bool = False) -> Union[str, FastTag, Tuple[FastTag, ...], None]:
    """
    Convert HTML string to a FastTag (FT) expression or object.

    Args:
        html: Input HTML string or bytes (auto-decoded to utf-8).
        attr1st: If True, place attributes before children in output string.
        validate: Override global; if True, run FastTags validation/healing.
        heal_parsing: If True, attempt healing on parse failures (separate from global auto_heal).
        strict: 'ignore' (silent), 'raise' (error), 'warn' (log/comment), 'heal' (fix); default 'warn'.
        raw_embedded: If True, disable auto-escaping of embedded content (e.g., scripts).
        quiet_unsafe: If True, suppress warnings for unsafe tags (e.g., <script>).
        return_obj: If True, return FT object/tuple (multi-root) or None (empty).

    Returns:
        str (FT expression), FastTag (single), Tuple[FastTag] (multi-root), or None (empty).

    Raises:
        CurativeError: On failures (based on strict), with fix suggestions.

    Examples:
        >>> html2ft('<div><h1>Hello</h1></div>')
        'Div(H1('Hello'))'
        >>> html2ft('<p>Text</p><div>More</div>', return_obj=True)  # Multi-root
        (P('Text'), Div('More'))
    """
    if isinstance(html, bytes):
        try:
            html = html.decode('utf-8')
        except UnicodeDecodeError as e:
            raise CurativeError(f"Bytes decoding failed: {e}", "1. Provide UTF-8 encoded bytes.\n2. Specify a different encoding if known.\n3. Convert to str before calling.") from e
    if not isinstance(html, str) or not html.strip():
        if strict == 'raise':
            raise CurativeError("Invalid input: html must be a non-empty string.", "1. Provide valid HTML.\n2. Check for empty inputs.")
        elif strict == 'warn':
            logging.warning("Empty or invalid input; returning None.")
        return None if return_obj else ''

    # Use heal_parsing (override) or fallback to ignore/warn if global auto_heal=True
    effective_heal = heal_parsing if heal_parsing is not None else False
    if heal_parsing is None and config.auto_heal:
        logging.warning("Global auto_heal is True, but heal_parsing not set; ignoring healing for parsing.")
        effective_heal = False  # Ignore and warn per your spec

    soup = None
    try:
        # Auto-detect SVG for parser mode switch (if lxml available)
        parser_features = 'html.parser'
        try:
            import lxml  # Optional
            if re.search(r'<svg', html, re.I):  # Simple pre-check for SVG
                parser_features = 'lxml-xml'  # XML mode for case/namespace preservation
        except ImportError:
            if re.search(r'<svg', html, re.I):
                logging.warning("SVG detected but lxml not installed; using html.parser (case/namespaces may not preserve perfectly).")
                if strict == 'raise':
                    raise CurativeError("lxml required for optimal SVG handling.", "1. Install lxml: pip install lxml\n2. Rerun conversion.")

        soup = BeautifulSoup(html.strip(), parser_features)
    except Exception as bs_error:
        if effective_heal:
            logging.warning(f"Parsing failed: {bs_error}. Attempting curative fallback.")
            fallback_result = _curative_fallback_parse(html)
            if fallback_result:
                soup = fallback_result
            elif strict == 'raise':
                raise CurativeError(f"Parsing failed even with fallback: {bs_error}", _get_detailed_prescription(bs_error)) from bs_error
            elif strict == 'warn':
                return f"# WARNING: Parsing failed; empty result.\n()"
            else:  # ignore or heal (but failed)
                return None if return_obj else '()'
        elif strict == 'raise':
            raise CurativeError(f"HTML parsing failed: {bs_error}", _get_detailed_prescription(bs_error)) from bs_error
        elif strict == 'warn':
            return f"# WARNING: Parsing failed; empty result.\n()"
        else:
            return None if return_obj else '()'

    # Remove comments
    for c in soup.find_all(string=risinstance(Comment)):
        c.extract()

    # Warn on unsafe tags if not quiet
    if not quiet_unsafe:
        for tag in _UNSAFE_TAGS:
            if soup.find(tag):
                logging.warning(f"Unsafe tag '{tag}' detected in HTML; potential security risk if output is rendered dynamically.")

    # Internal parsing helpers
    def _parse_children(cts: list, lvl: int, raw_embedded: bool) -> list[str]:
        """Parse children recursively, with optional escaping."""
        def process_content(c):
            if isinstance(c, str) and c.strip():
                return repr(escape(c.strip()) if not raw_embedded else c.strip())
            return _parse_element(c, lvl + 1, raw_embedded)
        return [process_content(c) for c in cts if str(c).strip()]

    def _parse_attrs(elm_attrs: dict) -> list[str]:
        """Parse and map attributes using FastTags' attrmap/keymap for DRY."""
        mapped_attrs = attrmap(elm_attrs)  # Reuse FastTags' attrmap
        attrs, exotic_attrs = [], {}
        for key, value in sorted(mapped_attrs.items(), key=lambda x: x[0] == 'class'):
            if isinstance(value, (tuple, list)):
                value = " ".join(value)
            # Use keymap for any additional mapping if needed (DRY)
            key = keymap(key)
            value = value or True
            if _re_h2x_attr_key.match(key):
                attrs.append(f'{key.replace("-", "_")}={value!r}')  # Underscore for Python
            else:
                exotic_attrs[key] = value
        if exotic_attrs:
            attrs.append(f'**{exotic_attrs!r}')
        return attrs

    def _parse_element(elm, lvl: int, indent: int = 4, raw_embedded: bool = False) -> str:
        """Parse a single element recursively."""
        if isinstance(elm, str):
            return repr(escape(elm.strip()) if not raw_embedded else elm.strip()) if elm.strip() else ''
        if isinstance(elm, list):
            return '\n'.join(_parse_element(o, lvl, raw_embedded) for o in elm)
        if elm.name == '[document]':
            return _parse_element(list(elm.children), lvl, raw_embedded)

        tag_name = elm.name.capitalize().replace("-", "_")  # Pythonic tag name
        cts = elm.contents
        cs = _parse_children(cts, lvl, raw_embedded)
        attrs = _parse_attrs(elm.attrs)

        spc = " " * lvl * indent
        onlychild = not cts or (len(cts) == 1 and isinstance(cts[0], str))
        j = ', ' if onlychild else f',\n{spc}'

        inner = j.join(filter(None, cs + attrs))
        if onlychild:
            if not attr1st:
                return f'{tag_name}({inner})'
            else:
                attrs_str = ', '.join(filter(None, attrs))
                return f'{tag_name}({attrs_str})({cs[0] if cs else ""})'
        if not attr1st or not attrs:
            return f'{tag_name}(\n{spc}{inner}\n{" " * (lvl - 1) * indent})'
        inner_cs = j.join(filter(None, cs))
        inner_attrs = ', '.join(filter(None, attrs))
        return f'{tag_name}({inner_attrs})(\n{spc}{inner_cs}\n{" " * (lvl - 1) * indent})'

    # Parse to list of expressions (for multi-root support)
    parsed_exprs = [_parse_element(child, 1, raw_embedded) for child in soup.children if str(child).strip()]

    if not parsed_exprs:
        return None if return_obj else '()'

    result_str = f"({' , '.join(parsed_exprs)})" if len(parsed_exprs) > 1 else parsed_exprs[0]

    # Add warnings as prefixed comments if strict='warn'
    if strict == 'warn' and not quiet_unsafe:
        warning_comment = "# WARNING: Unsafe tags detected (e.g., script/iframe); review for security.\n"
        result_str = warning_comment + result_str

    if return_obj:
        try:
            # Safely eval to list of FT objects (restricted globals)
            result_list = eval(f"[{', '.join(parsed_exprs)}]", {"__builtins__": {}}, {"ft": ft, **{t: partial(ft, t.lower()) for t in HTML_TAGS}})
            if validate or (validate is None and config.enable_validation):
                validator = HTMLValidator()
                result_list = [validator.validate_and_heal(el, config.validate_mode) for el in result_list if el]

            if not result_list:
                return None
            elif len(result_list) == 1:
                return result_list[0]  # Unwrap single
            else:
                return tuple(result_list)  # Multi-root tuple
        except Exception as e:
            if strict == 'raise':
                raise CurativeError(f"Failed to convert to FT object: {e}", "1. Check generated expression for syntax.\n2. Ensure valid HTML input.\n3. Disable return_obj and inspect string output.") from e
            elif strict == 'warn':
                return f"# WARNING: Eval failed; returning empty.\n()"
            else:
                return None
    else:
        return result_str

def _curative_fallback_parse(html: str) -> Optional[BeautifulSoup]:
    """Curative fallback parser using FastTags' validation modes if BeautifulSoup fails."""
    # Always try html5lib first (per spec)
    try:
        import html5lib
        parser = html5lib.HTMLParser()
        document = parser.parse(html)
        return BeautifulSoup(document.toxml(), 'html.parser')
    except ModuleNotFoundError:
        logging.warning("html5lib not installed; skipping to next fallback.")
    except Exception as e:
        logging.error(f"html5lib fallback failed: {e}")

    # Next, try config mode if not html5lib
    mode = config.validate_mode
    if mode == 'w3c':
        try:
            import requests
            url = "https://validator.w3.org/nu/"
            params = {"out": "json"}
            headers = {"Content-Type": "text/html; charset=utf-8"}
            response = requests.post(url, params=params, data=html.encode('utf-8'), headers=headers)
            if response.status_code == 200:
                results = response.json()
                errors = [msg['message'] for msg in results.get('messages', []) if msg['type'] == 'error']
                if errors:
                    error_msg = "\n".join(errors)
                    raise CurativeError(
                        f"W3C validation detected errors: {error_msg}",
                        "1. Fix the reported issues in your HTML.\n"
                        "2. Re-run html2ft after corrections.\n"
                        "3. Switch to a different validate_mode for tolerant parsing."
                    )
                # If no errors, retry BeautifulSoup
                return BeautifulSoup(html.strip(), 'html.parser')
            return None
        except Exception as e:
            logging.error(f"W3C fallback failed: {e}")
            return None

    # For 'static' or 'none', no fallback
    return None

def _get_detailed_prescription(error: Exception) -> str:
    """Generate detailed prescription for parsing errors."""
    base = "1. Verify HTML syntax.\n2. Install/update beautifulsoup4.\n3. Enable heal_parsing for fallback.\n4. Simplify input HTML."
    scenarios = (
        " - Unbalanced tags: Add missing closing tags (e.g., </div>).\n"
        " - Invalid characters: Encode special entities (e.g., & to &amp;).\n"
        " - Nested errors: Check for improper nesting (e.g., <div> inside <p>).\n"
        " - Attribute syntax: Fix invalid attributes (e.g., missing quotes around values).\n"
        " - Doctype issues: Add or correct <!DOCTYPE html>.\n"
        " - SVG-specific: Verify namespaces (e.g., xmlns for <svg>).\n"
        " - General: Validate input at https://validator.w3.org/ or simplify HTML."
    )
    return base + "\nCommon scenarios:\n" + scenarios

# html2ft is the main export; others are internal
__all__ = ['html2ft']
