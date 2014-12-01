from Products.CMFCore.utils import getToolByName
from zope.interface import implements

from uwosh.library.ws.core.webservice import WebServiceBase
from uwosh.library.ws.core.webresponse import WebResponseObject
from uwosh.library.ws.core.interfaces import IRegisteredService
from uwosh.library.ws.util import timeutil,security,solr

import httplib
import urllib
import urlparse
import simplejson

import logging
logger = logging.getLogger("WebServices")


class SolrHandler(WebServiceBase):
    implements(IRegisteredService)

    DEFAULT_QUERY = '*' # FINAL
    ENFORCE_TYPE = "Course"
    solr_url = "localhost"
    solr_port = 80
    solr_path = "/solr/"
    
    def setup(self):
        """ Setup before execution """
        WebServiceBase.setup(self)
        self.course_range = security._security_strip_allow_asterisk_ints(self.request.form.get('course_number_range','*')).lower().strip()
        self.termcode = security._security_strip_all(self.request.form.get('termCode','0650')).lower().strip()
        
        self.component = "select"
        self.start = security._security_strip_all(self.request.form.get('start','0')).lower().strip()
        self.rows = security._security_strip_all(self.request.form.get('rows','1000')).lower().strip()
        self.fl = security._security_strip_less(self.request.form.get('fl','')).strip()
        self.sort = security._security_strip_less(self.request.form.get('sort','custom')).strip()
        self.omitHeader = security._security_strip_less(self.request.form.get('omitHeader','true')).lower().strip()
        
        # adapt to solr specs
        if self.response_type == "jsonp":
            self.solr_response_type = "json" #solr does not handle jsonp
        else:
            self.solr_response_type = self.response_type
        
        if self.sort == 'custom':
            self.sort = "course_number_sortable asc, instructor_sortable asc"
            
    
    def execute(self):
        """ Execution """
        sro = SolrResponseObject(self.context,self.request)
        
        if security._security_component(self.component):
            data = self._connect(self.component)
            sro.set_data(data)
            
        self.setResponse(sro)
        
    def _connect(self,component):
        """ Connect to solr and get response """
        self._connection_setup()
        conn = httplib.HTTPConnection(self.solr_url, self.solr_port)
        conn.request("GET", self.solr_path + component + "/?" + self._build_query())
        response = conn.getresponse()
        content = response.read()
        conn.close()
        
        # Return Response Content
        return content
    
    def _connection_setup(self):
        """ Get Solr Connection Data from Portal Properties """
        url = getToolByName(self.context, 'portal_properties').external_resources.getProperty('solr_url')
        o = urlparse.urlparse(url)
        self.solr_url = o.hostname
        self.solr_port = o.port
        self.solr_path = o.path


    def _build_query(self):
        return self._build_query_selection() + self._additional_query_params()
 
    def _build_query_selection(self):
        """ split optional queries here """
        return "q=" + self._restrictions()


    def _additional_query_params(self):
        return str("&fl=" + urllib.quote(self.fl) + 
                   "&start=" + urllib.quote(self.start) + 
                   "&rows=" + urllib.quote(self.rows) + 
                   "&sort=" + urllib.quote(self.sort) +
                   "&wt=" + urllib.quote(self.solr_response_type) + 
                   "&omitHeader=" + urllib.quote(self.omitHeader)
                   )

    def _restrictions(self):
        """ Restrict on Term and by Type """
        return "term:" + self._determine_term() + solr._and() + \
               "type:" + self.ENFORCE_TYPE  + solr._and() + \
               "course_number:" + self._course_number_query()  + solr._and() + \
               "academic_group:COBA"
    
    def _course_number_query(self):
        if self.course_range == "*":
            return urllib.quote("[0 TO *]") # all
        return urllib.quote("[" + str(self.course_range) + "00 TO " + str(self.course_range) + "99]")
    
    def _determine_term(self):
        return solr._quotes(timeutil._translate_from_term_code(self.termcode))




class SolrResponseObject(WebResponseObject):
    """ Does nothing but hand if off, web service relay """
    
    def __init__(self,context,request):
        WebResponseObject.__init__(self,context,request)
        self.data = ''
        
    def set_data(self,data):
        self.data = data

    def toDict(self):
        return {}
    
    def toXML(self):
        if self.data == '':
            return '<?xml version="1.0" encoding="UTF-8" ?> <response/>'
        return self.data # response already formatted by solr, handing off...
    
    def toJSON(self):
        if self.data == '':
            return simplejson.dumps(self.toDict())
        return self.data # response already formatted by solr, handing off...
    