#import json
import cmislib
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

from pyramid_alfresco import resources

REST = 'https://api.alfresco.com/%(network)s/public/alfresco/versions/1/%(api)s'
CMIS = 'https://api.alfresco.com/%(network)s/public/cmis/versions/1.0/atom/%(api)s'
PAGE_SIZE = 20


def api_call(request, api, params=None, version=REST):
    if not params:
        params = {}
    params['access_token'] = request.session.get('oauthAccessToken')
    network = request.registry.settings.get('alfresco.network')
    r = requests.get(version % {'api':api,
                                'network': network},
                     params=params)
    if r.status_code != 200:
        raise HTTPForbidden('request contains wrong access token.')
    return r


def get_cmis_root(request):
    url = CMIS % {'api': '', 'network': request.registry.settings.get('alfresco.network')}
    client = cmislib.CmisClient(url, '', '', access_token=request.session.get('oauthAccessToken'))
    try:
        repo = client.getDefaultRepository()
    except cmislib.exceptions.PermissionDeniedException:
        raise HTTPForbidden('request contains wrong access token.')
    return repo


@view_config(route_name='home', renderer='templates/dashboard.pt', permission='view')
def dashboard(request):
    resources.unicorn.need()
    sites = get_cmis_root(request).getRootFolder().getChildren()[0].getChildren()
    main = get_renderer('templates/master.pt').implementation()
    return {'main': main,
            'sites': sites}


@view_config(route_name='path', renderer='templates/path.pt')
def path(request):
    resources.unicorn.need()
    path = request.matchdict['path']
    path = '/' + path
    repo = get_cmis_root(request)
    folder = repo.getObjectByPath(path.encode('utf-8'))
    folderActions = folder.getAllowableActions()
    pageSize = PAGE_SIZE
    skipCount = 0
    if ('maxItems' in request.GET.keys() and
        'skipCount' in request.GET.keys()):
        pageSize = int(request.GET['maxItems'])
        skipCount = int(request.GET['skipCount'])
        if skipCount < 0:
            skipCount = 0

    rs = folder.getChildren(includeAllowableActions=True,
                            maxItems=pageSize,
                            skipCount=skipCount,
                            orderBy='cmis:name,ASC')
 
    main = get_renderer('templates/master.pt').implementation()
    return {'page_title': folder.name,
            'path': path,
            'main': main,
            'actions': folderActions,
            'children': rs}


@view_config(route_name='details', renderer='templates/details.pt')
def details(request):
    resources.unicorn.need()
    path = request.matchdict['path']
    path = '/' + path
    repo = get_cmis_root(request)
    obj = repo.getObjectByPath(path.encode('utf-8'))
    main = get_renderer('templates/master.pt').implementation()
    return {'main': main,
            'page_title': obj.name,
            'path': path,
            'object': obj}


@view_config(route_name='uploadFile')
def upload_file(request):
    if 'Upload' in request.POST:
        targetPath = "/" + request.matchdict['path']
        repo = get_cmis_root(request)
        targetFolder = repo.getObjectByPath(targetPath)
        uploadedFile = request.POST.get('file')
        mimetype, encoding = mimetypes.guess_type(uploadedFile.filename)
        doc = targetFolder.createDocument(uploadedFile.filename,
                                          contentFile=uploadedFile.file,
                                          contentType=mimetype
                                          )
        return HTTPFound(location="/path" + targetPath)


@view_config(context=HTTPForbidden)
def forbidden_view(request):
    loc = route_url('login', request, _query=(('next', request.path),))
    if authenticated_userid(request):
        headers = forget(request)
        return HTTPFound(location=loc, headers=headers)
    return HTTPFound(location=loc)


@view_config(route_name='logout')
def logout_view(request):
    headers = forget(request)
    loc = route_url('home', request)
    return HTTPFound(location=loc, headers=headers)


@view_config(route_name='login', renderer='templates/sign.pt')
def login_view(request):
    resources.login.need()
    return {'login_url': login_url}


@view_config(context='velruse.AuthenticationComplete')
def login_complete_view(request):
    request.session['oauthAccessToken'] = request.context.credentials['oauthAccessToken']
    headers = remember(request, 'user')
    return HTTPFound(location=route_url('home', request), headers=headers)
