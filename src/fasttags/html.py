from .core import 

try:
    import black
    BLACK_INSTALLED = True
except ImportError:
    BLACK_INSTALLED = False

def html2ft(html: str, attr1st: bool = False, format_black: bool = False) -> str:
    """Convert HTML to an `ft` expression with improved readability and structure."""

    if not BEAUTIFUL_SOUP_INSTALLED:
        raise ImportError("BeautifulSoup is required for html2ft. Install with `pip install beautifulsoup4`")

    rev_map = {'class': 'cls', 'for': 'fr'}
    _re_attr_key = re.compile(r'^[A-Za-z_-][\w-]*$')

    def _parse(elm) -> str:
        # Handle string nodes
        if isinstance(elm, str):
            stripped = elm.strip()
            return repr(stripped) if stripped else ''

        # Handle list of elements
        if isinstance(elm, list):
            parsed = [_parse(child) for child in elm]
            filtered = list(filter(None, parsed))
            if not filtered:
                return ''
            joined = ', '.join(filtered)
            if len(filtered) == 1:
                return filtered[0]
            return f'({joined})'

        # Capitalize tag and replace dashes with underscores
        tag_name = elm.name.capitalize().replace(DASH, UNDERSCORE)

        # Special case for document root
        if tag_name == '[document]':
            return _parse(list(elm.children))

        # Process children content
        children = elm.contents
        parsed_children = [
            repr(c.strip()) if isinstance(c, str) else _parse(c)
            for c in children if str(c).strip()
        ]

        # Process attributes
        attrs = []
        exotic_attrs = {}
        # Sort attributes, prioritizing non-'class' first
        sorted_attrs = sorted(elm.attrs.items(), key=lambda x: x[0] == 'class')
        for key, value in sorted_attrs:
            if isinstance(value, (tuple, list)):
                value = " ".join(value)
            key_mapped = rev_map.get(key, key)
            value = value or True
            if _re_attr_key.match(key_mapped):
                attr_key = key_mapped.replace(DASH, UNDERSCORE)
                attrs.append(f'{attr_key}={value!r}')
            else:
                exotic_attrs[key_mapped] = value

        # Add exotic attributes as **kwargs
        if exotic_attrs:
            attrs.append(f'**{exotic_attrs!r}')

        # Determine if only child
        only_child = not children or (len(children) == 1 and isinstance(children[0], str))

        # Combine children and attributes
        inner = ', '.join(filter(None, parsed_children + attrs))

        # Format output based on presence of attributes and attr1st flag
        if only_child:
            if not attr1st:
                return f'{tag_name}({inner})'
            else:
                attrs_str = ', '.join(filter(None, attrs))
                child_str = parsed_children[0] if parsed_children else ""
                return f'{tag_name}({attrs_str})({child_str})'

        if not attr1st or not attrs:
            return f'{tag_name}({inner})'

        inner_children = ', '.join(filter(None, parsed_children))
        inner_attrs = ', '.join(filter(None, attrs))
        return f'{tag_name}({inner_attrs})({inner_children})'

    soup = BeautifulSoup(html.strip(), 'html.parser')
    # Remove comments
    for comment in soup.find_all(string=risinstance(Comment)):
        comment.extract()

    code = _parse(soup)
    if format_black:
        if BLACK_INSTALLED:
            code = black.format_str(code, mode=black.Mode())
        else:
            print("Black is not installed. Install with `pip install black` to format the code.", file=sys.stderr)

    return code
