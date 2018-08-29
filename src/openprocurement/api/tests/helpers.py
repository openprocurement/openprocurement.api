# -*- coding: utf-8 -*-
from base64 import b64encode
from libnacl.sign import Signer
from urllib import urlencode
from uuid import uuid4


def fake_docservice_url(signer_seed):
    """Generates fake Document Service document URL for tests"""
    doc_id = uuid4().hex
    signer = Signer(signer_seed.decode('hex'))
    key_id = signer.hex_vk()[:8]
    signature = b64encode(signer.signature("{}\0{}".format(doc_id, '0' * 32)))
    query = {'Signature': signature, 'KeyID': key_id}
    return "http://localhost/get/{}?{}".format(doc_id, urlencode(query))
