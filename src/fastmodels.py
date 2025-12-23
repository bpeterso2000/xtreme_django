import inspect
import sys
from decimal import Decimal
from datetime import date, time, datetime, timedelta
from typing import Any, List, Optional, Union, Type, Mapping, Literal, get_args, get_origin
from enum import Enum

# Real Django Imports
from django.db import models
from django import forms
from django.core import validators

# --- Relational Markers ---
class Relation: pass
class FK(Relation): pass
class M2M(Relation): pass
class OTO(Relation): pass

# --- Sliceable Type Logic ---
class SliceableMeta(type):
    def __getitem__(cls, item):
        return (cls, item)

class BaseHtmlType(metaclass=SliceableMeta): pass

# --- HTML Types ---
class Text(BaseHtmlType): pass
class Password(BaseHtmlType): pass
class Email(BaseHtmlType): pass
class TextArea(BaseHtmlType): pass
class Number(BaseHtmlType): pass
class Range(BaseHtmlType): pass
class Url(BaseHtmlType): pass
class File(BaseHtmlType): pass
class Image(BaseHtmlType): pass
class Hidden(BaseHtmlType): pass
class Color(BaseHtmlType): pass
class Pattern(BaseHtmlType): pass

# -- Validator Types ---
class IPv4(BaseHtmlType): pass
class IPv6(BaseHtmlType): pass

# -- Convenience Types ---
class Int(BaseHtmlType): pass
class Float(BaseHtmlType): pass
class Money(BaseHtmlType): pass
class Choices(BaseHtmlType): pass

# --- Helpers ---
def get_kwargs(default_val):
    """Extracts standard Django field kwargs from the default value."""
    if default_val is None: 
        return {'null': True, 'blank': True}
    if default_val is not ...: 
        return {'default': default_val}
    return {}

def parse_slice(sl):
    """Parses slice arguments for configuration."""
    if isinstance(sl, int): return None, sl, None # Text[100] -> max_length=100
    if isinstance(sl, slice): return sl.start, sl.stop, sl.step
    return None, None, None

def handle_str(typ, default, name, slice_args=None):
    kwargs = get_kwargs(default)
    kwargs.setdefault('max_length', 255)
    return models.CharField(**kwargs)

def handle_int(typ, default, name, slice_args=None):
    return models.IntegerField(**get_kwargs(default))

def handle_float(typ, default, name, slice_args=None):
    return models.FloatField(**get_kwargs(default))

def handle_bool(typ, default, name, slice_args=None):
    kwargs = get_kwargs(default)
    # Handle explicit None default as NullBoolean
    if kwargs.get('null'): 
        return models.BooleanField(null=True, blank=True)
    return models.BooleanField(**kwargs)

def handle_date(typ, default, name, slice_args=None):
    kwargs = get_kwargs(default)
    if default in (datetime.now, 'now'):
        kwargs.pop('default', None)
        kwargs['auto_now_add'] = True
    return models.DateField(**kwargs)

def handle_datetime(typ, default, name, slice_args=None):
    kwargs = get_kwargs(default)
    if default in (datetime.now, 'now'):
        kwargs.pop('default', None)
        kwargs['auto_now_add'] = True
    return models.DateTimeField(**kwargs)

def handle_time(typ, default, name, slice_args=None):
    kwargs = get_kwargs(default)
    if default in (datetime.now, 'now'):
        kwargs.pop('default', None)
        kwargs['auto_now_add'] = True
    return models.TimeField(**kwargs)

def handle_decimal(typ, default, name, slice_args=None):
    kwargs = get_kwargs(default)
    # Parse string default for precision: '.00' -> 2 places
    if isinstance(default, str) and '.' in default:
        kwargs['decimal_places'] = len(default.split('.')[1])
        kwargs['max_digits'] = 19 # Reasonable default
        kwargs['default'] = Decimal(0)
    else:
        kwargs.setdefault('decimal_places', 2)
        kwargs.setdefault('max_digits', 19)
    return models.DecimalField(**kwargs)

