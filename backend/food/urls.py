from django.urls import path

from .views import RecipeRedirectView

urlpatterns = [
    path(
        'SL/<slug:short_link>/',
        RecipeRedirectView.as_view(),
        name='recipe_redirect',
    )
]
