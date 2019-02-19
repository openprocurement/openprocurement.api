# -*- coding: utf-8 -*-
from mock import Mock

from openprocurement.api.migration import (
    AliasesInfoDTO,
    MigrationResourcesDTO,
)


def MigrationResourcesDTO_mock(db, aliases_info=None):
    ai = AliasesInfoDTO({'some_package': []} if not aliases_info else aliases_info)
    mr = MigrationResourcesDTO(db, ai)

    return mr
