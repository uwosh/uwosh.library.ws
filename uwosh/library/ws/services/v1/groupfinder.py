from zope.interface import implements
from plone.memoize import ram

from uwosh.librarygroupfinder.browser import util
from uwosh.librarygroupfinder.browser.locations import Locations

from uwosh.library.ws.core.webservice import WebServiceBase
from uwosh.library.ws.core.webresponse import WebResponseObject
from uwosh.library.ws.core.interfaces import IRegisteredService
from uwosh.library.ws.util import timeutil

from xml.dom import minidom
from time import time
import simplejson

import logging
logger = logging.getLogger("WebServices")


class GroupFinder(WebServiceBase):
    implements(IRegisteredService)

    def execute(self):
        if self.use_cache != "0":
            self.setResponse(self.buildObjectGFCache())
        else:
            self.setResponse(self.buildObject())
            
    @ram.cache(lambda *args: time() // (60 * 10))
    def buildObjectGFCache(self):
        return self.buildObject()
     
    def buildObject(self):
        LGFO = LibraryGroupFinderObject(self.context,self.request)
        today = util.gatherTodaysEvents(self)
        tomorrow = util.gatherTomorrowsEvents(self)
        upcoming = util.gatherUpcomingEvents(self)
        location = Locations(self.context,self.request)
        for brain in today:
            LGFO.addGroup(LGFO.today, brain.end, location.getLocationNameByUniqueId(brain.location), brain.start, brain.Title, brain.id)
        for brain in tomorrow:
            LGFO.addGroup(LGFO.tomorrow, brain.end, location.getLocationNameByUniqueId(brain.location), brain.start, brain.Title, brain.id)
        for brain in upcoming:
            LGFO.addGroup(LGFO.upcoming, brain.end, location.getLocationNameByUniqueId(brain.location), brain.start, brain.Title, brain.id)
        return LGFO
     
     

class LibraryGroupFinderObject(WebResponseObject):
    
    def __init__(self,context,request):
        WebResponseObject.__init__(self,context,request)
        self.today = []
        self.tomorrow = []
        self.upcoming = []
        self.description = "Study groups at Polk Library"

    def addGroup(self,get,end,location,start,title,id):
        get.append({'end':str(timeutil.adapter_enforce_gmt(end)),
                    'location':location,
                    'start':str(timeutil.adapter_enforce_gmt(start)),
                    'title':self.checkPrivateGroup(id,title)
                   })
    
    def checkPrivateGroup(self,id,title):
        if id.endswith('-0'):
            return "Private Group"
        return title
    
    def toXML(self):
        dom = minidom.Document()
        root = dom.createElementNS('GroupFinder-Study-Groups', 'groups')

        element = dom.createElement('description')
        text = dom.createTextNode(self.description)
        element.appendChild(text)
        root.appendChild(element)

        element = dom.createElement('cached_at')
        text = dom.createTextNode(self.cached_at)
        element.appendChild(text)
        root.appendChild(element)
        
        element = dom.createElement('today')
        element = self.setGroupNodes(self.today, element, dom)
        root.appendChild(element)
        
        element = dom.createElement('tomorrow')
        element = self.setGroupNodes(self.tomorrow, element, dom)
        root.appendChild(element)
        
        element = dom.createElement('upcoming')
        element = self.setGroupNodes(self.upcoming, element, dom)
        root.appendChild(element)
            
        dom.appendChild(root)
        return dom.toxml()
    
    
    def setGroupNodes(self,array,parent,dom):
        for group in array:
            element = dom.createElement('group')
            element.setAttribute('end',group['end'])
            element.setAttribute('location',group['location'])
            element.setAttribute('start',group['start'])
            element.setAttribute('title',group['title'])
            parent.appendChild(element)
        return parent


    def toJSON(self):
        obj = {'description':self.description, 'cached_at':self.cached_at, 
               'today':self.today, 'tomorrow':self.tomorrow, 'upcoming':self.upcoming }
        return simplejson.dumps(obj)

    def toDict(self):
        pass
