from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic.base import RedirectView

from .models import Recipe


class RecipeRedirectView(RedirectView):
    def get_redirect_url(self):
        recipe = get_object_or_404(Recipe, short_link=self.request.path)
        url = reverse('recipes-detail', args=(recipe.pk,))
        return url.replace('/api', '', 1)
