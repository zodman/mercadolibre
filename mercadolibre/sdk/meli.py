#!/usr/bin/env python
# -*- coding: utf-8 -*-

from configparser import SafeConfigParser
from urllib.parse import urlencode
import simplejson as json
import os
import re
import ssl
import requests
from .ssl_helper import SSLAdapter
from django.conf import settings


class Meli(object):

    def __init__(self, client_id, client_secret, access_token=None, refresh_token=None):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.expires_in = None

        parser = SafeConfigParser()
        parser.read(os.path.dirname(os.path.abspath(__file__))+'/config.ini')

        self._requests = requests.Session()
        try:
            self.SSL_VERSION = parser.get('config', 'ssl_version')
            self._requests.mount('https://', SSLAdapter(ssl_version=getattr(ssl, self.SSL_VERSION)))
        except Exception:
            self._requests = requests

        self.API_ROOT_URL = getattr(
            settings,
            'MERCADO_LIBRE_API_ROOT_URL',
            parser.get('config', 'api_root_url')
        )

        self.SDK_VERSION = getattr(
            settings,
            'MERCADO_LIBRE_SDK_VERSION',
            parser.get('config', 'sdk_version')
        )
        self.AUTH_URL = getattr(
            settings,
            'MERCADO_LIBRE_AUTH_URL',
            parser.get('config',  'auth_url')

        )

        self.OAUTH_URL = getattr(
            settings,
            'MERCADO_LIBRE_OAUTH_URL',
            parser.get('config', 'oauth_url')
        )

        self.headers = {'Accept': 'application/json', 'User-Agent': self.SDK_VERSION, 'Content-type': 'application/json'}

    # AUTH METHODS
    def auth_url(self, redirect_URI):
        params = {'client_id': self.client_id, 'response_type': 'code', 'redirect_uri': redirect_URI}
        url = self.AUTH_URL + '/authorization' + '?' + urlencode(params)
        return url

    def authorize(self, code, redirect_URI):
        params = {'grant_type': 'authorization_code', 'client_id': self.client_id, 'client_secret': self.client_secret, 'code': code, 'redirect_uri': redirect_URI}
        uri = self.make_path(self.OAUTH_URL)
        response = self._requests.post(uri, params=urlencode(params), headers=self.headers)
        if response.ok:
            response_info = response.json()
            self.access_token = response_info['access_token']
            if 'refresh_token' in response_info:
                self.refresh_token = response_info['refresh_token']
            else:
                self.refresh_token = '' # offline_access not set up
                self.expires_in = response_info['expires_in']

            return self.access_token, self.refresh_token
        else:
            # response code isn't a 200; raise an exception
            response.raise_for_status()

    def get_refresh_token(self, refresh_token):

        if refresh_token:
            params = {'grant_type': 'refresh_token', 'client_id': self.client_id, 'client_secret': self.client_secret, 'refresh_token': refresh_token}
            uri = self.make_path(self.OAUTH_URL)

            response = self._requests.post(uri, params=urlencode(params), headers=self.headers, data=params)
            if response.ok:
                response_info = response.json()
                self.access_token = response_info['access_token']
                self.refresh_token = response_info['refresh_token']
                self.expires_in = response_info['expires_in']
                return self.access_token, self.refresh_token
            else:
                # response code isn't a 200; raise an exception
                response.raise_for_status()
        else:
            raise (Exception, "Offline-Access is not allowed.")

    def get_user_data(self):
        params = {'access_token': self.access_token}
        response = self.get(path="/users/me", params=params)

        if response.status_code == requests.codes.ok:
            response_info = response.json()
            return response_info
        else:
            # response code isn't a 200; raise an exception
            response.raise_for_status()

    # REQUEST METHODS
    def get(self, path, params=False, headers=None):
        if not params:
            params = {}
        uri = self.make_path(path)
        if not headers:
            response = self._requests.get(uri, params=urlencode(params), headers=self.headers)
        else:
            response = self._requests.get(uri, params=urlencode(params), headers=headers)
        return response

    def post(self, path, body=False, params={}):
        uri = self.make_path(path)
        if body:
            body = json.dumps(body)
        # import q
        # q(uri, body, params, self.headers)
        response = self._requests.post(uri, data=body,
                                       params=urlencode(params),
                                       headers=self.headers)
        # q(response)
        return response

    def put(self, path, body=False, params={}):
        uri = self.make_path(path)
        if body:
            body = json.dumps(body)
        # import q
        # q(uri, body, params, self.headers)
        response = self._requests.put(uri, data=body, params=urlencode(params),
                                      headers=self.headers)
        # q(response)
        return response

    def delete(self, path, params={}):
        uri = self.make_path(path)
        response = self._requests.delete(uri, params=params, headers=self.headers)
        return response

    def post_file(self, path, file_path):
        try:
            files = {'upload_file': open(file_path, 'rb')}
        except Exception:
            # raise (Exception, "Not found file")
            return {'error': 'Not found file'}
        uri = self.make_path(path)
        response = self._requests.post(uri, headers=self.headers, files=files)
        return response

    def options(self, path, params={}):
        uri = self.make_path(path)
        response = self._requests.options(uri, params=urlencode(params), headers=self.headers)
        return response

    def make_path(self, path, params={}):
        # Making Path and add a leading / if not exist
        if not (re.search("^http", path)):
            if not (re.search("^\/", path)):
                path = "/" + path
            path = self.API_ROOT_URL + path
        if params:
            path = path + "?" + urlencode(params)
        return path
