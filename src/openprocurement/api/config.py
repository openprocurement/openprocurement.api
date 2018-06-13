# -*- coding: utf-8 -*-
from libnacl.sign import Signer, Verifier
from schematics.models import Model
from schematics.types import StringType, BaseType, ValidationError
from schematics.types.compound import ModelType, ListType
from schematics.types.serializable import serializable
from urlparse import urlsplit


class Main(Model):
    api_version = StringType(required=True, serialize_when_none=False)
    server_id = StringType(default='')


class Auth(Model):
    type = StringType(required=True, choices=['file', 'void'])
    src = StringType()

    def validate_src(self, data, value):
        if not data['src'] and data['type'] == 'void':
            return None
        elif not data['src']:
            raise ValidationError(u'This field is required.')


class User(Model):
    name = StringType(required=True)
    password = StringType(required=True)


class DefaultWriter(User):
    name = StringType(default="op")
    password = StringType(default="op")


class DB(Model):

    type = StringType(required=True, choices=['couchdb'])
    db_name = StringType(required=True)
    url = StringType(required=True)
    admin = ModelType(User)
    reader = ModelType(User)
    writer = ModelType(User, default=DefaultWriter)

    def create_url(self, field='writer'):
        scheme, netloc, path, _, _ = urlsplit(self.url)
        if not scheme:
            scheme = 'http'
            netloc = path
        if field not in ('admin', 'reader', 'writer'):
            raise ValidationError("Value must be on of ['admin', 'reader', 'writer']")
        if not self[field]:
            raise ValidationError("Field '{}' is not specified".format(field))
        return "{0}://{name}:{password}@{1}".format(scheme, netloc, **self[field].to_primitive())

    def validate_reader(self, data, value):
        if data['admin'] and not value:
            raise ValidationError(u'This field is required.')

    def validate_writer(self, data, value):
        if data['admin'] and not value:
            raise ValidationError(u'This field is required.')


class KeyType(StringType):

    def validate_type(self, value):
        try:
            Signer(value.decode('hex'))
        except (TypeError, ValueError) as exc:
            raise ValidationError(exc.message)


class DS(Model):
    user = ModelType(User, required=True)
    download_url = StringType(required=True)
    upload_url = StringType()
    dockey = KeyType(default='')
    dockeys = ListType(KeyType, required=True)

    @serializable(serialized_name="signer")
    def signer(self):
        return Signer(self['dockey'].decode('hex'))

    def init_keyring(self, dockey):
        keyring = {}
        dockeys = self['dockeys'] or dockey.hex_vk().split('\0')
        for key in dockeys:
            keyring[key[:8]] = Verifier(key)
        return keyring


class AuctionModule(Model):
    url = StringType(required=True)
    public_key = KeyType(required=True)

    @serializable(serialized_name="signer")
    def signer(self):
        return Signer(self['public_key'].decode('hex'))


class Config(Model):

    main = ModelType(Main, default={})
    auth = ModelType(Auth, required=True)
    ds = ModelType(DS)
    db = ModelType(DB, required=True)
    auction = ModelType(AuctionModule)


class AppMetaSchema(Model):
    config = ModelType(Config, required=True)
    plugins = BaseType(required=True)
    here = StringType(required=True)
