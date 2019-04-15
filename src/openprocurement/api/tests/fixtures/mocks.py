# -*- coding: utf-8 -*-
from openprocurement.api.utils.validation import (
    AuthData,
    Event,
)
from openprocurement.api.utils.context_provider import ContextProvider
from openprocurement.api.migration import (
    AliasesInfoDTO,
    MigrationResourcesDTO,
)


def MigrationResourcesDTO_mock(db, aliases_info=None):
    ai = AliasesInfoDTO({'some_package': []} if not aliases_info else aliases_info)
    mr = MigrationResourcesDTO(db, ai)

    return mr


def event_mock():
    auth = AuthData('test_iser_id', 'test_role', tuple())
    data = {}
    ctx = ContextProvider(None, None)
    event = Event(ctx, auth, data)

    return event
