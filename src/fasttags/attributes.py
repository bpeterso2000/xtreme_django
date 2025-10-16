from collections.abc import Mapping, Iterable
from .core import AttrValue, SafeHtml
from .utilities import add_quotes

SPECIAL_CHARS = {'-', ':', '.'}

def keymap(key: str) -> str:
    if not key:
        return '_'
    if key.startswith('_'):
        key = key[1:]
    if key == 'cls':
        return 'class'
    if any(c in key for c in SPECIAL_CHARS):
        return key
    return key.replace('_', '-')

def attrmap(attrs: dict[str, object]) -> dict[str, object]:
    return {keymap(k): v for k, v in attrs.items()}

def to_attr(key: str, value: AttrValue) -> str:
    match value:
        case False | None | '':
            return ''
        case True:
            return key
        case str():
            val = value
        case SafeHtml():
            val = value.__html__()
        case Mapping():
            val = '; '.join(f'{k}:{v}' for k, v in value.items())
        case Iterable():
            val = ' '.join(str(i) for i in value)
        case _:
            val = str(value)
    return f'{key}={add_quotes(val)}' if val else ''

def to_attrs(attrs: dict[str, AttrValue]) -> str:
    return ' '.join(filter(None, (to_attr(k, v) for k, v in attrs.items())))
