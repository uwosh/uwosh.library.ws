from zope.interface import implements
from Products.CMFCore.utils import getToolByName
from plone.memoize import ram

from uwosh.library.ws.db.schemas import schema
from uwosh.library.ws.core.webservice import WebServiceBase
from uwosh.library.ws.core.webresponse import WebResponseObject
from uwosh.library.ws.core.interfaces import IRegisteredService

from xml.dom import minidom
from DateTime import DateTime
from time import time
from sqlalchemy import create_engine
from sqlalchemy.sql import select,update,functions,or_
import pymysql
import datetime
import simplejson

import logging
logger = logging.getLogger("WebServices")


class ResourceAvailability(WebServiceBase):
    implements(IRegisteredService)
            
    def execute(self):
        if self.use_cache != "0":
            self.setResponse(self.buildObjectCACache())
        else:
            self.setResponse(self.buildObject()) 

    @ram.cache(lambda *args: time() // (60 * 10))
    def buildObjectCACache(self):
        return self.buildObject()
     
    def buildObject(self):
        RAO = ResourceAvailabilityObject(self.context,self.request)
        
        # Get Resources
        results = self._getResources()
        laptops = filter(lambda x: x['type']=='Laptop', results)
        sci_cal = filter(lambda x: x['type']=='Scientific Calculator', results)
        gra_cal = filter(lambda x: x['type']=='Graphing Calculator', results)
        RAO.addResource('Laptop', str(len(laptops)))
        RAO.addResource('Scientific Calculator', str(len(sci_cal)))
        RAO.addResource('Graphing Calculator', str(len(gra_cal)))
        
        # Get Computer Counts
        results = self._simpleQuery(select(['name,id'],or_('id=3','id=6','id=7','id=8','id=9'),'locations'))
        for result in results:
            RAO.addLocation(result['name'],str(self._getLocationAvailableCount(result['id'])))
   
        return RAO
        
    def _getLocationAvailableCount(self,location_id):
        results = self._simpleQuery(select(['status'],'status=1 and location_id='+str(location_id),'computers'))
        return len(results)
    
    def _getResources(self):
        return self._simpleQuery(select('*','','resources_more'))
    
    def _simpleQuery(self,statement):
        # simple enforce select only
        if statement.__class__.__name__ != "Select":
            return []
        
        engine = None
        resultProxy = None
        try:
            engine = create_engine('mysql://'+self._getLibraryResourcesURL(), echo=False, module=pymysql, strategy='threadlocal')
            resultProxy = engine.execute(statement) #execute handles failure
            results = resultProxy.fetchall()
            return results
        except Exception as e:
            logger.error(e)
            return []
        finally:
            try:
                resultProxy.close()
                engine.dispose()
            except: pass

    def _getLibraryResourcesURL(self):
        props = getToolByName(self.context,'portal_properties').external_resources
        return props.getProperty('computer_availability_db')


class ResourceAvailabilityObject(WebResponseObject):
    
    def __init__(self,context,request):
        WebResponseObject.__init__(self,context,request)
        self.resources = []
        self.computers = []
        self.computers_accessible = 'True' # dead code
        self.resources_accessible = 'True' # dead code
        self.description = "Resources Available at Polk Library"

    def addResource(self,name,count):
        self.resources.append({'name':name, 'available_count':count})
        
    def addLocation(self,name,count):
        self.computers.append({'name':name, 'available_count':count})

    def toXML(self):
        dom = minidom.Document()
        root = dom.createElementNS('Library-Resource-Availability', 'libraryresources')

        element = dom.createElement('description')
        text = dom.createTextNode(self.description)
        element.appendChild(text)
        root.appendChild(element)

        element = dom.createElement('cached_at')
        text = dom.createTextNode(self.cached_at)
        element.appendChild(text)
        root.appendChild(element)
        
        
        element = dom.createElement('computers')
        element.setAttribute('accessible',self.computers_accessible)
        for location in self.computers:
            child_ele = dom.createElement('location')
            child_ele.setAttribute('name',location['name'])
            child_ele.setAttribute('available_count',location['available_count'])
            element.appendChild(child_ele)
        root.appendChild(element)
            
        element = dom.createElement('resources')
        element.setAttribute('accessible',self.resources_accessible)
        for resource in self.resources:
            child_ele = dom.createElement('resource')
            child_ele.setAttribute('name',resource['name'])
            child_ele.setAttribute('available_count',resource['available_count'])
            element.appendChild(child_ele)
        root.appendChild(element)
            
        dom.appendChild(root)
        return dom.toxml()
    
    
    def toJSON(self):
        obj = {'description': self.description, 'cached_at':self.cached_at, 
               'resources': self.resources, 'resources_accessible':self.resources_accessible,
               'computers':self.computers, 'computers_accessible':self.resources_accessible 
               }
        return simplejson.dumps(obj)

    def toDict(self):
        pass
