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
        self.query = security._security_strip_all(self.request.form.get('query','all')).lower().strip()
        self.termcode = security._security_strip_all(self.request.form.get('termCode','0650')).lower().strip()
        
        self.component = "select"
        self.start = security._security_strip_all(self.request.form.get('start','0')).lower().strip()
        self.rows = security._security_strip_all(self.request.form.get('rows','1000')).lower().strip()
        self.fl = security._security_strip_less(self.request.form.get('fl','')).strip()
        self.sort = security._security_strip_less(self.request.form.get('sort','asc')).strip()
        self.omitHeader = security._security_strip_less(self.request.form.get('omitHeader','true')).lower().strip()
        
        # adapt to solr specs
        if self.response_type == "jsonp":
            self.solr_response_type = "json" #solr does not handle jsonp
        else:
            self.solr_response_type = self.response_type
        
        if self.sort == 'desc':
            self.sort = "subject_sortable desc"
        elif self.sort == 'asc':
            self.sort = "subject_sortable asc"
            
    
    def execute(self):
        """ Execution """
        sro = SolrResponseObject(self.context,self.request)
        
        if security._security_component(self.component) and self._is_summer_term():
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
        if self.query == "coba":
            return "q=" + self._restrictions() + "academic_group:COBA"
        elif self.query == "cols":
            return "q=" + self._restrictions() + "academic_group:COLS"
        elif self.query == "coehs":
            return "q=" + self._restrictions() + "academic_group:COEHS"
        elif self.query == "con":
            return "q=" + self._restrictions() + "academic_group:CON"
        elif self.query == "cnl":
            return "q=" + self._restrictions() + 'academic_group:' + urllib.quote('WE/ED')
        elif self.query == "grad":
            return "q=" + self._restrictions() + self._grad_classes()
        elif self.query == "online":
            return "q=" + self._restrictions() + self._online_classes()
        elif self.query == "field":
            return "q=" + self._restrictions() + self._field_study_classes()
        elif self.query == "inperson":
            return "q=" + self._restrictions() + self._inperson_classes()
        elif self.query == "independent":
            return "q=" + self._restrictions() + self._independent_study_classes()
        elif self.query == "hybrid":
            return "q=" + self._restrictions() + self._hybrid_study_classes()
        elif self.query == "onlinehybrid":
            return "q=" + self._restrictions() + solr._brackets(self._hybrid_and_online_classes())
        else:
            return "q=" + self._restrictions() + "academic_group:*" # DEFAULT = ALL

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
               "type:" + self.ENFORCE_TYPE  + solr._and()
    
    def _grad_classes(self):
        return "course_number:" + urllib.quote("[500 TO *]")
    
    def _inperson_classes(self):
        return "instruction_abbr:P"
    
    def _online_classes(self):
        return "instruction_abbr:OL"
    
    def _field_study_classes(self):
        return "instruction_abbr:FS"
    
    def _independent_study_classes(self):
        return "instruction_abbr:IS"
    
    def _hybrid_study_classes(self):
        return "instruction_abbr:HB"
    
    def _hybrid_and_online_classes(self):
        #http://141.233.19.157:8080/solr-aleph/select/?q=(term:Summer 2012 AND type:Course) AND (instruction:Online* OR instruction_abbr:H*) 
        return "instruction_abbr:HB" + solr._or() + "instruction_abbr:OL"

    def _determine_term(self):
        return solr._quotes(timeutil._translate_from_term_code(self.termcode))

    def _is_summer_term(self):
        return (self.termcode[3] == '8')



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
    