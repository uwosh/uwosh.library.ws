from zope.interface import implements
from DateTime import DateTime
from huTools import structured
import simplejson

from uwosh.library.ws.core.interfaces import IWebResponse

import logging
logger = logging.getLogger("Web Services")


class WebResponseObject(object):
    """
    Response class for any web service.
    """
    implements(IWebResponse)
    
    def __init__(self,context=None,request=None):
        self.context = context
        self.request = request
        self.cached_at = DateTime().PreciseTime()
        
    def toXML(self):
        return structured.dict2xml(self.toDict(),roottag='Responses',pretty=True)

    def toJSON(self):
        return simplejson.dumps(self.toDict())
    
    def toDict(self):
        return {'Response':'None' }
    
    def toCustom(self):
        return ''

    def __str__(self):
        return str(self.__dict__)