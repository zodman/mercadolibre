# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.contrib.auth.models import User
from django.db import models
from .mercado_libre import MeliApp
from django.conf import settings
from .utils import ItemCar, json_process, top_listing_pack
from datetime import datetime
from dateutil.parser import parse

_ = lambda x:x

MELI_PACKAGES = (
    ('gold_premium', 'Oro premium'),
    ('gold', 'Oro'),
    ('silver', 'Plata')
)


MODELS_OPTIONS = (
    ('MLM160392', 'Besta'), # ok
    # ('MLM160393', 'Cadenza'),
    # ('MLM160394', 'Carens'),
    # ('MLM160395', 'Carnival'),
    # ('MLM160412', 'Cerato'),
    # ('MLM160396', 'Clarus'),
    # ('MLM160397', 'Credos'),
    ('MLM160041', 'Forte'), # ok
    # ('MLM160398', 'Magentis'),
    # ('MLM160399', 'Mohave'),
    # ('MLM160400', 'Opirus'),
    ('MLM160413', 'Optima'), # Bug No attributes
    # ('MLM160401', 'Picanto'),
    # ('MLM160402', 'Pregio'),
    # ('MLM160403', 'Pride'),
    # ('MLM160404', 'Quoris'),
    ('MLM160405', 'Rio'), # ok
    # ('MLM160406', 'Sedona'),
    # ('MLM160407', 'Sephia'),
    # ('MLM160408', 'Shuma'),
    ('MLM160042', 'Sorento'), # Bug No Attributes
    ('MLM160409', 'Soul'), # ok
    ('MLM160040', 'Sportage'), # ok
    # ('MLM160411', 'Stylus'),
    ('MLM160043', 'Otros Modelos') # NIRO No attributes
)




MELI = MeliApp()

