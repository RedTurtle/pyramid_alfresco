#import json
import mimetypes
import requests
from pyramid.security import remember
from pyramid.security import forget
from pyramid.security import authenticated_userid
from pyramid.httpexceptions import HTTPFound
from pyramid.httpexceptions import HTTPForbidden
from pyramid.renderers import get_renderer
from pyramid.url import route_url
from pyramid.view import view_config
from velruse import login_url
from js.tinymce import tinymce

from .alfresco_views import get_cmis_root
from .models import DBSession, Document
from pyramid_alfresco import resources

PAGE_SIZE = 20


@view_config(route_name='docs_home', renderer='templates/docs.pt', permission='view')
def dashboard(request):
    resources.unicorn.need()
    tinymce.need()
    docs = DBSession.query(Document)
    main = get_renderer('templates/master.pt').implementation()
    return {'main': main,
            'docs': docs}


@view_config(route_name='docs_details', renderer='templates/doc_details.pt')
def details(request):
    resources.unicorn.need()
    id = request.matchdict['id']
    doc = DBSession.query(Document).get(id)
    main = get_renderer('templates/master.pt').implementation()
    return {'main': main,
            'path': '/docs/%s' % doc.name,
            'object': doc}


@view_config(route_name='createDoc')
def create_document(request):
    if 'Create' in request.POST:
        name = request.POST.get('name')
        text = request.POST.get('text')
        repo = get_cmis_root(request)
        path = '/sites/plone/documentlibrary'
        folder = repo.getObjectByPath(path.encode('utf-8'))
        folder.createFolder(name)
        path += '/%s' % name
        uploadedFile = request.POST.get('file')
        if uploadedFile != u'':
            mimetype, encoding = mimetypes.guess_type(uploadedFile.filename)
            document_folder = repo.getObjectByPath(path.encode('utf-8'))
            document_folder.createDocument(uploadedFile.filename,
                                           contentFile=uploadedFile.file,
                                           contentType=mimetype)
            doc = Document(name=name, text=text, attachment='%s/%s' % (path, uploadedFile.filename))
        else:
            doc = Document(name=name, text=text)
        DBSession.add(doc)
        return HTTPFound(location="/docs" )


@view_config(context=HTTPForbidden)
def forbidden_view(request):
    loc = route_url('login', request, _query=(('next', request.path),))

    # tries to refresh the token
    refresh_token = request.session.get('refresh_token')
    if refresh_token:
        print 'refreshing token'
        payload = {}
        payload['refresh_token'] = refresh_token
        payload['client_id'] = request.registry.settings.get('alfresco.consumer_key')
        payload['client_secret'] = request.registry.settings.get('alfresco.consumer_secret')
        payload['grant_type'] = 'refresh_token'
        r = requests.post('https://api.alfresco.com/auth/oauth/versions/2/token',
                          data=payload)
        if r.status_code != 200:
            headers = forget(request)
            request.session.invalidate()
            return HTTPFound(location=loc, headers=headers)
        else:
            request.session['access_token'] = r.json()['access_token']
            request.session['refresh_token'] = r.json()['refresh_token']
            return HTTPFound(location=request.path)

    elif authenticated_userid(request):
        headers = forget(request)
        return HTTPFound(location=loc, headers=headers)
    return HTTPFound(location=loc)


@view_config(route_name='logout')
def logout_view(request):
    headers = forget(request)
    loc = route_url('login', request)
    return HTTPFound(location=loc, headers=headers)


@view_config(route_name='login', renderer='templates/sign.pt')
def login_view(request):
    resources.login.need()
    return {'login_url': login_url}


@view_config(context='velruse.AuthenticationComplete')
def login_complete_view(request):
    request.session['access_token'] = request.context.credentials['access_token']
    request.session['refresh_token'] = request.context.credentials['refresh_token']
    headers = remember(request, 'user')
    return HTTPFound(location=route_url('home', request), headers=headers)
