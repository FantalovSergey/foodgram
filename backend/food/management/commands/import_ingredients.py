import csv
import os

from django.conf import settings
from django.core.management.base import BaseCommand

from food.models import Ingredient


class Command(BaseCommand):
    help = 'Импорт ингредиентов в базу данных.'

    def handle(self, *args, **options):
        self.load_ingredients(
            os.path.join(settings.BASE_DIR, 'ingredients.csv'),
        )

    def load_ingredients(self, filepath):
        with open(filepath, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            ingredients = []
            names = []
            for name, measurement_unit in reader:
                ingredients.append(
                    Ingredient(name=name, measurement_unit=measurement_unit),
                )
                names.append(name)
            ingredients_in_db = Ingredient.objects.filter(
                name__in=names).values_list('name', flat=True)
            ingredients_to_insert = [
                ingredient for ingredient in ingredients
                if ingredient.name not in ingredients_in_db
            ]
            Ingredient.objects.bulk_create(ingredients_to_insert)
