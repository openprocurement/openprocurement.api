# -*- coding: utf-8 -*-
from pyramid.events import subscriber
from pyramid.events import NewRequest, BeforeRender, ContextFound
from openprocurement.api.constants import VERSION
from openprocurement.api.utils import get_now, update_logging_context, fix_url


@subscriber(NewRequest)
def add_logging_context(event):
    request = event.request
    params = {
        'API_VERSION': VERSION,
        'TAGS': 'python,api',
        'USER': str(request.authenticated_userid or ''),
        'CURRENT_URL': request.url,
        'CURRENT_PATH': request.path_info,
        'REMOTE_ADDR': request.remote_addr or '',
        'USER_AGENT': request.user_agent or '',
        'REQUEST_METHOD': request.method,
        'TIMESTAMP': get_now().isoformat(),
        'REQUEST_ID': request.environ.get('REQUEST_ID', ''),
        'CLIENT_REQUEST_ID': request.headers.get('X-Client-Request-ID', ''),
    }

    request.logging_context = params


@subscriber(ContextFound)
def set_logging_context(event):
    request = event.request

    params = {}
    params['ROLE'] = str(request.authenticated_role)
    if request.params:
        params['PARAMS'] = str(dict(request.params))
    if request.matchdict:
        for x, j in request.matchdict.items():
            params[x.upper()] = j
    update_logging_context(request, params)


@subscriber(NewRequest)
def set_renderer(event):
    request = event.request

    try:
        json = request.json_body
    except ValueError:
        json = {}
    pretty = isinstance(json, dict) and json.get('options', {}).get('pretty') or request.params.get('opt_pretty')
    jsonp = request.params.get('opt_jsonp')
    if jsonp and pretty:
        request.override_renderer = 'prettyjsonp'
        return True
    if jsonp:
        request.override_renderer = 'jsonp'
        return True
    if pretty:
        request.override_renderer = 'prettyjson'
        return True


@subscriber(BeforeRender)
def beforerender(event):
    if event.rendering_val and isinstance(event.rendering_val, dict) and 'data' in event.rendering_val:
        fix_url(event.rendering_val['data'], event['request'].application_url)
