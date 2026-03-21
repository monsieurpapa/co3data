from django import template

register = template.Library()

@register.filter(name='getattr')
def getattr_filter(obj, attr):
    """Get an attribute of an object dynamically from a string name."""
    import builtins
    return builtins.getattr(obj, attr, None)

@register.filter
def get(dictionary, key):
    """Get a value from a dictionary by key."""
    if dictionary:
        return dictionary.get(key)
    return None

@register.filter
def multiply(value, arg):
    """Multiply the value by the argument."""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return None

@register.filter
def split(value, arg):
    """Split the string by the argument."""
    return value.split(arg)

@register.filter
def getitem(obj, key):
    """Get an item from an object (dictionary or form) by key."""
    try:
        return obj[key]
    except (KeyError, TypeError, IndexError):
        return None

@register.filter
def label(bound_field):
    """Get the label of a bound field."""
    if hasattr(bound_field, 'label'):
        return bound_field.label
    return ""

@register.filter
def errors(bound_field):
    """Get the errors of a bound field."""
    if hasattr(bound_field, 'errors'):
        return bound_field.errors
    return None
