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
''':mod:`views.diagnostics`
===========================

:Synopsis:
  REST call handlers for GMN diagnostic APIs.
  These are used in various diagnostics, debugging and testing scenarios.
  Access is unrestricted in debug mode. Disabled in production.
:Author: DataONE (Dahl)
'''
# Stdlib.
import cgi
import collections
import csv
import datetime
import glob
import hashlib
import httplib
import logging
import mimetypes
import os
import pprint
import re
import stat
import sys
import time
import urllib
import urlparse
import uuid

# Django.
from django.http import HttpResponse
from django.http import HttpResponseNotAllowed
from django.http import HttpResponseBadRequest
from django.http import Http404
from django.template import Context, loader
from django.shortcuts import render_to_response
from django.db.models import Avg, Max, Min, Count
from django.core.exceptions import ObjectDoesNotExist

# 3rd party.
try:
  import iso8601
except ImportError, e:
  sys.stderr.write('Import error: {0}\n'.format(str(e)))
  sys.stderr.write('Try: sudo apt-get install python-setuptools\n')
  sys.stderr.write('     sudo easy_install http://pypi.python.org/packages/' \
                   '2.5/i/iso8601/iso8601-0.1.4-py2.5.egg\n')
  raise

# DataONE APIs.
import d1_common.const
import d1_common.types.exceptions
import d1_common.types.generated.dataoneErrors as dataoneErrors
import d1_common.types.generated.dataoneTypes as dataoneTypes

# App.
import d1_assert
import mn.db_filter
import mn.event_log
import mn.lock_pid
import mn.models
import mn.psycopg_adapter
import mn.sysmeta
import mn.urls
import mn.util
import service.settings


def replicate_post(request):
  return replicate_post(request)


def replicate_get(request):
  return render_to_response(
    'replicate_get.html',
    {'replication_queue': mn.models.Replication_work_queue.objects.all()}
  )


def replicate_get_xml(request):
  return render_to_response('replicate_get.xml',
    {'replication_queue': mn.models.Replication_work_queue.objects.all() },
    mimetype=d1_common.const.MIMETYPE_XML)


def replicate_clear(request):
  mn.models.Replication_work_queue.objects.all().delete()
  return HttpResponse('OK')


def test(request):
  if request.method != 'GET':
    return HttpResponseNotAllowed(['GET'])

  return render_to_response('test.html', {})


def cert(request):
  if request.method != 'GET':
    return HttpResponseNotAllowed(['GET'])

  return HttpResponse(pprint.pformat(request, 2))


def slash(request, p1, p2, p3):
  '''
  '''
  if request.method != 'GET':
    return HttpResponseNotAllowed(['GET'])

  return render_to_response('test_slash.html', {'p1': p1, 'p2': p2, 'p3': p3})


def exception(request, exc):
  if request.method != 'GET':
    return HttpResponseNotAllowed(['GET'])

  raise Exception("not a dataone exception")
  #raise d1_common.types.exceptions.InvalidRequest(0, 'Test exception')
  #raise d1_common.types.exceptions.NotFound(0, 'Test exception', '123')

  # Return the pid.
  pid_ser = d1_common.types.pid_serialization.Identifier('testpid')
  doc, content_type = pid_ser.serialize('text/xml')
  return HttpResponse(doc, content_type)


def invalid_return(request, type):
  if type == "200_html":
    return HttpResponse("invalid") #200, html
  elif type == "200_xml":
    return HttpResponse("invalid", "text/xml") #200, xml
  elif type == "400_html":
    return HttpResponseBadRequest("invalid") #400, html
  elif type == "400_xml":
    return HttpResponseBadRequest("invalid", "text/xml") #400, xml

  return HttpResponse("OK")


def get_request(request):
  if request.method != 'GET':
    return HttpResponseNotAllowed(['GET'])

  pp = pprint.PrettyPrinter(indent=2)
  return HttpResponse('<pre>{0}</pre>'.format(cgi.escape(pp.pformat(request))))


def clear_database(request):
  mn.models.Object.objects.all().delete()
  mn.models.Object_format.objects.all().delete()
  mn.models.Checksum_algorithm.objects.all().delete()

  mn.models.DB_update_status.objects.all().delete()


def delete_all_objects(request):
  '''Remove all objects from db.
  '''
  if request.method != 'GET':
    return HttpResponseNotAllowed(['GET'])

  for object_ in mn.models.Object.objects.all():
    _delete_object(object_.pid)

  # Log this operation.
  logging.info(
    'client({0}): Deleted all repository object records'.format(
      mn.util.request_to_string(request)
    )
  )

  return HttpResponse('OK')


