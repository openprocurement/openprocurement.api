# -*- coding: utf-8 -*-
import unittest
import os
import random
from datetime import timedelta

from openprocurement.api.models import get_now
from openprocurement.api.tests.base import BaseTenderWebTest, test_tender_data
from openprocurement.api.utils import get_revision_changes
from jsonpatch import make_patch, apply_patch as _apply_patch
#from json_tools import diff, patch as _patch
from iso8601 import parse_date

IGNORE = ['_attachments', '_revisions', 'revisions', 'dateModified', "_id", "_rev", "doc_type"]


def conflicts_resolve0(db):
    """ Auto sorted algorithm """
    for c in db.view('conflicts/all', include_docs=True, conflicts=True):
        tid = c[u'id']
        trev = c[u'doc'][u'_rev']
        conflicts = c[u'doc'][u'_conflicts']
        open_revs = dict([(i, None) for i in conflicts])
        open_revs[trev] = sorted(set([i.get('rev') for i in ctender['revisions']]))
        td = {trev: c[u'doc']}
        for r in conflicts:
            t = c[u'doc'] if r == trev else db.get(tid, rev=r)
            open_revs[r] = sorted(set([i.get('rev') for i in t['revisions']]))
            if r not in td:
                td[r] = t.copy()
        common_rev = [i[0] for i in zip(*open_revs.values()) if all(map(lambda x: i[0]==x, i))][-1]
        tt = {}
        for r in open_revs:
            t = td[r]
            revs = t['revisions']
            common_index = [i.get('rev') for i in revs].index(common_rev)
            for rev in revs[common_index:][::-1]:
                tn = t.copy()
                t = _apply_patch(t, rev['changes'])
                #t = _patch(t, rev['changes'])
                ti = dict([x for x in t.items() if x[0] not in IGNORE])
                tj = dict([x for x in tn.items() if x[0] not in IGNORE])
                tt[rev['date']] = (rev['date'], rev, get_revision_changes(ti, tj))
            if r == trev:
                t['revisions'] = revs[:common_index]
                td[common_rev] = t
        tt = tt.values()
        tt.sort(key=lambda i: i[0])
        ctender = td[common_rev]
        for i in tt:
            print 'changes', i[2]
            t = ctender.copy()
            ctender.update(_apply_patch(t, i[2]))
            #_patch(ctender, i[2])
            patch = get_revision_changes(ctender, t)
            print 'patch', patch
            revision = i[1]
            revision['changes'] = patch
            revision['rev'] = common_rev
            ctender['revisions'].append(revision)
        uu=[]
        dateModified = max([parse_date(i['dateModified']) for i in td.values()])
        dateModified += timedelta(microseconds=1)
        ctender['dateModified'] = dateModified.isoformat()
        for r in open_revs:
            if r == trev:
                continue
            uu.append({'_id': tid, '_rev': r, '_deleted': True})
        try:
            db.save(ctender)
        except:
            continue
        else:
            db.update(uu)


def conflicts_resolve(db):
    """ Branch apply algorithm """
    for c in db.view('conflicts/all', include_docs=True, conflicts=True):
        ctender = c[u'doc']
        tid = c[u'id']
        trev = ctender[u'_rev']
        conflicts = ctender[u'_conflicts']
        open_revs = dict([(i, None) for i in conflicts])
        open_revs[trev] = sorted(set([i.get('rev') for i in ctender['revisions']]))
        td = {trev: ctender}
        for r in conflicts:
            t = ctender if r == trev else db.get(tid, rev=r)
            open_revs[r] = sorted(set([i.get('rev') for i in t['revisions']]))
            if r not in td:
                td[r] = t.copy()
        common_rev = [i[0] for i in zip(*open_revs.values()) if all(map(lambda x: i[0]==x, i))][-1]
        common_index = [i.get('rev') for i in ctender['revisions']].index(common_rev)
        applied = [rev['date'] for rev in ctender['revisions'][common_index:]]
        for r in conflicts:
            tt = []
            t = td[r]
            revs = t['revisions']
            common_index = [i.get('rev') for i in revs].index(common_rev)
            for rev in revs[common_index:][::-1]:
                tn = t.copy()
                t = _apply_patch(t, rev['changes'])
                #t = _patch(t, rev['changes'])
                ti = dict([x for x in t.items() if x[0] not in IGNORE])
                tj = dict([x for x in tn.items() if x[0] not in IGNORE])
                tt.append((rev['date'], rev, get_revision_changes(ti, tj)))
            for i in tt[::-1]:
                if i[0] in applied:
                    continue
                print 'changes', i[2]
                t = ctender.copy()
                ctender.update(_apply_patch(t, i[2]))
                #_patch(ctender, i[2])
                patch = get_revision_changes(ctender, t)
                print 'patch', patch
                revision = i[1]
                revision['changes'] = patch
                revision['rev'] = common_rev
                #revision['rev'] = trev
                ctender['revisions'].append(revision)
                applied.append(i[0])
        uu=[]
        #dateModified = max([parse_date(i['dateModified']) for i in td.values()])
        #dateModified += timedelta(microseconds=1)
        #ctender['dateModified'] = dateModified.isoformat()
        ctender['dateModified'] = get_now().isoformat()
        for r in conflicts:
            uu.append({'_id': tid, '_rev': r, '_deleted': True})
        try:
            db.save(ctender)
        except:
            continue
        else:
            db.update(uu)


