from django.views.generic.base import RedirectView

from .models import Recipe


class RecipeRedirectView(RedirectView):
    def get_redirect_url(self, **kwargs):
        try:
            recipe = Recipe.objects.get(short_link=kwargs['short_link'])
        except Recipe.DoesNotExist:
            return '/not-found/'
        return f'/recipes/{recipe.pk}/'
