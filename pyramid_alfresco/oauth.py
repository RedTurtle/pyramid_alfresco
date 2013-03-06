"""Alfresco Authentication Views"""
import requests
import uuid

from pyramid.httpexceptions import HTTPFound
from pyramid.security import NO_PERMISSION_REQUIRED

from velruse.api import (
    AuthenticationComplete,
    AuthenticationDenied,
    register_provider,
)
from velruse.exceptions import CSRFError
from velruse.exceptions import ThirdPartyFailure
from velruse.settings import ProviderSettings
from velruse.utils import flat_url


class AlfrescoAuthenticationComplete(AuthenticationComplete):
    """Alfresco auth complete"""


def includeme(config):
    config.add_directive('add_alfresco_login', add_alfresco_login)
    config.add_directive('add_alfresco_login_from_settings',
                         add_alfresco_login_from_settings)


def add_alfresco_login_from_settings(config, prefix='velruse.alfresco.'):
    settings = config.registry.settings
    p = ProviderSettings(settings, prefix)
    p.update('consumer_key', required=True)
    p.update('consumer_secret', required=True)
    p.update('scope')
    p.update('login_path')
    p.update('callback_path')
    p.update('secure')
    p.update('domain')
    config.add_alfresco_login(**p.kwargs)


def add_alfresco_login(config,
                       consumer_key,
                       consumer_secret,
                       scope=None,
                       login_path='/login/alfresco',
                       callback_path='/login/alfresco/callback',
                       secure=True,
                       domain='api.alfresco.com',
                       name='alfresco'):
    """
    Add a Alfresco login provider to the application.
    """
    provider = AlfrescoProvider(name,
                                consumer_key,
                                consumer_secret,
                                scope,
                                secure,
                                domain)

    config.add_route(provider.login_route, login_path)
    config.add_view(provider, attr='login', route_name=provider.login_route,
                    permission=NO_PERMISSION_REQUIRED)

    config.add_route(provider.callback_route, callback_path,
                     use_global_views=True,
                     factory=provider.callback)

    register_provider(config, name, provider)


class AlfrescoProvider(object):
    def __init__(self,
                 name,
                 consumer_key,
                 consumer_secret,
                 scope,
                 secure,
                 domain):
        self.name = name
        self.type = 'alfresco'
        self.consumer_secret = consumer_secret
        self.consumer_key = consumer_key
        self.scope = scope
        self.protocol = 'http' if secure is False else 'https'
        self.domain = domain

        self.login_route = 'velruse.%s-login' % name
        self.callback_route = 'velruse.%s-callback' % name

    def login(self, request):
        """Initiate a alfresco login"""
        scope = request.POST.get('scope', self.scope)
        request.session['state'] = state = uuid.uuid4().hex
        gh_url = flat_url(
            '%s://%s/auth/oauth/versions/2/authorize' % (self.protocol, self.domain),
            scope=scope,
            response_type='code',
            client_id=self.consumer_key,
            redirect_uri=request.route_url(self.callback_route),
            state=state)
        return HTTPFound(location=gh_url)

    def callback(self, request):
        """Process the alfresco redirect"""
        sess_state = request.session.get('state')
        req_state = request.GET.get('state')
        if not sess_state or sess_state != req_state:
            raise CSRFError(
                'CSRF Validation check failed. Request state {req_state} is not '
                'the same as session state {sess_state}'.format(
                    req_state=req_state,
                    sess_state=sess_state
                )
            )
        code = request.GET.get('code')
        if not code:
            reason = request.GET.get('error', 'No reason provided.')
            return AuthenticationDenied(reason=reason,
                                        provider_name=self.name,
                                        provider_type=self.type)

        # Now retrieve the access token with the code
        access_url = flat_url(
        '%s://%s/auth/oauth/versions/2/token' % (self.protocol, self.domain))
        payload = {}
        payload['client_id'] = self.consumer_key,
        payload['client_secret'] = self.consumer_secret,
        payload['redirect_uri'] = request.route_url(self.callback_route),
        payload['code'] = code
        payload['grant_type'] = 'authorization_code'
        r = requests.post(access_url,data=payload)
        if r.status_code != 200:
            raise ThirdPartyFailure("Status %s: %s" % (
                r.status_code, r.content))

        profile = {}
        profile['accounts'] = [{
                'domain':self.domain,
        }]

        cred = {'access_token': r.json()['access_token'],
                'refresh_token': r.json()['refresh_token']}

        return AlfrescoAuthenticationComplete(profile=profile,
                                              credentials=cred,
                                              provider_name=self.name,
                                              provider_type=self.type)
