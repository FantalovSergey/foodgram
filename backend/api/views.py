from django.db.models import Exists, OuterRef, Sum, Value
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import permissions
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from . import serializers
from .filters import IngredientFilter, RecipeFilter
from .permissions import IsAuthorOrReadOnly
from .utils import create_delete_object, get_pdf_in_response
from food import models


class FoodgramUserViewSet(UserViewSet):
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    @action(
        methods=['get'],
        detail=False,
        permission_classes=(permissions.IsAuthenticated,)
    )
    def me(self, request):
        serializer = serializers.FoodgramUserSerializer(
            request.user, context={'request': request},
        )
        return Response(serializer.data, status.HTTP_200_OK)

    @action(
        methods=['delete', 'put'],
        detail=False,
        url_path=r'me/avatar',
        permission_classes=(permissions.IsAuthenticated,),
    )
    def avatar(self, request):
        user = request.user
        if request.method == 'DELETE':
            request.user.avatar.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = serializers.UserAvatarSerializer(user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status.HTTP_200_OK)

    @action(
        methods=['delete', 'post'],
        detail=True,
        permission_classes=(permissions.IsAuthenticated,),
    )
    def subscribe(self, request, id):
        author = get_object_or_404(self.queryset, id=id)
        user = request.user
        if request.method == 'DELETE':
            was_deleted, _ = user.subscriptions.filter(author=author).delete()
            if not was_deleted:
                raise ValidationError('Подписки не существует.')
            return Response(status=status.HTTP_204_NO_CONTENT)
        if author == user:
            raise ValidationError('Нельзя подписаться на самого себя.')
        _, was_created = user.subscriptions.get_or_create(author=author)
        if not was_created:
            raise ValidationError('Уже в подписках.')
        serializer = serializers.SubscriptionSerializer(
            author, context={'request': request},
        )
        return Response(serializer.data, status.HTTP_201_CREATED)

    @action(
        methods=['get'],
        detail=False,
        permission_classes=(permissions.IsAuthenticated,),
    )
    def subscriptions(self, request):
        subs = request.user.subscriptions.values_list('author', flat=True)
        queryset = self.queryset.filter(pk__in=subs)
        page = self.paginate_queryset(queryset)
        serializer = serializers.SubscriptionSerializer(
            page, context={'request': request}, many=True,
        )
        return self.get_paginated_response(serializer.data)


class IngredientViewSet(ReadOnlyModelViewSet):
    queryset = models.Ingredient.objects.all()
    serializer_class = serializers.IngredientSerializer
    pagination_class = None
    permission_classes = (permissions.AllowAny,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class TagViewSet(ReadOnlyModelViewSet):
    queryset = models.Tag.objects.all()
    serializer_class = serializers.TagSerializer
    permission_classes = (permissions.AllowAny,)
    pagination_class = None


class RecipeViewSet(ModelViewSet):
    permission_classes = (
        permissions.IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly,
    )
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    http_method_names = ('get', 'post', 'patch', 'delete')

    def get_queryset(self):
        user = self.request.user
        if user.is_anonymous:
            return models.Recipe.objects.annotate(
                is_favorited=Value(False), is_in_shopping_cart=Value(False),
            ).order_by('-created_at')
        in_favorites = user.favorites.filter(recipe=OuterRef('pk'))
        in_shopping_cart = user.shoppingcart.filter(recipe=OuterRef('pk'))
        return models.Recipe.objects.annotate(
            is_favorited=Exists(in_favorites),
            is_in_shopping_cart=Exists(in_shopping_cart),
        ).order_by('-created_at')

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return serializers.RecipeReadSerializer
        return serializers.RecipeWriteSerializer

    @action(methods=['get'], detail=True, url_path='get-link')
    def get_link(self, request, pk):
        recipe = get_object_or_404(models.Recipe, pk=pk)
        relative_uri = '/SL/' + recipe.short_link + '/'
        data = {'short-link': request.build_absolute_uri(relative_uri)}
        return Response(data, status.HTTP_200_OK)

    @action(methods=['post', 'delete'], detail=True)
    def favorite(self, request, pk):
        return create_delete_object(
            models.Favorites, request, self.get_queryset(), pk,
        )

    @action(methods=['post', 'delete'], detail=True)
    def shopping_cart(self, request, pk):
        return create_delete_object(
            models.ShoppingCart, request, self.get_queryset(), pk,
        )

    @action(
        methods=['get'],
        detail=False,
        permission_classes=(permissions.IsAuthenticated,),
    )
    def download_shopping_cart(self, request):
        ingredients = models.RecipeIngredient.objects.filter(
            recipe__in_shoppingcart__user=request.user
        ).values(
            'ingredient__name', 'ingredient__measurement_unit',
        ).annotate(
            amount=Sum('amount')
        ).order_by(
            'ingredient__name'
        )
        shopping_cart = {
            ingredient['ingredient__name']: (
                ingredient['amount'],
                ingredient['ingredient__measurement_unit'],
            ) for ingredient in ingredients
        }
        return get_pdf_in_response(shopping_cart)
