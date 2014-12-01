from uwosh.library.ws.util.hours_lookup import HoursLookup as HoursLookupBase, Hours
from Products.CMFCore.utils import getToolByName

from persistent import Persistent
from persistent.dict import PersistentDict
import ZODB 
from ZODB import DB
from ZODB.FileStorage import FileStorage
import transaction
import os

from DateTime import DateTime
from time import time as fromtime, mktime
import datetime
import time

import logging
logger =logging.getLogger('HOURSLOOKUP')


class HoursLookup(HoursLookupBase):
    """
    Extends original HoursLookup.  This one hashes calls to google and remembers them.
    Reason is there is no need to contact google 20 times to find out today's hours.  This
    calls them once and hashes it.
    """
    def __init__(self,context):
        self.context = context
        #path = getToolByName(self.context,'portal_properties').zodb_properties.getProperty('zodb_cache_file')
        HoursLookupBase.__init__(self)
        #self.hashtable = HoursHandler(path)
    
    def getMainHoursForToday(self):
        today = datetime.datetime.now()
        #if self.hashtable.isHashed(today):
        #    #logger.info("GETTING CACHED HOURS from cache.fs")
        #    return self.hashtable.getHours(today)
        #else:
            #logger.info("GETTING FRESH HOURS and storing in cache.fs")
        hours = HoursLookupBase.getMainHoursForToday(self)
        if not hours.is_open:
            hours = self.isClosed(today)
            #self.hashtable.add(hours)
        return hours

    def getMainHoursForDate(self, date):
        #if self.hashtable.isHashed(date):
            #logger.info("GETTING CACHED HOURS from cache.fs")
        #    hours = self.hashtable.getHours(date)
        #    return hours
        #else:
            #logger.info("GETTING FRESH HOURS and storing in cache.fs")
            hours = HoursLookupBase.getMainHoursForDate(self, date)
            if not hours.is_open:
                hours = self.isClosed(date)
        #    self.hashtable.add(hours)
            return hours
        
    def isClosed(self,date):
        h = Hours(0)
        start = date + datetime.timedelta(minutes=1)
        end = date + datetime.timedelta(minutes=-1)
        setattr(h,'start',start)
        setattr(h,'end',end)
        return h
        
        
class HoursHandler():
    """
    Sets up a cache.fs ZODB filestorage for the cache hash.  It will add to the hash, get
    from the hash, recreate the hash.
    
    This is experimental!!!
    
    """
    
    def __init__(self,path=None):
        self.path = path
        try:
            self.map = {}
            self.setup()
            self.load()
            self.refresh()
        except Exception as e:
            logger.error(   "Error INIT HoursHash: " + str(e) )
            
    def refresh(self):
        created_date = datetime.datetime.fromtimestamp(self.created)
        created_date = created_date + datetime.timedelta(days=3)
        now = datetime.datetime.now()
        #print str(now) + " --- "  + str(created_date)
        if now >= created_date:
            self.reset()
            self.load()
    
    def add(self,hours):
        try:
            key = self._getkey(hours.start)
            self.map[key] = self._createHoursStruct(hours.start,hours.end,hours.is_open)
            self.save()
        except Exception as e:
            print "error"
        
    def isHashed(self,start):
        try:
            self.map[self._getkey(start)]
            return True
        except Exception:
            return False
    
    def getHours(self,start): 
        try:
            diction = self._loadHoursStruct(self.map[self._getkey(start)])
            hours = Hours(diction['is_open'])
            setattr(hours,'start',diction['start'])
            setattr(hours,'end',diction['end'])
            return hours
        except Exception as e:
            hours = Hours(0)
            setattr(hours,'start',start)
            setattr(hours,'end',start)
            return hours
        
    def _getkey(self,dt):
        return str(dt.year) + str(dt.month) + str(dt.day)
    
    def load(self):
        db = ZODBConnector(path=self.path)
        try:
            hash = db.getData('google_hash')
            created = db.getData('google_hash_created')
            if hash != None:
                self.map = hash
            else:
                self.map = {}
                
            if created != None:
                self.created = created
            else:
                self.created = 123
            
        except Exception as e:
            logger.error(   "Could not load: " + str(e) )
        finally:
            db.close()
            
    def save(self):
        db = ZODBConnector(path=self.path)
        try:
            #import pdb; pdb.set_trace()
            new_dict = dict(self.map)
            db.setData('google_hash',new_dict)
        except Exception as e:
            logger.error(  "ERROR IN SAVE: " + str(e) )
        finally:
            db.close()

    def setup(self,reset=False):
        db = ZODBConnector(path=self.path)
        try:
            hash = db.getData('google_hash')
            if hash == None or reset == True:
                diction = {}
                db.setData('google_hash', diction)
                created = mktime(datetime.datetime.now().timetuple())
                db.setData('google_hash_created',created)
        except Exception as e:
            logger.error(  "ERROR IN SETUP: " + str(e) )
        finally:
            db.close()
    
    def reset(self):
        try:
            os.remove(self.path)
            os.remove(self.path + '.lock')
            os.remove(self.path + '.tmp')
            os.remove(self.path + '.index')
        except Exception as e:
            logger.error(  "ERROR IN DELETING: " + str(e) )
        
        db = ZODBConnector(path=self.path)
        try:
            diction = {}
            db.setData('google_hash', diction)
            created = mktime(datetime.datetime.now().timetuple())
            db.setData('google_hash_created',created)
        except Exception as e:
            logger.error(  "ERROR IN RESET: " + str(e) )
        finally:
            db.close()
            
    def _loadHoursStruct(self,tuples):
        return {'start':datetime.datetime.fromtimestamp(int(tuples[0])),
                'end':datetime.datetime.fromtimestamp(int(tuples[1])),
                'is_open':int(tuples[2])
                }
    
    def _createHoursStruct(self,start,end,is_open):
        return self._create([mktime(start.timetuple()),mktime(end.timetuple()),is_open])
    
    def _create(self,listing):
        return tuple(listing)


class ZODBConnector(object):
    # from ZODB.FileStorage import FileStorage
    # FileStorage('cache.fs')
    path = '/var/filestorage/cache.fs'
    
    def __init__(self, path=None):
        if path == None:
            path = self.path
            
        try:
            self.storage = FileStorage(path)
            self.db = DB(self.storage)
            self.connection = self.db.open()
            self.root = self.connection.root()
        except Exception as e:
            logger.error(  "ZODB CONNECTOR ERROR: " + str(e) )
        
    def getData(self,name):
        try:
            item = self.root[name]
            transaction.commit()
            return item
        except Exception as e:
            logger.error(  "GETTING DATA DB --- RETURNING NONE!!!! Data: " + str(e))
            return None
    
    def setData(self,name,value):
        try:
            self.root[name] = value
            transaction.commit()
        except Exception as e:
            transaction.abort()
            logger.error( "Set Data Error: " + str(e) )
    
    def close(self):
        try:
            self.connection.close()
            self.db.close()
            self.storage.close()
        except Exception as e:
            logger.error("CLOSING DB ERROR" + str(e))

