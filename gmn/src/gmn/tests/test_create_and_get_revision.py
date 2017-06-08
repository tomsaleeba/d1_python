#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This work was created by participants in the DataONE project, and is
# jointly copyrighted by participating institutions in DataONE. For
# more information on DataONE, see our web site at http://dataone.org.
#
#   Copyright 2009-2016 DataONE
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
"""Test MNStorage.create() and MNRead.get() with revision chains
"""

from __future__ import absolute_import

import StringIO

import pytest
import responses

import d1_common.const
import d1_common.types.dataoneTypes
import d1_common.types.exceptions
import d1_common.util
import d1_common.xml

import gmn.tests.gmn_mock
import gmn.tests.gmn_test_case
import gmn.tests.gmn_test_client


class TestCreateAndGetRevision(gmn.tests.gmn_test_case.GMNTestCase):
  @responses.activate
  def test_1010(self):
    """MNStorage.create(): Creating a standalone object with new PID and SID
    does not raise exception
    """

    def test(client):
      self.create_obj(client)

    test(self.client_v1)
    test(self.client_v2)

  @responses.activate
  def test_1020(self):
    """MNStorage.create(): Reusing existing SID as PID when creating
    a standalone object raises IdentifierNotUnique
    """

    def test(client):
      pid, sid, sciobj_str, sysmeta_pyxb = self.create_obj(client, sid=True)
      with pytest.raises(d1_common.types.exceptions.IdentifierNotUnique):
        self.create_obj(client, sid)

    # Only applicable to v2.
    test(self.client_v2)

  @responses.activate
  def test_1030(self):
    """MNStorage.create(): Attempting to reuse existing SID as SID when creating
    a standalone object raises IdentifierNotUnique
    """

    def test(client):
      pid, sid, sciobj_str, sysmeta_pyxb = self.create_obj(client, sid=True)
      with pytest.raises(d1_common.types.exceptions.IdentifierNotUnique):
        self.create_obj(client, sid=sid)

    # Only applicable to v2.
    test(self.client_v2)

  @responses.activate
  def test_1040(self):
    """MNStorage.get(): v2.get() retrieves object created with v1.create()"""
    pid, sid, send_sciobj_str, send_sysmeta_pyxb = self.create_obj(
      self.client_v1
    )
    recv_sciobj_str, recv_sysmeta_pyxb = self.get_obj(self.client_v2, pid)
    assert send_sciobj_str == recv_sciobj_str
    assert recv_sysmeta_pyxb.identifier.value() == pid
    assert recv_sysmeta_pyxb.seriesId is None

  @responses.activate
  def test_1050(self):
    """MNStorage.get(): v1.get() retrieves object created with v2.create()"""
    pid, sid, send_sciobj_str, send_sysmeta_pyxb = self.create_obj(
      self.client_v2
    )
    recv_sciobj_str, recv_sysmeta_pyxb = self.get_obj(self.client_v1, pid)
    assert send_sciobj_str == recv_sciobj_str
    assert recv_sysmeta_pyxb.identifier.value() == pid
    assert not hasattr(recv_sysmeta_pyxb, 'seriesId')

  @responses.activate
  def test_1060(self):
    """MNStorage.get(): Attempting to pass a SID to v1.get() raises NotFound
    even though the SID exists (by design, we don't resolve SIDs for v1)
    """
    pid, sid, sciobj_str, sysmeta_pyxb = self.create_obj(
      self.client_v2, sid=True
    )
    with pytest.raises(d1_common.types.exceptions.NotFound):
      sciobj_str, sysmeta_pyxb = self.get_obj(self.client_v1, sid)

  @responses.activate
  def test_1070(self):
    """MNStorage.create(): Creating standalone object with
    sysmeta.obsoletes pointing to known object raises InvalidSystemMetadata
    """

    def test(client):
      old_pid, old_sid, old_sciobj_str, old_sysmeta_pyxb = (
        self.create_obj(client)
      )
      new_pid, sid, new_sciobj_str, new_sysmeta_pyxb = (
        self.generate_sciobj_with_defaults(client)
      )
      new_sysmeta_pyxb.obsoletes = old_pid

      with pytest.raises(d1_common.types.exceptions.InvalidSystemMetadata):
        client.create(
          new_pid, StringIO.StringIO(new_sciobj_str), new_sysmeta_pyxb
        )

    with gmn.tests.gmn_mock.disable_auth():
      test(self.client_v1)
      test(self.client_v2)

  @responses.activate
  def test_1080(self):
    """MNStorage.create(): Creating standalone object with
    sysmeta.obsoletes pointing to unknown object raises InvalidSystemMetadata
    """

    def test(client):
      new_pid, sid, sciobj_str, sysmeta_pyxb = (
        self.generate_sciobj_with_defaults(client)
      )
      sysmeta_pyxb.obsoletes = self.random_pid()

      with pytest.raises(d1_common.types.exceptions.InvalidSystemMetadata):
        client.create(new_pid, StringIO.StringIO(sciobj_str), sysmeta_pyxb)

    with gmn.tests.gmn_mock.disable_auth():
      test(self.client_v1)
      test(self.client_v2)

  @responses.activate
  def test_1090(self):
    """MNStorage.create(): Creating standalone object with
    sysmeta_pyxb.obsoletedBy pointing to known object raises InvalidSystemMetadata
    """

    def test(client):
      old_pid, old_sid, old_sciobj_str, old_sysmeta_pyxb = (
        self.create_obj(client)
      )
      new_pid, sid, new_sciobj_str, new_sysmeta_pyxb = (
        self.generate_sciobj_with_defaults(client)
      )
      new_sysmeta_pyxb.obsoletedBy = old_pid

      with pytest.raises(d1_common.types.exceptions.InvalidSystemMetadata):
        client.create(
          new_pid, StringIO.StringIO(new_sciobj_str), new_sysmeta_pyxb
        )

    with gmn.tests.gmn_mock.disable_auth():
      test(self.client_v1)
      test(self.client_v2)

  @responses.activate
  def test_1100(self):
    """MNStorage.create(): Creating standalone object with
    sysmeta_pyxb.obsoletedBy pointing to unknown object raises InvalidSystemMetadata
    """

    def test(client):
      new_pid, sid, sciobj_str, sysmeta_pyxb = (
        self.generate_sciobj_with_defaults(client)
      )
      sysmeta_pyxb.obsoletes = self.random_pid()

      with pytest.raises(d1_common.types.exceptions.InvalidSystemMetadata):
        client.create(new_pid, StringIO.StringIO(sciobj_str), sysmeta_pyxb)

    with gmn.tests.gmn_mock.disable_auth():
      test(self.client_v1)
      test(self.client_v2)
