from django.contrib import admin
from .models import Agent, Property


@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'phone_number')


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ('title', 'location', 'price', 'property_type', 'agent', 'created_at')
    list_filter = ('property_type', 'agent')
    search_fields = ('title', 'location')
