from django.contrib import admin
from .models import MLCity as City, MLState as State, MeliAccount
from django.conf.urls import url
from django.template.response import TemplateResponse
from django.utils.text import capfirst
from django.utils.encoding import force_text


@admin.register(MeliAccount)
class MeliAccountAdmin(admin.ModelAdmin):
    pass

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


class MixinAdminBaseML:

    def get_urls(self):
        # Return Model admin URLs plus custom urls
        urls = super(MixinAdminBaseML, self).get_urls()
        # info = self.model._meta.app_label, self.model._meta.model_name
        custom_urls = [
            url(r'^mercadolibre',
                self.admin_site.admin_view(self.meli_info_view),
                name='meli_auth'),
        ]
        return custom_urls + urls

    def meli_info_view(self, request):
        """
        Show MercadoLibre login information.
        """
        model = self.model
        opts = model._meta
        context = dict(
            self.admin_site.each_context(request),
            title=u'Información Importante - MercadoLibre',
            module_name=capfirst(force_text(opts.verbose_name_plural)),
            opts=opts,
        )
        return TemplateResponse(request, 'admin/mercadolibre/meli_info.html',
                                context)
