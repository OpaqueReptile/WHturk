from django.contrib import admin

# Register your models here.

from .models import Character, System, Connection

admin.site.register(Character)
admin.site.register(System)
admin.site.register(Connection)