def delete_single_object(request, pid):
  '''Delete an object from the Member Node, where the object is either a data
  object or a science metadata object.
  
  Note: The semantics for this method are different than for the production
  method that deletes an object. This method removes all traces that the object
  ever existed.
  '''
  if request.method != 'GET':
    return HttpResponseNotAllowed(['GET'])

  _delete_object(pid)

  # Log this operation. Event logs are tied to particular objects, so we can't
  # log this event in the event log. Instead, we log it.
  logging.info(
    'client({0}) pid({1}) Deleted object'.format(
      mn.util.request_to_string(request), pid
    )
  )

  # Return the pid.
  pid_ser = d1_common.types.pid_serialization.Identifier(pid)
  doc, content_type = pid_ser.serialize(request.META.get('HTTP_ACCEPT', None))
  return HttpResponse(doc, content_type)


def _delete_object(pid):
  d1_assert.object_exists(pid)
  sciobj = mn.models.Object.objects.get(pid=pid)

  # If the object is wrapped, only delete the reference. If it's managed, delete
  # both the object and the reference.

  try:
    url_split = urlparse.urlparse(sciobj.url)
  except ValueError:
    raise d1_common.types.exceptions.ServiceFailure(
      0, 'pid({0}) url({1}): Invalid URL'.format(pid, sciobj.url)
    )

  if url_split.scheme == 'file':
    sciobj_path = mn.util.store_path(service.settings.OBJECT_STORE_PATH, pid)
    try:
      os.unlink(sciobj_path)
    except EnvironmentError:
      pass

  # At this point, the object was either managed and successfully deleted or
  # wrapped and ignored.

  mn.sysmeta.delete_sysmeta_from_store(pid)

  # Delete the DB entry.
  #
  # By default, Django's ForeignKey emulates the SQL constraint ON DELETE
  # CASCADE. In other words, any objects with foreign keys pointing at the
  # objects to be deleted will be deleted along with them.
  #
  # TODO: This causes associated permissions to be deleted, but any subjects
  # that are no longer needed are not deleted. The orphaned subjects should
  # not cause any issues and will be reused if they are needed again.
  sciobj.delete()


def delete_event_log(request):
  '''Remove all log records.
  '''
  # Clear the access log.
  mn.models.Event_log.objects.all().delete()
  mn.models.Event_log_ip_address.objects.all().delete()
  mn.models.Event_log_event.objects.all().delete()

  # Log this operation.
  logging.info(
    None, 'client({0}): delete_mn.event_log', mn.util.request_to_string(
      request
    )
  )

  return HttpResponse('OK')


def inject_event_log(request):
  '''Inject a fictional log.
  '''
  if request.method != 'POST':
    return HttpResponseNotAllowed(['POST'])

  d1_assert.post_has_mime_parts(request, (('file', 'csv'), ))

  # Create event log entries.
  csv_reader = csv.reader(request.FILES['csv'])

  for row in csv_reader:
    pid = row[0]
    event = row[1]
    ip_address = row[2]
    user_agent = row[3]
    subject = row[4]
    timestamp = iso8601.parse_date(row[5])
    member_node = row[6]

    # Create fake request object.
    request.META = {
      'REMOTE_ADDR': ip_address,
      'HTTP_USER_AGENT': user_agent,
      'REMOTE_ADDR': subject,
    }

    mn.event_log._log(pid, request, event, timestamp)

  return HttpResponse('OK')


def delete_all_access_rules(request):
  # The deletes are cascaded so all subjects are also deleted.
  mn.models.Permission.objects.all().delete()
  return HttpResponse('OK')

# ------------------------------------------------------------------------------
# Test Concurrency.
# ------------------------------------------------------------------------------

#test_shared_dict = collections.defaultdict(lambda: '<undef>')

test_shared_dict = mn.urls.test_shared_dict


def concurrency_clear(request):
  test_shared_dict.clear()
  return HttpResponse('OK')


@mn.lock_pid.for_read
def concurrency_read_lock(request, key, sleep_before, sleep_after):
  time.sleep(float(sleep_before))
  #ret = test_shared_dict
  ret = test_shared_dict[key]
  time.sleep(float(sleep_after))
  return HttpResponse('{0}'.format(ret))


@mn.lock_pid.for_write
def concurrency_write_lock(request, key, val, sleep_before, sleep_after):
  time.sleep(float(sleep_before))
  test_shared_dict[key] = val
  time.sleep(float(sleep_after))
  return HttpResponse('OK')


# No locking.
def concurrency_get_dictionary_id(request):
  time.sleep(3)
  ret = id(test_shared_dict)
  time.sleep(3)
  return HttpResponse('{0}'.format(ret))
