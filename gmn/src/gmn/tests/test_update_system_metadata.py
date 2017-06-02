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
"""Test MNStorage.updateSystemMetadata() and access policy enforcement

MNStorage.updateSystemMetadata() is a convenient place to check GMN enforcement
of access policies, though it's not the only channel through which policy
changes can arrive
"""

from __future__ import absolute_import

import time
import datetime

import responses

import d1_common.xml
import d1_common.util
import d1_common.const
import d1_common.system_metadata
import d1_common.types.exceptions
import d1_common.types.dataoneTypes

import gmn.tests.gmn_mock
import gmn.tests.gmn_test_case
import gmn.tests.gmn_test_client


# @gmn.tests.gmn_mock.trusted_subjects_decorator(['trusted_subj'])
class TestUpdateSystemMetadata(gmn.tests.gmn_test_case.D1TestCase):
  # MNStorage.updateSystemMetadata(). Method was added in v2.

  @gmn.tests.gmn_mock.disable_auth_decorator
  def _update_access_policy(self, pid, permission_list):
    access_policy_pyxb = self.generate_access_policy(self.v2, permission_list)
    sciobj_str, sysmeta_pyxb = self.get_obj(self.client_v2, pid)
    sysmeta_pyxb.accessPolicy = access_policy_pyxb
    # self.dump_pyxb(sysmeta_pyxb)
    self.client_v2.updateSystemMetadata(pid, sysmeta_pyxb)

  def _get(self, pid, active_subj_list):
    with gmn.tests.gmn_mock.set_auth_context(
        active_subj_list, ['trusted_subj']
    ):
      self.client_v2.get(pid)

  @responses.activate
  def test_0110(self):
    """updateSystemMetadata(): Sequence of access policy changes"""

    # Create object with default access policy:
    # 'subj1': 'read'
    # 'subj2', 'subj3', 'subj4': 'read', 'write'
    # 'subj5', 'subj6', 'subj7', 'subj8': 'read', 'changePermission'
    # 'subj9', 'subj10', 'subj11', 'subj12': 'changePermission'
    pid, sid, sciobj_str, sysmeta_pyxb = self.create_obj(
      self.client_v2, self.v2, sid=True
    )

    # Check read access

    # Single unknown subject raises NotAuthorized
    with self.assertRaises(d1_common.types.exceptions.NotAuthorized):
      self._get(pid, ['unk_subj'])
    # Multiple unknown subject raise NotAuthorized
    with self.assertRaises(d1_common.types.exceptions.NotAuthorized):
      self._get(pid, ['unk_subj', 'subj2_', '_subj33', 'subj12!'])
    # A single known subject allows access
    self._get(pid, ['subj12'])
    # A single known subject allows access even if there are also unknown
    # subjects
    self._get(pid, ['unk_subj', 'subj2_', '_subj33', 'subj12!', 'subj1'])

    # Update access policy
    # Remove permissions for subj1-4
    # Lower permissions for subj9-12 from changePermission to write
    new_permission_list = [
      (['subj5', 'subj6', 'subj7', 'subj8'], ['read', 'changePermission']),
      (['subj9', 'subj10', 'subj11'], ['write']),
    ]
    self._update_access_policy(pid, new_permission_list)

    # Access now denied for single previously allowed subjects.
    for subject_str in [['subj1']]:
      with self.assertRaises(d1_common.types.exceptions.NotAuthorized):
        self._get(pid, subject_str)

    # Access now denied for multiple previously allowed subjects that had read,
    # write and changePermission
    for subject_str in [['subj1', 'subj2'], ['subj3', 'subj4', 'subj12']]:
      with self.assertRaises(d1_common.types.exceptions.NotAuthorized):
        self._get(pid, subject_str)

    # Access still allowed for subject that retained access but switched level
    for subject_str in [['subj5', 'subj6', 'subj7', 'subj8'],
                        ['subj9', 'subj10'], ['subj11']]:
      self._get(pid, subject_str)

    # isAuthorized() raises NotAuthorized for unknown subject
    with gmn.tests.gmn_mock.set_auth_context(['unk_subj'], ['trusted_subj']):
      with self.assertRaises(d1_common.types.exceptions.NotAuthorized):
        self.client_v2.isAuthorized(pid, 'read')
      with self.assertRaises(d1_common.types.exceptions.NotAuthorized):
        self.client_v2.isAuthorized(pid, 'write')
      with self.assertRaises(d1_common.types.exceptions.NotAuthorized):
        self.client_v2.isAuthorized(pid, 'changePermission')

    # isAuthorized() raises InvalidRequest for bogus permission
      with self.assertRaises(d1_common.types.exceptions.InvalidRequest):
        self.client_v2.isAuthorized(pid, '_bogus_permission_')

    # isAuthorized() raises NotAuthorized for known subject with inadequate
    # permission level
    with gmn.tests.gmn_mock.set_auth_context(['subj9'], ['trusted_subj']):
      with self.assertRaises(d1_common.types.exceptions.NotAuthorized):
        self.client_v2.isAuthorized(pid, 'changePermission')

    # isAuthorized() returns True for known subject with adequate permission
    # level
    with gmn.tests.gmn_mock.set_auth_context(['subj5'], ['trusted_subj']):
      self.assertTrue(self.client_v2.isAuthorized(pid, 'changePermission'))
      self.assertTrue(self.client_v2.isAuthorized(pid, 'write'))

  @responses.activate
  @gmn.tests.gmn_mock.disable_auth_decorator
  def test_3060(self):
    """MNStorage.updateSystemMetadata(): Update blocked due to modified
    timestamp mismatch
    """

    def test(client, binding):
      pid, sid, sciobj_str, sysmeta_pyxb = self.create_obj(
        client, binding, sid=True
      )
      # Get sysmeta
      sciobj_str, sysmeta_pyxb = self.get_obj(client, pid)
      # Change something
      sysmeta_pyxb.dateSysMetadataModified = datetime.datetime.now(
      ) + datetime.timedelta(1, 2)
      sysmeta_pyxb.submitter = 'new_submitter'
      # Update
      with self.assertRaises(d1_common.types.exceptions.InvalidRequest):
        client.updateSystemMetadata(pid, sysmeta_pyxb)

    # Not relevant for v1
    test(self.client_v2, self.v2)

  @responses.activate
  @gmn.tests.gmn_mock.disable_auth_decorator
  def test_3061(self):
    """MNStorage.updateSystemMetadata(): Successful update"""

    def test(client, binding):
      pid, sid, sciobj_str, sysmeta_pyxb = self.create_obj(
        client, binding, sid=True
      )
      # Get sysmeta
      sciobj_str, sysmeta_pyxb = self.get_obj(client, pid)
      # Update rightsHolder
      self.assertEqual(sysmeta_pyxb.rightsHolder.value(), 'rights_holder_subj')
      sysmeta_pyxb.rightsHolder = 'newRightsHolder'
      self.assertTrue(client.updateSystemMetadata(pid, sysmeta_pyxb))
      # Verify
      sciobj_str, new_sysmeta_pyxb = self.get_obj(client, pid)
      self.assertEqual(new_sysmeta_pyxb.rightsHolder.value(), 'newRightsHolder')

    # Not relevant for v1
    test(self.client_v2, self.v2)

  @responses.activate
  @gmn.tests.gmn_mock.disable_auth_decorator
  @gmn.tests.gmn_mock.no_client_trust_decorator
  def test_3063(self):
    """MNStorage.updateSystemMetadata()
    - Does not change dateUploaded
    - Does update dateSysMetadataModified
    """

    def test(client, binding):
      # Create base object with SID
      pid, sid, sciobj_str, sysmeta_pyxb = self.create_obj(
        client, binding, sid=True
      )
      # Get sysmeta
      old_sciobj_str, old_sysmeta_pyxb = self.get_obj(client, pid)
      self.dump_pyxb(old_sysmeta_pyxb)
      old_sysmeta_pyxb.formatId = 'new_format_id'
      # Ensure update gets a new dateSysMetadataModified
      time.sleep(.2)
      self.assertTrue(client.updateSystemMetadata(pid, old_sysmeta_pyxb))
      new_sciobj_str, new_sysmeta_pyxb = self.get_obj(client, pid)
      # self.dump_pyxb(old_sysmeta_pyxb)
      self.dump_pyxb(new_sysmeta_pyxb)
      self.assertEqual(old_sysmeta_pyxb.formatId, new_sysmeta_pyxb.formatId)
      self.assertEqual(
        old_sysmeta_pyxb.dateUploaded, new_sysmeta_pyxb.dateUploaded
      )
      self.assertGreater(
        new_sysmeta_pyxb.dateSysMetadataModified,
        old_sysmeta_pyxb.dateSysMetadataModified
      )

    # Not relevant for v1
    test(self.client_v2, self.v2)

  @responses.activate
  @gmn.tests.gmn_mock.disable_auth_decorator
  def test_3064(self):
    """MNStorage.updateSystemMetadata() and MNStorage.getSystemMetadata()
    A series of updates and downloads using the same client and network
    connection correctly frees up the connection
    """

    def test(client, binding):
      # Create base object with SID
      pid, sid, sciobj_str, sysmeta_pyxb = self.create_obj(
        client, binding, sid=True
      )
      for i in range(10):
        random_subject_str = self.random_tag('subject')
        sysmeta_pyxb = client.getSystemMetadata(pid)
        sysmeta_pyxb.rightsHolder = random_subject_str
        self.assertTrue(client.updateSystemMetadata(pid, sysmeta_pyxb))
        new_sysmeta_pyxb = client.getSystemMetadata(pid)
        self.assertEqual(
          new_sysmeta_pyxb.rightsHolder.value(), random_subject_str
        )

    # Not relevant for v1
    test(self.client_v2, self.v2)

  @responses.activate
  @gmn.tests.gmn_mock.disable_auth_decorator
  def test_3070(self):
    """MNStorage.updateSystemMetadata()
    Using updateSystemMetadata() to add new preferred and blocked nodes
    """

    def test(client, binding):
      # Create base object with SID
      base_pid, sid, sciobj_str, ver1_sysmeta_pyxb = self.create_obj(
        client, binding, sid=True
      )
      ver2_sciobj_str, ver2_sysmeta_pyxb = self.get_obj(client, base_pid)
      # Add a new preferred node
      ver2_sysmeta_pyxb.replicationPolicy.preferredMemberNode.append('new_node')
      client.updateSystemMetadata(base_pid, ver2_sysmeta_pyxb)
      ver3_sciobj_str, ver3_sysmeta_pyxb = self.get_obj(client, base_pid)
      # Check that the count of preferred nodes increased by one
      self.assertEqual(
        len(ver1_sysmeta_pyxb.replicationPolicy.preferredMemberNode) + 1,
        len(ver3_sysmeta_pyxb.replicationPolicy.preferredMemberNode),
      )
      # Second round of changes
      ver3_sysmeta_pyxb.replicationPolicy.preferredMemberNode.append(
        'preferred_1'
      )
      ver3_sysmeta_pyxb.replicationPolicy.preferredMemberNode.append(
        'preferred_2'
      )
      ver3_sysmeta_pyxb.replicationPolicy.blockedMemberNode.append('blocked_1')
      ver3_sysmeta_pyxb.replicationPolicy.blockedMemberNode.append('blocked_2')
      client.updateSystemMetadata(base_pid, ver3_sysmeta_pyxb)
      # Check
      ver4_sciobj_str, ver4_sysmeta_pyxb = self.get_obj(client, base_pid)
      self.assertTrue(
        d1_common.system_metadata.
        is_equivalent_pyxb(ver3_sysmeta_pyxb, ver4_sysmeta_pyxb)
      )

    # Not relevant for v1
    test(self.client_v2, self.v2)