def as_text_like(typ, default, name, slice_args=None):
    kwargs = get_kwargs(default)
    start, stop, step = parse_slice(slice_args)
    
    kwargs.setdefault('max_length', stop if stop else 255)
    validators_list = kwargs.setdefault('validators', [])
    
    if start: 
        validators_list.append(validators.MinLengthValidator(start))
    
    # Specific Type Mapping
    if typ is Email: 
        return models.EmailField(**kwargs)
    if typ is IPv4:
        return models.GenericIPAddressField(protocol='IPv4', **kwargs)
    if typ is IPv6:
        return models.GenericIPAddressField(protocol='IPv6', **kwargs)
    if typ is Url:
        return models.URLField(**kwargs)
    
    # Base CharField with Widget overrides
    field = models.CharField(**kwargs)
    
    if typ is Password: field._fast_widget = forms.PasswordInput
    elif typ is Hidden: field._fast_widget = forms.HiddenInput
    elif typ is Color: field._fast_widget = forms.TextInput(attrs={'type': 'color'})
    
    return field

def as_text_area(typ, default, name, slice_args=None):
    kwargs = get_kwargs(default)
    start, stop, step = parse_slice(slice_args)
    
    field = models.TextField(**kwargs)
    field._fast_widget = forms.Textarea
    
    # Use 'step' from slice as 'rows' configuration
    if step:
        field._fast_widget_attrs = {'rows': step}
    return field

def as_num_range(typ, default, name, slice_args=None):
    kwargs = get_kwargs(default)
    start, stop, step = parse_slice(slice_args)
    
    validators_list = kwargs.setdefault('validators', [])
    if start is not None: validators_list.append(validators.MinValueValidator(start))
    if stop is not None: validators_list.append(validators.MaxValueValidator(stop))
    
    return models.IntegerField(**kwargs)

def as_file_image(typ, default, name, slice_args=None):
    kwargs = get_kwargs(default)
    if typ is Image: return models.ImageField(**kwargs)
    return models.FileField(**kwargs)

def handle_relation(typ, default, name, slice_args=None):
    kwargs = get_kwargs(default)
    # Simple inference: 'author' -> 'Author'
    target = name.title().replace('_', '')
    
    if typ is FK: return models.ForeignKey(target, on_delete=models.CASCADE, **kwargs)
    if typ is OTO: return models.OneToOneField(target, on_delete=models.CASCADE, **kwargs)
    if typ is M2M: return models.ManyToManyField(target, **kwargs)
    return None

# --- The Lookup Table ---
handlers = [
    str, int, float, bool, date, time, datetime, Decimal
]

func_types = {
    as_text_like: [Text, Password, Email, IPv4, IPv6, Url, Hidden, Color],
    as_text_area: [TextArea],
    as_num_range: [Number, Range],
    as_file_image: [File, Image],
    handle_relation: [FK, M2M, OTO],
    lambda t, d, n, s: models.DurationField(**get_kwargs(d)): [timedelta],
}
func_types.update({locals()['handle_' + typ.__name__]: [typ] for typ in handlers})

TYPES_TO_FUNCTIONS = {t: f for f, types in func_types.items() for t in types}


FIELD_HANDLERS = {
    # Primitives
    str: handle_str,
    int: handle_int,
    float: handle_float,
    bool: handle_bool,
    
    # Dates
    date: handle_date,
    time: handle_time,
    datetime: handle_datetime,
    timedelta: lambda t, d, n, s: models.DurationField(**get_kwargs(d)),
    
    # Financials
    Decimal: handle_decimal,
    Money: as_decimal_like,

    # HTML / Complex Groups
    Text: as_text_like,
    Password: as_text_like,
    Email: as_text_like,
    Url: as_text_like,
    Hidden: as_text_like,
    Color: as_text_like,
    
    TextArea: as_text_area,
    
    Number: as_num_range,
    Range: as_num_range,
    
    File: as_file_image,
    Image: as_file_image,
    
    # Relations
    FK: handle_relation,
    M2M: handle_relation,
    OTO: handle_relation,

    # Additional Validators
    Pattern: as_text_like
}

