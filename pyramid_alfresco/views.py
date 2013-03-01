#import json
from pyramid.security import remember
from pyramid.security import authenticated_userid
from pyramid.httpexceptions import HTTPFound
from pyramid.httpexceptions import HTTPForbidden
from pyramid.url import route_url
from pyramid.view import view_config
from velruse import login_url

from .resources import pyramid_alfresco


@view_config(route_name='home', renderer='templates/welcome.pt', permission='view')
def welcome(request):
    pyramid_alfresco.need()
    return {'login_url': login_url}


@view_config(context=HTTPForbidden)
def forbidden_view(request):
    # do not allow a user to login if they are already logged in
    if authenticated_userid(request):
        return HTTPForbidden()
    loc = route_url('login', request, _query=(('next', request.path),))
    return HTTPFound(location=loc)


@view_config(route_name='login', renderer='templates/sign.pt')
def login_view(request):
    pyramid_alfresco.need()
    return {'login_url': login_url}


@view_config(context='velruse.AuthenticationComplete')
def login_complete_view(request):
    #pyramid_alfresco.need()
    #context = request.context
    #result = {
    #    'profile': context.profile,
    #    'credentials': context.credentials,
    #}
    headers = remember(request, 'user')
    return HTTPFound(location=route_url('home', request), headers=headers)
