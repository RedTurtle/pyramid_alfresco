from pyramid.config import Configurator
from pyramid_beaker import session_factory_from_settings
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.security import Authenticated
from pyramid.security import Allow
from sqlalchemy import engine_from_config
from .models import DBSession, Base


class Root(object):
    __acl__ = [(Allow, Authenticated, 'view'),]
    def __init__(self, request):
        self.request = request


def groupfinder(userid, request):
    return []


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine
    session_factory = session_factory_from_settings(settings)
    authn_policy = AuthTktAuthenticationPolicy('supersecret',
                                               callback=groupfinder)
    authz_policy = ACLAuthorizationPolicy()
    config = Configurator(settings=settings,
                          authentication_policy=authn_policy,
                          authorization_policy=authz_policy,
                          root_factory=Root)
    config.set_session_factory(session_factory)
    config.include('pyramid_fanstatic')
    config.include('pyramid_beaker')
    config.include('pyramid_alfresco.oauth')
    config.add_alfresco_login_from_settings(prefix='alfresco.')
    config.add_static_view('static', 'static', cache_max_age=3600)

    config.add_route('home', '/')
    config.add_route('folders', '/sites/{site}/folders')
    config.add_route('path', '/path/{path:.*}')
    config.add_route('details', '/details/{path:.*}')
    config.add_route('delete', '/delete/{path:.*}')
    config.add_route('file', '/file/{path:.*}')
    config.add_route('createFolder', '/createFolder/{path:.*}')
    config.add_route('uploadFile', '/uploadFile/{path:.*}')

    config.add_route('docs_home', '/docs')
    config.add_route('docs_details', '/docs/details/{id:.*}')
    config.add_route('createDoc', '/docs/createDoc')

    config.add_route('login', '/login')
    config.add_route('logout', '/logout')
    config.add_route('oauth', '/alfresco_oauth')
    config.scan()
    return config.make_wsgi_app()