# Create your models here.
class MeliAccount(models.Model):
    id = models.DecimalField(verbose_name='id de mercado libre', max_digits=15, decimal_places=0, primary_key=True)
    user = models.OneToOneField(User, related_name='meli_account', verbose_name='Cuenta de mercado libre', on_delete=models.CASCADE)
    temporal_code = models.CharField(max_length=255)
    temporal_access_token = models.CharField(max_length=255)
    refresh_token = models.CharField(max_length=255)
    site_id = models.CharField(max_length=10)
    nickname = models.CharField(max_length=255)
    country_id = models.CharField(max_length=255)

    class Meta:
        verbose_name ='cuenta de mercado libre'
        verbose_name_plural = 'cuentas de mercado libre'

    def __str__(self):
        return self.temporal_access_token


    def __unicode__(self):
        return self.temporal_access_token

    def refresh_access_token(self):
        """
        using the refresh_token get a new access_token
        :return: String: token
        """

        self.temporal_access_token, self.refresh_token = MELI.refresh_token(self.refresh_token)
        self.save()
        return self.temporal_access_token

    @property
    def user_meliapp(self):
        """
        Create a instance class of Meli for use the SDK
        :return: MeliApp Object
        """
        self.refresh_access_token()
        return MeliApp(
            access_token=self.temporal_access_token,
            refresh_token=self.refresh_token)

    def categories(self, category_id=None, attribute=None, raw=False):
        """
        description of category, if not pass category_id return the category of site
        """
        if not category_id:
            category_id = getattr(settings, 'DEFAULT_CATEGORY')
        meli = self.user_meliapp
        response = meli.category(self.site_id, category_id, attribute=attribute, raw=raw)
        return response

    def get_promotion_packs(self, category_id=None, raw=False):
        """
        List of all promotions packs
        :param category_id: String: the category id of Mercado libre
        :param raw: Boolean: if you want the request object of python
        :return: Dictionary / Object (Raw case)
        """
        if not category_id:
            category_id = getattr(settings, 'DEFAULT_CATEGORY')
        meli = self.user_meliapp
        return meli.get_promotion_packs(category_id=category_id, raw=raw)

    def have_user_promotion_packs(self, raw=False):
        """
        consult for check if the user have promotions packs
        :param raw: Boolean: if you want the request object of python
        :return: Dictionary / Object (Raw case)
        """
        meli = self.user_meliapp
        return meli.have_user_promotion_packs(
            user_id=self.id,
            access_token=self.temporal_access_token,
            raw=raw)

    def get_user_promotion_packs(self, raw=False):
        """
        get the user purchase promotions packs
        :param raw: Boolean: if you want the request object of python
        :return: Dictionary / Object (Raw case)
        """
        meli = self.user_meliapp
        return meli.get_user_promotion_packs(
            user_id=self.id,
            access_token=self.temporal_access_token,
            raw=raw)

    def active_promotion_pack(self, category_id, promotion_pack_id):
        """
        Active a promotion pack
        :param category_id: String
        :param promotion_pack_id:  String
        :return: Dictionary
        """
        meli = self.user_meliapp
        return meli.active_promotion_pack(
            user_id=self.id,
            access_token=self.temporal_access_token,
            category_id=category_id,
            promotion_pack_id=promotion_pack_id)

    def post_item(self, category_id, title, description, kmts,
                  year, price, version, pictures, address_line,
                  zip_code, city_id, listing_type='free'):

        """
        :param category_id:
        :param title:
        :param description:
        :param kmts:
        :param year:
        :param price:
        :param version:
        :param pictures:
        :param address_line:
        :param zip_code:
        :param city_id:
        :return: Object type ItemCar -> utils
        """
        car = ItemCar(self, category_id, title, description, price, pictures, listing_type=listing_type)
        car.set_location(address_line, zip_code, city_id)
        car.set('YEAR', year)
        car.set('PLACA', 'No tiene')
        car.set('COLORENGOMADO', 'No tiene')
        car.set('HOLOGRAMA', 'No tiene')
        car.set('KMTS', kmts, is_value=True)
        car.set('VEHICLE_YEAR', year, is_value=True)
        car.set('KILOMETERS', "{}km".format(kmts), is_value=True)
        car.set('DOORS', 5, is_value=True)
        car.set('FUEL_TYPE', "Gasolina", is_value=True)
        car.set('VERS', version, is_value=True)
        # car.append_attribute('MLM1743-PLACA', 'MLM1743-PLACA-NO_TIENE')

        return car

    def update_item(self, item_id, updated_data, raw=False):
        """
        :param item_id: String: ID of Item in Mercado libre
        :param updated_data: Dictionary: Updated attributes and values
        :param raw: Boolean: True for return the Request
        :return: Django Request/Dictionary
        """
        meli = self.user_meliapp
        return meli.item_update(
            item_id,
            updated_data,
            raw)

    def item_update_description(self, item_id, updated_data, raw=False):
        """
        :param item_id: String: ID of Item in Mercado libre
        :param updated_data: Dictionary: Updated attributes and values
        :param raw: Boolean: True for return the Request
        :return: Django Request/Dictionary
        """
        meli = self.user_meliapp
        return meli.item_update_description(
            item_id,
            updated_data,
            raw)

    def get_top_promo_pack(self, category_id=None, promotion_pack_id=None):
        if not category_id:
            category_id = getattr(settings, 'DEFAULT_CATEGORY')
        meli = self.user_meliapp
        promotion_packs = meli.active_promotion_pack(
            user_id=self.id,
            access_token=self.temporal_access_token,
            category_id=category_id,
            promotion_pack_id=promotion_pack_id)
        promo_pack = promotion_packs[0]
        listings = promo_pack['listing_details']

        try:
            return top_listing_pack(listings)['listing_type_id']
        except IndexError:
            return None


# class Categories(models.Model):
#     id = models.CharField(max_length=25, primary_key=True)
#     name = models.CharField(max_length=250,)
#
#     class Meta:
#         verbose_name = 'categoria'
#         verbose_name_plural= 'categorias'
#
#     def __unicode__(self):
#         return self.name


class MLCountry(models.Model):
    id = models.CharField(max_length=150, primary_key=True)
    name = models.CharField(max_length=250, verbose_name=_("Nombre Pais de ML"))
    decimal_separator = models.CharField(max_length=5)
    currency_id = models.CharField(max_length=25)
    time_zone = models.CharField(max_length=150)

    class Meta:
        verbose_name = u'País'
        verbose_name_plural = 'Países'

    def __unicode__(self):
        return self.name

    def __str__(self):
        return self.name

    def get_dict(self):
        return {
            'id': self.id,
            'name': self.name
        }


