# -*- coding: utf-8 -*-
from cornice import resource
from openprocurement.api.plugins.related_processes.views.related_processes import (
    RelatedProcessesResource,
)


def add_related_processes_views(configurator, base_path, factory):
    """Add related_processes resource basing on some parent resource

        :param configurator: pyramid configurator.

        :param base_path: path for the resource.

        :param factory: factory method from the corresponding traversal module.

    """
    postfix = '/related_processes/{relatedProcess_id}'
    collection_postfix = '/related_processes'

    rp_path = base_path + postfix
    rp_collection_path = base_path + collection_postfix

    rp_res = resource.add_resource(
        RelatedProcessesResource,
        collection_path=rp_collection_path,
        path=rp_path,
        factory=factory
    )
    configurator.add_cornice_resource(rp_res)
