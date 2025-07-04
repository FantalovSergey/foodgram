import re

from django.core.exceptions import ValidationError


def validate_username(value):
    field = 'username'
    invalid_symbols = re.sub(r'[\w.@+-]', '', value)
    if invalid_symbols:
        message = (
            f'Недопустимые символы в имени пользователя: {invalid_symbols}')
        raise ValidationError({field: message})
    if re.fullmatch(r'^me$', value):
        message = 'Запрещено использовать me в качестве имени пользователя.'
        raise ValidationError({field: message})
