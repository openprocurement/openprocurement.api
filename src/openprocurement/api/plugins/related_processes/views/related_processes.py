# -*- coding: utf-8 -*-
from openprocurement.api.interfaces import IResourceManager
from openprocurement.api.utils.common import context_unpack
from openprocurement.api.utils.api_resource import (
    APIResource,
    json_view,
)
from openprocurement.api.validation import (
    validate_related_process_data,
    validate_patch_related_process_data,
)


post_validators = (
    validate_related_process_data,
)
patch_validators = (
    validate_patch_related_process_data,
)


class RelatedProcessesResource(APIResource):

    @json_view(content_type="application/json", permission='create_related_process', validators=post_validators)
    def collection_post(self):
        """Create Related Process"""
        related_process = self.request.validated['relatedProcess']
        parent = related_process.__parent__

        saved = self.request.registry.getAdapter(
            parent,
            IResourceManager,
        ).related_processes_manager.create(self.request)

        if saved:
            self.LOGGER.info(
                'Created related process {}'.format(related_process.id),
                extra=context_unpack(
                    self.request, {'MESSAGE_ID': 'related_processes_create'},
                    {'related_process': related_process.id})
            )
            self.request.response.status = 201
            related_process_route = self.request.matched_route.name.replace("collection_", "")
            self.request.response.headers['Location'] = self.request.current_route_url(
                _route_name=related_process_route,
                relatedProcess_id=related_process.id,
                _query={}
            )
            return {'data': related_process.serialize("view")}

    def collection_get(self):
        """Related Process List"""
        collection_data = [i.serialize("view") for i in self.context.relatedProcesses]
        return {'data': collection_data}

    def get(self):
        """Related Process Read"""
        related_process = self.request.context
        return {'data': related_process.serialize("view")}

    @json_view(content_type="application/json", permission='edit_related_process', validators=patch_validators)
    def patch(self):
        """Related Process Update"""
        related_process = self.request.context
        parent = related_process.__parent__

        applied = self.request.registry.getAdapter(
            parent,
            IResourceManager
        ).related_processes_manager.update(self.request)
        if applied:
            self.LOGGER.info(
                'Updated relatedProcess {}'.format(related_process.id),
                extra=context_unpack(self.request, {'MESSAGE_ID': 'related_process_patch'})
            )
            return {'data': related_process.serialize("view")}

    @json_view(permission='delete_related_process')
    def delete(self):
        """Related Process Delete"""
        related_process = self.request.context
        parent = related_process.__parent__

        deleted = self.request.registry.getAdapter(
            parent,
            IResourceManager
        ).related_processes_manager.delete(self.request)
        if deleted:
            self.LOGGER.info(
                'Delete relatedProcess {}'.format(related_process.id),
                extra=context_unpack(self.request, {'MESSAGE_ID': 'related_process_patch'})
            )
            self.request.response.status = 200
            return {'data': None}
