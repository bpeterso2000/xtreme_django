from typing import Protocol, runtime_checkable, Iterable, Mapping, Sequence, Union

@runtime_checkable
class FastTag(Protocol):
    tag: str
    children: list['Element']
    attrs: dict[str, 'AttrValue']
    void: bool
    def __ft__(self) -> str: ...

@runtime_checkable
class SafeHtml(Protocol):
    def __html__(self) -> str: ...

Primitive = Union[str, int, float, bool, None]
Json = Union[Primitive, Sequence['Json'], Mapping[Primitive, 'Json']]
JsonSerializable = Mapping[Primitive, Json]

Element = Union[
    FastTag, SafeHtml, str, bytes, JsonSerializable,
    Iterable['Element'], object
]

AttrValue = Union[
    None, bool, str, SafeHtml, Iterable[object], Mapping[Primitive, object], object
]

# HTML5 tags (capitalized)
HTML_TAGS = {
    "A", "Abbr", "Address", "Area", "Article", "Aside", "Audio", "B", "Base",
    "Bdi", "Bdo", "Blockquote", "Body", "Br", "Button", "Canvas", "Caption",
    "Cite", "Code", "Col", "Colgroup", "Data", "Datalist", "Dd", "Del", "Details",
    "Dfn", "Dialog", "Div", "Dl", "Dt", "Em", "Embed", "Fieldset", "Figcaption",
    "Figure", "Footer", "Form", "H1", "H2", "H3", "H4", "H5", "H6", "Head",
    "Header", "Hr", "Html", "I", "Iframe", "Img", "Input", "Ins", "Kbd", "Label",
    "Legend", "Li", "Link", "Main", "Map", "Mark", "Meta", "Meter", "Nav",
    "Noscript", "Object", "Ol", "Optgroup", "Option", "Output", "P", "Param",
    "Picture", "Pre", "Progress", "Q", "Rp", "Rt", "Ruby", "S", "Samp", "Script",
    "Section", "Select", "Small", "Source", "Span", "Strong", "Style", "Sub",
    "Summary", "Sup", "Table", "Tbody", "Td", "Template", "Textarea", "Tfoot",
    "Th", "Thead", "Time", "Title", "Tr", "Track", "U", "Ul", "Var", "Video", "Wbr"
}

# Void elements (self-closing)
VOID_ELEMENTS = {
    "Area", "Base", "Br", "Col", "Embed", "Hr", "Img", "Input",
    "Link", "Meta", "Param", "Source", "Track", "Wbr"
}

class CurativeError(Exception):
    """Custom error with prescription for healing."""
    def __init__(self, message: str, prescription: str):
        super().__init__(f"{message}\n\nPrescription:\n{prescription}")
