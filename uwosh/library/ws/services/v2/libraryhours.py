from zope.interface import Interface,implements
from Products.CMFCore.utils import getToolByName
from plone.memoize import ram

from uwosh.library.ws.external.hours_cache import HoursCache
from uwosh.library.ws.core.webservice import WebServiceBase
from uwosh.library.ws.core.webresponse import WebResponseObject
from uwosh.library.ws.core.interfaces import IRegisteredService
from uwosh.library.ws.util import timeutil

from time import time,mktime
from huTools import structured
import datetime,calendar,simplejson,logging,re

logger = logging.getLogger("WebServices")

"""
NOTE:
 - The WS hours are determined when the CRONJOB is run.
"""
def cache_purge(method, self, modified):
    return (modified, time() // (60 * 10))

class LibraryHoursHandler(WebServiceBase):
    implements(IRegisteredService)

    def setup(self):
        """ Setup before execution """
        WebServiceBase.setup(self)
        self.date = self.request.form.get('date',None)
        
    def execute(self):
        """ Execution """
        if self.date == None and self.use_cache != "0":
            self.setResponse(self.buildObjectLHCache(self.getCache().modified))
        else:
            self.setResponse(self.buildObject())

    @ram.cache(cache_purge)
    def buildObjectLHCache(self,reset):
        return self.buildObject()

    def buildObject(self):
        return LibraryHoursObject(self.context, self.request, self.date)

    def getCache(self):
        caches = getToolByName(self.context,'portal_catalog').searchResults(portal_type='LibraryCache', path={'query':'/sites1/library/hours','depth':1})
        if caches:
            return caches[0]
        return None
    
    
class LibraryHoursObject(WebResponseObject):

    DT_FMT = '%Y-%m-%d %H:%M'

    def __init__(self, context, request, date):
        WebResponseObject.__init__(self,context,request)
        self.times = []
        self.description = "Hours of operation today for polk library"
        self.status = "Load Error"
        self.is_open = 0
        self.offset = timeutil.offsets()
        self.status_link = self.getProp('library_hours_url')
        
        if date:
            dt = datetime.datetime.strptime(date, '%Y-%m-%d')
            cache = HoursCache(context)
            cache.setup()
            hours = cache.query_date(dt)
            self.addTime(open=datetime.datetime.strptime(hours['start'],self.DT_FMT),
                         close=datetime.datetime.strptime(hours['end'],self.DT_FMT),
                         is_open=hours['is_open'],
                         title=hours['title'],
                         content=hours['content'])
        else:
            self.determineHours()
        
    def addTime(self,open,close,is_open,title,content):
        self.times.append({'open':open.strftime("%B %d, %Y - %I:%M %p"),
                          'close':close.strftime("%B %d, %Y - %I:%M %p"),
                          'is_open':str(is_open),
                          'open_loc':timeutil.removeTrailingZero(str(mktime(open.timetuple()))),
                          'open_utc':str(calendar.timegm(open.timetuple())),
                          'close_loc':timeutil.removeTrailingZero(str(mktime(close.timetuple()))),
                          'close_utc':str(calendar.timegm(close.timetuple())),
                          'title':title,
                          'content':content
                          })
        
    def determineHours(self):
        cache = None
        caches = getToolByName(self.context,'portal_catalog').searchResults(portal_type='LibraryCache', path={'query':'/sites1/library/hours','depth':1})
        if caches:
            cache = caches[0].getObject().getCache()
            if cache:
                for hours in cache:
                    self.addTime(open=datetime.datetime.strptime(hours['start'],self.DT_FMT),
                                 close=datetime.datetime.strptime(hours['end'],self.DT_FMT),
                                 is_open=hours['is_open'],
                                 title=hours['title'],
                                 content=hours['content'])
                
                self.times.pop(0) # remove yesterday from list
                open_status = timeutil.determineOpenStatus(cache[0], cache[1]) # yesterday , today
                try:
                    content = cache[1]['content']
                except:
                    content = ''
                    
                if self.getProp('is_msg_override_on'):
                    self.setOverrideStatus()
                elif 'status=' in content:
                    self.setCalendarStatus(content)
                elif open_status['is_open']:
                    self.setOpenStatus(open_status['times'])
                elif not open_status['is_open']:
                    self.setClosedStatus(open_status['times'])

    def getProp(self,prop):
        return getToolByName(self.context,"portal_properties").webservice_properties.getProperty(prop)
        
        
    def setOverrideStatus(self):
        self.status = self.getProp('msg_override')
        self.is_open = 1
        
    def setCalendarStatus(self,content):
        groups = re.search(r'\[([^]]*)\]',content)
        if groups:
            group = groups.group(1)
            if group.startswith('status='):
                status = group.split('=')[1]
        self.status = status
        if not status:
            self.status = self.getProp('msg_override')
        self.is_open = 1
        
    def setClosedStatus(self,hours):
        self.status = self.transform_snippets(self.getProp('msg_closed'),hours)
        self.is_open = 0

    def setOpenStatus(self,hours):
        self.status = self.transform_snippets(self.getProp('msg_open'),hours)
        self.is_open = 1

    def transform_snippets(self,text,hours):
        text=text.replace("{open}", timeutil.removeLeadingZero( datetime.datetime.strptime(hours['start'],self.DT_FMT).strftime("%I:%M%p").lower()))
        text=text.replace("{close}", timeutil.removeLeadingZero( datetime.datetime.strptime(hours['end'],self.DT_FMT).strftime("%I:%M%p").lower()))
        return text

    def toDict(self):
        return {'description': self.description,'cached_at':self.cached_at,'offset':self.offset,
                'current_status_text':self.status, 'library_hours_url':self.status_link, 
                'currently_is_open':self.is_open,'times': self.times }
    
    def toXML(self):
        return structured.dict2xml(self.toDict(),roottag='libraryhours',listnames={'times': 'time'},pretty=True)
    
    def toJSON(self):
        return simplejson.dumps(self.toDict())
        
