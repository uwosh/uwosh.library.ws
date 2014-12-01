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
from sqlalchemy.sql import select,update,functions,insert
import pymysql
import datetime
import simplejson

import logging
logger = logging.getLogger("WebServices")


class SetResourceAvailability(WebServiceBase):
    implements(IRegisteredService)
    
    is_mac = 0

    def setup(self):
        WebServiceBase.setup(self)
        self.computer_id = self.request.form.get('computerId','')
        self.computer_status = self.request.form.get('status',-1)
        self.is_mac = 0
        
    def execute(self):
        self.setResponse(self.buildObject())

    def buildObject(self):
        CAO = ComputerAvailabilityObject(self.context,self.request)
        try:
            self.computer_status = int(self.computer_status)
            self.computer_id = self._mergeMacNames(str(self.computer_id))
            if self._checkResources():
                self._updateResources()
            else:
                self._insertResources()
        except Exception as e:
            logger.error(e)
        CAO.update(self.computer_id, self.computer_status)
        return CAO
    
    def _checkResources(self):
        count = self._simpleQuery(select(['status'],'computername="'+self.computer_id+'"','computers'))
        print str(len(count))
        return bool(len(count))
        
    def _insertResources(self):
        query = {'status':self.computer_status , 'update0':functions.now() , 'update1':functions.now() , 
                 'computername':self.computer_id, 'is_mac': self.is_mac}
        self._simpleQuery(insert(schema.computers).values(query))
               
    def _updateResources(self):
        query = {'status':self.computer_status,'is_mac': self.is_mac}
        if self.computer_status == 0:
            query['update0'] = functions.now()
        else:
            query['update1'] = functions.now()
        self._simpleQuery(update(schema.computers,schema.computers.c.computername==self.computer_id,values=query))  
    
    def _simpleQuery(self,statement):
        returned = False
        if statement.__class__.__name__ == "Select":
            returned = True
        engine = None
        resultProxy = None
        try:
            engine = create_engine('mysql://'+self._getLibraryResourcesURL(), echo=False, module=pymysql, strategy='threadlocal')
            resultProxy = engine.execute(statement)
            if returned:
                return resultProxy.fetchall()
        except Exception as e:
            logger.error(e)
            if returned:
                return []
        finally:
            try:
                resultProxy.close()
                engine.dispose()
            except: pass

    def _getLibraryResourcesURL(self):
        props = getToolByName(self.context,'portal_properties').external_resources
        return props.getProperty('computer_availability_db')

    def _mergeMacNames(self,id):
        swap = [{'from':'emcmac01.local','to':'EMC07PC'},]
        for s in swap:
            id = id.replace(s['from'],s['to'])
        
        check = ['PC','MAC','mac.local','MAC.local','MAC.LOCAL','mac01.local','MAC01.LOCAL']
        for c in check:
            if id.endswith(c):
                self.is_mac = 1
                return id.replace(c,'').upper()
        return id.upper()

class ComputerAvailabilityObject(WebResponseObject):

    def __init__(self,context,request):
        WebResponseObject.__init__(self,context,request)
        self.computer_status = 0
        self.computer_id = ""
        self.description = "Computer Availability"
    
    def update(self,computer_id,computer_status):
        self.computer_id = computer_id
        self.computer_status = computer_status
        
    def toXML(self):
        dom = minidom.Document()
        root = dom.createElementNS("ComputerLogin", "computerLogin")

        element = dom.createElement("description")
        text = dom.createTextNode(self.description)
        element.appendChild(text)
        root.appendChild(element)
        
        element = dom.createElement("login")
        element.setAttribute("status", str(self.computer_status))
        element.setAttribute("name", self.computer_id)
        root.appendChild(element)
        
        dom.appendChild(root)
        return dom.toxml()
    
    def toJSON(self):
        obj = {'description': self.description, 'status':self.computer_status, 'name': self.computer_id }
        return simplejson.dumps(obj)
    
    def toDict(self):
        pass
    