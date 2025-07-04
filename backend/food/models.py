from random import choice

from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
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
        ordering = ('name', 'id')
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
        validators=[MinValueValidator(constants.MIN_COOKING_TIME)],
        verbose_name='Время приготовления, мин',
    )
    short_link = models.CharField(
        unique=True,
        blank=True,
        max_length=constants.SHORT_LINK_MAX_LENGTH,
        verbose_name='Короткая ссылка',
    )

    class Meta:
        ordering = ('-id',)
        default_related_name = 'recipes'
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def in_favorites_count(self):
        return len(self.in_favorites.all())

    in_favorites_count.short_description = 'Добавлений в избранное'

    def save(self, **kwargs):
        if self.short_link:
            return super().save(**kwargs)
        while True:
            self.short_link = '/SL' + ''.join(
                [
                    chr(choice(constants.VALID_SYMBOLS))
                    for _ in range(constants.SHORT_LINK_SIGNIFICANT_LENGTH)
                ]
            ) + '/'
            if not Recipe.objects.filter(short_link=self.short_link).exists():
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
        ordering = ('id',)
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецепте'


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='in_favorites',
        verbose_name='Рецепт',
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_addition_in_favorites',
                violation_error_message=(
                    'Рецепт уже в избранном у пользователя.'),
            )
        ]
        ordering = ('-id',)
        verbose_name = 'Рецепт в избранном'
        verbose_name_plural = 'Рецепты в избранном'

    def __str__(self):
        return (
            f'{self.recipe.name[:constants.STR_MAX_LENGTH_SHORT]} '
            'в избранном у '
            f'{self.user.username[:constants.STR_MAX_LENGTH_SHORT]}.'
        )


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='in_shopping_cart',
        verbose_name='Рецепт',
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_addition_in_shopping_cart',
                violation_error_message=(
                    'Рецепт уже в списке покупок пользователя.'),
            )
        ]
        ordering = ('-id',)
        verbose_name = 'Рецепт в списке покупок'
        verbose_name_plural = 'Рецепты в списке покупок'

    def __str__(self):
        return (
            f'{self.recipe.name[:constants.STR_MAX_LENGTH_SHORT]} '
            'в списке покупок у '
            f'{self.user.username[:constants.STR_MAX_LENGTH_SHORT]}.'
        )
