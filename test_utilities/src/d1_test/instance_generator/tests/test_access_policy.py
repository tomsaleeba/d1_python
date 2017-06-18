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

from __future__ import absolute_import

import d1_test.d1_test_case
import d1_test.instance_generator.access_policy as access_policy

#===============================================================================


@d1_test.d1_test_case.reproducible_random_decorator('TestAccessPolicy')
class TestAccessPolicy(d1_test.d1_test_case.D1TestCase):
  def test_0010(self):
    """select_random_set_of_permissions()"""
    permissions = access_policy.random_set_of_permissions()
    self.assert_equals_sample(
      permissions, 'inst_gen__access_policy__select_random_set_of_permissions'
    )

  def test_0020(self):
    """permissions_to_tag_string()"""
    permissions = access_policy.random_set_of_permissions()
    s = access_policy.permissions_to_tag_string(permissions)
    self.assert_equals_sample(
      s, 'inst_gen__access_policy__permissions_to_tag_string'
    )

  def test_0030(self):
    """random_subject_with_permission_labels()"""
    permissions = access_policy.random_set_of_permissions()
    s = access_policy.random_subject_with_permission_labels(permissions)
    self.assert_equals_sample(
      s, 'inst_gen__access_policy__random_subject_with_permission_labels'
    )

  def test_0040(self):
    """random_subjects_with_permission_labels()"""
    permissions = access_policy.random_set_of_permissions()
    subjects = access_policy.random_subjects_with_permission_labels(permissions)
    self.assert_equals_sample(
      subjects,
      'inst_gen__access_policy__random_subjects_with_permission_labels'
    )

  def test_0050(self):
    """generate()"""
    access_policy_pyxb = access_policy.generate()
    self.assert_equals_sample(
      access_policy_pyxb, 'inst_gen__access_policy__generate'
    )

  def test_0060(self):
    """random_subject_list()"""
    subject_list = access_policy.random_subject_list()
    self.assert_equals_sample(
      subject_list, 'inst_gen__access_policy__random_subject_list'
    )
