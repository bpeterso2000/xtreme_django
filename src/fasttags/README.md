<think>
First, the user wants me to update the README with information about the tidy function. The provided README is a long string, and I need to incorporate details about the updated `tidy()` function.

Key points from the updated `tidy()` function:
- It now tries to use lxml first for pretty-printing if installed.
- Falls back to Beautiful Soup if lxml fails (e.g., not installed).
- If neither is installed, it uses a basic fallback if auto_heal is enabled.
- This enhances performance and provides a fallback mechanism.

Where in the README to add this?
- The README has a section called "## Rendering" which already mentions:
  - `tidy(html): Pretty-print (uses BeautifulSoup if installed; basic fallback if healing enabled).`
- I should update this description to reflect the new behavior.

Possible updates:
- In the "## Rendering" section, replace or expand the line for `tidy(html)`.
- Also, in the "Installation" section under "Optional Dependencies", add lxml since it's now a dependency for tidy.

Updated description for tidy:
- Original: "Pretty-print (uses BeautifulSoup if installed; basic fallback if healing enabled)."
- New: "Pretty-print HTML using lxml if available (for better performance), falling back to BeautifulSoup if installed, or a basic fallback if healing is enabled."

In the "API Reference" under "Rendering (rendering.py)", there's a line for `tidy(html): Prettify HTML.`, which I can update similarly.

Ensure the README remains coherent. Don't add unnecessary sections; just integrate the info.

Final structure:
- Update the "## Rendering" section.
- Update the "API Reference" if needed.
- In "Installation", add lxml to optional dependencies.

The user provided the README twice at the end, but it's the same content. I'll work with the full text.

Output the entire updated README for clarity.
</think>Below is the updated README file with the necessary information about the `tidy()` function incorporated. I've made the following changes for accuracy and completeness:

### Key Updates:
- **In the "Installation" section:** Added `lxml` to the optional dependencies list, as it's now the primary option for the `tidy()` function.
- **In the "Rendering" section:** Updated the description of the `tidy()` function to reflect its new behavior: it first attempts to use lxml for better performance, falls back to Beautiful Soup if lxml is not installed, and uses a basic fallback if neither is available and auto-healing is enabled.
- **In the "API Reference" under "Rendering (rendering.py)":** Updated the description of `tidy(html)` to match the new implementation.
- **Rationale:** These changes ensure the documentation is current, highlighting the improved functionality, dependencies, and fallback logic without altering the overall structure or adding unnecessary content.

Here's the full updated README:

---

# FastTags Documentation

