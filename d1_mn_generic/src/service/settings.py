#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This work was created by participants in the DataONE project, and is
# jointly copyrighted by participating institutions in DataONE. For
# more information on DataONE, see our web site at http://dataone.org.
#
#   Copyright ${year}
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
'''
:mod:`settings`
===============

:Synopsis:
  App level settings.

.. moduleauthor:: Roger Dahl
'''

# Stdlib.
import os
import sys

# Member Node configuration.

ENABLE_IP_AUTH = False

# Enable functionality that should only be accessible during testing and debugging.
GMN_DEBUG = True

MN_NAME = 'dryad_mn'

MN_IP = [
  '68.35.3.230', # Roger
  '74.107.75.34', # Dave
  '152.3.105.16', # Karya
  '127.0.0.1' # localhost
]

# CN IPs.
CN_IP = [
  '68.35.3.230', # Roger
  '74.107.75.34', # Dave
  '152.3.105.16', # Karya
  '127.0.0.1', # localhost
]

# Django settings for service project.

# Discover the path of this module
_here = lambda *x: os.path.join(os.path.abspath(os.path.dirname(__file__)), *x)

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
  # ('roger', 'dahl@unm.edu'),
)

MANAGERS = ADMINS

DATABASE_ENGINE = 'sqlite3' # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
DATABASE_NAME = _here('gmn.sq3')
DATABASE_USER = '' # Not used with sqlite3.
DATABASE_PASSWORD = '' # Not used with sqlite3.
DATABASE_HOST = '' # Set to empty string for localhost. Not used with sqlite3.
DATABASE_PORT = '' # Set to empty string for default. Not used with sqlite3.

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/Chicago'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = ''

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/media/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = '(ok#4)+n++u0#x&j1-xsy)u8fijlyv&ycn2t(@cys$ozawzlb-'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
  'django.template.loaders.filesystem.load_template_source',
  'django.template.loaders.app_directories.load_template_source',
  'django.template.loaders.eggs.load_template_source',
)

MIDDLEWARE_CLASSES = (
  'django.middleware.common.CommonMiddleware',
  'django.contrib.sessions.middleware.SessionMiddleware',
  'django.contrib.auth.middleware.AuthenticationMiddleware',
  #'django.middleware.profile.ProfileMiddleware',
  'service.mn.middleware.request_handler.request_handler',
  'service.mn.middleware.exception_handler.exception_handler',
  'service.mn.middleware.response_handler.response_handler',
  'service.mn.middleware.view_handler.view_handler',

  #    'service.cn.middleware.request_handler.request_handler',
  #    'service.cn.middleware.exception_handler.exception_handler',
  #    'service.cn.middleware.response_handler.response_handler',
  #    'service.cn.middleware.view_handler.view_handler',
)

ROOT_URLCONF = 'service.urls'

TEMPLATE_DIRS = (_here('mn/templates'), _here('cn/templates'), )

FIXTURE_DIRS = (_here('mn/fixtures'), _here('cn/fixtures'), )

INSTALLED_APPS = (
  'service.mn',
  'service.cn',

  #    'django.contrib.auth',
  #    'django.contrib.contenttypes',
  #    'django.contrib.sessions',
  #    'django.contrib.sites',
  'django.contrib.admin',
  'django.contrib.admindocs',
)

APPEND_SLASH = False

LOG_PATH = _here('./mn.log')
XSD_PATH = _here('./coordinating_node_sysmeta.xsd')
ROOT_PATH = _here('./')

# GMN.
SYSMETA_CACHE_PATH = _here('./sysmeta_cache')
OBJECT_STORE_PATH = _here('./object_store')
STATIC_STORE_PATH = _here('./static_store')

# Test CN.
CN_SYSMETA_STORE_PATH = _here('./cn_sysmeta_store')

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), './lib')))
