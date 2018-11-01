# -*- coding: utf-8 -*-
import os
import re
import sys
from ConfigParser import ConfigParser, DEFAULTSECT

from iso8601 import parse_date
from pytz import timezone
from datetime import datetime
from pkg_resources import get_distribution
from logging import getLogger
from requests import Session

PKG = get_distribution(__package__)
LOGGER = getLogger(PKG.project_name)
VERSION = '{}.{}'.format(int(PKG.parsed_version[0]), int(PKG.parsed_version[1]) if PKG.parsed_version[1].isdigit() else 0)
ROUTE_PREFIX = '/api/{}'.format(VERSION)
SESSION = Session()
SCHEMA_VERSION = 24
SCHEMA_DOC = 'openprocurement_schema'

TZ = timezone(os.environ['TZ'] if 'TZ' in os.environ else 'Europe/Kiev')
SANDBOX_MODE = os.environ.get('SANDBOX_MODE', False)

DOCUMENT_BLACKLISTED_FIELDS = ('title', 'format', 'url', 'dateModified', 'hash')
DOCUMENT_WHITELISTED_FIELDS = ('id', 'datePublished', 'author', '__parent__')

def read_json(name):
    import os.path
    from json import loads
    curr_dir = os.path.dirname(os.path.realpath(__file__))
    file_path = os.path.join(curr_dir, name)
    with open(file_path) as lang_file:
        data = lang_file.read()
    return loads(data)

CPV_CODES = read_json('cpv.json')
CPV_CODES.append('99999999-9')
DK_CODES = read_json('dk021.json')
FUNDERS = [(i['scheme'], i['id']) for i in read_json('funders.json')['data']]
#DKPP_CODES = read_json('dkpp.json')
ORA_CODES = [i['code'] for i in read_json('OrganisationRegistrationAgency.json')['data']]
WORKING_DAYS = read_json('working_days.json')

ATC_CODES = read_json('atc.json')
INN_CODES = read_json('inn.json')

ADDITIONAL_CLASSIFICATIONS_SCHEMES = [u'ДКПП', u'NONE', u'ДК003', u'ДК015', u'ДК018']
ADDITIONAL_CLASSIFICATIONS_SCHEMES_2017 = [u'ДК003', u'ДК015', u'ДК018', u'specialNorms']
COORDINATES_REG_EXP = re.compile(r'-?\d{1,3}\.\d+|-?\d{1,3}')

CPV_ITEMS_CLASS_FROM = datetime(2017, 1, 1, tzinfo=TZ)
CPV_BLOCK_FROM = datetime(2017, 6, 2, tzinfo=TZ)

ATC_INN_CLASSIFICATIONS_FROM = datetime(2017, 12, 22, tzinfo=TZ)

def get_default_constants_file_path():
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), 'constants.ini')

def load_constants(file_path):
    config = ConfigParser()
    try:
        with open(file_path) as fp:
            config.readfp(fp)
    except Exception as e:
        raise type(e), type(e)(
            'Can\'t read file \'{0}\': use current path or override using '
            'CONSTANTS_FILE_PATH env variable'.format(file_path)), sys.exc_info()[2]
    return config

def parse_date_tz(datestring):
    return parse_date(datestring, TZ)

def get_constant(config, constant, section=DEFAULTSECT, parse_func=parse_date_tz):
    return parse_func(config.get(section, constant))

CONSTANTS_FILE_PATH = os.environ.get('CONSTANTS_FILE_PATH', get_default_constants_file_path())
CONSTANTS_CONFIG = load_constants(CONSTANTS_FILE_PATH)

BUDGET_PERIOD_FROM = get_constant(CONSTANTS_CONFIG, 'BUDGET_PERIOD_FROM')
