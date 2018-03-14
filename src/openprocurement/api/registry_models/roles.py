# -*- coding: utf-8 -*-
from schematics.transforms import whitelist, blacklist
from couchdb_schematics.document import SchematicsDocument

schematics_default_role = SchematicsDocument.Options.roles['default'] + blacklist("__parent__")
schematics_embedded_role = SchematicsDocument.Options.roles['embedded'] + blacklist("__parent__")

plain_role = (blacklist('_attachments', 'revisions', 'dateModified') + schematics_embedded_role)
listing_role = whitelist('dateModified', 'doc_id')
draft_role = whitelist('status')

document_create_role = blacklist('id', 'datePublished', 'dateModified', 'author', 'download_url')
document_edit_role = blacklist('id', 'url', 'datePublished', 'dateModified', 'author', 'hash', 'download_url')
document_embedded_role = (blacklist('url', 'download_url') + schematics_embedded_role)
document_view_role = (blacklist('revisions') + schematics_default_role)
document_revisions_role =  whitelist('url', 'dateModified')


document_roles = {
    'create': document_create_role,
    'edit': document_edit_role,
    'embedded': document_embedded_role,
    'view': document_view_role,
    'revisions': document_revisions_role,
}


organization_roles = {
   'embedded': schematics_embedded_role,
   'view': schematics_default_role,
}