# -*- coding: utf-8 -*-
from zope.interface import Interface


class IOPContent(Interface):
    """ Openprocurement Content """


class IContentConfigurator(Interface):
    """ Content configurator """


class IValidator(Interface):
    pass


class ISerializable(Interface):
    pass