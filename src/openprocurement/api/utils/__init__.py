# -*- coding: utf-8 -*-
from zope.deprecation import moved


message = "openprocurement.api.utils now contains submodules. "
"Please, fix outdated imports"

moved('openprocurement.api.utils.api_resource', message)
moved('openprocurement.api.utils.common', message)
moved('openprocurement.api.utils.decorators', message)
moved('openprocurement.api.utils.documents', message)
moved('openprocurement.api.utils.migration', message)
moved('openprocurement.api.utils.plugins', message)
moved('openprocurement.api.utils.searchers', message)
moved('openprocurement.api.utils.timestuff', message)
