from django import template

register = template.Library()

@register.filter
def get_attr(obj, attr_name):
    return getattr(obj, attr_name)

@register.filter
def display_field(obj, field):
    value = getattr(obj, field)

    if field == 'password':
        return '********'

    return value

