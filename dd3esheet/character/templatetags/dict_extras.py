from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Permite `mydict|get_item:variable` em templates."""
    if not dictionary:
        return None
    return dictionary.get(key)
