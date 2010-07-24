''' 
Module d1pythonitk.logrecorditerator
====================================
 
:Created: 20100724
:Author: vieglais

'''

import logging


class LogRecordIterator(object):
  '''Implements an iterator that iterates over the entire set of LogRecords 
  for a DataONE node.  Data is retrieved from the target only when required.
  '''

  def __init__(self, client, start=0, startTime=None):
    '''Initializes the iterator.
    
     TODO: Extend this with date range and other restrictions

    :param DataOneClient client: The client instance for retrieving stuff.
    :param integer start: The starting index value
    '''
    self._logRecords = None
    self._czero = 0
    self._client = client
    self._pagesize = 500
    self.startTime = startTime
    self._loadMore(start=start)

  def __iter__(self):
    return self

  def next(self):
    '''Implements the next() method for the iterator.  Returns the next 
    logEntry instance.
    '''
    if self._citem >= len(self._logRecords.logEntry):
      try:
        self._loadMore(start=self._czero + len(self._logRecords.logEntry))
      except Exception, e:
        logging.exception(e)
        raise StopIteration
      if len(self._logRecords.logEntry) < 1:
        raise StopIteration
    res = self._logRecords.logEntry[self._citem]
    self._citem += 1
    return res

  def _loadMore(self, start=0):
    '''Retrieves the next page of results
    '''
    self._czero = start
    self._citem = 0
    self._logRecords = self._client.getLogRecords(
      start=start, count=self._pagesize,
      startTime=self.startTime
    )

#===============================================================================
if __name__ == "__main__":
  '''A simple demonstration of the iterator.  Walks over the list of log 
  entries available from a given node.
  '''
  import d1pythonitk.client
  import sys
  logging.basicConfig(level=logging.INFO)
  target = "http://dev-dryad-mn.dataone.org/mn"
  #target = "http://129.24.0.15/mn"
  #target = "http://knb-mn.ecoinformatics.org/knb"
  if len(sys.argv) > 1:
    target = sys.argv[1]
  client = d1pythonitk.client.DataOneClient(target=target)
  rl = LogRecordIterator(client)
  counter = 0
  for e in rl:
    counter += 1
    print "==== #%d ====" % counter
    print "Event      = %s" % e.event
    print "Timestamp  = %s" % e.dateLogged.isoformat()
    print "IP Addres  = %s" % e.ipAddress
    print "Identifier = %s" % e.identifier
    print "User agent = %s" % e.userAgent
    print "Principal  = %s" % e.principal