def create_field(typ, default_val, name):
    """
    Dispatcher function using the lookup table.
    """
    # 1. Handle Sliceable Types (e.g. Text[:100])
    is_slice = isinstance(typ, tuple) and len(typ) == 2
    base_type = typ[0] if is_slice else typ
    slice_args = typ[1] if is_slice else None

    # 2. Direct Lookup
    handler = FIELD_HANDLERS.get(base_type)
    if handler:
        return handler(base_type, default_val, name, slice_args)

    # 3. Fallback for Special Types (Literal, Enum)
    origin = get_origin(base_type)
    
    # Handle Literal
    if origin is Literal:
        args = get_args(base_type)
        choices = [(str(x), str(x).capitalize()) for x in args]
        kwargs = get_kwargs(default_val)
        kwargs['choices'] = choices
        kwargs.setdefault('max_length', 255)
        return models.CharField(**kwargs)

    # Handle Enum
    if isinstance(base_type, type) and issubclass(base_type, Enum):
        choices = [(e.value, e.name) for e in base_type]
        kwargs = get_kwargs(default_val)
        kwargs['choices'] = choices
        if all(isinstance(e.value, int) for e in base_type):
            return models.IntegerField(**kwargs)
        kwargs.setdefault('max_length', 255)
        return models.CharField(**kwargs)

    return models.CharField(max_length=255)

def create_model_form(model_class):
    """Generates a ModelForm with custom widget attachments."""
    widgets = {}
    for name, field in model_class.__dict__.items():
        if hasattr(field, '_fast_widget') and field._fast_widget:
            widgets[name] = field._fast_widget
            # Apply widget attrs (like rows) if present
            if hasattr(field, '_fast_widget_attrs'):
                # In real Django, we'd instantiate the widget with attrs here
                # For simplicity, we map the class, but in production code:
                # widgets[name] = field._fast_widget(attrs=field._fast_widget_attrs)
                pass

    class Meta:
        model = model_class
        fields = '__all__'
        if widgets:
            widgets = widgets

    name = f"{model_class.__name__}Form"
    return type(name, (forms.ModelForm,), {'Meta': Meta})

def model(cls):
    """Decorator to convert class to Django Model."""
    annotations = getattr(cls, '__annotations__', {})
    class_dict = {'__module__': cls.__module__}
    
    for name, typ in annotations.items():
        default_val = getattr(cls, name, ...)
        django_field = create_field(typ, default_val, name)
        if django_field:
            class_dict[name] = django_field
            
    new_class = type(cls.__name__, (models.Model,), class_dict)
    new_class.Form = create_model_form(new_class)
    return new_class

# --- Additional Handlers ---

def as_pattern(typ, default, name, slice_args=None):
    """Handles Pattern types (Regex validation)."""
    kwargs = get_kwargs(default)
    # In a real scenario, the regex pattern might be passed via the type or default
    # For this spec, Pattern is a marker. We assume CharField.
    kwargs.setdefault('max_length', 255)
    # We could add a RegexValidator here if the pattern was provided
    return models.CharField(**kwargs)

def as_money(typ, default, name, slice_args=None):
    """Handles Money types (Decimal with specific defaults)."""
    kwargs = get_kwargs(default)
    start, stop, step = parse_slice(slice_args)
    
    kwargs.setdefault('max_digits', 19)
    kwargs.setdefault('decimal_places', 2)
    kwargs.setdefault('default', Decimal('0.00'))
    
    validators_list = kwargs.setdefault('validators', [])
    if start is not None: validators_list.append(validators.MinValueValidator(start))
    if stop is not None: validators_list.append(validators.MaxValueValidator(stop))
    
    return models.DecimalField(**kwargs)

# --- Updating the Lookup Table ---
# We extend the previous dictionary with these new
# --- Updating the Lookup Table ---
# We extend the previous dictionary with these new handlers
FIELD_HANDLERS.update({
    Pattern: as_pattern,
    Money: as_money,
    CreditCard: as_text_like,  # Reuse as_text_like for CharField + validators
})

