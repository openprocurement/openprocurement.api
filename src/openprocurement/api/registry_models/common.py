# -*- coding: utf-8 -*-
from schematics.types import StringType, BaseType
from schematics.types.compound import DictType, ListType, ModelType
from openprocurement.api.utils import get_now
from schematics.types.serializable import serializable
from couchdb_schematics.document import SchematicsDocument

from .schematics_extender import Model, IsoDateTimeType


class Revision(Model):
    author = StringType()
    date = IsoDateTimeType(default=get_now)
    changes = ListType(DictType(BaseType), default=list())
    rev = StringType()


class BaseResourceItem(SchematicsDocument, Model):
    owner = StringType()
    owner_token = StringType()
    mode = StringType(choices=['test'])
    dateModified = IsoDateTimeType()

    _attachments = DictType(DictType(BaseType), default=dict())  # couchdb attachments
    revisions = ListType(ModelType(Revision), default=list())

    __name__ = ''

    def __repr__(self):
        return '<%s:%r@%r>' % (type(self).__name__, self.id, self.rev)

    @serializable(serialized_name='id')
    def doc_id(self):
        """A property that is serialized by schematics exports."""
        return self._id

    def import_data(self, raw_data, **kw):
        """
        Converts and imports the raw data into the instance of the model
        according to the fields in the model.
        :param raw_data:
            The data to be imported.
        """
        data = self.convert(raw_data, **kw)
        del_keys = [k for k in data.keys() if data[k] == self.__class__.fields[k].default or data[k] == getattr(self, k)]
        for k in del_keys:
            del data[k]
        self._data.update(data)
        return self
