from zope.interface import Interface,implements
from Products.CMFCore.utils import getToolByName
from plone.memoize import ram

from uwosh.library.ws.external.hours_cache import HoursCache
from uwosh.library.ws.core.webservice import WebServiceBase
from uwosh.library.ws.core.webresponse import WebResponseObject
from uwosh.library.ws.core.interfaces import IRegisteredService

from xml.dom import minidom
from DateTime import DateTime
from time import time
import datetime, simplejson, logging

logger = logging.getLogger("WebServices")


class LibraryHours(WebServiceBase):
    implements(IRegisteredService)

    def setup(self):
        WebServiceBase.setup(self)
        self.date = self.request.form.get('date',None)
    
    def execute(self):
        if self.date == None and self.use_cache != "0":
            self.setResponse(self.buildObjectLHCache())
        else:
            self.setResponse(self.buildObject())
        
    @ram.cache(lambda *args: time() // (60 * 10))
    def buildObjectLHCache(self):
        return self.buildObject()

    def buildObject(self):
        LHO = LibraryHoursObject(self.context,self.request)
        
        if self.date:
            dt = datetime.datetime.strptime(self.date, '%Y-%m-%d')
            cache = HoursCache(self.context)
            cache.setup()
            hours = cache.query_date(dt)
            open=datetime.datetime.strptime(hours['start'],'%Y-%m-%d %H:%M')
            close=datetime.datetime.strptime(hours['end'],'%Y-%m-%d %H:%M')
            LHO.addTime(close.hour,close.minute,
                        open.strftime("%A, %b. %d"), hours['is_open'], 
                        open.hour, open.minute)
            
        else:
            cache = None
            caches = getToolByName(self.context,'portal_catalog').searchResults(portal_type='LibraryCache', 
                                                                                path={'query':'/sites1/library/hours','depth':1})
            if caches:
                cache = caches[0].getObject().getCache()
                if cache:
                    for hours in cache:
                        open=datetime.datetime.strptime(hours['start'],'%Y-%m-%d %H:%M')
                        close=datetime.datetime.strptime(hours['end'],'%Y-%m-%d %H:%M')
                        LHO.addTime(close.hour, close.minute, 
                                     open.strftime("%A, %b. %d"), hours['is_open'],  
                                     open.hour, open.minute)
                    if LHO.times:
                        LHO.times.pop(0) # remove yesterday
        
        return LHO

            
    
class LibraryHoursObject(WebResponseObject):
    
    times = []

    def __init__(self,context,request):
        WebResponseObject.__init__(self,context,request)
        self.times = []
        self.description = "Hours of operation today for polk library"

    def addTime(self,close,close_minutes,day,is_open,open,open_minutes):
        self.times.append({'close':str(close),
                     'close_minutes':str(close_minutes),
                     'day':str(day),
                     'is_open':str(is_open),
                     'open':str(open),
                     'open_minutes':str(open_minutes),
                     })
        
    def toXML(self):
        dom = minidom.Document()
        root = dom.createElementNS("LibraryHours", "libraryhours")

        element = dom.createElement("description")
        text = dom.createTextNode(self.description)
        element.appendChild(text)
        root.appendChild(element)
        
        element = dom.createElement('cached_at')
        text = dom.createTextNode(self.cached_at)
        element.appendChild(text)
        root.appendChild(element)
        
        for time in self.times:
            element = dom.createElement("time")
            element.setAttribute("close", time['close'])
            element.setAttribute("close_minutes", time['close_minutes'])
            element.setAttribute("day", time['day'])
            element.setAttribute("is_open", time['is_open'])
            element.setAttribute("open", time['open'])
            element.setAttribute("open_minutes", time['open_minutes'])
            root.appendChild(element)
        dom.appendChild(root)
        return dom.toxml()
    
    def toJSON(self):
        obj = {'description': self.description, 'cached_at':self.cached_at, 'times': self.times }
        return simplejson.dumps(obj)

    def toDict(self):
        pass
