from uwosh.librarycache.core import CacheCore

import base64
import gdata.calendar.service
import datetime
import time 
# credit: http://home.blarg.net/~steveha/pyfeed.html
from feed.date import rfc3339 

import logging
logger = logging.getLogger("WebServices")


class HoursCacheEmpty(CacheCore):
    """ Easy way to purge """
    def build(self):
        return []
    
    
class HoursCache(CacheCore):

    SERVICE_USERNAME = 'polkservices@gmail.com'
    SERVICE_PASSWORD = base64.decodestring('Ym9va3MycGVvcGxl')
    DATE_STORAGE_FORMAT = '%Y-%m-%d %H:%M'
    DATE_UID_STORAGE_FORMAT = '%Y%m%d'
    MAX_CONNECTION_ERRORS_ALLOWED = 3
    connection_counts = 0
    
    def build(self):
        self.setup()
        return self.rotate_cache_through_next_X_days(14, datetime.datetime.today())

    def setup(self):
        self.service = gdata.calendar.service.CalendarService()
        self.service.email = self.SERVICE_USERNAME
        self.service.password = self.SERVICE_PASSWORD
        self.service.source = 'Polk-HoursLookup-1.0'
        self.service.ProgrammaticLogin()

    def rotate_cache_through_next_X_days(self, amount, today):
        data = self.context.getCache()
        if not data:
            data = []
        
        yest = today + datetime.timedelta(days=-1)
        yest = int(yest.strftime(self.DATE_UID_STORAGE_FORMAT))
        data = filter(lambda x: x['sid'] >= yest, data)

        for i in range(-1,amount+1):
            date = today + datetime.timedelta(days=i)
            #date = datetime.datetime(2013, 10, 1, 0, 0, 0) + datetime.timedelta(days=i)
            
            if self.check_for_missing(data,date):
                #print "GET NEW DAY: " + date.strftime(self.DATE_UID_STORAGE_FORMAT)
                data.append(self.query_date(date))
            elif self.check_open(data,date):
                #print "Re-check Closed Date: " + date.strftime(self.DATE_UID_STORAGE_FORMAT)
                data = filter(lambda x: x['sid'] != int(date.strftime(self.DATE_UID_STORAGE_FORMAT)), data) #remove old date
                data.append(self.query_date(date))
                
        return sorted(data, key=lambda x: x['sid'])

    def check_open(self,data,date):
        for d in data:
            if d['sid'] == int(date.strftime(self.DATE_UID_STORAGE_FORMAT)) and d['is_open'] == 0:
                return True
        return False
    
    def check_for_missing(self,data,date):
        missing = True
        for d in data:
            if d['sid'] == int(date.strftime(self.DATE_UID_STORAGE_FORMAT)):
                missing = False
        return missing
    
    def query_date(self, date):
        self.connection_counts = 0
        MAIN_CALENDAR = 'jddhd44evhje61lk98san123u8@group.calendar.google.com'
        query = gdata.calendar.service.CalendarEventQuery(MAIN_CALENDAR, 'private', 'full')

        date = date.replace(hour=3, minute=0, second=0, microsecond=0)
        query.start_min = self._to_rfc3339(date)
        query.start_max = self._to_rfc3339(date + datetime.timedelta(days=1))
        
        feed = self.calendar_query(query)
        
        
        try:
            start = self._from_rfc3339(feed.entry[0].when[0].start_time)
            end = self._from_rfc3339(feed.entry[0].when[0].end_time)
            is_open = 1
            title = self._none_to_empty_str(feed.entry[0].title.text)
            content = self._none_to_empty_str(feed.entry[0].content.text)
        except:
            start = date
            end = date
            is_open = 0
            title = 'No title'
            content = 'No content'
        
        return {'sid' : int(start.strftime(self.DATE_UID_STORAGE_FORMAT)),
                'start' : start.strftime(self.DATE_STORAGE_FORMAT),
                'end' : end.strftime(self.DATE_STORAGE_FORMAT),
                'title' : title,
                'content' : content,
                'is_open' : is_open,
                }
    
    def _none_to_empty_str(self, o):
        if not o:
            return ''
        return o
    
    def calendar_query(self, query):
        """ Will Recheck if network failure occurs """
        
        try:
            self.connection_counts+=1
            return self.service.CalendarQuery(query)
        except Exception as e:
            if self.connection_counts < self.MAX_CONNECTION_ERRORS_ALLOWED:
                logger.warn("UNABLE TO RETREIVE HOURS, RETRYING: " + str(e))
                time.sleep(5)
                return self.calendar_query(query)
            logger.error("TERMINATING... COULD NOT RETREIVE HOURS: " + str(e))
            return None

    def _to_rfc3339(self, dt):
        tf = time.mktime(dt.timetuple())
        return rfc3339.timestamp_from_tf(tf)
    
    def _from_rfc3339(self, rfc_time):
        tf = rfc3339.tf_from_timestamp(rfc_time)
        return datetime.datetime.fromtimestamp(tf)


class FakeHoursCache(HoursCache):
    """ This purely used for local testing and manipulation of live times """

    def build(self):
        self.setup()
        tmp = []
        tmp = self.rotate_cache_through_next_X_days(5, datetime.datetime(2013,11,29,4,15,0))
        print '['
        for t in tmp:
            print str(t) + ' ,'
        print ']'
        print ''
        
        #return tmp
        #return []
        return [
                {'start': '2013-12-02 03:00', 'end': '2013-12-02 03:00', 'is_open': 0, 'sid': 20131202} ,
                {'start': '2013-12-03 07:00', 'end': '2013-12-03 16:30', 'is_open': 1, 'sid': 20131203} ,
                {'start': '2013-12-04 03:00', 'end': '2013-12-04 03:00', 'is_open': 0, 'sid': 20131204} ,
                {'start': '2013-12-05 16:00', 'end': '2013-12-05 01:00', 'is_open': 1, 'sid': 20131205} ,
                {'start': '2013-12-06 07:00', 'end': '2013-12-06 01:00', 'is_open': 1, 'sid': 20131206} ,
                {'start': '2013-12-07 07:00', 'end': '2013-12-07 01:00', 'is_open': 1, 'sid': 20131207} ,
                {'start': '2013-12-08 07:00', 'end': '2013-12-08 01:00', 'is_open': 1, 'sid': 20131208} ,
                ]









