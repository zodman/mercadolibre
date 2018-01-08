from django.contrib import admin
from .models import City, State

@admin.register(City)
class CarCustomerAdmin(admin.ModelAdmin):
    search_fields = ('name',)
    fields = ('id', 'name', 'state')
    list_display = ('name', 'state')
    ordering = ('state', 'name')
    list_filter = ('state',)

@admin.register(State)
class CarCustomerAdmin(admin.ModelAdmin):
    search_fields = ('name',)
    fields = ('id', 'name')
    ordering = ('name',)
    list_display = ('name', 'total_ciudades')


    def total_ciudades(self, state):
        return state.cities.count()


