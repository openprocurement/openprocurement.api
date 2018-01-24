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
        """Launching awarding proccess."""
        raise NotImplementedError

    def back_to_awarding():
        """Relaunch awarding process with another award,    
           when owner has not qualified the previous one.
        """
        raise NotImplementedError

    def check_award_status():
        """Checking protocol and contract loading by the owner in time."""
        raise NotImplementedError
