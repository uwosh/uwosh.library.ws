Introduction
============

Library Web Services
====================

This product acts as a layer on top of our Plone site.  The LWSP (Library Web Service Product)
provides web services built in python and/or based from plone functionality.

LWSP can:
- Determine at runtime if a service is available
- Allows simple versioning of web services.
- IP Restrict Services
- Allows for Python Based Services
- Allows for Plone Based Services
- Is dependency aware.
- Handles automatically xml/json and other commonly used functionality.

LWSP cannot:
- Web service Code cannot be changed in ZMI.




How to add a new web service?
=============================

Straight forward really.  Just remember everything is connected/mapped by naming convention.

Step 1:
-------
 - Go to register.zcml
 - Add your new service.

   >>> <browser:page
   >>>     for=".register.IWSYourService"
   >>>     name="getYourService"
   >>>     class=".register.WSYourService"
   >>>     permission="zope.Public"
   >>> />


Step 2:
-------
 - Go to register.py
 - Add your new Controller Class
 
	>>>	class WSYourService(WebServiceController):
	>>>	    implements(IWebService)
	>>>	    dependencies = []
	>>>	    installed_dependencies = []
	>>>	    service_name = "your_file_name"
	
	   
	    dependencies = []
		 - This is for any module dependencies this service will need.
	    installed_dependencies = []
	     - This is for any plone installed product dependencies needed.  In simpler terms
	       what product must be installed on your plone site for this service to be active.
	    service_name = "your_file_name"
	     - This is the python file that will be in one of the Version folders.  It must
	       be the same name!  Do not include the .py extension though.
	
	>>> class IWSYourService(Interface):
	>>>     """ Marker interface """
	
		This will allow the web service to assigned to a specific location on your Plone site.


Step 3:
-------
 - Go to services folder.
 - Pick a version folder, I'd recommend starting on Version 1 if the service doesn't exist yet.
 - Create a file called named the same as the service_name = "your_file_name", so your_file_name.py.

	>>># here is a simple example...
	>>>
	>>>from zope.interface import implements
	>>>from uwosh.library.ws.core.webservice import WebServiceBase
	>>>from uwosh.library.ws.core.webresponse import WebResponseObject
	>>>from uwosh.library.ws.core.interfaces import IRegisteredService
	>>>import simplejson
	>>>
	>>>    class YourService(WebServiceBase):
	>>>        implements(IRegisteredService)
	>>>
	>>>        def setup(self):
	>>>            # WebServiceBase.setup(self)
	>>>            # Extend if you need more setup functionality
	>>>
	>>>        def execute(self):
	>>>            # Must be implemented, handles service execution, you should return a WebResponseObject
	>>>            response = YourResponseObject(self.context,self.request)
	>>>
	>>>            # You can create your own Response Object and assign whatever here
	>>>            # ... .. .
	>>>
	>>>            # Finalize, set the final response
	>>>            self.setResponse(response)
	>>>
	>>>    class YourResponseObject(WebResponseObject):
	>>>        """ Does nothing but hand if off, web service relay """
	>>>        
	>>>        a_variable = 'stuff_eh'
	>>>    
	>>>        def set_something(self,data):
	>>>            self.a_variable = a_variable
	>>>
	>>>        def toDict(self):
	>>>            return {}
	>>>    
	>>>        def toXML(self):
	>>>            # You can use a xml class, just return the xml string.
	>>>            return '<?xml version="1.0" encoding="UTF-8" ?> <response/>'
	>>>    
	>>>        def toJSON(self):
	>>>            return simplejson.dumps(self.toDict())
	>>>        

 - Your class YourService(WebServiceBase) must be registered, to do this implement IRegisteredService.
   If you want caching of these services I recommend you use ram memoize on your WebResponseObject,
   set it before the self.setResponse(response).  Just decorate the response variable.
 - Your class YourResponseObject(WebResponseObject) is a storage object and formatting object of the
   stored data.




How to add another version of a service?
========================================

Very easy.

Step 1:
-------
 - Copy the class your_file_name.py over to the next version folder.
 - Don't change the original.
 - Do any changes to the new copy (add new parameters, new functionality, new whatever)
 - It is now accessible by adding parameter v=2




How to add another version folder?
==================================

Very simple.

Step 1:
-------
 - Go to services folder.
 - Go to configure.zcml.
 - You will see some...
 
    <include package=".v1" />
    <include package=".v2" />

 - Add another line with a raised v* number, I will add a version 3, so v3...
    
    <include package=".v3" />

Step 2:
-------
 - Go to services folder.
 - Add new folder called v3 or whatever version you are on.
 - Once created, add a empty __init__.py to declare package.
 - Once created, add a configure.zcml for zope registration.
 
    <configure
      xmlns="http://namespaces.zope.org/zope"
      i18n_domain="uwosh.library.ws">
    </configure>