class MLState(models.Model):
    id = models.CharField(max_length=150, primary_key=True)
    region = models.CharField(max_length=50, blank=True, null=True)
    name = models.CharField(max_length=250, verbose_name="Nombre de estado ML")
    country = models.ForeignKey(MLCountry, related_name='states',
                                on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Estado'
        verbose_name_plural = 'Estados'

    def __unicode__(self):
        return self.name

    def __str__(self):
        return self.name

    def get_dict(self):
        return {
            'id': self.id,
            'name': self.name
        }


class MLCity(models.Model):
    id = models.CharField(max_length=150, primary_key=True)
    name = models.CharField(max_length=250,
                                verbose_name=_("Nombre de ciudad ML"))
    state = models.ForeignKey(MLState, related_name="cities", on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Ciudad'
        verbose_name_plural = 'Ciudades'
        ordering = ('name',)

    def __str__(self):
        return self.name


    def __unicode__(self):
        return self.name

    def get_dict(self):
        return {
            'id': self.id,
            'name': self.name
        }


# class Geolocation(models.Model):
#     content_type = models.ForeignKey(ContentType)
#     object_id = models.CharField(max_length=150)
#     latitude = models.DecimalField()
#     longitude = models.DecimalField()
#
#     class Meta:
#         verbose_name = 'geolocalización'
#         verbose_name_plural = 'geolocalizaciones'
#         unique_together = ('content_type', 'object_id')
#
#     def __unicode__(self):
#         return u'%s , %s' % (self.latitude, self.longitude)


class MeliCar(models.Model):
    id = models.CharField(max_length=150, primary_key=True)
    site_id = models.CharField(max_length=10)
    title = models.CharField(max_length=70)
    subtitle = models.CharField(max_length=70, null=True, blank=True)
    description = models.TextField()
    seller = models.ForeignKey(MeliAccount, related_name='cars',
                               on_delete=models.CASCADE)
    category_id = models.CharField(max_length=100)
    official_store_id = models.CharField(max_length=100, null=True, blank=True)
    price = models.IntegerField()
    base_price = models.IntegerField()
    original_price = models.IntegerField(null=True)
    currency_id = models.CharField(max_length=10)
    initial_quantity = models.IntegerField(default=1)
    available_quantity = models.IntegerField(default=1)
    sold_quantity = models.IntegerField(default=0)
    buying_mode = models.CharField(max_length=50, default='classified')
    listing_type_id = models.CharField(max_length=50, default='free')
    start_time = models.DateTimeField(default=datetime.now)
    stop_time = models.DateTimeField()
    condition = models.CharField(max_length=150, default='used')
    video_id = models.CharField(max_length=150, blank=True)
    accepts_mercadopago = models.BooleanField(default=False)

    class Meta:
        abstract = True

    def __unicode__(self):
        return self.title

    def initialize_by_json(self, json_data):
        obj_json = json_process(json_data)
        # import ipdb; ipdb.set_trace()
        self.id = obj_json.id
        self.site_id = obj_json.site_id
        self.title = obj_json.title
        if obj_json.subtitle:
            self.subtitle = obj_json.subtitle
        # self.description = obj_json.descriotion
        seller_id = int(obj_json.seller_id)
        self.seller = MeliAccount.objects.get(id=seller_id)
        self.category_id = obj_json.category_id
        if self.official_store_id:
            self.official_store_id = obj_json.official_store_id
        self.price = int(obj_json.price)
        self.base_price = int(obj_json.base_price)
        if obj_json.original_price:
            self.original_price = int(obj_json.original_price)
        self.currency_id = obj_json.currency_id
        self.initial_quantity = int(obj_json.initial_quantity)
        self.available_quantity = int(obj_json.available_quantity)
        self.sold_quantity = int(obj_json.sold_quantity)
        self.buying_mode = obj_json.buying_mode
        self.listing_type_id = obj_json.listing_type_id
        self.start_time = parse(obj_json.start_time)
        self.stop_time = parse(obj_json.stop_time)
        self.condition = obj_json.condition
        if obj_json.video_id:
            self.video_id = obj_json.video_id
        self.accepts_mercadopago = obj_json.accepts_mercadopago
        self.save()
        for picture in obj_json.pictures:
            pic = MeliCarPictures()
            pic.id = picture.id
            pic.car = self
            pic.url = picture.url
            pic.secure_url = picture.secure_url
            pic.size = picture.size
            pic.max_size = picture.max_size
            pic.quality = picture.quality
            pic.save()
        return self


class MeliCarPictures(models.Model):
    id = models.CharField(max_length=250, primary_key=True)
    #car = models.ForeignKey(MeliCar, related_name='pictures', on_delete=models.CASCADE)
    url = models.URLField()
    secure_url = models.URLField(null=True)
    size = models.CharField(max_length=100)
    max_size = models.CharField(max_length=100)
    quality = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        abstract = True

    def __unicode__(self):
        return self.url
