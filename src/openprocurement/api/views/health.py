# -*- coding: utf-8 -*-
from cornice.service import Service
from pyramid.response import Response


health = Service(name='health', path='/health', renderer='json')


@health.get()
def get_spore(request):
    tasks = request.registry.admin_couchdb_server.tasks()
    request.errors.status = 503
    if not(tasks and all([True
                          for task in tasks
                          if 'progress' in task and task['progress'] > request.registry.health_threshold])):
        return Response(json_body=tasks, status=503)
    return tasks
