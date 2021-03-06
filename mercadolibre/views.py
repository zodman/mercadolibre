from django.views import View
from django.contrib import messages
from django.shortcuts import redirect
from django.core.urlresolvers import reverse_lazy
from .mercado_libre import MeliApp
from .models import MeliAccount
from django.conf import settings
# Create your views here.

MELI = MeliApp()


class AutorizeApp(View):
    """
    View for interactions with mercado libre
    """
    def get(self, request):
        uri = reverse_lazy('mercadolibre:meli_redirect')
        auth_url = MELI.autenticate_url(request=request, redirect_to=uri)
        return redirect(auth_url)


class Redirect(View):
    def get(self, request):
        user = request.user
        get_data = request.GET.dict()
        code = get_data.get('code')
        uri = reverse_lazy('mercadolibre:meli_redirect')
        token, refresh = MELI.generate_tokens(request=request, code=code,
                                              redirect_to=uri)
        extra_data = MELI.account()
        meliaccount = MeliAccount()
        meliaccount.user = user
        meliaccount.refresh_token = refresh
        meliaccount.temporal_access_token = token
        meliaccount.temporal_code = code
        meliaccount.id = extra_data['id']
        meliaccount.site_id = extra_data['site_id']
        meliaccount.nickname = extra_data['nickname']
        meliaccount.country_id = extra_data['country_id']
        meliaccount.save()

        reverse_str = getattr(settings, "MERCADO_LIBRE_REDIRECT",
                              'admin:konfidence_car_changelist')
        redirect_url = reverse_lazy(reverse_str)
        messages.info(request,"Usuario [{}] Autentificado con ML".format(extra_data["nickname"]))
        return redirect(redirect_url)
