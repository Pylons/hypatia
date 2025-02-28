##############################################################################
#
# Copyright (c) 2012 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################

import os
import sys

from setuptools import setup, find_packages, Extension
from distutils.command.build_ext import build_ext
from distutils.errors import CCompilerError
from distutils.errors import DistutilsExecError
from distutils.errors import DistutilsPlatformError

class optional_build_ext(build_ext):
    """This class subclasses build_ext and allows
       the building of C extensions to fail.
    """
    def run(self):
        if os.environ.get("PURE_PYTHON"):
            self._unavailable("Environment defines 'PURE_PYTHON'")
            return
        try:
            build_ext.run(self)
        
        except DistutilsPlatformError as e:
            self._unavailable(e)

    def build_extension(self, ext):
        if os.environ.get("PURE_PYTHON"):
            self._unavailable("Environment defines 'PURE_PYTHON'")
            return
        try:
           build_ext.build_extension(self, ext)
        
        except (CCompilerError, DistutilsExecError) as e:
           self._unavailable(e)

    def _unavailable(self, e):
        def errprint(x):
            sys.stderr.write('%s\n' % x)
        errprint('*' * 80)
        errprint("""WARNING:

        An optional code optimization (C extension) could not be compiled.

        Optimizations for this package will not be available!""")
        errprint('')
        errprint(e)
        errprint('*' * 80)

try:
    here = os.path.abspath(os.path.dirname(__file__))

    with open(os.path.join(here, 'README.rst')) as f:
        README = f.read()

    with open(os.path.join(here, 'CHANGES.rst')) as f:
        CHANGES = f.read()
except IOError:
    README = CHANGES = ''

install_requires = [
    'persistent',
    'BTrees',
    'ZODB>=4.0.0b2', # py3 compat
    'zope.interface',
    ]

testing_extras = ['pytest', 'coverage']

docs_extras = [
    'Sphinx >= 3.0.0',  # Force RTD to use >= 3.0.0
    'docutils',
    'pylons-sphinx-themes >= 1.0.8',  # Ethical Ads
]


setup(name='hypatia',
      version='0.6dev0',
      description='Python package for searching and indexing',
      long_description=README + '\n\n' +  CHANGES,
      classifiers=[
        "Intended Audience :: Developers",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Topic :: Internet :: WWW/HTTP :: Indexing/Search",
        ],
      keywords='indexing catalog search',
      author="Zope Foundation and Contributors",
      author_email="pylons-discuss@googlegroups.com",
      url="http://pylonsproject.org",
      license="ZPL 2.1",
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      tests_require = install_requires,
      install_requires = install_requires,
      extras_require = {
        'benchmark': ['PyChart'],
        'testing': testing_extras,
        'docs': docs_extras,
        },
      ext_modules=[
          Extension('hypatia.text.okascore',
              [os.path.join('hypatia', 'text', 'okascore.c')]),
      ],
      cmdclass = {'build_ext':optional_build_ext},
      ## entry_points = """\
      ## [console_scripts]
      ## catalog_benchmark = hypatia.benchmark.benchmark:run
      ## sortbench = hypatia.benchmark.sortbench:main
      ## """,
      )

