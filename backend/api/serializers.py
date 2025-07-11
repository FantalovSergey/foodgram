from django.contrib.auth import get_user_model
from django.db import transaction
from djoser.serializers import UserSerializer
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from .fields import Base64ImageField
from food.models import Ingredient, Recipe, RecipeIngredient, Tag

User = get_user_model()


class FoodgramUserSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ('avatar', 'is_subscribed')

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        return (
            request
            and request.user.is_authenticated
            and request.user.subscriptions.filter(author=obj).exists()
        )


class UserAvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ('avatar',)

    def validate_avatar(self, value):
        if not value:
            raise ValidationError({'avatar': 'Поле не может быть пустым.'})
        return value


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('id', 'name', 'slug')
        model = Tag


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(), source='ingredient',
    )
    name = serializers.SlugRelatedField(
        source='ingredient', slug_field='name', read_only=True,
    )
    measurement_unit = serializers.SlugRelatedField(
        source='ingredient', slug_field='measurement_unit', read_only=True,
    )

    class Meta:
        fields = ('id', 'name', 'amount', 'measurement_unit')
        model = RecipeIngredient


class RecipeReadSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True)
    author = FoodgramUserSerializer()
    ingredients = RecipeIngredientSerializer(
        many=True, source='ingredients_for',
    )
    is_favorited = serializers.BooleanField(default=False)
    is_in_shopping_cart = serializers.BooleanField(default=False)
    image = Base64ImageField()

    class Meta:
        fields = (
            'id', 'tags', 'author', 'ingredients', 'is_favorited',
            'is_in_shopping_cart', 'name', 'image', 'text', 'cooking_time',
        )
        model = Recipe


class RecipeWriteSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True,
    )
    ingredients = RecipeIngredientSerializer(
        many=True, source='ingredients_for',
    )
    image = Base64ImageField()

    class Meta:
        fields = (
            'id', 'tags', 'ingredients', 'name',
            'image', 'text', 'cooking_time',
        )
        model = Recipe

    def validate(self, attrs):
        if 'ingredients_for' in attrs:
            attrs['ingredients'] = attrs.pop('ingredients_for')
            error = {}
        else:
            error = {'ingredients': 'Обязательное поле.'}
        for field in ('tags', 'ingredients'):
            for message, condition in (
                ('Обязательное поле.', field not in attrs),
                ('Поле не должно быть пустым.', not attrs.get(field)),
            ):
                if field not in error and condition:
                    error[field] = message
        if error:
            raise ValidationError(error)
        return attrs

    def validate_tags(self, value):
        if len(value) != len(set(value)):
            raise ValidationError(
                {'tags': 'Теги не должны повторяться.'}
            )
        return value

    def validate_ingredients(self, value):
        id_list = [ingredient['ingredient'] for ingredient in value]
        if len(id_list) != len(set(id_list)):
            raise ValidationError(
                {'ingredients': 'id ингредиентов не должны повторяться.'}
            )
        return value

    def add_tags_and_ingredients(self, recipe, tags, ingredients):
        recipe.tags.set(tags)
        ingredients_to_insert = [
            RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient['ingredient'],
                amount=ingredient['amount'],
            ) for ingredient in ingredients
        ]
        recipe.ingredients_for.bulk_create(ingredients_to_insert)
        return recipe

    @transaction.atomic
    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        validated_data['author'] = self.context['request'].user
        recipe = Recipe.objects.create(**validated_data)
        return self.add_tags_and_ingredients(recipe, tags, ingredients)

    @transaction.atomic
    def update(self, instance, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        instance.ingredients.clear()
        instance = self.add_tags_and_ingredients(instance, tags, ingredients)
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        return RecipeReadSerializer(instance, context=self.context).data


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    image = Base64ImageField()

    class Meta:
        fields = ('id', 'name', 'image', 'cooking_time')
        model = Recipe


class SubscriptionSerializer(FoodgramUserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta(FoodgramUserSerializer.Meta):
        fields = (
            FoodgramUserSerializer.Meta.fields + ('recipes', 'recipes_count')
        )

    def get_recipes(self, obj):
        recipes_limit = self.context['request'].GET.get('recipes_limit')
        if recipes_limit is not None:
            try:
                recipes_limit = int(recipes_limit)
            except ValueError:
                raise serializers.ValidationError(
                    'recipes_limit должен быть int.')
        queryset = obj.recipes.all()[:recipes_limit]
        return RecipeMinifiedSerializer(queryset, many=True).data

    def get_recipes_count(self, obj):
        return obj.recipes.count()


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('id', 'name', 'measurement_unit')
        model = Ingredient
