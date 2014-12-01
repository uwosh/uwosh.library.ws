from zope.interface import implements
from Products.CMFCore.utils import getToolByName
from plone.memoize import ram
from DateTime import DateTime

from uwosh.library.ws.core.webservice import WebServiceBase
from uwosh.library.ws.core.webresponse import WebResponseObject
from uwosh.library.ws.core.interfaces import IRegisteredService

from huTools import structured
from datetime import datetime, timedelta
from time import time
from sqlalchemy import create_engine
from sqlalchemy.sql import select,or_,and_
import pymysql
import simplejson

import logging
logger = logging.getLogger("WebServices")


class ResourceAvailability(WebServiceBase):
    implements(IRegisteredService)
            
    def execute(self):
        if self.use_cache != "0":
            self.setResponse(self._response_cache_wrapper())
        else:
            self.setResponse(self._response()) 

    @ram.cache(lambda *args: time() // (60 * 2))
    def _response_cache_wrapper(self):
        return self._response()
    
    def _response(self):
        RAO = ResourceAvailabilityObject(self.context,self.request)
        
        # All PC Computers
        results = self._simple_query(select(['name,id'],or_('id=3','id=5','id=6','id=7','id=8','id=9','id=10'),'locations'))
        for result in results:
            data = self._simple_query(select(['computername,status'],
                                     and_('location_id='+str(result['id']),'is_mac=0'),'computers'))
            if data:
                RAO.addResource(result['name'], 'PC', 'computername', 'status', data)
        
        # All MAC Computers 
        results = self._simple_query(select(['name,id'],or_('id=3','id=5','id=6','id=7','id=8','id=9','id=10'),'locations'))
        for result in results:
            data = self._simple_query(select(['computername,status'],
                                     and_('location_id='+str(result['id']),'is_mac=1'),'computers'))
            if data:
                RAO.addResource(result['name'], 'MAC', 'computername', 'status', data)
                            
        
        # Laptops
        RAO.addResource('Circulation', 'Laptop', 'name', 'status', 
                        self._simple_query(select('*','type="Laptop"','resources_more')))
            
        # Scientific Calculator
        RAO.addResource('Circulation', 'Scientific Calculator', 'name', 'status', 
                        self._simple_query(select('*','type="Scientific Calculator"','resources_more')))
            
        # Graphing Calculator
        RAO.addResource('Circulation', 'Graphing Calculator', 'name', 'status', 
                        self._simple_query(select('*','type="Graphing Calculator"','resources_more')))

        # Study Locations
        locations = getToolByName(self.context, 'portal_catalog').searchResults(portal_type='GroupLocation')
        for location in locations:
            self._handle_events(RAO,location.Title,location.UID)
        return RAO
        
        
    def _handle_events(self,response,title,id):
        try:
            start = DateTime(datetime.now().replace(hour=0, minute=0, second=0))
            end = DateTime(datetime.now().replace(hour=23, minute=59, second=59))
            brains = getToolByName(self.context, 'portal_catalog').searchResults(portal_type='GroupFinderEvent',start={'query': (start, end), 'range': 'min:max'},sort_on='start')
            brains = filter(lambda x: x['location'] == id, brains) #filter only one location
            brains = filter(lambda x: DateTime(x['end']).greaterThan(DateTime()), brains) #filter out past events
            
            available = 1
            for brain in brains:
                bs = DateTime(brain.start)
                be = DateTime(brain.end)
                now = DateTime(datetime.now())
                if bs.lessThanEqualTo(now) and be.greaterThanEqualTo(now):
                    available = 0
                    break
               
            response.addStudyArea(brains,title,id,available)
        except Exception as e:
            print str(e)
            
    
    def _simple_query(self,statement):
        if statement.__class__.__name__ != "Select": return []
        
        engine = None
        resultProxy = None
        try:
            url = getToolByName(self.context,'portal_properties').get('external_resources').getProperty('computer_availability_db')
            engine = create_engine('mysql://' + url, echo=False, module=pymysql, strategy='threadlocal')
            resultProxy = engine.execute(statement) #execute handles failure
            results = resultProxy.fetchall()
            return results
        except Exception as e:
            logger.error(str(e))
            return []
        finally:
            try:
                resultProxy.close()
                engine.dispose()
            except Exception as e: 
                logger.error(str(e))
                

class ResourceAvailabilityObject(WebResponseObject):
    
    def __init__(self,context,request):
        WebResponseObject.__init__(self,context,request)
        self.locations = []
        self.studyareas = []
        
    def addResource(self,location,type,name,count,items):
        available, unavailable, resources = 0, 0, []
        for item in items:
            resources.append({'name' : item[name], 'status' : item[count]})
            if item[count] == 1: available += 1
            else: unavailable += 1
        self.locations.append({'name' : location, 'type' : type, 'available' : available, 'unavailable' : unavailable, 
                               'total' : (available+unavailable), 'resources' : resources})
        
    def addStudyArea(self,brains,location_name,location_id,available):
        events = []
        for brain in brains:
            events.append(self._addStudyEvent(brain,location_name))
        self.studyareas.append({'name' : location_name, 'id' : location_id, 'status' : available, 
                               'events' : events})
        
    def _addStudyEvent(self,brain,location_name):
        if brain.id.endswith('-0'):
            brain.Title = 'Private Group'
        return {'name':brain.Title,
                'location':location_name,
                'date_start': DateTime(brain.start).strftime("%B %d, %Y"),
                'date_end': DateTime(brain.end).strftime("%B %d, %Y"),
                'time_start': DateTime(brain.start).strftime("%I:%M %p"),
                'time_end': DateTime(brain.end).strftime("%I:%M %p"),
                }
        
    def toXML(self):
        return structured.dict2xml(self.toDict(),roottag='resources', 
                                   listnames={'locations': 'location','resources':'resource',
                                              'study_areas': 'studyarea', 'events':'event'}, pretty=True)

    def toJSON(self):
        return simplejson.dumps(self.toDict())

    def toDict(self):
        return { 'cached' : self.cached_at, 'locations' : self.locations, 'study_areas' : self.studyareas }
    
    
    
    