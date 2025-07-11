from random import choice

from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from . import constants

User = get_user_model()


class Ingredient(models.Model):
    name = models.CharField(
        max_length=constants.INGREDIENT_NAME_MAX_LENGTH,
        verbose_name='Ингредиент',
    )
    measurement_unit = models.CharField(
        max_length=constants.MEASUREMENT_UNIT_MAX_LENGTH,
        verbose_name='Единица измерения',
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_name_unit',
                violation_error_message='Ингредиент уже добавлен.',
            )
        ]
        ordering = ('name', 'measurement_unit')
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return (
            f'{self.name[:constants.STR_MAX_LENGTH_SHORT]}, '
            f'{self.measurement_unit[:constants.STR_MAX_LENGTH_SHORT]}'
        )


class Tag(models.Model):
    name = models.CharField(
        max_length=constants.TAG_FIELDS_MAX_LENGTH,
        unique=True,
        verbose_name='Тег',
    )
    slug = models.SlugField(
        max_length=constants.TAG_FIELDS_MAX_LENGTH,
        unique=True,
        verbose_name='Слаг',
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    tags = models.ManyToManyField(Tag, verbose_name='Теги')
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name='Автор',
    )
    ingredients = models.ManyToManyField(
        Ingredient, through='RecipeIngredient', verbose_name='Ингредиенты',
    )
    name = models.CharField(
        max_length=constants.RECIPE_NAME_MAX_LENGTH, verbose_name='Название',
    )
    image = models.ImageField(upload_to='recipes', verbose_name='Изображение')
    text = models.TextField(verbose_name='Описание')
    cooking_time = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(constants.MIN_COOKING_TIME),
            MaxValueValidator(constants.MAX_COOKING_TIME),
        ],
        verbose_name='Время приготовления, мин',
    )
    short_link = models.CharField(
        unique=True,
        blank=True,
        max_length=constants.SHORT_LINK_MAX_LENGTH,
        verbose_name='Короткая ссылка',
    )
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name='Добавлен',
    )

    class Meta:
        ordering = ('-created_at',)
        default_related_name = 'recipes'
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def get_short_link(self):
        return (
            ''.join(
                [
                    chr(choice(constants.VALID_SYMBOLS))
                    for _ in range(constants.SHORT_LINK_SIGNIFICANT_LENGTH)
                ]
            )
        )

    def save(self, **kwargs):
        if not self.short_link:
            while True:
                self.short_link = self.get_short_link()
                if not (
                    Recipe.objects.filter(short_link=self.short_link).exists()
                ):
                    break
        return super().save(**kwargs)

    def __str__(self):
        return (
            f'{self.name[:constants.STR_MAX_LENGTH_SHORT]}, '
            f'{self.author.username[:constants.STR_MAX_LENGTH_SHORT]}'
        )


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='ingredients_for',
        verbose_name='Рецепт',
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Ингредиент',
    )
    amount = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(constants.MIN_INGREDIENT_AMOUNT)],
        verbose_name='Количество',
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_ingredient',
                violation_error_message='Ингредиент уже в рецепте.',
            )
        ]
        ordering = ('-recipe', 'ingredient__name')
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецепте'


class FavoritesShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='%(class)s',
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='in_%(class)s',
        verbose_name='Рецепт',
    )

    class Meta:
        abstract = True
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_addition_in_%(class)s',
                violation_error_message='Рецепт уже добавлен.',
            )
        ]
        ordering = ('user__username', '-recipe')


class Favorites(FavoritesShoppingCart):

    class Meta(FavoritesShoppingCart.Meta):
        verbose_name = 'Рецепт в избранном'
        verbose_name_plural = 'Рецепты в избранном'

    def __str__(self):
        return (
            f'{self.recipe.name[:constants.STR_MAX_LENGTH_SHORT]} '
            'в избранном у '
            f'{self.user.username[:constants.STR_MAX_LENGTH_SHORT]}.'
        )


class ShoppingCart(FavoritesShoppingCart):

    class Meta(FavoritesShoppingCart.Meta):
        verbose_name = 'Рецепт в списке покупок'
        verbose_name_plural = 'Рецепты в списке покупок'

    def __str__(self):
        return (
            f'{self.recipe.name[:constants.STR_MAX_LENGTH_SHORT]} '
            'в списке покупок у '
            f'{self.user.username[:constants.STR_MAX_LENGTH_SHORT]}.'
        )
