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
"""
Module d1_instance_generator.tests.test_systemmetadata
======================================================

:Synopsis: Unit tests for system metadata generator.
:Created: 2011-12-05
:Author: DataONE (Dahl)
"""

# Stdlib
import unittest

# App
import d1_test.instance_generator.checksum as checksum

#===============================================================================


class TestChecksum(unittest.TestCase):
  def setUp(self):
    pass

  def test_010(self):
    """random_checksum_algorithm(): Returns a valid checksum algorithm"""
    algorithm_str = checksum.random_checksum_algorithm()
    self.assertIn(algorithm_str, ('MD5', 'SHA-1'))
