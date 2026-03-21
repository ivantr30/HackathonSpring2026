from django import template

register = template.Library()


@register.filter(name="has_group")
def has_group(user, group_name: str):
    return user.groups.filter(name=group_name).exists()


@register.filter(name="has_any_group")
def has_any_group(user, group_names: str):
    groups = [name.strip() for name in group_names.split(",")]
    return user.groups.filter(name__in=groups).exists()
