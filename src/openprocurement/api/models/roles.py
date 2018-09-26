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
document_revisions_role = whitelist('url', 'dateModified')

item_create_role = blacklist()
item_edit_role = blacklist('id')
item_view_role = (schematics_default_role + blacklist())


item_roles = {
    'create': item_create_role,
    'edit': item_edit_role,
    'view': item_view_role,
}


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

english_auctionParameters_edit_role = blacklist('type', 'dutchSteps')
insider_auctionParameters_edit_role = blacklist('type')
auctionParameters_roles = {
    'create': blacklist('type', 'dutchSteps'),
    'edit_1.sellout.english': english_auctionParameters_edit_role,
    'edit_2.sellout.english': english_auctionParameters_edit_role,
    'edit_3.sellout.insider': insider_auctionParameters_edit_role
}

Administrator_role = whitelist(
    'auctionPeriod',
    'lots',
    'mode',
    'procuringEntity',
    'status',
    'suspended',
)

related_process_roles = {
    'view': (schematics_default_role + blacklist()),
    'create': whitelist(
        'type',
        'relatedProcessID',
        'childID',
    ),
    'edit': whitelist(
        'type',
        'relatedProcessID',
        'childID',
    ),
    'concierge': whitelist('identifier')
}
