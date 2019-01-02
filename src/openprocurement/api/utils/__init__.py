# -*- coding: utf-8 -*-
from zope.deprecation import moved


message = "openprocurement.api.utils now contains submodules. "
"Please, fix outdated imports"

moved('openprocurement.api.utils.common', message)
moved('openprocurement.api.utils.timestuff', message)
moved('openprocurement.api.utils.migration', message)
