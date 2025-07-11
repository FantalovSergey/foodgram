from django.contrib import admin
from django.db.models import Count

from . import models


class RecipeIngredientInline(admin.TabularInline):
    model = models.RecipeIngredient
    min_num = 1
    extra = 0


class RecipeTagInline(admin.TabularInline):
    model = models.Recipe.tags.through
    min_num = 1
    extra = 0


@admin.register(models.Recipe)
class RecipeAdmin(admin.ModelAdmin):
    inlines = (RecipeIngredientInline, RecipeTagInline)
    exclude = ('tags',)
    search_fields = ('author__username', 'name')
    list_filter = ('tags',)
    readonly_fields = ('created_at', 'in_favorites_count', 'short_link')

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            in_favorites_count=Count('in_favorites')
        ).order_by(
            '-created_at'
        )

    def in_favorites_count(self, obj):
        return obj.in_favorites_count

    in_favorites_count.short_description = 'Добавлений в избранное'


@admin.register(models.Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    search_fields = ('name',)


admin.site.register((models.Favorites, models.ShoppingCart, models.Tag))