class TenderConflictsTest(BaseTenderWebTest):

    def setUp(self):
        super(TenderConflictsTest, self).setUp()
        self.app2 = self.app.__class__(
            "config:tests2.ini", relative_to=os.path.dirname(__file__))
        self.app2.RequestClass = self.app.RequestClass
        self.app2.authorization = ('Basic', ('token', ''))
        self.db2 = self.app2.app.registry.db

    def tearDown(self):
        #del self.db2[self.tender_id]
        del self.couchdb_server[self.db2.name]
        super(TenderConflictsTest, self).tearDown()

    def patch_tender(self, i, j, app):
        for i in range(i, j):
            a = app(i)
            c = random.choice(['USD', 'UAH', 'RUB'])
            response = a.patch_json('/tenders/{}'.format(self.tender_id), {'data': {
                'title': "title changed #{}".format(i),
                'description': "description changed #{}".format(i),
                'value': {
                    'amount': i*1000 + 500,
                    'currency': c
                },
                'minimalStep': {
                    'currency': c
                }
            }})
            self.assertEqual(response.status, '200 OK')

    def test_conflict_simple(self):
        self.couchdb_server.replicate(self.db.name, self.db2.name)
        self.couchdb_server.replicate(self.db2.name, self.db.name)
        response = self.app.get('/tenders/{}'.format(self.tender_id))
        self.assertEqual(response.status, '200 OK')
        tender = response.json['data']
        response = self.app2.get('/tenders/{}'.format(self.tender_id))
        self.assertEqual(response.status, '200 OK')
        tender2 = response.json['data']
        self.assertEqual(tender, tender2)
        self.patch_tender(0, 10, lambda i: [self.app, self.app2][i % 2])
        self.couchdb_server.replicate(self.db.name, self.db2.name)
        self.couchdb_server.replicate(self.db2.name, self.db.name)
        self.assertGreater(len(self.db.view('conflicts/all')), 0)
        conflicts_resolve(self.db)
        self.assertEqual(len(self.db.view('conflicts/all')), 0)
        self.couchdb_server.replicate(self.db.name, self.db2.name)
        self.couchdb_server.replicate(self.db2.name, self.db.name)
        self.assertEqual(len(self.db.view('conflicts/all')), 0)
        tender = self.db.get(self.tender_id)
        self.assertEqual(len(tender['revisions']), 11)

    def test_conflict_insdel211(self):
        self.set_status('active.tendering')
        self.couchdb_server.replicate(self.db.name, self.db2.name)
        self.couchdb_server.replicate(self.db2.name, self.db.name)
        response = self.app.get('/tenders/{}'.format(self.tender_id))
        self.assertEqual(response.status, '200 OK')
        tender = response.json['data']

        response = self.app2.post_json('/tenders/{}/bids'.format(self.tender_id), {'data': {'tenderers': [tender["procuringEntity"]], "value": {"amount": 401}}})
        self.assertEqual(response.status, '201 Created')
        bid_id = response.json['data']['id']

        response = self.app.post_json('/tenders/{}/bids'.format(self.tender_id), {'data': {'tenderers': [tender["procuringEntity"]], "value": {"amount": 402}}})
        self.assertEqual(response.status, '201 Created')
        response = self.app.delete('/tenders/{}/bids/{}'.format(self.tender_id, response.json['data']['id']))
        self.assertEqual(response.status, '200 OK')

        self.couchdb_server.replicate(self.db.name, self.db2.name)
        self.couchdb_server.replicate(self.db2.name, self.db.name)
        self.assertGreater(len(self.db.view('conflicts/all')), 0)
        conflicts_resolve(self.db)
        self.assertEqual(len(self.db.view('conflicts/all')), 0)
        self.couchdb_server.replicate(self.db.name, self.db2.name)
        self.couchdb_server.replicate(self.db2.name, self.db.name)
        self.assertEqual(len(self.db.view('conflicts/all')), 0)
        tender = self.db.get(self.tender_id)
        self.assertEqual(len(tender['bids']), 1)
        print [i["id"] for i in tender['bids']]
        self.assertEqual(tender['bids'][0]["id"], bid_id)
        self.assertEqual(tender['bids'][0]["value"]["amount"], 401)

    def test_conflict_insdel121(self):
        self.set_status('active.tendering')
        self.couchdb_server.replicate(self.db.name, self.db2.name)
        self.couchdb_server.replicate(self.db2.name, self.db.name)
        response = self.app.get('/tenders/{}'.format(self.tender_id))
        self.assertEqual(response.status, '200 OK')
        tender = response.json['data']

        response = self.app.post_json('/tenders/{}/bids'.format(self.tender_id), {'data': {'tenderers': [tender["procuringEntity"]], "value": {"amount": 402}}})
        self.assertEqual(response.status, '201 Created')
        bid_id_to_del = response.json['data']['id']

        response = self.app2.post_json('/tenders/{}/bids'.format(self.tender_id), {'data': {'tenderers': [tender["procuringEntity"]], "value": {"amount": 401}}})
        self.assertEqual(response.status, '201 Created')
        bid_id = response.json['data']['id']

        response = self.app.delete('/tenders/{}/bids/{}'.format(self.tender_id, bid_id_to_del))
        self.assertEqual(response.status, '200 OK')

        self.couchdb_server.replicate(self.db.name, self.db2.name)
        self.couchdb_server.replicate(self.db2.name, self.db.name)
        self.assertGreater(len(self.db.view('conflicts/all')), 0)
        conflicts_resolve(self.db)
        self.assertEqual(len(self.db.view('conflicts/all')), 0)
        self.couchdb_server.replicate(self.db.name, self.db2.name)
        self.couchdb_server.replicate(self.db2.name, self.db.name)
        self.assertEqual(len(self.db.view('conflicts/all')), 0)
        tender = self.db.get(self.tender_id)
        self.assertEqual(len(tender['bids']), 1)
        print [i["id"] for i in tender['bids']]
        self.assertEqual(tender['bids'][0]["id"], bid_id)
        self.assertEqual(tender['bids'][0]["value"]["amount"], 401)

    def test_conflict_insdel112(self):
        self.set_status('active.tendering')
        self.couchdb_server.replicate(self.db.name, self.db2.name)
        self.couchdb_server.replicate(self.db2.name, self.db.name)
        response = self.app.get('/tenders/{}'.format(self.tender_id))
        self.assertEqual(response.status, '200 OK')
        tender = response.json['data']

        response = self.app.post_json('/tenders/{}/bids'.format(self.tender_id), {'data': {'tenderers': [tender["procuringEntity"]], "value": {"amount": 402}}})
        self.assertEqual(response.status, '201 Created')
        response = self.app.delete('/tenders/{}/bids/{}'.format(self.tender_id, response.json['data']['id']))
        self.assertEqual(response.status, '200 OK')

        response = self.app2.post_json('/tenders/{}/bids'.format(self.tender_id), {'data': {'tenderers': [tender["procuringEntity"]], "value": {"amount": 401}}})
        self.assertEqual(response.status, '201 Created')
        bid_id = response.json['data']['id']

        self.couchdb_server.replicate(self.db.name, self.db2.name)
        self.couchdb_server.replicate(self.db2.name, self.db.name)
        self.assertGreater(len(self.db.view('conflicts/all')), 0)
        conflicts_resolve(self.db)
        self.assertEqual(len(self.db.view('conflicts/all')), 0)
        self.couchdb_server.replicate(self.db.name, self.db2.name)
        self.couchdb_server.replicate(self.db2.name, self.db.name)
        self.assertEqual(len(self.db.view('conflicts/all')), 0)
        tender = self.db.get(self.tender_id)
        self.assertEqual(len(tender['bids']), 1)
        print [i["id"] for i in tender['bids']]
        self.assertEqual(tender['bids'][0]["id"], bid_id)
        self.assertEqual(tender['bids'][0]["value"]["amount"], 401)

    def test_conflict_complex(self):
        self.couchdb_server.replicate(self.db.name, self.db2.name)
        self.couchdb_server.replicate(self.db2.name, self.db.name)
        self.patch_tender(0, 5, lambda i: [self.app, self.app2][i % 2])
        self.couchdb_server.replicate(self.db.name, self.db2.name)
        self.couchdb_server.replicate(self.db2.name, self.db.name)
        self.assertGreater(len(self.db.view('conflicts/all')), 0)
        conflicts_resolve(self.db)
        self.assertEqual(len(self.db.view('conflicts/all')), 0)
        tender = self.db.get(self.tender_id)
        self.assertEqual(len(tender['revisions']), 6)
        self.assertGreater(len(self.db2.view('conflicts/all')), 0)
        self.patch_tender(5, 10, lambda i: self.app2)
        self.couchdb_server.replicate(self.db.name, self.db2.name)
        self.couchdb_server.replicate(self.db2.name, self.db.name)
        self.assertGreater(len(self.db.view('conflicts/all')), 0)
        conflicts_resolve(self.db)
        self.assertEqual(len(self.db.view('conflicts/all')), 0)
        self.couchdb_server.replicate(self.db.name, self.db2.name)
        self.couchdb_server.replicate(self.db2.name, self.db.name)
        self.assertEqual(len(self.db.view('conflicts/all')), 0)
        tender = self.db.get(self.tender_id)
        self.assertEqual(len(tender['revisions']), 11)

    def test_conflict_oneway(self):
        self.couchdb_server.replicate(self.db.name, self.db2.name)
        self.couchdb_server.replicate(self.db2.name, self.db.name)
        self.patch_tender(0, 5, lambda i: [self.app, self.app2][i % 2])
        self.assertEqual(len(self.db.view('conflicts/all')), 0)
        self.couchdb_server.replicate(self.db2.name, self.db.name)
        self.assertGreater(len(self.db.view('conflicts/all')), 0)
        conflicts_resolve(self.db)
        self.assertEqual(len(self.db.view('conflicts/all')), 0)
        tender = self.db.get(self.tender_id)
        self.assertEqual(len(tender['revisions']), 6)
        self.patch_tender(5, 10, lambda i: self.app2)
        self.couchdb_server.replicate(self.db2.name, self.db.name)
        self.assertGreater(len(self.db.view('conflicts/all')), 0)
        conflicts_resolve(self.db)
        self.assertEqual(len(self.db.view('conflicts/all')), 0)
        tender = self.db.get(self.tender_id)
        self.assertEqual(len(tender['revisions']), 11)
        self.patch_tender(10, 15, lambda i: self.app2)
        self.couchdb_server.replicate(self.db.name, self.db2.name)
        self.couchdb_server.replicate(self.db2.name, self.db.name)
        self.assertGreater(len(self.db.view('conflicts/all')), 0)
        conflicts_resolve(self.db)
        self.assertEqual(len(self.db.view('conflicts/all')), 0)
        self.couchdb_server.replicate(self.db.name, self.db2.name)
        self.couchdb_server.replicate(self.db2.name, self.db.name)
        self.assertEqual(len(self.db.view('conflicts/all')), 0)
        tender = self.db.get(self.tender_id)
        self.assertEqual(len(tender['revisions']), 16)

    def test_conflict_tworesolutions(self):
        self.couchdb_server.replicate(self.db.name, self.db2.name)
        self.couchdb_server.replicate(self.db2.name, self.db.name)
        self.patch_tender(0, 10, lambda i: [self.app, self.app2][i % 2])
        self.assertEqual(len(self.db.view('conflicts/all')), 0)
        self.couchdb_server.replicate(self.db.name, self.db2.name)
        self.couchdb_server.replicate(self.db2.name, self.db.name)
        self.assertGreater(len(self.db.view('conflicts/all')), 0)
        conflicts_resolve(self.db)
        self.assertEqual(len(self.db.view('conflicts/all')), 0)
        self.assertGreater(len(self.db2.view('conflicts/all')), 0)
        conflicts_resolve(self.db2)
        self.assertEqual(len(self.db2.view('conflicts/all')), 0)
        #
        self.couchdb_server.replicate(self.db.name, self.db2.name)
        self.couchdb_server.replicate(self.db2.name, self.db.name)
        self.assertGreater(len(self.db.view('conflicts/all')), 0)
        conflicts_resolve(self.db)
        self.assertEqual(len(self.db.view('conflicts/all')), 0)
        #
        self.couchdb_server.replicate(self.db.name, self.db2.name)
        self.couchdb_server.replicate(self.db2.name, self.db.name)
        self.assertEqual(len(self.db.view('conflicts/all')), 0)
        tender = self.db.get(self.tender_id)
        self.assertEqual(len(tender['revisions']), 11)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TenderConflictsTest))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
