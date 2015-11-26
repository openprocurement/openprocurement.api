from zope.interface import Interface


class IBaseTender(Interface):
    """ Base tender marker interface """


class ITender(IBaseTender):
    """ Tender marker interface """
