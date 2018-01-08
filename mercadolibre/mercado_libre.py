# -*- coding: utf-8 -*-
__author__ = 'sergio'
from django.conf import settings
# from django.core.urlresolvers import reverse_lazy
from .utils import get_host, response_by_raw
from sdk.meli import Meli


class MeliApp(object):

    def __init__(self, access_token=None, refresh_token=None):
        self.app_id = getattr(settings, 'MERCADO_LIBRE_ID')
        self.secret_token = getattr(settings,  'MERCADO_LIBRE_SECRET_KEY')
        self.access_token = access_token

        if access_token and refresh_token:
            self.SDK = Meli(
                client_id=self.app_id,
                client_secret=self.secret_token,
                access_token=access_token,
                refresh_token=refresh_token
            )
        else:
            self.SDK = Meli(
                client_id=self.app_id,
                client_secret=self.secret_token)

    def _process_get_request(self, uri, params={}, headers=None, raw=False):
        """
        Made a GET request and precess the response
        :param uri: String
        :param params: Dictionary
        :param headers: Dictionary: Custom header
        :param raw: Boolean: if you want the request object of python
        :return: Dictionary / Object (Raw case)
        """
        if headers:
            resp = self.SDK.get(path=uri, params=params, headers=headers)
        else:
            resp = self.SDK.get(path=uri, params=params)
        return response_by_raw(resp, raw)

    def create_test_user(self, raw=False):
        uri = '/users/test_user'
        params = {'access_token': self.access_token}
        body = {'site_id': getattr(settings, 'DEFAULT_SITE_ID')}
        resp = self.SDK.post(uri, body, params)
        return response_by_raw(resp, raw)

    def autenticate_url(self, request, redirect_to):
        """
        :param request: Object; HTTP request of a Django View
        :param redirect_to: String: URI, register in the app
        :return: String: URL for authorize the app
        """
        host = get_host(request)
        uri = host + str(redirect_to)
        auth_url = self.SDK.auth_url(redirect_URI=uri)
        return auth_url

    def generate_tokens(self, request, code, redirect_to):
        """
        :param request: Object; HTTP request of a Django View
        :param code: String: Code obtained when authorizing the application
        :param redirect_to: String: URI for redirect. the same of app
        :return: (String, String): (access_token, refresh_token)
        """
        host = get_host(request)
        uri = host + str(redirect_to)
        return self.SDK.authorize(code=code, redirect_URI=uri)

    def account(self):
        """
        Get the user data
        :return: Dictionary
        """
        return self.SDK.get_user_data()

    def notificaciones(self):
        """
        Get a dictionary with the notifications of user
        :return: Dictionary
        """
        return self.SDK.get(path='/myfeeds', params={'app_id': self.app_id})

    def refresh_token(self, refresh_token):
        """
        Refresh the access token of the user
        :param refresh_token: String
        :return: String: New Access token
        """
        return self.SDK.get_refresh_token(refresh_token)

    def get_promotion_packs(self, category_id=None, raw=False):
        """
        List of all promotions packs
        :param category_id: String
        :param raw: Boolean
        :return: Dictionary / Object (Raw case)
        """
        if not category_id:
            category_id = getattr(settings, 'DEFAULT_CATEGORY')
        uri = '/categories/%s/classifieds_promotion_packs' % category_id
        return self._process_get_request(uri=uri, raw=raw)

    def have_user_promotion_packs(self, user_id, access_token, raw=False):
        """
        consult for check if the user have promotions packs
        :param user_id: String
        :param access_token: String
        :param raw: Boolean
        :return: Dictionary / Object (Raw case)
        """
        if not (user_id and access_token):
            raise (Exception, "user_id and access_token is required")
        uri = '/users/%s/classifieds_promotion_packs/' \
              'silver?access_token=%s' % (user_id, access_token)
        resp = self._process_get_request(uri=uri, raw=True)
        return response_by_raw(resp, raw)

    def get_user_promotion_packs(self, user_id, access_token, raw=False):
        """
        get the user purchase promotions packs
        :param user_id: String
        :param access_token: String
        :param raw: Boolean
        :return: Dictionary / Object (Raw case)
        """
        if not (user_id and access_token):
            raise (Exception, "user_id and access_token is required")
        uri = '/users/%s/classifieds_promotion_packs?access_token=%s' % (user_id, access_token)
        resp = self._process_get_request(uri=uri, raw=True)
        return response_by_raw(resp, raw)

    def active_promotion_pack(self, user_id, access_token, category_id, promotion_pack_id, raw=False):
        """
        active one promotion pack
        :param user_id: String
        :param access_token: String
        :param category_id: String
        :param promotion_pack_id: String
        :return: Dictionary / Object (Raw case)
        """
        params = {'categ_id': category_id,
                  'promotion_pack_id': promotion_pack_id,
                  'engagement_type': 'none',
                  'status': 'active'}
        path = '/users/%s/classifieds_promotion_packs?access_token=%s' % (user_id, access_token)
        resp = self.SDK.get(path=path, params=params)
        return response_by_raw(resp, raw)

    def list(self, type_path, attributes=False):
        """
        :param type_path:
        :param attributes:
        :return: Django Request
        """
        uri = '/%s' % type_path
        if attributes:
            uri = '/%sall?withAttributes=true' % type_path
        return self._process_get_request(uri)

    def details(self, type_path, type_id):
        """
        :param type_path: String: States/Cities/Country/...
        :param type_id: String: ID of Mercado libre
        :return: Django Request
        """
        uri = 'classified_locations/%s/%s' % (type_path, type_id)
        return self._process_get_request(uri)

    def category(self, site_id, category_id=None, attribute=None, raw=False):
        """
        Get the dictionary of category by id
        get the attribute of dictionary
        :param site_id: String
        :param category_id: String
        :param attribute: String
        :param raw: Boolean: if you want the request object of python
        :return: Dictionary / Object (Raw case)
        """
        if category_id:
            uri = '/categories/%s?withAttributes=true' % category_id
        else:
            uri = '/sites/%s/categories/' % site_id
        resp = self.SDK.get(path=uri)
        json_data = response_by_raw(resp, raw)
        if attribute:
            return json_data[attribute]
        else:
            return json_data

    def post_item(self, item_data, raw=False):
        """
        :param item_data: Dictionary
        :param raw: Boolean: True for return the Request
        :return: Django Request/Dictionary
        """
        params = {'access_token': self.access_token}
        uri = '/items'
        resp = self.SDK.post(uri, body=item_data, params=params)
        return response_by_raw(resp, raw)

    def item_update(self, item_id, updated_data, raw=False):
        """
        :param updated_data: Dictionary
        :param raw: Boolean: True for return the Request
        :return:  Django Request/Dictionary
        """
        params = {'access_token': self.access_token}
        uri = '/items/%s' % item_id
        resp = self.SDK.put(uri, body=updated_data, params=params)
        return response_by_raw(resp, raw)

    def item_update_description(self, item_id, updated_data, raw=False):
        """
        :param updated_data: Dictionary
        :param raw: Boolean: True for return the Request
        :return:  Django Request/Dictionary
        """
        params = {'access_token': self.access_token}
        # uri = '/items/%s' % item_id
        uri = '/items/%s/description' % item_id
        resp = self.SDK.put(uri, body=updated_data, params=params)
        return response_by_raw(resp, raw)

    def upload_picture(self, file_path, access_token, raw=False):
        uri = '/pictures?access_token=%s' % access_token
        resp = self.SDK.post_file(uri, file_path)
        return response_by_raw(resp, raw)
