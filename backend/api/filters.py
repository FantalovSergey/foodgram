from django_filters.rest_framework import BooleanFilter, CharFilter, FilterSet

from food.models import Ingredient, Recipe


class IngredientFilter(FilterSet):
    name = CharFilter(lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ('name',)


class RecipeFilter(FilterSet):
    is_favorited = BooleanFilter(method='boolean_recipe_filter')
    is_in_shopping_cart = BooleanFilter(method='boolean_recipe_filter')
    tags = CharFilter(method='tags_filter')

    class Meta:
        fields = ('author', 'is_favorited', 'is_in_shopping_cart', 'tags')
        model = Recipe

    def boolean_recipe_filter(self, queryset, name, value):
        user = self.request.user
        if user.is_authenticated:
            manager = (
                user.favorites if name == 'is_favorited'
                else user.shopping_cart
            )
            recipes = manager.values_list('recipe', flat=True)
        else:
            recipes = []
        return (
            queryset.filter(pk__in=recipes) if value
            else queryset.exclude(pk__in=recipes)
        )

    def tags_filter(self, queryset, name, _):
        tags = self.data.getlist(name)
        return queryset.filter(tags__slug__in=tags).distinct()