def create_model_form(model_class):
    """Generates a ModelForm with custom widget attachments."""
    widgets = {}
    for name, field in model_class.__dict__.items():
        if hasattr(field, '_fast_widget') and field._fast_widget:
            widget_class = field._fast_widget
            # If widget attributes are specified (e.g., rows for TextArea), instantiate the widget
            if hasattr(field, '_fast_widget_attrs'):
                widgets[name] = widget_class(attrs=field._fast_widget_attrs)
            else:
                widgets[name] = widget_class

    class Meta:
        model = model_class
        fields = '__all__'
        if widgets:
            widgets = widgets

    name = f"{model_class.__name__}Form"
    return type(name, (forms.ModelForm,), {'Meta': Meta})

# ----------------------------------------------------------------------
# FAST MODELS EXPORTER
# ----------------------------------------------------------------------

def format_value(val):
    """
    Helper to format values for code generation.
    Handles strings, classes, and enums gracefully.
    """
    if isinstance(val, str):
        return f"'{val}'"
    if inspect.isclass(val) and issubclass(val, models.Model):
        return f"'{val.__name__}'"
    return repr(val)

def generate_model_code(model_class):
    """
    Introspects a Django model class (created via fastmodels or otherwise)
    and returns a string containing the standard Django class definition.
    """
    class_name = model_class.__name__
    lines = []
    
    # 1. Class Definition
    lines.append(f"class {class_name}(models.Model):")
    
    # 2. Iterate over fields
    # We use local_fields to get standard fields and local_many_to_many for M2M
    all_fields = model_class._meta.local_fields + model_class._meta.local_many_to_many
    
    for field in all_fields:
        # Skip the automatic 'id' field unless it was manually defined
        if field.auto_created:
            continue

        # The magic of Django: deconstruct() returns exactly what we need
        # to recreate the field (name, path, args, kwargs)
        name, path, args, kwargs = field.deconstruct()
        
        # Clean up the field type name (e.g., 'django.db.models.CharField' -> 'models.CharField')
        field_type = path.split('.')[-1]
        
        # Construct the arguments string
        arg_strings = []
        
        # Handle positional args (rare in modern Django, but possible)
        for arg in args:
            arg_strings.append(format_value(arg))
            
        # Handle keyword args
        for k, v in kwargs.items():
            # Special handling for related models to ensure they are strings
            if k in ['to', 'model']: 
                if hasattr(v, '__name__'):
                    v = v.__name__
                arg_strings.append(f"{k}='{v}'")
            # Special handling for choices to format them nicely
            elif k == 'choices':
                # We output the list of tuples directly
                arg_strings.append(f"{k}={v}")
            else:
                arg_strings.append(f"{k}={format_value(v)}")
        
        # Join everything
        field_def = f"    {field.name} = models.{field_type}({', '.join(arg_strings)})"
        lines.append(field_def)

    # 3. Handle Meta (Optional, but good for completeness)
    meta_options = []
    if model_class._meta.ordering:
        meta_options.append(f"        ordering = {model_class._meta.ordering}")
    if model_class._meta.verbose_name_plural != f"{model_class._meta.verbose_name}s":
        meta_options.append(f"        verbose_name_plural = '{model_class._meta.verbose_name_plural}'")
        
    if meta_options:
        lines.append("")
        lines.append("    class Meta:")
        lines.extend(meta_options)

    # 4. Add __str__ if it exists and isn't default object.__str__
    # (Hard to reverse engineer dynamic lambdas, but we can add a placeholder)
    lines.append("")
    lines.append("    def __str__(self):")
    lines.append(f"        return str(self.pk)  # TODO: Update this")

    return "\n".join(lines)

def export_app_models(models_list):
    """
    Takes a list of model classes and prints the full models.py content.
    """
    print("from django.db import models")
    print("from datetime import date, datetime, time")
    print("from decimal import Decimal")
    print("\n# --- Generated Standard Django Models --- \n")
    
    for model in models_list:
        print(generate_model_code(model))
        print("\n")
