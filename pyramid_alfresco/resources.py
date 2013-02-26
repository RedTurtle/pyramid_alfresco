from fanstatic import Library
from fanstatic import Resource
from fanstatic import Group
from js.bootstrap import bootstrap_js#, bootstrap_responsive_css

library = Library('pyramid_alfresco', 'resources')

spacelab = Resource(library, 'spacelab.min.css')
css_resource = Resource(library, 'main.css', depends=[spacelab])
js_resource = Resource(library, 'main.js', bottom=True, depends=[bootstrap_js])
pyramid_alfresco = Group([css_resource, js_resource,])
