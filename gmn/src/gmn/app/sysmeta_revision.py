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
"""Utilities for manipulating revision chains in the database
"""

from __future__ import absolute_import

import gmn.app.auth
import gmn.app.util
import gmn.app.models
import gmn.app.sysmeta_sid
import gmn.app.sysmeta_util


def is_obsoleted(pid):
  return gmn.app.sysmeta_util.get_sci_model(pid).obsoleted_by is not None


def set_revision(pid, obsoletes_pid=None, obsoleted_by_pid=None):
  sciobj_model = gmn.app.sysmeta_util.get_sci_model(pid)
  set_revision_by_model(sciobj_model, obsoletes_pid, obsoleted_by_pid)
  sciobj_model.save()


def set_revision_by_model(sciobj_model, obsoletes_pid, obsoleted_by_pid):
  if obsoletes_pid:
    sciobj_model.obsoletes = gmn.app.models.did(obsoletes_pid)
  if obsoleted_by_pid:
    sciobj_model.obsoleted_by = gmn.app.models.did(obsoleted_by_pid)


def is_in_revision_chain(pid):
  sciobj_model = gmn.app.models.ScienceObject.objects.get(pid__did=pid)
  return bool(sciobj_model.obsoleted_by or sciobj_model.obsoletes)


def cut_from_chain(pid):
  """Remove an object from a revision chain.

  Preconditions:
  - The object with the pid is verified to exist and to be a member of an
  revision chain. E.g., with:

  gmn.app.views.asserts.is_pid(pid)
  gmn.app.views.asserts.is_in_revision_chain(pid)

  - The object can be at any location in the chain, including the head or tail.

  Postconditions:
  - The given object is a standalone object with empty obsoletes, obsoletedBy
  and seriesId fields.
  - The previously adjacent objects in the chain are adjusted to close any gap
  that was created or remove dangling reference at the head or tail.
  - If the object was the last object in the chain and the chain has a SID, the
  SID reference is shifted over to the new last object in the chain.
  """
  sciobj_model = gmn.app.sysmeta_util.get_sci_model(pid)
  if is_head(sciobj_model):
    _cut_head_from_chain(sciobj_model)
  elif is_tail(sciobj_model):
    _cut_tail_from_chain(sciobj_model)
  else:
    _cut_embedded_from_chain(sciobj_model)


def _cut_head_from_chain(sciobj_model):
  new_head_model = gmn.app.sysmeta_util.get_sci_model(
    sciobj_model.obsoletes.did
  )
  new_head_model.obsoleted_by = None
  sciobj_model.obsoletes = None
  sciobj_model.save()
  new_head_model.save()


def _cut_tail_from_chain(sciobj_model):
  new_tail_model = gmn.app.sysmeta_util.get_sci_model(
    sciobj_model.obsoleted_by.did
  )
  new_tail_model.obsoletes = None
  sciobj_model.obsoleted_by = None
  sciobj_model.save()
  new_tail_model.save()


def _cut_embedded_from_chain(sciobj_model):
  prev_model = gmn.app.sysmeta_util.get_sci_model(sciobj_model.obsoletes.did)
  next_model = gmn.app.sysmeta_util.get_sci_model(sciobj_model.obsoleted_by.did)
  prev_model.obsoleted_by = next_model.pid
  next_model.obsoletes = prev_model.pid
  sciobj_model.obsoletes = None
  sciobj_model.obsoleted_by = None
  sciobj_model.save()
  prev_model.save()
  next_model.save()


# def update_revision_chain(pid, obsoletes_pid, obsoleted_by_pid, sid):
#   with sysmeta_file.SysMetaFile(pid) as sysmeta_pyxb:
#     sysmeta_file.update_revision_chain(
#       sysmeta_pyxb, obsoletes_pid, obsoleted_by_pid, sid
#     )
#   sysmeta_db.update_revision_chain(sysmeta_pyxb)

#    if sysmeta.obsoletes is not None:
# chain_pid_list = [pid]
#  sci_obj = mn.models.ScienceObject.objects.get(pid__did=pid)
#  while sci_obj.obsoletes:
#    obsoletes_pid = sysmeta_pyxb.obsoletes.value()
#    chain_pid_list.append(obsoletes_pid)
#    sci_obj = mn.models.ScienceObject.objects.get(pid__did=obsoletes_pid)
#  sci_obj = mn.models.ScienceObject.objects.get(pid__did=pid)
#  while sci_obj.obsoleted_by:
#    obsoleted_by_pid = sysmeta_pyxb.obsoleted_by.value()
#    chain_pid_list.append(obsoleted_by_pid)
#    sci_obj = mn.models.ScienceObject.objects.get(pid__did=obsoleted_by_pid)
#  return chain_pid_list


def is_head(sciobj_model):
  return sciobj_model.obsoletes and not sciobj_model.obsoleted_by


def is_tail(sciobj_model):
  return sciobj_model.obsoleted_by and not sciobj_model.obsoletes


def get_pids_in_revision_chain(pid):
  """Given the PID of any object in a chain, return a list of all PIDs in the
  chain. The returned list is in the same order as the chain. The initial PID is
  typically obtained by resolving a SID. If the given PID is not in a chain, a
  list containing the single object is returned.
  """
  sci_model = gmn.app.sysmeta_util.get_sci_model(pid)
  while sci_model.obsoletes:
    sci_model = gmn.app.sysmeta_util.get_sci_model(sci_model.obsoletes.pid.did)
  chain_pid_list = [sci_model.pid.did]
  while sci_model.obsoleted_by:
    sci_model = gmn.app.sysmeta_util.get_sci_model(
      sci_model.obsoleted_by.pid.did
    )
    chain_pid_list.append(sci_model.pid.did)
  return chain_pid_list


def is_sid_in_revision_chain(sid, pid):
  """Determine if {sid} resolves to an object in the revision chain to which
  {pid} belongs.

  Preconditions:
  - {sid} is verified to exist. E.g., with gmn.app.views.asserts.is_sid().
  """
  chain_pid_list = get_pids_in_revision_chain(pid)
  resolved_pid = gmn.app.sysmeta_sid.resolve_sid(sid)
  return resolved_pid in chain_pid_list


def get_sid_by_pid(pid):
  """Given the {pid} of the object in a chain, return the SID for the chain.
  Return None if there is no SID for the chain.

  Preconditions:
  - {pid} is verified to exist. E.g., with gmn.app.views.asserts.is_pid().
  """
  chain_pid_list = get_pids_in_revision_chain(pid)
  for chain_pid in chain_pid_list:
    try:
      return gmn.app.models.SeriesIdToScienceObject.objects.get(
        sciobj__pid__did=chain_pid
      ).sid.did
    except gmn.app.models.SeriesIdToScienceObject.DoesNotExist:
      pass