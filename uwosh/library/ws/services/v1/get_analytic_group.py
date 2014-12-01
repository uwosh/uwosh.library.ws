from huTools import structured
from plone.memoize import ram
from Products.CMFCore.utils import getToolByName
from uwosh.library.ws.core.webservice import WebServiceBase
from uwosh.library.ws.core.webresponse import WebResponseObject
from uwosh.library.ws.core.interfaces import IRegisteredService
from uwosh.library.ws.util import timeutil
from zope.interface import implements

import simplejson
import logging
logger = logging.getLogger("WebServices")


class GetAnalyticGroupService(WebServiceBase):
    implements(IRegisteredService)

    def setup(self):
        """ Setup before execution """
        WebServiceBase.setup(self)

    def execute(self):
        self.setResponse(GetAnalyticGroupResponse(self.context, self.request))
            
    
class GetAnalyticGroupResponse(WebResponseObject):
    
    INTERNAL_STAFF = 'Internal Staff'
    INTERNAL_PUBLIC = 'Internal Public'
    EXTERNAL = 'External'
    INSTRUCTIONAL = 'Instructional'
    ERROR = 'WS Error'
    
    data = None
    
    def __init__(self,context,request):
        WebResponseObject.__init__(self,context,request)
        self.data = {}
        try:
            self.data['group'] = self._get_category()
        except Exception as e:
            self.data['group'] = self.ERROR

    def get_ip(self):
        ip = ''
        if 'HTTP_X_FORWARDED_FOR' in self.request.environ:
            ip = self.request.environ['HTTP_X_FORWARDED_FOR'] # Virtual host
        elif 'HTTP_HOST' in self.request.environ:
            ip = self.request.environ['REMOTE_ADDR'] # Non-virtualhost
        ipl = ip.split(',')
        return ipl[0].strip()
        
    def _get_category(self):
        
        ip = self.get_ip()
        staff = getToolByName(self.context, 'portal_properties').library_ip_ranges.getProperty('internal_staff',[])
        public = getToolByName(self.context, 'portal_properties').library_ip_ranges.getProperty('internal_public',[])
        instructional = getToolByName(self.context, 'portal_properties').library_ip_ranges.getProperty('instructional',[])
        
        if ip in staff:
            return self.INTERNAL_STAFF
        if ip in public:
            return self.INTERNAL_PUBLIC
        if ip in instructional:
            return self.INSTRUCTIONAL
        return self.EXTERNAL
            
    def toDict(self):
        return self.data
    
    def toXML(self):
        return structured.dict2xml(self.toDict(),roottag='analytics',pretty=True)
    
    def toJSON(self):
        return simplejson.dumps(self.toDict())
    
    