# -*- coding: utf-8 -*-
from schematics.types.base import BaseType
from schematics.types.serializable import Serializable as BaseSerializable

class ContentConfigurator(object):
    """ Base OP Content Configuration adapter """

    name = "Base Openprocurement Content Configurator"

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __repr__(self):
        return "<Configuration adapter for %s>" % type(self.context)


class Serializable(BaseSerializable):
    serialized_name = None
    serialize_when_none = True


    def __init__(self, tender):
        self.context = tender
        serialized_type = self.context._fields.get(self.serialized_name, BaseType())
        super(Serializable, self).__init__(
            self.__call__, type=serialized_type, serialized_name=self.serialized_name,
            serialize_when_none=self.serialize_when_none
        )

    def __call__(self, obj, *args, **kwargs):
        raise NotImplemented