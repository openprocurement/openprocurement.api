# -*- coding: utf-8 -*-
class ContextConfigurator(object):
    """ Base OP Context Configuration adapter """

    name = "Base Context Configurator"

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __repr__(self):
        return "<Configuration adapter for %s>" % type(self.context)
