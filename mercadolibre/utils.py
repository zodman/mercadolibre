# -*- coding: utf-8 -*-
__author__ = 'sergio'
from django.contrib.sites.shortcuts import get_current_site
from django.conf import settings
from django.template import loader
from argparse import Namespace
from django.utils import timezone
import simplejson as json

STOP_AFTER_DAYS = getattr(settings, 'STOP_AFTER_DAYS', 90)
LISTING_PACKS = ['silver', 'gold', 'gold_premium']


def extract_meli_account(user):
    if hasattr(user, 'meli_account'):
        return user.meli_account
    return


def get_host(request):
    """
    :param request: Object: Django request
    :return: String: URL host of the site
    """
    site = get_current_site(request)
    protocol = 'https' if getattr(settings, 'USE_SSL', False) else 'http'
    return u'%s://%s' % (protocol, site.domain)


def response_by_raw(resp, raw=False):
    """
    :param resp: Object: request python
    :param raw: Boolean
    :return: Object / Dictionary
    """
    if raw:
        return resp
    if resp.ok:
        return resp.json()
    else:
        resp.raise_for_status()


def json_process(json_data):
    return json.loads(
        json.dumps(json_data),
        object_hook=lambda d: Namespace(**d)
    )


def html_description(car):
    """
    Returns item's description with HTML format.
    :param car: Car: selected vehicle.
    :return: String: formatted HTML description.
    """
    from django.contrib.sites.models import Site
    context = {
        'car_obj': car,
        'dealer': car.dealer,
        'site': Site.objects.get_current(),
        'debug': getattr(settings, 'DEBUG'),
    }
    return loader.render_to_string('mercadolibre/description.html', context=context)


def listing_pack_value(pack):
    type = pack['listing_type_id']
    return LISTING_PACKS.index(type)


def top_listing_pack(listings):
    top_listing = listings[0]
    for listing in listings:
        if listing['remaining_listings'] > 0:
            if listing_pack_value(listing) > listing_pack_value(top_listing):
                top_listing = listing

    return top_listing

##
#  u'[invalid property type: [start_time] expected DateTime but was String value: 2017-09-05 22:47:29.672649+00:00]'}"

#
FORMAT = "%Y-%m-%dT%h:%m:00.000Z"


