from django.template.defaulttags import register


@register.filter
def loop(number: int, reverse: bool = False):
    return reversed(range(number)) if reverse else range(number)


@register.filter
def get(data: list, index: int):
    return data[index]
