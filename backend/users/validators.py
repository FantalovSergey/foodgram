import re

from django.core.exceptions import ValidationError


def validate_username(value):
    field = 'username'
    invalid_symbols = re.sub(r'[\w.@+-]', '', value)
    if invalid_symbols:
        message = (
            f'Недопустимые символы в имени пользователя: {invalid_symbols}')
        raise ValidationError({field: message})