FastTags is a comprehensive Python toolkit for rapidly composing HTML content programmatically in a structured, safe, and type-safe manner. It leverages functional composition, chaining, generator types, and protocols to build complex HTML structures efficiently. Inspired by and integral to frameworks like FastHTML (as described in the [FastHTML Components documentation](https://fastht.ml/about/components)), FastTags enables the creation of reusable, component-based HTML elements that can be easily integrated into web applications. It emphasizes error prevention and recovery through validation, auto-healing, and prescriptive error handling, making it ideal for dynamic web development where robustness is key.

## Table of Contents
- [Overview](#overview)
- [Installation](#installation)
- [Quickstart](#quickstart)
- [Core Concepts](#core-concepts)
- [Configuration](#configuration)
- [Validation and Healing](#validation-and-healing)
- [Rendering](#rendering)
- [Utilities](#utilities)
- [API Reference](#api-reference)
- [Advanced Usage: Building Components](#advanced-usage-building-components)
- [Prototyping and Production Migration](#prototyping-and-production-migration)
- [Contributing and Maintenance](#contributing-and-maintenance)

## Overview
FastTags provides a fluent interface for generating HTML5 elements, with built-in support for automatic escaping, attribute mapping, and nested structures. As highlighted in the FastHTML components guide, FastTags treats HTML generation as a functional process where components are Python functions returning FastTag objects. This allows for reusable, composable UI elements (e.g., a "card" component that combines `Div`, `H2`, and `P` tags).

Key features:
- **Type-Safe Element Creation**: Factory functions for all standard HTML5 elements.
- **Fluent Chaining**: Build and modify structures dynamically.
- **Validation Modes**: Check against static lists, html5lib, or W3C API.
- **Curative Design**: Auto-healing for errors (e.g., fuzzy matching typos) and prescriptive error messages.
- **Integration with FastHTML**: Use FastTags to define server-side components that render to HTML, enabling rapid web app development without JavaScript.
- **Modular and Extensible**: Separate concerns for core, validation, rendering, etc., with optional dependencies.

It targets Python 3.10+ and follows a "living standard" approach, similar to HTML itself, with tools to check and update validation rules.

## Installation
Install via pip (assuming the package is published; otherwise, install from source):

```bash
pip install fasttags
```

### Optional Dependencies
- For 'html5lib' validation: `pip install html5lib`
- For 'w3c' validation: `pip install requests`
- For tidy/pretty-print: `pip install lxml` (preferred for performance) or `pip install beautifulsoup4`
- For highlight: `pip install pygments`

## Quickstart
Import tags and create HTML structures or components:

```python
from fasttags.html import *  # Imports all tag factories (e.g., Div, Img)
from fasttags import to_xml, config

# Simple structure
div = Div(
    H1("Hello, FastTags!"),
    P("This is a paragraph.", cls="text"),
    Img(src="image.png", alt="An image")
)

# Render to HTML
html = to_xml(div)
print(html)
# Output: <div><h1>Hello, FastTags!</h1><p class="text">This is a paragraph.</p><img src="image.png" alt="An image" /></div>

# Component example (as per FastHTML concepts)
def card(title: str, content: str):
    return Div(
        H2(title),
        P(content),
        cls="card"
    )

my_card = card("My Title", "Some content")
print(to_xml(my_card))
# Output: <div class="card"><h2>My Title</h2><p>Some content</p></div>

# With validation and healing
config.enable_validation = True
config.validate_mode = 'static'
config.auto_heal = True
config.heal_fuzzy = True

# Invalid attr 'scr' (typo for 'src') will be fuzzy-healed to 'src'
img = Img(scr="image.png")
print(to_xml(img))
# Logs healing message and outputs: <img src="image.png" />
```

## Core Concepts
- **FT Class**: The core implementation for HTML elements. Create via `ft(tag, *children, **attrs)` or tag factories.
- **Tag Factories**: Bulk import from `fasttags.html import *` for convenience (e.g., `Div()`, `Span()`). These are partials of `ft` with void handling.
- **Attributes**: Python-friendly mapping (e.g., `cls="my-class"` → `class="my-class"`; underscores to hyphens).
- **Children**: Supports nested elements, strings, iterables; automatically flattened.
- **Void Elements**: Automatically self-closing (e.g., `Img()`); warnings for overrides.
- **Component-Based Design**: As per FastHTML docs, define functions returning FT objects for reusable UI components, promoting modularity and reuse in web apps.

## Configuration
Configure via the global `config` object (instance of `FastTagConfig`):

```python
from fasttags import config

config.enable_validation = True
config.validate_mode = 'html5lib'  # 'none', 'static', 'html5lib', 'w3c'
config.auto_heal = True
config.heal_fuzzy = True
config.escape_by_default = True
```

- Environment Variable: Set `FASTTAG_VALIDATE_MODE` for default mode.
- Per-Element: Pass `validate_mode` to `FT` constructor.

## Validation and Healing
Validation runs during rendering if `validate=True` in `to_xml`, checking attributes against the selected mode.

- **Modes**:
  - `'none'`: Skip validation (default).
  - `'static'`: Check against built-in allowlist (`VALID_ATTRS` + `GLOBAL_ATTRS`).
  - `'html5lib'`: Strict local parsing with html5lib (syntax-focused).
  - `'w3c'`: Comprehensive remote validation via W3C API.

- **Healing** (opt-in via `auto_heal`):
  - Drop invalid attributes/tags.
  - Fuzzy matching for typos (if `heal_fuzzy=True`): Uses edit distance to replace (e.g., 'scr' → 'src').

- **Allowlist Check**: Run `check_allowlist_current()` to verify `VALID_ATTRS` against MDN data and suggest updates.

- **Error Handling**: `CurativeError` provides prescriptions for issues like missing modules (e.g., installation steps, fallbacks).

## Rendering
- `to_xml(*elements, validate=False)`: Render to HTML string with optional validation.
- `tidy(html)`: Pretty-print HTML using lxml if available (for better performance and handling of large documents), falling back to BeautifulSoup if installed, or a basic fallback if healing is enabled.
- `highlight(html)`: Syntax-highlight (uses Pygments if installed; raw fallback if healing enabled).
- `showtags(html)`: Placeholder for preformatted display.

## Utilities
- `flatten(nested)`: Flatten nested structures for children.
- `as_json(obj)`: Serialize to JSON.
- `add_quotes(value)`: Smart quoting for attributes.
- `check_allowlist_current()`: Verify static allowlist against MDN (returns diff for updates).

## API Reference
### Core (core.py)
- `FT(tag, *children, void=False, validate_mode='none', **attrs)`: Create element.
- `ft(...)`: Alias for FT.

### Attributes (attributes.py)
- `keymap(key)`: Map Python names to HTML.
- `attrmap(attrs)`: Apply keymap to dict.
- `to_attr(key, value)`: Convert to HTML attribute string.
- `to_attrs(attrs)`: Convert dict to attribute string.

### Rendering (rendering.py)
- `to_xml(*contents, escape=html.escape, newline='\n', validate=False)`: Render HTML.
- `tidy(html)`: Prettify HTML using lxml if available, with fallback to BeautifulSoup or basic formatting.
- `highlight(html)`: Syntax-highlight HTML.
- `showtags(html)`: Display with tags.

### Validation (validation.py)
- `HTMLValidator.validate_and_heal(el, mode)`: Validate/heal element.
- `check_allowlist_current()`: Check allowlist currency.

### Config (config.py)
- `config`: Global config object.

## Advanced Usage: Building Components
As emphasized in the [FastHTML Components guide](https://fastht.ml/about/components), FastTags excels at creating reusable components. Components are simply Python functions that return FastTag objects, allowing you to abstract common UI patterns.

### Example: Reusable Card Component
```python
from fasttags.html import *

def card(title: str, content: str, image_src: str = None):
    elements = [H2(title), P(content)]
    if image_src:
        elements.append(Img(src=image_src, alt=title))
    return Div(*elements, cls="card border rounded p-4")

# Usage
my_card = card("Article Title", "This is the content.", "img.jpg")
print(to_xml(my_card))
# Output: <div class="card border rounded p-4"><h2>Article Title</h2><p>This is the content.</p><img src="img.jpg" alt="Article Title" /></div>
```

- **Composition**: Combine components (e.g., a form component inside a card).
- **Validation in Components**: Set `validate_mode` on the root element for checked rendering.
- **FastHTML Integration**: In FastHTML apps, return components from route handlers for server-side rendering.

## Prototyping and Production Migration
This version of FastTags is specifically designed for prototyping, pilot projects, and small-scale deployments, where rapid iteration and simplicity are paramount. It allows developers to quickly build and test HTML structures and components using Python's expressive power, without the overhead of a full web framework. The library's functional, component-based approach (as inspired by FastHTML) enables fast experimentation, with built-in tools for validation and error recovery to catch issues early.

For scaling to large-scale production environments, FastTags includes planned tools and integrations to seamlessly migrate prototypes to more robust systems like Django:

- **Conversion Tools to Django Templates**: 
  - FastTags provides utilities (forthcoming in future releases) to convert FastTag-based components into native Django templates. This involves rendering FastTag structures to static HTML snippets or dynamic templates with Django's templating syntax (e.g., converting a `card` component to a `{% include "card.html" %}` with variables).
  - **Workflow**: Use FastTags for initial development, then run a conversion script to generate Django-compatible templates. This preserves logic while leveraging Django's scalability, caching, and ecosystem for high-traffic sites.
  - **Benefits**: Reduces migration friction; prototypes can be "exported" with minimal rewriting, ensuring consistency between dev and prod.

- **Django Middleware for Prototyping**:
  - A dedicated Django middleware (in development) allows embedding FastTags directly in Django views for prototyping. This middleware intercepts responses and renders FastTag objects on-the-fly, enabling hybrid apps where new features are prototyped with FastTags while existing code uses traditional templates.
  - **Quick Migration**: Once prototyped, use built-in tools to convert FastTag code to pure Django templates. The middleware includes migration assistants (e.g., auto-generating template files from FastTag routes).
  - **Example Use Case**: In a Django view, return a FastTag component; the middleware handles rendering. For production, migrate to templates for better performance and integration with Django's ORM/views.

This prototyping-to-production path makes FastTags an ideal starting point for projects that may grow into full Django applications. It bridges the gap between minimal, server-side HTML generation (like FastHTML) and enterprise frameworks, allowing teams to start small and scale without major rewrites. Future updates will expand these tools—check the repo for progress.

## Contributing and Maintenance
- **Source**: [Assume GitHub repo link here].
- **Issues**: Report bugs or suggest features.
- **Updating Allowlist**: Run `check_allowlist_current()` and update `VALID_ATTRS` based on diffs from MDN.
- **Dependencies**: All optional; library provides prescriptions and healings for missing modules.

This documentation is based on the current version of FastTags. For updates, check the repo or FastHTML resources.

---

This updated README is ready for use. If you need further modifications, let me know!