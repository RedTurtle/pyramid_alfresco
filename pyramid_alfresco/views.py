#import json
import cmislib
import mimetypes
import requests
from xml.dom import minidom
from xml.parsers.expat import ExpatError
from StringIO import StringIO
from pyramid.response import Response
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


#def api_call(request, api, params=None, version=REST):
#    if not params:
#        params = {}
#    params['access_token'] = request.session.get('access_token')
#    network = request.registry.settings.get('alfresco.network')
#    r = requests.get(version % {'api':api,
#                                'network': network},
#                     params=params)
#    if r.status_code != 200:
#        raise HTTPForbidden('request contains wrong access token.')
#    return r

def custom_post(self, url, payload, contentType, **kwargs):
    if (len(self.extArgs) > 0):
        kwargs.update(self.extArgs)
    headers = {'Authorization': 'Bearer %s' % kwargs.get('access_token')}
    result = requests.post(url, data=payload, headers=headers)
    if result.status_code == 201:
        try:
            return minidom.parse(StringIO(result.text))
        except ExpatError:
            raise cmislib.exceptions.CmisException('Could not parse server response', url)

def get_cmis_root(request):
    url = CMIS % {'api': '', 'network': request.registry.settings.get('alfresco.network')}
    cmislib.CmisClient.post = custom_post
    client = cmislib.CmisClient(url, '', '', access_token=request.session.get('access_token'))
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


@view_config(route_name='delete')
def delete(request):
    targetPath = "/" + request.matchdict['path']
    repo = get_cmis_root(request)
    targetObj = repo.getObjectByPath(targetPath)
    if hasattr(targetObj, "deleteTree"):
        targetObj.deleteTree()
    else:
        targetObj.delete()
    pathPartList = targetPath.split('/')[:-1]
    if len(pathPartList) <= 1:
        redirectPath = "/path/"
    else:
        redirectPath = "/path" + '/'.join(pathPartList)
    return HTTPFound(location=redirectPath)


@view_config(route_name='uploadFile')
def upload_file(request):
    if 'Upload' in request.POST:
        targetPath = "/" + request.matchdict['path']
        repo = get_cmis_root(request)
        targetFolder = repo.getObjectByPath(targetPath)
        uploadedFile = request.POST.get('file')
        mimetype, encoding = mimetypes.guess_type(uploadedFile.filename)
        targetFolder.createDocument(uploadedFile.filename,
                                    contentFile=uploadedFile.file,
                                    contentType=mimetype
                                    )
        return HTTPFound(location="/path" + targetPath)


@view_config(route_name='createFolder')
def create_folder(request):
    if 'Create' in request.POST:
        folderName = request.POST.get('name')
        targetPath = request.POST.get('targetPath')
        repo = get_cmis_root(request)
        targetFolder = repo.getObjectByPath(targetPath)
        targetFolder.createFolder(folderName)
        #request.session.flash('Form was submitted successfully.')
        return HTTPFound(location="/path" + targetPath)


@view_config(route_name='file')
def get_file(request):
    path = request.matchdict['path']
    path = '/' + path
    repo = get_cmis_root(request)
    obj = repo.getObjectByPath(path.encode('utf-8'))
    return Response(body=obj.getContentStream().read(), content_type=str(obj.properties['cmis:contentStreamMimeType']))


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
