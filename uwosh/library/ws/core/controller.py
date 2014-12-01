from Products.CMFCore.utils import getToolByName
from uwosh.library.ws.core.webservice import WebServiceBase
from uwosh.library.ws.core.interfaces import IRegisteredService
from uwosh.library.ws.util.common import has_dependencies, get_ip
import sys
import inspect
import traceback
import logging
logger = logging.getLogger("Web Services")


class WebServiceController(object):
    """
    When a new web sercive is registered, the controller class should extend this class.
    It will determine what version of the service should be called.
    """
    
    package = 'uwosh.library.ws.services'
    
    def __init__(self,context,request):
        self.context = context
        self.request = request
        
    def __call__(self):
        return self.service()

    def service(self):
        if has_dependencies(self.dependencies) and self.passes_ip_restrictions() and self._check_installed():
            return self._service_setup()
        else:
            return self._default()
    
    def _default(self):
        obj = WebServiceBase(self.context,self.request)
        obj()
        return obj.sendResponse()
    
    def _service_setup(self):
        version = ''.join(['v',self.request.form.get('v','1')])
        module_name = '.'.join([self.package,version,self.service_name])
        try:
            __import__(module_name)
            webservice_module = sys.modules[module_name]
            class_ref = self._get_registered_class(webservice_module)
            return self._execute_class(class_ref)
        except Exception as e:
            #logger.error(self.service_name + " : " + str(e))
            logger.warning("Can't find version : " + str(e) + " :: "  +  traceback.format_exc())
            return self._default()

    def _execute_class(self,class_ref):
        obj = class_ref(self.context,self.request)
        obj(True)
        return obj.sendResponse()

    def _get_registered_class(self,module):
        classes = inspect.getmembers(module, inspect.isclass)
        ext_obj = None
        for name,obj in classes:
            if IRegisteredService.implementedBy(obj):
                ext_obj = obj
        return ext_obj
        raise Exception('No registered class found, implement IRegisteredService')
            
    def passes_ip_restrictions(self):
        restrictions = self.context.portal_properties.webservice_ip_restrictions
        ips = restrictions.getProperty(self.service_name,[])
        if not ips:
            return True
        return self.check_ips(ips)
        
    def check_ips(self,ips):
        remote_addr = get_ip(self.request)
        if remote_addr in ips or '*' in ips:
            return True
        return False
    
    def _check_installed(self):
        for prod in self.installed_dependencies:
            if not getToolByName(self.context,"portal_quickinstaller").isProductInstalled(prod):
                return False
        return True
            
    def setPackagePath(self,path):
        self.package = path
        
