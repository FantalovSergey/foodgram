from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin

from .models import Subscription

User = get_user_model()


@admin.register(User)
class FoodgramUserAdmin(UserAdmin):
    fieldsets = (
        (None, {
            "fields": (
                'username', 'email', 'first_name', 'last_name',
                'avatar', 'password', 'is_active',
            ),
        }),
    )
    search_fields = ('username', 'email')


admin.site.register(Subscription)
