from functools import partial
from .core import FastTag, Element, HTML_TAGS, VOID_ELEMENTS
from .attributes import attrmap, keymap
from .utilities import flatten
from .validation import warn_void_override
from .rendering import to_xml

class FT:
    internal_attrs = {
        'tag', 'children', 'attrs', 'void', 'validate_mode',
        'list', 'get', 'set',
        '__getitem__', '__setitem__', '__iter__', '__call__',
        '__repr__', '__str__', '__html__', '__ft__',
    }

    def __init__(self, tag: str, *contents: Element, void: bool = False, validate_mode: str = 'none', **attrs):
        self.tag = tag.lower()
        expected_void = tag.title() in VOID_ELEMENTS
        if void != expected_void:
            warn_void_override(tag, void, expected_void)
        self.void = void
        self.validate_mode = validate_mode  # Per-instance mode
        self.children = flatten(contents)
        self.attrs = attrmap(attrs)

    def __setattr__(self, key, val):
        if key in FT.internal_attrs:
            super().__setattr__(key, val)
        else:
            self.attrs[keymap(key)] = val

    def __getattr__(self, key):
        return self.attrs.get(keymap(key))

    def __html__(self):
        return to_xml(self)

    __str__ = __ft__ = __html__

    def __repr__(self):
        return f"{self.tag}({tuple(self.children)}, {self.attrs})"

    def __iter__(self):
        return iter(self.children)

    def __getitem__(self, idx):
        return self.children[idx]

    def __setitem__(self, idx, el):
        self.children = self.children[:idx] + flatten(el) + self.children[idx + 1:]

    def __call__(self, *children: Element, **attrs):
        if children:
            self.children += flatten(children)
        if attrs:
            self.attrs.update(attrmap(attrs))
        return self

    def set(self, *children: Element, keep_attrs: set = frozenset({'id', 'name'}), **attrs):
        if children:
            self.children = flatten(children)
        if attrs:
            preserved = {k: self.attrs[k] for k in keep_attrs if k in self.attrs}
            self.attrs = {**preserved, **attrmap(attrs)}
        return self

    @property
    def list(self):
        return [self.tag, tuple(self.children), self.attrs]

    @property
    def html(self):
        return self.__ft__()

    @property
    def tidy(self):
        from .rendering import tidy
        return tidy(self.html)

    @property
    def highlight(self):
        from .rendering import highlight
        return highlight(self.tidy)

    @property
    def showtags(self):
        from .rendering import showtags
        return showtags(self.tidy)

def ft(*args, **kwargs):
    return FT(*args, **kwargs)
