from fanstatic import Library
from fanstatic import Resource
from fanstatic import Group
from js.bootstrap import bootstrap_js, bootstrap_responsive_css
from js.jqueryui import jqueryui

library = Library('pyramid_alfresco', 'resources')

#spacelab = Resource(library, 'spacelab.min.css')
login = Group([Resource(library, 'unicorn.login.css',
                        depends=[bootstrap_responsive_css]),
               Resource(library, 'unicorn.login.js',
                        bottom=True,
                        depends=[bootstrap_js])])
unicorn_css = Resource(library, 'unicorn.main.css', depends=[bootstrap_responsive_css])
unicorn = Group([Resource(library, 'unicorn.grey.css',
                          depends=[unicorn_css]),
                 Resource(library, 'unicorn.js',
                        bottom=True,
                        depends=[bootstrap_js, jqueryui])])

css_resource = Resource(library, 'main.css', depends=[bootstrap_responsive_css])
js_resource = Resource(library, 'main.js', bottom=True, depends=[bootstrap_js])

pyramid_alfresco = Group([css_resource, js_resource,])
