# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
# from raven.contrib.django.raven_compat.models import client
from django.conf import settings
from mercadolibre.mercado_libre import MeliApp
from mercadolibre.models import Country, State, City

import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Start load data'
    # def add_arguments(self, parser):
    #     parser.add_argument('origin', type=str)
    #     parser.add_argument('destiny', type=str)

    def handle(self, *args, **options):
        logger.info('start')
        meli = MeliApp()
        country_id = getattr(settings, 'DEFAULT_COUNTRY_ID', 'MX')
        country_data = meli.details('countries', country_id)

        country = Country()
        country.currency_id = country_data['currency_id']
        country.decimal_separator = country_data['decimal_separator']
        country.id = country_data['id']
        country.name = country_data['name']
        country.time_zone = country_data['time_zone']
        country.save()

        for state_data in country_data['states']:
            state = State()
            state.id = state_data['id']
            state.name = state_data['name']
            state.country = country
            state.save()

            cities_data = meli.details('states', state_data['id'])
            for city_data in cities_data['cities']:
                city = City()
                city.name = city_data['name']
                city.id = city_data['id']
                city.state = state
                city.save()

        logger.info('done!')