class ItemCar(object):

    dic_base = {
        "site_id": getattr(settings, 'DEFAULT_SITE_ID',1),
        "title": "",
        "category_id": "",
        "official_store_id": None,
        "price": 380000,
        "currency_id": getattr(settings, 'DEFAULT_CURRENCY', 'MXN'),
        "available_quantity": 1,
        # "sold_quantity": 0,
        # "buying_mode": "classified",
        "listing_type_id": "free",
        "start_time":"".format(timezone.now().strftime(FORMAT)),
        "condition": "used",
        "pictures": list(),
        "video_id": None,
        "accepts_mercadopago": False,
        "non_mercado_pago_payment_methods": list(),
        "shipping": {
            "mode": "not_specified",
            "local_pick_up": False,
            "free_shipping": False,
            "methods": list(),
            "dimensions": None,
            "tags": list()
        },
        "location": {},
        "coverage_areas": list(),
        "attributes": list(),
        "variations": list(),
        "status": "active",
        "automatic_relist": False,
    }

    def __init__(self, account, category_id, title, description, price, pictures, listing_type='free'):
        self.dic_base.update({
            'title': title,
            'description': {'plain_text': description},
            'price': price,
            'category_id': category_id,
            'listing_type_id': listing_type
        })
        self._account = account
        self._app = account.user_meliapp
        self._category_id = category_id
        self._obj_data = self._dict_to_object()
        self._car_attributes = list()
        self.default_options()
        # self.set_seller()
        self.set_pictures(pictures)

    @staticmethod
    def json_process(json_data):
        return json.loads(
            json.dumps(json_data),
            object_hook=lambda d: Namespace(**d)
        )

    def _dict_to_object(self):
        cat_with_attributes = getattr(settings, 'DEFAULT_SUBCATEGORY', 'MLM1744')
        car = self._account.categories(cat_with_attributes)
        return self.json_process(car)

    def _attribute(self, attribute_id):
        for attr in self._obj_data.attributes:
            if attr.id == attribute_id:
                return attr

    def append_attribute(self, attribute_id, option_id):
        """
        Add the attribute of a Item
        :param attribute_id:
        :param option_id:
        :return:
        """
        value_option = None
        attr = self._attribute(attribute_id)
        if hasattr(attr, 'values'):
            for item in attr.values:
                if item.id == option_id:
                    value_option = item
                    break
        if not value_option:
            value_option = self.json_process({'id': '', 'name': option_id})

        tmp = {
            "id": attr.id,
            "name": attr.name,
            "value_id": value_option.id,
            "value_name": value_option.name,
            "attribute_group_id": attr.attribute_group_id,
            "attribute_group_name": attr.attribute_group_name
        }
        self._car_attributes.append(tmp)

    @property
    def attributes(self):
        """
        All attributes of the Item (Item of Mercado libre)
        :return:
        """
        opts = list()
        for item in self._obj_data.attributes:
            opts.append((item.id, item.name))
        return opts

    @property
    def attributes_required(self):
        """
        Required attributes
        :return:
        """
        opts = list()
        for item in self._obj_data.attributes:
            if hasattr(item.tags, 'required'):
                opts.append((item.id, item.name))
        return opts

    def attributes_options(self, attribute_id):
        """
        :param attribute_id: String
        :return:
        """
        opts = list()
        attr = self._attribute(attribute_id)
        if hasattr(attr, 'values'):
            for item in attr.values:
                opts.append(item)
        return opts

    def default_options(self):
        """
        Define the required attributes withe only one option.
        :return:
        """
        for attribute_id, name in self.attributes_required:
            options = self.attributes_options(attribute_id)
            if len(options) == 1:
                self.append_attribute(attribute_id, options[0].id)
        self.dic_base.update({'attributes': self._car_attributes})
        return self._car_attributes

    def set_pictures(self, files):
        """
        :param files: list: list with URLS of pictures
        :return: Dictionary
        """
        pictures = list()
        for file in files:
            pictures.append({"source": file})
        return self.dic_base.update({'pictures': pictures})

    def set_location(self, address_line, zip_code, city_id):
        """
        :param address_line: String
        :param zip_code: String
        :param city_id: String: ID of the city in Mercado libre
        :return: Dictionary: the dictionary updated
        """
        from .models import MLCity as City, MLCountry as Country
        country = Country.objects.first()
        # state = State.objects.get(id=state_id)
        city = City.objects.get(id=city_id)

        location = {
            "address_line": address_line,
            "zip_code": zip_code,
            "city": city.get_dict(),
            "state": city.state.get_dict(),
            "country": country.get_dict(),
            "latitude": '',
            "longitude": '',
            "open_hours": ''
        }

        self.dic_base.update({'location': location})
        return self.dic_base

    def set(self, type_substr, name_value, is_value=False):
        """
        Method for find a attibute and a option
        MLM1743-PLACA: type_substr = PLACA
        :param type_substr: String
        :param name_value: String/Integer: Can be the real value for append
        :param is_value: Boolean: define if the name_value is the real value
        :return: Duple of the ID_attributes, ID_option
        """
        attr_id = False
        opt_id = False
        for item in self.attributes:
            if type_substr in item[0]:
                attr_id = item[0]
                break
        if is_value:
            opt_id = name_value
        else:
            for option in self.attributes_options(attr_id):
                if str(name_value).lower() in option.name.lower() or option.name.lower() == str(name_value).lower():
                    opt_id = option.id
                    break
        if attr_id and opt_id:
            self.append_attribute(attr_id, opt_id)
        return attr_id, opt_id

    def post(self, raw=False):
        """
        Post the item in mercado libre
        :param raw: Boolean
        :return: Dictionary / Object (Raw case)
        """
        return self._app.post_item(self.dic_base, raw=raw)
