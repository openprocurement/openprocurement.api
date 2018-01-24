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

    def start_awarding():
        """
            Method that call for start awarding process(create awards)
        """
        pass

    def back_to_awarding():
        """
            Method that call when we need to qualify another bidder
        """
        pass
