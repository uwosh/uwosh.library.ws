from zope.interface import implements
from Products.CMFCore.utils import getToolByName
from plone.memoize import ram

from uwosh.library.ws.core.webservice import WebServiceBase
from uwosh.library.ws.core.webresponse import WebResponseObject
from uwosh.library.ws.core.interfaces import IRegisteredService

from huTools import structured
from time import time
import simplejson

class DatabaseInformationService(WebServiceBase):
    implements(IRegisteredService)

    def setup(self):
        """ Setup before execution """
        WebServiceBase.setup(self)

    def execute(self):
        ids = self.request.form.get('id','').split(',')
        self.setResponse( DatabaseInformationObject(self.context,self.request,ids) )

class DatabaseInformationObject(WebResponseObject):

    databases = []

    def __init__(self,context,request,ids):
        WebResponseObject.__init__(self,context,request)
        self.databases = filter(lambda x: x['id'] in ids, self.saved_cache())
            
    @ram.cache(lambda *args: time() // (60 * 10))
    def saved_cache(self):
        path = getToolByName(self.context,'portal_properties').get('base_paths').getProperty('base_atoz_path','/')
        brains = getToolByName(self.context, 'portal_catalog').searchResults(portal_type='LibraryCache', path={'query':path,'depth':10})
        if brains:
            return brains[0].getObject().getCache() # getObject is a performance hit
        return []
            
    def toDict(self):
        return {'databases':self.databases} 
    
    def toXML(self):
        return structured.dict2xml(self.toDict(),roottag='response',listnames={'databases': 'database'},pretty=True)
    
    def toJSON(self):
        return simplejson.dumps(self.toDict())
    
    