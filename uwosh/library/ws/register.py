from zope.interface import Interface,implements
from uwosh.library.ws.core.controller import WebServiceController
from uwosh.library.ws.core.interfaces import IWebService

"""
@note: When adding a new web service follow the guidelines.  Everything
       is achieved by name mapping and interfaces.

    class IMarkerInterface(Interface):
        ''' Marker Interface '''
        
    class WSYourWebService(WebServiceController):
        implements(IWebService)
        dependencies = ["product.dependencies","more.if.needed"]
        service_name = "file_name_in_v*_folders" 
        #package = "some.other.product" # NOT NEEDED UNLESS... SEE NOTE BELOW
        
@note: If you are making your own custom product which uses these core class,
       make sure to add this variable to each class registration. This will 
       change the lookup to your versioned services in your folders.       
        
"""

class IWSLibraryHours(Interface):
    """ Marker interface """
class WSLibraryHours(WebServiceController):
    implements(IWebService)
    dependencies = []
    installed_dependencies = []
    service_name = "libraryhours"
    
    
class IWSGroupfinder(Interface):
    """ Marker interface """
class WSGroupfinder(WebServiceController):
    implements(IWebService)
    dependencies = ["uwosh.librarygroupfinder"]
    installed_dependencies = ["uwosh.librarygroupfinder"]
    service_name = "groupfinder"
    

class IWSSetResourceAvailability(Interface):
    """ Marker interface """
class WSSetResourceAvailability(WebServiceController):
    implements(IWebService)
    dependencies = []
    installed_dependencies = []
    service_name = "setavailability"
    
    
class IWSLibraryAvailability(Interface):
    """ Marker interface """
class WSLibraryAvailability(WebServiceController):
    implements(IWebService)
    dependencies = []
    installed_dependencies = []
    service_name = "resourceavailability"

     
class IWSGetSiteIndex(Interface):
    """ Marker interface """
class WSGetSiteIndex(WebServiceController):
    implements(IWebService)
    dependencies = []
    installed_dependencies = []
    service_name = "get_site_index"
    
    
class IWSSolrGetSuggestedCourses(Interface):
    """ Marker interface """
class WSSolrGetSuggestedCourses(WebServiceController):
    implements(IWebService)
    dependencies = []
    installed_dependencies = []
    service_name = "get_suggested_courses"


class IWSSolrGetSummerSessionCourses(Interface):
    """ Marker interface """
class WSSolrGetSummerSessionCourses(WebServiceController):
    implements(IWebService)
    dependencies = []
    installed_dependencies = []
    service_name = "get_summer_session_courses"
    

class IWSSolrCOBCourses(Interface):
    """ Marker interface """
class WSSolrCOBCourses(WebServiceController):
    implements(IWebService)
    dependencies = []
    installed_dependencies = []
    service_name = "get_cob_courses"
    
class IWSSolrSiteAndCoursesSearch(Interface):
    """ Marker interface """
class WSSolrSiteAndCoursesSearch(WebServiceController):
    implements(IWebService)
    dependencies = []
    installed_dependencies = []
    service_name = "search_site_and_courses"
    
class IGetBookByBidId(Interface):
    """ Marker interface """
class GetBookByBidId(WebServiceController):
    implements(IWebService)
    dependencies = []
    installed_dependencies = []
    service_name = "get_book_by_bibid"
    
class IGetSubjectGuide(Interface):
    """ Marker interface """
class GetSubjectGuide(WebServiceController):
    implements(IWebService)
    dependencies = []
    installed_dependencies = []
    service_name = "get_subject_guide"
    
class IGetAnalyticGroup(Interface):
    """ Marker interface """
class GetAnalyticGroup(WebServiceController):
    implements(IWebService)
    dependencies = []
    installed_dependencies = []
    service_name = "get_analytic_group"
    
class IGetDatabaseInformation(Interface):
    """ Marker interface """
class GetDatabaseInformation(WebServiceController):
    implements(IWebService)
    dependencies = []
    installed_dependencies = []
    service_name = "get_database_information"
    
    
    