# -*- coding: utf-8 -*-
from zope.interface import (
    Attribute, Interface
)


class IOPContent(Interface):
    """ Openprocurement Content """


class IORContent(Interface):
    """ OpenRegistry Content """


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

    def check_award_status(request, award, now):
        """Checking protocol and contract loading by the owner in time."""
        raise NotImplementedError


class IAwardingNextCheck(Interface):
    """Awarding part of next_check field"""
    name = Attribute("Awarding Type Name")

    def add_awarding_checks(auction):
        raise NotImplementedError
