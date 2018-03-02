# -*- coding: utf-8 -*-
class ContentConfigurator(object):
    """ Base OP Content Configuration adapter """

    name = "Base Openprocurement Content Configurator"

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __repr__(self):
        return "<Configuration adapter for %s>" % type(self.context)


class AwardingNextCheckAdapter(object):
    """ Base Awarding Next Check Adapter"""

    name = "Base Awarding Next Check Adapter"

    def __init__(self, context):
        self.context = context

    def __repr__(self):
        return "<Awarding next_check adapter for %s>" % type(self.context)
