# -*- coding: utf-8 -*-
def includeme(config):
    print "Init api"
    config.scan("openprocurement.api.views")
