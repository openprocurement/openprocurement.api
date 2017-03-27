# -*- coding: utf-8 -*-
def includeme(config):
    config.scan("openprocurement.api.views")
    config.scan("openprocurement.api.subscribers")
