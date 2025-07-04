from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from . import serializers
from .filters import IngredientFilter, RecipeFilter
from .permissions import IsAuthorOrReadOnly
from .utils import create_delete_object, get_pdf_in_response
from food.models import Favorite, Ingredient, Recipe, ShoppingCart, Tag
from users.models import Subscription


class CustomUserViewSet(UserViewSet):
    def get_permissions(self):
        action = self.action
        if (
            action in (
                'activation', 'resend_activation', 'reset_password',
                'reset_password_confirm', 'set_username',
                'reset_username', 'reset_username_confirm',
            )
        ):
            raise NotFound()
        if action not in ('me', 'subscriptions', 'subscribe'):
            self.permission_classes = (IsAuthenticatedOrReadOnly,)
        return super().get_permissions()

    @action(
        ['get', 'delete', 'put'], detail=False, url_path=r'(me(|/avatar))',
    )
    def me(self, request, *args, **kwargs):
        self.get_object = self.get_instance
        user = request.user
        if request.method == 'GET':
            return self.retrieve(request, *args, **kwargs)
        if request.method == 'DELETE':
            user.avatar = None
            user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = serializers.UserAvatarSerializer(user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status.HTTP_200_OK)

    @action(['post', 'delete'], detail=True)
    def subscribe(self, request, id):
        return create_delete_object(Subscription, request, self.queryset, id)

    @action(['get'], detail=False)
    def subscriptions(self, request):
        subs = request.user.subscriptions.values_list('author', flat=True)
        queryset = self.queryset.filter(pk__in=subs)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = serializers.SubscriptionSerializer(
                page, context={'request': request}, many=True,
            )
            return self.get_paginated_response(serializer.data)
        serializer = serializers.SubscriptionSerializer(queryset)
        return Response(serializer.data, status.HTTP_200_OK)


class IngredientViewSet(ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = serializers.IngredientSerializer
    pagination_class = None
    permission_classes = (AllowAny,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class TagViewSet(ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = serializers.TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class RecipeViewSet(ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = serializers.RecipeSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    http_method_names = ('get', 'post', 'patch', 'delete')

    def get_permissions(self):
        if self.action != 'download_shopping_cart':
            self.permission_classes = (
                IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly,
            )
        return super().get_permissions()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(['get'], detail=True, url_path='get-link')
    def get_link(self, request, pk):
        serializer = serializers.RecipeGetLinkSerializer(
            get_object_or_404(Recipe, pk=pk), context={'request': request},
        )
        return Response(serializer.data, status.HTTP_200_OK)

    @action(['post', 'delete'], detail=True)
    def favorite(self, request, pk):
        return create_delete_object(Favorite, request, self.queryset, pk)

    @action(['post', 'delete'], detail=True)
    def shopping_cart(self, request, pk):
        return create_delete_object(ShoppingCart, request, self.queryset, pk)

    @action(['get'], detail=False)
    def download_shopping_cart(self, request):
        recipes = request.user.shopping_cart.values_list('recipe', flat=True)
        queryset = self.queryset.filter(pk__in=recipes)
        shopping_cart = {}
        for recipe in queryset:
            for name, amount, unit in recipe.ingredients_for.values_list(
                'ingredient__name',
                'amount',
                'ingredient__measurement_unit',
            ):
                existing_amount = shopping_cart.get(name, [0, 'шт.'])[0]
                shopping_cart[name] = [amount + existing_amount, unit]
        return get_pdf_in_response(shopping_cart)
