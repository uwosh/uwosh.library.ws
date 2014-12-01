from zope.interface import implements
from Products.CMFCore.utils import getToolByName

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


class CourseSuggestions(WebServiceBase):
    implements(IRegisteredService)

    DEFAULT_QUERY = '*' # FINAL
    COURSE_TYPE = "Course"
    solr_url = "localhost"
    solr_port = 80
    solr_path = "/solr/"

    def setup(self):
        """ Setup before execution """
        WebServiceBase.setup(self)
        self.component = security._security_strip_all(self.request.form.get('component','boosted'))
        self.query = security._security_strip_all(self.request.form.get('q',''))
        self.start = security._security_strip_all(self.request.form.get('start','0'))
        self.rows = security._security_strip_all(self.request.form.get('rows','10'))
        self.fl = security._security_strip_less(self.request.form.get('fl',''))
        self.sort = security._security_strip_less(self.request.form.get('sort','desc'))
        
        # adapt to solr specs
        if self.response_type == "jsonp":
            self.solr_response_type = "json" #solr does not handle jsonp
        else:
            self.solr_response_type = self.response_type
        
        if self.sort == 'desc':
            self.sort = "score desc"
        elif self.sort == 'asc':
            self.sort = "score asc"
            
        if self.query == '':
            self.query = self.DEFAULT_QUERY
    
    
    def execute(self):
        """ Execution """
        sro = SolrResponseObject(self.context,self.request)
        
        if security._security_component(self.component):
            sro.set_data(self._connect(self.component))
            
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
        return "q=" \
                + self._query() \
                + self._additional_query_params()
                
    def _additional_query_params(self):
        return "&fl=" + urllib.quote(self.fl) \
                + "&start=" + urllib.quote(self.start) \
                + "&rows=" + urllib.quote(self.rows) \
                + "&sort=" + urllib.quote(self.sort) \
                + "&fq=" + self._filter_query() \
                + "&wt=" + urllib.quote(self.solr_response_type)
              
    def _query(self):
        return urllib.quote(self.query)
        
    def _filter_query(self):
        return 'term:' + self._get_current_term() + solr._and() + 'type:' + self.COURSE_TYPE + solr._and() + urllib.quote('(is_combined_course:0)') 
       
    def _get_current_term(self):
        termcode = getToolByName(self.context, 'portal_properties').webservice_properties.getProperty('current_term_code')
        return solr._quotes(timeutil._translate_from_term_code(termcode))



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
    