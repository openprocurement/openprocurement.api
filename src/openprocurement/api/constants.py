# -*- coding: utf-8 -*-
import os
import re

from datetime import datetime, timedelta
from logging import getLogger

from pkg_resources import get_distribution
from pytz import timezone
from requests import Session

PKG = get_distribution(__package__)
LOGGER = getLogger(PKG.project_name)
VERSION = '{}.{}'.format(
    int(PKG.parsed_version[0]),
    int(PKG.parsed_version[1]) if PKG.parsed_version[1].isdigit() else 0
)
ROUTE_PREFIX = '/api/{}'.format(VERSION)
SESSION = Session()
SCHEMA_VERSION = 24
SCHEMA_DOC = 'openprocurement_schema'

TZ = timezone(os.environ['TZ'] if 'TZ' in os.environ else 'Europe/Kiev')
SANDBOX_MODE = os.environ.get('SANDBOX_MODE', False)
AUCTIONS_COMPLAINT_STAND_STILL_TIME = timedelta(days=3)

DOCUMENT_BLACKLISTED_FIELDS = ('title', 'format', 'url', 'dateModified', 'hash')
DOCUMENT_WHITELISTED_FIELDS = ('id', 'datePublished', 'author', '__parent__')


def read_json(name):
    import inspect
    import os.path
    from json import loads
    caller_file = inspect.stack()[1][1]
    caller_dir = os.path.dirname(os.path.realpath(caller_file))
    file_path = os.path.join(caller_dir, name)
    with open(file_path) as lang_file:
        data = lang_file.read()
    return loads(data)


DEBTOR_TYPES = ['naturalPerson', 'legalPerson']

DEFAULT_CURRENCY = u'UAH'

DEFAULT_ITEM_CLASSIFICATION = u'CAV'
DEFAULT_LOKI_ITEM_CLASSIFICATION = u'CAV-PS'


DOCUMENT_TYPES = ['notice', 'technicalSpecifications', 'illustration', 'virtualDataRoom', 'x_presentation']

CPV_CODES = read_json('cpv.json')
CPV_CODES.append('99999999-9')
CAV_CODES = read_json('cav.json')

CPVS_CODES = read_json('cpvs.json')
CAV_PS_CODES = read_json('cav_ps.json')

DK_CODES = read_json('dk021.json')
FUNDERS = [(i['scheme'], i['id']) for i in read_json('funders.json')['data']]
# DKPP_CODES = read_json('dkpp.json')
ORA_CODES = [i['code'] for i in read_json('OrganisationRegistrationAgency.json')['data']]
WORKING_DAYS = read_json('working_days.json')

ATC_CODES = read_json('atc.json')
INN_CODES = read_json('inn.json')

ADDITIONAL_CLASSIFICATIONS_SCHEMES = [u'ДКПП', u'NONE', u'ДК003', u'ДК015', u'ДК018', u'CPVS']
ADDITIONAL_CLASSIFICATIONS_SCHEMES_2017 = [u'ДК003', u'ДК015', u'ДК018', u'specialNorms']
COORDINATES_REG_EXP = re.compile(r'-?\d{1,3}\.\d+|-?\d{1,3}')

CPV_ITEMS_CLASS_FROM = datetime(2017, 1, 1, tzinfo=TZ)
CPV_BLOCK_FROM = datetime(2017, 6, 2, tzinfo=TZ)

ATC_INN_CLASSIFICATIONS_FROM = datetime(2017, 12, 22, tzinfo=TZ)

ITEM_CLASSIFICATIONS = {
    u'CAV': CAV_CODES,
    # u'CAV-PS': []
}

LOKI_ITEM_CLASSIFICATION = {
    u'CAV-PS': CAV_PS_CODES
}
LOKI_ITEM_ADDITIONAL_CLASSIFICATIONS = {
    u'UA-EDR': [],
    u'CPVS': CPVS_CODES,
    u'cadastralNumber': []
}

IDENTIFIER_CODES = ORA_CODES
