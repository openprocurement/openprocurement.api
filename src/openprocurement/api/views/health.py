# -*- coding: utf-8 -*-
from cornice.service import Service
from pyramid.response import Response

health = Service(name='health', path='/health', renderer='json')
HEALTH_THRESHOLD_FUNCTIONS = {
    'any': any,
    'all': all
}


@health.get()
def get_health(request):
    health_threshold = float(request.params.get('health_threshold', request.registry.health_threshold))
    health_threshold_func_name = request.params.get('health_threshold_func', request.registry.health_threshold_func)
    health_threshold_func = HEALTH_THRESHOLD_FUNCTIONS.get(health_threshold_func_name, all)

    tasks = getattr(request.registry, 'admin_couchdb_server', request.registry.couchdb_server).tasks()
    replications_tasks = filter(lambda task: task.get('type', '') == 'replication', tasks)

    replications = {}
    replications_healthy = []

    for repl in replications_tasks:
        seq_diff = repl['source_seq'] - repl['checkpointed_source_seq']
        healthy = (seq_diff <= health_threshold)
        replication_id = repl['replication_id']
        replications[replication_id] = {
            'progress': repl['progress'],
            'seq_diff': seq_diff,
            'healthy': healthy
        }

        replications_healthy.append(healthy)

    server_healthy = health_threshold_func(replications_healthy)

    output = {
        'health_params': {
            'type': 'seq_diff',
            'threshold': health_threshold,
            'reduce_func': health_threshold_func_name if health_threshold_func_name in HEALTH_THRESHOLD_FUNCTIONS else 'all'
        },
        'replications': replications,
        'server_healthy': server_healthy
    }

    if not(replications and server_healthy):
        return Response(json_body=output, status=503)
    return output
