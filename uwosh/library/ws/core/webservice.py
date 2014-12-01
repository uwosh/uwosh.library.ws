from Products.Five import BrowserView
from xml.dom import minidom
from uwosh.library.ws.core.webresponse import WebResponseObject

import logging
logger = logging.getLogger("Web Services")

    
class WebServiceBase(BrowserView):
    """
    Any Web Service should extend this class, this will setup the basic
    functionality and return types for any service.
    """
    
    DEFAULT_RESPONSE_TYPE = 'xml'
    DEFAULT_CALLBACK = '?'
    APPLICATION_JSON = 'application/json'
    APPLICATION_XML = 'application/xml'
    RESPONSE_TYPE_JSON = 'json'
    RESPONSE_TYPE_JSONP = 'jsonp'
    RESPONSE_TYPE_XML = 'xml'
    
    response = None
    
    def __call__(self,proceed=False):
        self.response = WebResponseObject(self.context,self.request) # Default
        self.setup()
        if proceed: 
            self.execute()
    
    def setup(self):
        """ Setup before execution """
        self.use_cache = self.request.form.get('use_cache','')
        self.response_type = self.request.form.get('alt',self.DEFAULT_RESPONSE_TYPE)
        self.callback = self.request.form.get('callback',self.DEFAULT_CALLBACK)
        content_type = self.request.form.get('content_type','text/html')
        
        if self.response_type == self.RESPONSE_TYPE_JSON or \
           self.response_type == self.RESPONSE_TYPE_JSONP:
            self.request.response.setHeader('Content-Type', self.APPLICATION_JSON)
        elif self.response_type == self.RESPONSE_TYPE_XML:
            self.request.response.setHeader('Content-Type', self.APPLICATION_XML)
        else:
            self.request.response.setHeader('Content-Type', content_type)

    def execute(self):
        """ Execution """
        raise Exception("Must implement execute()")

    def sendResponse(self):
        if self.response_type == self.RESPONSE_TYPE_JSON:
            return self.response.toJSON()
        elif self.response_type == self.RESPONSE_TYPE_JSONP:
            return str(self.callback) + "(" + self.response.toJSON() + ")"
        elif self.response_type == self.RESPONSE_TYPE_XML:
            return self.response.toXML()
        else:
            return self.response.toCustom()

    def setResponse(self,value):
        self.response = value
        
  