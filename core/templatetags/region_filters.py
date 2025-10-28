from django import template

register = template.Library()

@register.filter
def get_region_nombre(regiones, region_id):
    """
    Dado una lista de regiones y un id, retorna el nombre de la región.
    Uso: {{ regiones|get_region_nombre:region_id }}
    """
    try:
        region_id = int(region_id)
    except (ValueError, TypeError):
        return "Desconocida"
    for reg in regiones:
        if getattr(reg, 'id', None) == region_id:
            return getattr(reg, 'nombre', 'Desconocida')
    return "Desconocida"
