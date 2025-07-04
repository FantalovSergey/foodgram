from django.contrib import admin

from . import models


class RecipeIngredientInline(admin.TabularInline):
    model = models.RecipeIngredient
    min_num = 1
    extra = 0


class RecipeTagInline(admin.TabularInline):
    model = models.Recipe.tags.through
    min_num = 1
    extra = 0


class RecipeAdmin(admin.ModelAdmin):
    inlines = (RecipeIngredientInline, RecipeTagInline)
    exclude = ('tags',)
    search_fields = ('author__username', 'name')
    list_filter = ('tags',)
    readonly_fields = ('in_favorites_count', 'short_link')


class IngredientAdmin(admin.ModelAdmin):
    search_fields = ('name',)


admin.site.register((models.Favorite, models.ShoppingCart, models.Tag))
admin.site.register(models.Ingredient, IngredientAdmin)
admin.site.register(models.Recipe, RecipeAdmin)
