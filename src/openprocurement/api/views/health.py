# -*- coding: utf-8 -*-
from cornice.service import Service
from pyramid.response import Response

health = Service(name='health', path='/health', renderer='json')
HEALTH_THRESHOLD_FUNCTIONS = {
    'any': any,
    'all': all
}


@health.get()
def get_spore(request):
    tasks = getattr(request.registry, 'admin_couchdb_server', request.registry.couchdb_server).tasks()
    output = {
        task['replication_id']: task['progress'] for task in
        tasks if 'type' in task and
        task['type'] == 'replication'
    }
    try:
        health_threshold = float(request.params.get('health_threshold', request.registry.health_threshold))
    except ValueError:
        health_threshold = request.registry.health_threshold
    health_threshold_func_name = request.params.get('health_threshold_func', request.registry.health_threshold_func)
    health_threshold_func = HEALTH_THRESHOLD_FUNCTIONS.get(health_threshold_func_name, all)
    if not(output and health_threshold_func(
            [True if (task['source_seq'] - task['checkpointed_source_seq']) <= health_threshold else False
             for task in tasks if 'type' in task and task['type'] == 'replication']
    )):
        return Response(json_body=output, status=503)
    return output
