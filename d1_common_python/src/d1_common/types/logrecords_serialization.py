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
Module d1_common.types.logrecords_serialization
==============================================

Implements serializaton and de-serialization for the LogRecords.
'''

# Stdlib.
import csv
import datetime
import os
import StringIO
import sys
import types
import urllib
import wsgiref.handlers
import time

try:
  import cjson as json
except:
  import json

# 3rd party.
# Lxml
#try:
#  from lxml import etree
#except ImportError, e:
#  sys.stderr.write('Import error: {0}\n'.format(str(e)))
#  sys.stderr.write('Try: sudo apt-get install python-lxml\n')
#  raise

#try:
#  import iso8601
#except ImportError, e:
#  sys.stderr.write('Import error: {0}\n'.format(str(e)))
#  sys.stderr.write('Try: sudo apt-get install python-setuptools\n')
#  sys.stderr.write('     sudo easy_install http://pypi.python.org/packages/2.5/i/iso8601/iso8601-0.1.4-py2.5.egg\n')
#  raise

# MN API.
try:
  import d1_common
  import d1_common.exceptions
  import d1_common.ext.mimeparser
  import d1_common.util
except ImportError, e:
  sys.stderr.write('Import error: {0}\n'.format(str(e)))
  sys.stderr.write(
    'Try: svn co https://repository.dataone.org/software/cicore/trunk/api-common-python/src/d1_common\n'
  )
  raise

try:
  import d1_common.types.generated.dataoneTypes
except ImportError, e:
  sys.stderr.write('Import error: {0}\n'.format(str(e)))
  sys.stderr.write('Try: sudo easy_install pyxb\n')
  raise

#===============================================================================


def logEntryToText(logEntry):
  '''Returns a human readable string representation of a logEntry
  '''
  txt = []
  txt.append(
    "%s (%s): %s" % (
      logEntry.memberNode, logEntry.event, logEntry.entryId.value(
      )
    )
  )
  txt.append("  object id: %s" % logEntry.identifier.value())
  txt.append("    ip addr: %s" % logEntry.ipAddress)
  txt.append("      agent: %s" % logEntry.userAgent)
  txt.append("       date: %s" % logEntry.dateLogged.isoformat())
  return "\n".join(txt)


def logEntriesToText(logEntries):
  res = []
  for entry in logEntries.logEntry:
    res.append(logEntryToText(entry))
  return "\n".join(res)


class LogRecords(object):
  '''Implements serialization of DataONE LogEntry
  '''

  def __init__(self):
    self.serialize_map = {
      'application/json': self.serialize_json,
      'text/csv': self.serialize_csv,
      'text/xml': self.serialize_xml,
      'application/xml': self.serialize_xml,
      'application/rdf+xml': self.serialize_rdf_xml,
      'text/html': self.serialize_null, #TODO: Not in current REST spec.
      'text/log': self.serialize_null, #TODO: Not in current REST spec.
    }

    self.deserialize_map = {
      'application/json': self.deserialize_json,
      'text/csv': self.deserialize_csv,
      'text/xml': self.deserialize_xml,
      'application/xml': self.deserialize_xml,
      'application/rdf+xml': self.deserialize_rdf_xml,
      'text/html': self.deserialize_null, #TODO: Not in current REST spec.
      'text/log': self.deserialize_null, #TODO: Not in current REST spec.
    }

    self.pri = [
      'application/json',
      'text/csv',
      'text/xml',
      'application/xml',
      'application/rdf+xml',
      #'text/html',
      #'text/log',
    ]

    self.log = d1_common.types.generated.dataoneTypes.log()

  def serialize(self, accept='application/json', pretty=False, jsonvar=False):
    '''
    '''
    # Determine which serializer to use. If client does not supply accept, we
    # default to JSON.
    try:
      content_type = d1_common.ext.mimeparser.best_match(self.pri, accept)
    except ValueError:
      # An invalid Accept header causes mimeparser to throw a ValueError.
      #sys_log.debug('Invalid HTTP_ACCEPT value. Defaulting to JSON')
      content_type = 'application/json'
    # Deserialize object
    return self.serialize_map[d1_common.util.get_content_type(content_type)](
      pretty, jsonvar
    ), content_type

  #<?xml version="1.0" encoding="UTF-8"?>
  #<d1:log xmlns:d1="http://dataone.org/service/types/logging/0.1"
  #     xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  #     xsi:schemaLocation="http://dataone.org/service/types/logging/0.1 https://repository.dataone.org/software/cicore/trunk/schemas/logging.xsd">
  #    <logEntry>
  #        <entryId>845797</entryId>
  #        <identifier>nceas.951.27</identifier>
  #        <ipAddress>128.111.220.17</ipAddress>
  #        <userAgent>Kepler/1.0.0</userAgent>
  #        <principal>public</principal>
  #        <event>read</event>
  #        <dateLogged>2010-02-01T00:00:11.152</dateLogged>
  #        <memberNode>mnode:001:KNB</memberNode>
  #    </logEntry> 
  #    <logEntry>
  #        <entryId>846267</entryId>
  #        <identifier>nceas.962.1</identifier>
  #        <ipAddress>128.111.242.15</ipAddress>
  #        <userAgent>Morpho/1.8.0</userAgent>
  #        <principal>uid=jones,o=unaffiliated,dc=ecoinformatics,dc=org</principal>
  #        <event>create</event>
  #        <dateLogged>2010-02-01T09:51:46.068</dateLogged>
  #        <memberNode>mnode:002:Dryad</memberNode>
  #    </logEntry> 
  #</d1:log>
  def serialize_xml(self, pretty=False, jsonvar=False):
    '''
    '''
    return self.log.toxml()

  def serialize_json(self, pretty=False, jsonvar=False):
    '''Serialize LogRecords to JSON.
    '''
    obj = {}
    obj['logEntry'] = []

    for o in self.log.logEntry:
      logEntry = {}
      logEntry['entryId'] = o.entryId.value()
      logEntry['identifier'] = o.identifier.value()
      logEntry['ipAddress'] = o.ipAddress
      logEntry['userAgent'] = o.userAgent
      logEntry['principal'] = o.principal
      logEntry['event'] = o.event
      logEntry['dateLogged'] = datetime.datetime.isoformat(o.dateLogged)
      logEntry['memberNode'] = o.memberNode

      # Append object to response.
      obj['logEntry'].append(logEntry)

    if pretty:
      if jsonvar is not False:
        return jsonvar + ' = ' + json.dumps(obj, indent=2)
      else:
        return json.dumps(obj, indent=2)
    else:
      if jsonvar is not False:
        return jsonvar + '=' + json.dumps(obj)
      else:
        return json.dumps(obj)

  def serialize_csv(self, pretty=False, jsonvar=False):
    '''Serialize LogRecords to CSV.
    '''
    io = StringIO.StringIO()
    csv_writer = csv.writer(
      io, dialect=csv.excel,
      quotechar='"', quoting=csv.QUOTE_MINIMAL
    )

    # Comment containing start, count and total.
    for o in self.log.logEntry:
      logEntry = []
      logEntry.append(o.entryId.value())
      logEntry.append(o.identifier.value())
      logEntry.append(o.ipAddress)
      logEntry.append(o.userAgent)
      logEntry.append(o.principal)
      logEntry.append(o.event)
      logEntry.append(datetime.datetime.isoformat(o.dateLogged))
      logEntry.append(o.memberNode)

      csv_writer.writerow(logEntry)
    return io.getvalue()

  def serialize_rdf_xml(self, doc):
    '''
    '''
    raise d1_common.exceptions.NotImplemented(0, 'serialize_rdf_xml not implemented.')

  def serialize_null(self, doc, pretty=False, jsonvar=False):
    '''
    '''
    raise d1_common.exceptions.NotImplemented(0, 'Serialization method not implemented.')

    #== Deserialization methods ==================================================
  def deserialize(self, doc, content_type='application/json'):
    '''
    '''
    return self.deserialize_map[d1_common.util.get_content_type(content_type)](doc)

  def deserialize_xml(self, doc):
    '''
    '''
    self.log = d1_common.types.generated.dataoneTypes.CreateFromDocument(doc)
    return self.log

  def deserialize_json(self, doc):
    '''
    '''
    j = json.loads(doc)
    logEntries = []

    for o in j['logEntry']:
      logEntry = d1_common.types.generated.dataoneTypes.LogEntry()

      logEntry.entryId = o['entryId']
      logEntry.identifier = o['identifier']
      logEntry.ipAddress = o['ipAddress']
      logEntry.userAgent = o['userAgent']
      logEntry.principal = o['principal']
      logEntry.event = o['event']
      logEntry.dateLogged = datetime.datetime.isoformat(o['dateLogged'])
      logEntry.memberNode = o['memberNode']
      logEntries.append(logEntry)
    self.log.logEntry = logEntries
    return self.log

  def deserialize_csv(self, doc):
    '''Serialize object to CSV.
    '''
    io = StringIO.StringIO(doc)
    csv_reader = csv.reader(
      io, dialect=csv.excel,
      quotechar='"', quoting=csv.QUOTE_MINIMAL
    )

    logEntries = []

    for csv_line in csv_reader:
      logEntry = d1_common.types.generated.dataoneTypes.LogEntry()
      logEntry.identifier = csv_line[0]
      logEntry.objectFormat = csv_line[1]
      logEntry.checksum = csv_line[2]
      logEntry.checksum.algorithm = csv_line[3]
      logEntry.dateSysMetadataModified = csv_line[4]
      logEntry.size = csv_line[5]
      logEntries.append(logEntry)
    self.log.logEntry = logEntries
    return self.log

  def deserialize_rdf_xml(self, doc):
    '''
    '''
    raise d1_common.exceptions.NotImplemented(0, 'deserialize_rdf_xml not implemented.')

  def deserialize_null(self, doc):
    '''
    '''
    raise d1_common.exceptions.NotImplemented(
      0, 'Deserialization method not implemented.'
    )
