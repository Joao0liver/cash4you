from django import template

register = template.Library()


@register.filter
def field(bound_form, name):
    return bound_form[name]


@register.filter
def get_item(mapping, key):
    return mapping.get(key, [])
