# -*- coding: utf-8 -*-
from zope.interface import Interface
from zope.interface import Attribute


class IOPContent(Interface):
    """ Openprocurement Content """


class IContentConfigurator(Interface):
    """ Content configurator """
    name = Attribute('Name of configurator')
    model = Attribute('Model of content type')
    award_model = Attribute('Model of Award')

    def add_award():
        """Add award"""
