import json
from pyramid.view import view_config
from velruse import login_url

from .resources import pyramid_alfresco


@view_config(name='login', renderer='templates/sign.pt')
def welcome(request):
    pyramid_alfresco.need()
    return {'login_url': login_url}

@view_config(
    context='velruse.AuthenticationComplete',
    renderer='templates/welcome.pt')
def login_complete_view(request):
    pyramid_alfresco.need()
    context = request.context
    result = {
        'profile': context.profile,
        'credentials': context.credentials,
    }
    return {
        'result': json.dumps(result, indent=4),
    }
