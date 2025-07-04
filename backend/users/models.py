from django.contrib.auth.models import AbstractUser
from django.db import models

from . import constants
from .validators import validate_username


class User(AbstractUser):
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    email = models.EmailField(
        unique=True, max_length=constants.EMAIL_FIELD_MAX_LENGTH,
        verbose_name='Адрес электронной почты',
    )
    username = models.CharField(
        unique=True,
        max_length=constants.CHAR_FIELD_MAX_LENGTH,
        validators=[validate_username],
        verbose_name='Имя пользователя',
    )
    first_name = models.CharField(
        max_length=constants.CHAR_FIELD_MAX_LENGTH, verbose_name='Имя',
    )
    last_name = models.CharField(
        max_length=constants.CHAR_FIELD_MAX_LENGTH, verbose_name='Фамилия',
    )
    password = models.CharField(verbose_name='Пароль')
    avatar = models.ImageField(
        upload_to='avatars', null=True, blank=True, verbose_name='Аватар',
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Действующий',
        help_text='Уберите галочку, чтобы заблокировать пользователя.',
    )

    class Meta:
        ordering = ('username',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username[:constants.STR_MAX_LENGTH]


class Subscription(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='followers',
        verbose_name='Автор',
    )
    follower = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name='Подписчик',
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['author', 'follower'],
                name='unique_subscription',
                violation_error_message='Такая подписка уже существует.',
            ),
            models.CheckConstraint(
                check=~models.Q(author=models.F('follower')),
                name='author_is_not_follower',
                violation_error_message=(
                    'Поля "author" и "follower" должны различаться.'),
            ),
        ]
        ordering = ('-id',)
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

    def __str__(self):
        return (
            f'{self.follower.username[:constants.STR_MAX_LENGTH_SHORT]} '
            'подписан на '
            f'{self.author.username[:constants.STR_MAX_LENGTH_SHORT]}.'
        )
