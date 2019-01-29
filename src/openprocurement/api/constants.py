# -*- coding: utf-8 -*-
import os
import re

from datetime import datetime, timedelta
from logging import getLogger

from pkg_resources import get_distribution
from pytz import timezone
from requests import Session

from zope.component import getGlobalSiteManager

from openprocurement.api.interfaces import IProjectConfigurator

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

APP_META_FILE = 'app_meta.yaml'

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

CPV_CODES = read_json('json_data/cpv.json')
CPV_CODES.append('99999999-9')
CAV_CODES = read_json('json_data/cav.json')

CPVS_CODES = read_json('json_data/cpvs.json')
KVTSPZ_CODES = read_json('json_data/kvtspz.json')
CAV_PS_CODES = read_json('json_data/cav_ps.json')

DK_CODES = read_json('json_data/dk021.json')
FUNDERS = [(i['scheme'], i['id']) for i in read_json('json_data/funders.json')['data']]
# DKPP_CODES = read_json('json_data/dkpp.json')
ORA_CODES = [i['code'] for i in read_json('json_data/OrganisationRegistrationAgency.json')['data']]

ORA_CODES_AUCTIONS = [i['code'] for i in read_json('json_data/OrganisationRegistrationAgency_auctions.json')['data']]
ORA_CODES_AUCTIONS[0:0] = ["UA-IPN", "UA-FIN"]

WORKING_DAYS = read_json('json_data/working_days.json')

ATC_CODES = read_json('json_data/atc.json')
INN_CODES = read_json('json_data/inn.json')

ADDITIONAL_CLASSIFICATIONS_SCHEMES = [u'ДКПП', u'NONE', u'ДК003', u'ДК015', u'ДК018', u'CPVS']
ADDITIONAL_CLASSIFICATIONS_SCHEMES_2017 = [u'ДК003', u'ДК015', u'ДК018', u'specialNorms']
COORDINATES_REG_EXP = re.compile(r'-?\d{1,3}\.\d+|-?\d{1,3}')

CAV_CODES_FLASH = read_json('json_data/cav_flash.json')

CPV_ITEMS_CLASS_FROM = datetime(2017, 1, 1, tzinfo=TZ)
CPV_BLOCK_FROM = datetime(2017, 6, 2, tzinfo=TZ)

ATC_INN_CLASSIFICATIONS_FROM = datetime(2017, 12, 22, tzinfo=TZ)

DK018_CODES = read_json('json_data/dk018.json')

ITEM_CLASSIFICATIONS = {
    u'CAV': CAV_CODES,
    # u'CAV-PS': []
}

LOKI_ITEM_CLASSIFICATION = {
    u'CAV-PS': CAV_PS_CODES,
    u'CPV': CPV_CODES
}
LOKI_ITEM_ADDITIONAL_CLASSIFICATIONS = {
    u'UA-EDR': [],
    u'CPVS': CPVS_CODES,
    u'cadastralNumber': [],
    u'dk018': DK018_CODES,
    u'kvtspz': KVTSPZ_CODES
}

LOKI_DOCUMENT_TYPES = [
    'notice', 'technicalSpecifications', 'illustration', 'x_presentation',
    'informationDetails', 'cancellationDetails', 'x_dgfAssetFamiliarization',
    'evaluationCriteria', 'clarifications'
]
DOCUMENT_TYPE_OFFLINE = ['x_dgfAssetFamiliarization']
DOCUMENT_TYPE_URL_ONLY = ['virtualDataRoom', 'x_dgfPublicAssetCertificate', 'x_dgfPlatformLegalDetails']

ADDITIONAL_CLASSIFICATIONS_SCHEMES = [u'ДКПП', u'NONE', u'ДК003', u'ДК015', u'ДК018']

IDENTIFIER_CODES = ORA_CODES

ALL_ACCREDITATIONS_GRANTED = '0'
TEST_ACCREDITATION = 't'

RELATED_PROCESS_TYPE_CHOICES = (
    'asset',
    'auction',
    'lot',
)

TEMPORARY_DOCUMENT_EXPIRATION_SECONDS = 300
DOCSERVICE_KEY_ID_LENGTH = 8
DOCSERVICE_UPLOAD_RETRY_COUNT = 10


class ProjectConfigurator(object):
    """
        This class get registered configurator from GSM(Global Site Manager) and save it when
        you try to get some attribute for the first time.
        We need that proxy class for real configurator because constants.py is
        loaded before Configurator was registered so if we assign Configurator
        directly to project_configurator we will get None in project_configurator variable.
        Instance of this class will be used in views and functions that called from views, so
        in such moments we will have registered configurator in GSM.
        :param configurator
            openprocurement.api.configurator.Configurator instance
    """
    _configurator = None

    def __getattr__(self, item):
        if self._configurator is None:
            self._configurator = getGlobalSiteManager().queryUtility(IProjectConfigurator)
        return getattr(self._configurator, item)
