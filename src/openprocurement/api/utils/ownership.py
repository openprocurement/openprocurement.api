# -*- coding: utf-8 -*-
from schematics.types import StringType
from hashlib import sha512

from openprocurement.api.utils.common import generate_id


class OwnershipOperator(object):

    DIRECT_SET_TRANSFER_TOKEN_ROLES = ('concierge', 'convoy')

    def __init__(self, m):
        """
        Create OwnershipOperator

        :param m: model to work with
        """
        self.m = m

    def _userid_could_set_transfer_token(self, user_id):
        return user_id in self.DIRECT_SET_TRANSFER_TOKEN_ROLES

    @staticmethod
    def create_transfer_token():
        transfer_token = generate_id()
        hashed_token = sha512(transfer_token).hexdigest()

        return transfer_token, hashed_token

    def set_ownership(self, user_id, transfer_token):
        if not self.m.get('owner'):
            self.m.owner = user_id
        owner_token = generate_id()
        self.m.owner_token = owner_token
        acc = {'token': owner_token}

        if isinstance(getattr(type(self.m), 'transfer_token', None), StringType):
            if transfer_token and self._userid_could_set_transfer_token(user_id):
                self.m.transfer_token = transfer_token
            else:
                transfer_token, hashed_token = self.create_transfer_token()
                self.m.transfer_token = hashed_token
                acc['transfer'] = transfer_token
        return acc
