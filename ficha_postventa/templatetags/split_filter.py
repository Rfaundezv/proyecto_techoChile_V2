from django import template

register = template.Library()

@register.filter
def split(value, delimiter=','):
    """Divide una cadena usando el delimitador especificado."""
    return value.split(delimiter)

@register.filter
def lookup(obj, attr):
    """Obtiene el valor de un atributo de un objeto usando getattr."""
    try:
        return getattr(obj, attr)
    except (AttributeError, TypeError):
        return None
