# -*- coding: utf-8 -*-
from cornice.service import Service
from pyramid.response import Response

health = Service(name='health', path='/health', renderer='json')


@health.get()
def get_spore(request):
    tasks = getattr(request.registry, 'admin_couchdb_server', request.registry.couchdb_server).tasks()
    output = {task['replication_id']: task['progress'] for task in tasks if 'type' in task and task['type'] == 'replication'}
    if not(output and all([True if progress >= request.registry.health_threshold else False
                          for progress in output.values()])):
        return Response(json_body=output, status=503)
    return output
