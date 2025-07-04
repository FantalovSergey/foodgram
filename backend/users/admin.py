from django.contrib import admin

from .models import Subscription, User


class UserAdmin(admin.ModelAdmin):
    fields = (
        'username', 'email', 'first_name', 'last_name',
        'avatar', 'password', 'is_active',
    )
    search_fields = ('username', 'email')


admin.site.register(User, UserAdmin)
admin.site.register(Subscription)
