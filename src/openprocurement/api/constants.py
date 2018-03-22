from logging import getLogger
from pkg_resources import get_distribution

AWARDING_OF_PROCUREMENT_METHOD_TYPE = {
    'belowThreshold': 'awarding_1_0',
    'dgfFinancialAssets': 'awarding_2_1',
    'dgfOtherAssets': 'awarding_2_1',
    'dgfInsider': 'awarding_2_1',
}


# Declares what roles can interact with document in different statuses
STATUS4ROLE = {
    'complaint_owner': ['draft', 'answered'],
    'reviewers': ['pending'],
    'tender_owner': ['claim'],
}


PKG = get_distribution(__package__)
LOGGER = getLogger(PKG.project_name)
VERSION = '{}.{}'.format(int(PKG.parsed_version[0]), int(PKG.parsed_version[1]) if PKG.parsed_version[1].isdigit() else 0)
ROUTE_PREFIX = '/api/{}'.format(VERSION)
