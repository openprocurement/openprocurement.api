# -*- coding: utf-8 -*-
class Manager(object):
    parent_name = ''
    parent = None

    def __init__(self, parent=None, parent_name=''):
        if all([parent, parent_name]):
            setattr(self, parent_name, parent)
        elif any([parent, parent_name]):
            raise AttributeError('parent and parent_name should be present or absent both')

    def get(self, request):
        raise NotImplementedError

    def get_list(self, request):
        raise NotImplementedError

    def create(self, request):
        raise NotImplementedError

    def update(self, request):
        raise NotImplementedError

    def delete(self, request):
        raise NotImplementedError
