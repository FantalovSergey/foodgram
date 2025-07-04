from django.contrib.auth import get_user_model
from djoser.conf import settings as djoser_settings
from djoser.serializers import UserSerializer
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from .fields import Base64ImageField
from food.models import Ingredient, Recipe, RecipeIngredient, Tag

User = get_user_model()


class CustomUserSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = tuple(User.REQUIRED_FIELDS) + (
            djoser_settings.USER_ID_FIELD,
            djoser_settings.LOGIN_FIELD,
        ) + ('avatar', 'is_subscribed')

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        return (
            obj.pk in user.subscriptions.values_list('author', flat=True)
            if user.is_authenticated else False
        )


class UserAvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ('avatar',)


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.values_list('id', flat=True),
        source='ingredient',
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


class RecipeSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True,
    )
    author = CustomUserSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(
        many=True, source='ingredients_for',
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField()

    class Meta:
        fields = (
            'id', 'tags', 'author', 'ingredients', 'is_favorited',
            'is_in_shopping_cart', 'name', 'image', 'text', 'cooking_time',
        )
        model = Recipe

    def get_is_favorited(self, obj):
        user = self.context['request'].user
        return (
            obj.pk in user.favorites.values_list('recipe', flat=True)
            if user.is_authenticated else False
        )

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user
        return (
            obj.pk in user.shopping_cart.values_list('recipe', flat=True)
            if user.is_authenticated else False
        )

    def validate(self, attrs):
        if 'ingredients_for' in attrs:
            attrs['ingredients'] = attrs.pop('ingredients_for')
            error = {}
        else:
            error = {'ingredients': 'Required field.'}
        for field in ('tags', 'ingredients'):
            for message, condition in (
                ('Required field.', field not in attrs),
                ('The field must be filled.', not attrs.get(field)),
            ):
                if field not in error and condition:
                    error[field] = message
        if error:
            raise ValidationError(error)
        return attrs

    def validate_tags(self, value):
        if len(value) != len(set(value)):
            raise ValidationError(
                {'tags': 'Repetitive tags are not allowed.'}
            )
        return value

    def validate_ingredients(self, value):
        id = [ingredient['ingredient'] for ingredient in value]
        if len(id) != len(set(id)):
            raise ValidationError(
                {'ingredients': 'id must be unique in the list.'}
            )
        return value

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        ingredients_to_insert = [
            RecipeIngredient(
                recipe=recipe,
                ingredient=Ingredient.objects.get(id=ingredient['ingredient']),
                amount=ingredient['amount'],
            ) for ingredient in ingredients
        ]
        recipe.ingredients_for.bulk_create(ingredients_to_insert)
        return recipe

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', None)
        ingredients = validated_data.pop('ingredients', None)
        instance.name = validated_data.get('name')
        instance.image = validated_data.get('image', instance.image)
        instance.text = validated_data.get('text')
        instance.cooking_time = validated_data.get('cooking_time')
        if tags:
            instance.tags.set(tags)
        if ingredients:
            instance.ingredients_for.all().delete()
            ingredients_to_insert = [
                RecipeIngredient(
                    recipe=instance,
                    ingredient=Ingredient.objects.get(
                        id=ingredient['ingredient']
                    ),
                    amount=ingredient['amount'],
                ) for ingredient in ingredients
            ]
            instance.ingredients_for.bulk_create(ingredients_to_insert)
        instance.save()
        return instance

    def to_representation(self, instance):
        self.fields['tags'] = TagSerializer(many=True)
        return super().to_representation(instance)


class RecipeGetLinkSerializer(serializers.Serializer):
    short_link = serializers.SerializerMethodField()

    class Meta:
        fields = ('short_link',)

    def get_short_link(self, obj):
        return self.context['request'].build_absolute_uri(obj.short_link)

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['short-link'] = representation.pop('short_link')
        return representation


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    image = Base64ImageField()

    class Meta:
        fields = ('id', 'name', 'image', 'cooking_time')
        model = Recipe


class SubscriptionSerializer(CustomUserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta(CustomUserSerializer.Meta):
        fields = tuple(User.REQUIRED_FIELDS) + (
            djoser_settings.USER_ID_FIELD,
            djoser_settings.LOGIN_FIELD,
        ) + ('avatar', 'is_subscribed', 'recipes', 'recipes_count')

    def get_recipes(self, obj):
        recipes_limit = self.context['request'].GET.get('recipes_limit')
        if recipes_limit is not None:
            try:
                recipes_limit = int(recipes_limit)
            except ValueError:
                raise serializers.ValidationError(
                    'recipes_limit must be int.')
        queryset = obj.recipes.all()[:recipes_limit]
        return RecipeMinifiedSerializer(queryset, many=True).data

    def get_recipes_count(self, obj):
        return len(obj.recipes.all())


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('id', 'name', 'measurement_unit')
        model = Ingredient


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('id', 'name', 'slug')
        model = Tag
