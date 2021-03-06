import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.md')).read()
CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()

requires = [
    'pyramid',
    'SQLAlchemy',
    'transaction',
    'pyramid_tm',
    'pyramid_debugtoolbar',
    'zope.sqlalchemy',
    'waitress',
    'pyramid_fanstatic',
    'js.bootstrap==2.2.2',
    'js.jqueryui',
    'js.tinymce',
    'velruse',
    'pyramid_beaker',
    'cmislib'
    ]

setup(name='pyramid_alfresco',
      version='0.0',
      description='pyramid_alfresco',
      long_description=README + '\n\n' + CHANGES,
      classifiers=[
        "Programming Language :: Python",
        "Framework :: Pyramid",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        ],
      author='',
      author_email='',
      url='',
      keywords='web wsgi bfg pylons pyramid',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      test_suite='pyramid_alfresco',
      install_requires=requires,
      entry_points="""\
      [paste.app_factory]
      main = pyramid_alfresco:main
      [console_scripts]
      initdb = pyramid_alfresco.initdb:main
      [fanstatic.libraries]
      pyramid_alfresco = pyramid_alfresco.resources:library
      """,
      )
