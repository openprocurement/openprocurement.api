from logging import getLogger
from pkg_resources import get_distribution

AWARDING_OF_PROCUREMENT_METHOD_TYPE = {
    'belowThreshold': 'awarding_1_0',
    'dgfFinancialAssets': 'awarding_2_0',
    'dgfOtherAssets': 'awarding_2_0',
    'dgfInsider': 'awarding_2_0',
}
PKG = get_distribution(__package__)
LOGGER = getLogger(PKG.project_name)
VERSION = '{}.{}'.format(int(PKG.parsed_version[0]), int(PKG.parsed_version[1]) if PKG.parsed_version[1].isdigit() else 0)
ROUTE_PREFIX = '/api/{}'.format(VERSION)
