from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """
    Retrieves an item from a dictionary using the specified key.
    Usage: {{ my_dict|get_item:my_key }}
    """
    if not dictionary:
        return None
    return dictionary.get(str(key))
