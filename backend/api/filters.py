from django_filters.rest_framework import BooleanFilter, CharFilter, FilterSet

from food.models import Ingredient, Recipe


class IngredientFilter(FilterSet):
    name = CharFilter(lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ('name',)


class RecipeFilter(FilterSet):
    is_favorited = BooleanFilter(method='is_favorited_filter')
    is_in_shopping_cart = BooleanFilter(method='is_in_shopping_cart_filter')
    tags = CharFilter(method='tags_filter')

    class Meta:
        fields = ('author', 'is_favorited', 'is_in_shopping_cart', 'tags')
        model = Recipe

    def is_favorited_filter(self, queryset, _, value):
        user = self.request.user
        if user.is_anonymous or not isinstance(value, bool):
            return queryset
        return (
            queryset.filter(in_favorites__user=user) if value
            else queryset.exclude(in_favorites__user=user)
        )

    def is_in_shopping_cart_filter(self, queryset, _, value):
        user = self.request.user
        if user.is_anonymous or not isinstance(value, bool):
            return queryset
        return (
            queryset.filter(in_shoppingcart__user=user) if value
            else queryset.exclude(in_shoppingcart__user=user)
        )

    def tags_filter(self, queryset, name, _):
        tags = self.data.getlist(name)
        return queryset.filter(tags__slug__in=tags).distinct()
