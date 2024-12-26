from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Template filter to access dictionary value by key"""
    return dictionary.get(key)



@register.filter
def to_float(value):
    try:
        return float(value)
    except (ValueError, TypeError):
        return value