from django.urls import re_path

from .views import RecipeRedirectView

urlpatterns = [
    re_path(
        r'^SL[a-zA-Z0-9]+/$',
        RecipeRedirectView.as_view(),
        name='recipe_redirect',
    )
]
