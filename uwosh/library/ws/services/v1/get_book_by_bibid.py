from zope.interface import implements
from plone.memoize import ram

from uwosh.library.ws.core.webservice import WebServiceBase
from uwosh.library.ws.core.webresponse import WebResponseObject
from uwosh.library.ws.core.interfaces import IRegisteredService
from uwosh.library.ws.util import timeutil
from uwosh.library.ws.external.voyager import VoyagerDAO,VoyagerTransformer

from xml.dom import minidom
from huTools import structured
from time import time
import simplejson

import logging
logger = logging.getLogger("WebServices")


class GetBookService(WebServiceBase):
    implements(IRegisteredService)

    def setup(self):
        """ Setup before execution """
        WebServiceBase.setup(self)
        self.bibid = self.request.form.get('bibid','')
        self.fullresponse = self.request.form.get('full','0')

    def execute(self):
        self.setResponse(self.buildObject())
            
    def buildObject(self):
        gbso = GetBookServiceObject(self.context,self.request)
        gbso.setParameters(self.bibid,self.fullresponse)
        gbso.execute()
        return gbso
    
     
     

class GetBookServiceObject(WebResponseObject):
    
    full = False
    bibid = ''
    data = None
    
    def __init__(self,context,request):
        WebResponseObject.__init__(self,context,request)
        dao = VoyagerDAO()
        
    def execute(self):
        dao = VoyagerDAO()
        self.data = dao.get_holding_service(self.bibid)

    def setParameters(self,bibid,full):
        if full == '1':
            self.full = True
        self.bibid = bibid
            
    def toDict(self):
        transformer = VoyagerTransformer()
        return transformer.get_holdings_service_min_XMLToDict(self.data)
    
    def toXML(self):
        if self.full:
            return self.data.toxml()
        return structured.dict2xml(self.toDict(),roottag='book',pretty=True)
    
    def toJSON(self):
        return simplejson.dumps(self.toDict())
    
    