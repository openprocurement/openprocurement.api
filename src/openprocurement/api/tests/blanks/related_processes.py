# -*- coding: utf-8 -*-
from copy import deepcopy


class RelatedProcessesTestMixinBase(object):
    """This test mixin assumes that relatedProcesses on every resource behave the same

    The only difference is the URL-prefix, that is located before '/relatedProcesses' in the
    request path. This mixin requires URL-providing method to adapt to different resources.

    Note, that this mixin must be system-wide applicable, so it will test only basic things,
    like:
        - Ability to create the resource
        - GET the resource
        - Change the resource
        - Delete the resource

    Knowing this, all the parent-related functions tesing must be introduced in the child mixin
    of this one.
    """

    RESOURCE_POSTFIX = '/related_processes'
    RESOURCE_ID_POSTFIX = '/related_processes/{0}'

    def mixinSetUp(self):
        """Local mixin setup, depending on setUp of test case

        What needs to be preparated:
            Ensure urls to work with:
                self.base_resource_url ~~ '/auctions/ididid'
                self.base_resource_collection_url ~~ '/auctions' <-- to test batch mode

            Setup access header:
                self.access_header ~~ {'X-Access-Token': 'tokenvalue'}

            Setup initial data
                self.base_resource_initial_data ~~ dict with initial data of base resource
                self.initial_related_process_data ~~ dict with initial data of related process model
        """
        raise NotImplementedError

    def test_related_process_listing(self):
        self.mixinSetUp()

        response = self.app.get(self.base_resource_url + self.RESOURCE_POSTFIX)
        self.assertEqual(len(response.json['data']), 0)

        response = self.app.post_json(
            self.base_resource_url + self.RESOURCE_POSTFIX,
            params={
                'data': self.initial_related_process_data
            },
            headers=self.access_header
        )
        self.assertEqual(response.status, '201 Created')
        self.assertIn('id', response.json['data'])
        self.assertEqual(
            response.json['data']['relatedProcessID'],
            self.initial_related_process_data['relatedProcessID'])
        self.assertEqual(response.json['data']['type'], self.initial_related_process_data['type'])

        response = self.app.get(self.base_resource_url + self.RESOURCE_POSTFIX)
        self.assertEqual(len(response.json['data']), 1)

    def test_create_related_process(self):
        self.mixinSetUp()

        response = self.app.get(self.base_resource_url + self.RESOURCE_POSTFIX)
        self.assertEqual(len(response.json['data']), 0)

        data = deepcopy(self.initial_related_process_data)
        data['identifier'] = 'UA-SOME-VALUE'
        data['id'] = '1' * 32

        # Create relatedProcess
        response = self.app.post_json(
            self.base_resource_url + self.RESOURCE_POSTFIX,
            params={
                'data': data
            },
            headers=self.access_header
        )
        self.assertEqual(response.status, '201 Created')
        self.assertIn('id', response.json['data'])
        self.assertNotEqual(response.json['data']['id'], data['id'])
        self.assertIn('identifier', response.json['data'])
        self.assertEqual(
            response.json['data']['relatedProcessID'],
            self.initial_related_process_data['relatedProcessID'])
        self.assertEqual(response.json['data']['type'], self.initial_related_process_data['type'])

        response = self.app.get(self.base_resource_url + self.RESOURCE_POSTFIX)
        self.assertEqual(len(response.json['data']), 1)

        response = self.app.get(self.base_resource_url + self.RESOURCE_POSTFIX)
        self.assertEqual(len(response.json['data']), 1)

    def test_patch_related_process(self):
        self.mixinSetUp()

        response = self.app.get(self.base_resource_url + self.RESOURCE_POSTFIX)
        self.assertEqual(len(response.json['data']), 0)

        data = deepcopy(self.initial_related_process_data)

        # Create relatedProcess
        response = self.app.post_json(
            self.base_resource_url + self.RESOURCE_POSTFIX,
            params={
                'data': data
            },
            headers=self.access_header
        )
        related_process_id = response.json['data']['id']
        self.assertEqual(response.status, '201 Created')
        self.assertIn('id', response.json['data'])
        self.assertEqual(
            response.json['data']['relatedProcessID'],
            self.initial_related_process_data['relatedProcessID']
        )
        self.assertEqual(response.json['data']['type'], self.initial_related_process_data['type'])

        childID = 'ch' * 16
        new_data = {
            'relatedProcessID': '2' * 32,
            'childID': childID,
        }

        # Patch relatedProcess
        response = self.app.patch_json(
            self.base_resource_url + self.RESOURCE_ID_POSTFIX.format(related_process_id),
            params={
                'data': new_data
            },
            headers=self.access_header
        )
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json['data']['id'], related_process_id)
        self.assertEqual(response.json['data']['relatedProcessID'], new_data['relatedProcessID'])
        self.assertEqual(response.json['data']['type'], self.initial_related_process_data['type'])
        self.assertEqual(response.json['data']['childID'], childID)

        response = self.app.get(
            self.base_resource_url + self.RESOURCE_ID_POSTFIX.format(related_process_id),
            params={
                'data': new_data
            },
        )
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json['data']['id'], related_process_id)
        self.assertEqual(response.json['data']['relatedProcessID'], new_data['relatedProcessID'])
        self.assertEqual(response.json['data']['type'], self.initial_related_process_data['type'])

    def test_delete_related_process(self):
        self.mixinSetUp()

        response = self.app.get(self.base_resource_url + self.RESOURCE_POSTFIX)
        self.assertEqual(len(response.json['data']), 0)

        # Create relatedProcess
        response = self.app.post_json(
            self.base_resource_url + self.RESOURCE_POSTFIX,
            params={
                'data': self.initial_related_process_data
            },
            headers=self.access_header
        )
        related_process_id = response.json['data']['id']
        self.assertEqual(response.status, '201 Created')
        self.assertIn('id', response.json['data'])
        self.assertEqual(
            response.json['data']['relatedProcessID'],
            self.initial_related_process_data['relatedProcessID']
        )
        self.assertEqual(response.json['data']['type'], self.initial_related_process_data['type'])

        response = self.app.get(self.base_resource_url + self.RESOURCE_POSTFIX)
        self.assertEqual(len(response.json['data']), 1)

        # Delete relatedProcess
        response = self.app.delete(
            self.base_resource_url + self.RESOURCE_ID_POSTFIX.format(related_process_id),
            headers=self.access_header
        )
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json['data'], None)

        response = self.app.get(self.base_resource_url + self.RESOURCE_POSTFIX)
        self.assertEqual(len(response.json['data']), 0)

    def test_patch_with_concierge(self):
        self.mixinSetUp()

        response = self.app.get(self.base_resource_url + self.RESOURCE_POSTFIX)
        self.assertEqual(len(response.json['data']), 0)

        # Create relatedProcess
        response = self.app.post_json(
            self.base_resource_url + self.RESOURCE_POSTFIX,
            params={
                'data': self.initial_related_process_data
            },
            headers=self.access_header
        )
        self.assertEqual(response.status, '201 Created')
        self.assertIn('id', response.json['data'])
        self.assertEqual(
            response.json['data']['relatedProcessID'],
            self.initial_related_process_data['relatedProcessID'])
        self.assertEqual(response.json['data']['type'], self.initial_related_process_data['type'])

    def test_create_related_process_batch_mode(self):
        self.mixinSetUp()

        data = deepcopy(self.base_resource_initial_data)
        related_process_1 = {
            'id': '1' * 32,
            'identifier': 'SOME-IDENTIFIER',
            'type': 'asset',
            'relatedProcessID': '2' * 32
        }
        data['relatedProcesses'] = [
           related_process_1
        ]
        response = self.app.post_json(self.base_resource_collection_url, params={'data': data})
        parent_id = response.json['data']['id']
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(len(response.json['data']['relatedProcesses']), 1)
        self.assertEqual(response.json['data']['relatedProcesses'][0]['type'], related_process_1['type'])
        self.assertEqual(
            response.json['data']['relatedProcesses'][0]['relatedProcessID'],
            related_process_1['relatedProcessID']
        )
        self.assertNotEqual(response.json['data']['relatedProcesses'][0]['id'], related_process_1['id'])
        self.assertIn('identifier', response.json['data']['relatedProcesses'][0])

        related_process_id = response.json['data']['relatedProcesses'][0]['id']

        # Check relatedProcess resource
        # due to test universality, there's a trying to avoid tight places
        templates = ('/{0}', '{0}')
        for t in templates:
            try:
                response = self.app.get(
                    self.base_resource_collection_url +
                    t.format(parent_id) +
                    self.RESOURCE_ID_POSTFIX.format(related_process_id)
                )
            except Exception:
                continue
        self.assertEqual(response.json['data']['type'], related_process_1['type'])
        self.assertEqual(response.json['data']['relatedProcessID'], related_process_1['relatedProcessID'])
        self.assertNotEqual(response.json['data']['id'], related_process_1['id'])
        self.assertIn('identifier', response.json['data'])
