# FastTags Module Requirements Specification

This document outlines the requirements for the FastTags Python library, based on the cumulative understanding from our discussions. FastTags is a toolkit for programmatic HTML generation, validation, and conversion, emphasizing a curative design (error prevention/recovery with prescriptions), component-based development (inspired by FastHTML), and prototyping workflows with migration paths to production systems like Django. The spec covers functional and non-functional requirements, assumptions, and outstanding items. It assumes the library is in active development, targeting Python 3.10+.

## Introduction
- **Purpose**: FastTags enables type-safe, fluent creation of HTML structures using Python objects (e.g., FT class and tag factories). It supports validation/healing, rendering, and conversion utilities for rapid prototyping, with tools for scaling to production (e.g., Django integration).
- **Target Users**: Developers building web prototypes, FastHTML-style apps, or migrating HTML designs to dynamic components.
- **Key Inspirations**: FastHTML components (https://fastht.ml/about/components), curative error handling, and one-time conversion for production migration.
- **Version Scope**: This spec reflects the current state (post-refactoring of parsing.py, middleware, etc.). Future versions may add Django template generation as a separate module.

## Functional Requirements

### Core HTML Generation
- Provide `FT` class for creating elements with tag, children, attributes, and void handling.
- Include tag factories (e.g., Div, Img) via partials, imported from html.py, supporting all HTML5 tags and void elements.
- Support attribute mapping (e.g., cls → class, underscores to hyphens) via attributes.py.
- Handle children as nested elements, strings, iterables (flattened via utilities.flatten).

### Configuration
- Global config object (config.py) with settings like enable_validation, validate_mode ('none', 'static', 'html5lib', 'w3c'), auto_heal, heal_fuzzy, escape_by_default.
- Support environment variables (e.g., FASTTAG_VALIDATE_MODE).
- Per-element overrides (e.g., validate_mode in FT init).

### Validation and Healing
- HTMLValidator class (validation.py) for attribute/tag checks, with modes integrating optional deps (html5lib, requests).
- Auto-healing: Drop invalids, fuzzy-match typos (using difflib); tied to config.auto_heal/heal_fuzzy.
- CurativeError for prescriptive errors (e.g., install instructions for missing modules).
- Allowlist checker (check_allowlist_current) against MDN, extended to separate SVG_VALID_ATTRS (sourced from MDN SVG docs).

### Rendering
- to_xml/to_html for generating HTML strings, with optional validation and escaping.
- tidy (pretty-print via BeautifulSoup or fallback), highlight (Pygments or raw), showtags (placeholder).
- Handle multi-root and empty cases gracefully.

### Utilities
- flatten for nested iterables.
- as_json for serialization.
- add_quotes for attribute quoting.
- normalize_coll (parsing.py) for type conversions (tuples/lists, with match_len and healing).
- risinstance for curried type checks.

### Parsing and Conversion
- html2ft (parsing.py): Convert HTML (str/bytes) to FT expression string or object/tuple (multi-root support: tuple for multiple, single unwrapped, None for empty).
  - Params: attr1st, validate (override), heal_parsing (separate, fallback to ignore/warn if global auto_heal), strict ('warn' default: comments in output), raw_embedded (disable escaping), quiet_unsafe.
  - Preserve SVG (case/namespaces via lxml optional, auto-switch on detection; html.parser fallback with warning/CurativeError).
  - Preserve embedded XML/JSON/scripts as escaped single strings (raw option to disable).
  - Curative fallbacks on parse failure: Try html5lib first (skip if missing), then config mode; detailed prescriptions for common errors.
  - Warnings for unsafe tags (logging, suppressible).
  - Auto-decode bytes (utf-8, CurativeError on failure).
  - Reuse attrmap/keymap for attributes.

### Django Middleware
- FastTagsMiddleware for views returning FT objects; renders to HttpResponse with security headers, CSRF injection, and production opt-in (FASTTAGS_PROD_ENABLED).
- Restricted to DEBUG or explicit enable; robust error handling.

### CLI Wrapper
- Command-line interface for html2ft using click (optional dep; CurativeError if missing).
- Auto-detect input: File if path exists, URL (fetch via requests, no auth/headers), pasted string otherwise; stdin if no args.
- Single-input only; output to stdout (default) or file (-o flag); always string format.
- Colorized output for errors/prescriptions (click styles, plain text fallback).
- Pass through html2ft params (e.g., --validate, --heal-parsing).

## Non-Functional Requirements
- **Readability**: Prioritize clear code (type hints, comments, descriptive names) over performance; for offline/one-time use.
- **Security**: Curative errors with prescriptions; optional deps with fallbacks; warnings for unsafe content; no sanitization (warn only).
- **Compatibility**: Python 3.10+; optional deps (bs4, html5lib, requests, lxml, pygments, click) with graceful degradation.
- **Testing**: Pytest with 80%+ coverage; include real-world examples from open-source/CC sources (e.g., Wikimedia for SVG).
- **Documentation**: Full docs, TL;DR version; snippets in docstrings (no doctests).
- **Maintenance**: Extend allowlist checks to SVG; focus on prototyping (small deployments); migration tools for Django.

## Assumptions
- **Environment**: Users have pip for deps; virtualenvs for isolation. No async/live rendering needs.
- **Input Quality**: HTML is mostly well-formed; severe malformations trigger curative responses but may not fully recover.
- **SVG Handling**: lxml optional; if absent, best-effort with html.parser (may lose case/namespaces). Detection is post-initial parse.
- **Error Behavior**: 'strict' interacts with heal_parsing (e.g., 'heal' enables healing even if heal_parsing=False); warnings as prefixed comments don't break eval.
- **CLI**: Click is optional; if missing, CLI skips with error (no basic fallback). URL fetches are simple (no timeouts/retries).
- **Unspecified Edges**: Empty inputs return None/tuple(); multi-root as plain tuple expression; no synthetic roots.
- **Integration**: Params override globals function-scope only; no conflict warnings.

## Outstanding Items
- **Testing Suite**: Implement pytest tests (80% coverage) with real-world examples (e.g., CC-licensed HTML/SVG from Wikimedia). Pending: Coverage.py integration.
- **SVG Allowlist Extension**: Implement separate SVG_VALID_ATTRS fetched from MDN SVG docs (e.g., via JSON API); integrate into check_allowlist_current.
- **CLI Completion**: Finalize auto-detection logic (file > URL > string); test edge cases (e.g., ambiguous args like "http.txt").
- **Documentation Updates**: Add CLI usage to full/TL;DR docs; include SVG notes.
- **Potential Expansions**: Reverse FT-to-HTML (low priority); Django template generation module (separate phase).
- **Validation Gaps**: SVG attrs may be dropped in validation (as not in VALID_ATTRS); consider auto-merging SVG list during checks.
- **Review**: Manual testing for bytes decoding, multi-root eval, and lxml auto-switch.

This spec can be refined as development progresses. If ready, I can generate code or address specific items!