from pyramid.view import view_config

from .resources import pyramid_alfresco


@view_config(route_name='home', renderer='templates/welcome.pt')
def my_view(request):
    pyramid_alfresco.need()
    return {}
