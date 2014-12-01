from Products.CMFCore.utils import getToolByName
from xml.dom import minidom
from StringIO import StringIO
import lxml
import cookielib, urllib2
import socket
import logging
import re
logger = logging.getLogger("Plone")

class VoyagerDAO:
    """
    Connects to the VoyagersDB's Webservices and returns results in XML format.
    There is a formatter to transfer the XML data into python objects.
    @author: David Hietpas
    @version: 1.0
    """
    xmldoc = None
    DEFAULT_TIMEOUT_SECONDS = 20
    
    def __init__(self):
        """
        Initializes the Voyager Session for handling requests.
        """
        self.session = self._createCookieHandler()


    def _createCookieHandler(self):
        """
        Creates the Cookie for handling the session.
        """
        cj = cookielib.CookieJar()
        socket.setdefaulttimeout(self.DEFAULT_TIMEOUT_SECONDS)
        return urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
    
    @property
    def _getVoyagerUrl(self):
        props = getToolByName(self, 'portal_properties')
        return props.external_resources.getProperty('voyager_xml_over_http')


    def _connect(self,service,parameters):
        """
        Generic Voyager Connector
        """
        xml = None
        try:
            socket = self.session.open(self._getVoyagerUrl + '/' + service + '?' + parameters, 
                                       timeout=self.DEFAULT_TIMEOUT_SECONDS)
            xml = minidom.parse(socket).documentElement
            socket.close()
        except Exception as e:
            logger.warning(e)
        return xml


    def get_holding_service(self,bibid):
        xml = None
        if bibid != None:
            params = "bibId=" + bibid 
            xml = self._connect("GetHoldingsService",params)
        return xml


    def testConnection(self):
        self.voyagerSearchService(searchArg="foo")
        results = self.xmlToList(xml=self.voyagerSearchResultsService(searchType="FIND",maxResultsPerPage="1"))
        if results != None:
            if len(results) > 0:
                return True
            return False
        return False




class VoyagerTransformer(object):
    """ """

    def __init__(self):
        pass

    def get_holdings_service_min_XMLToDict(self,xml):
        results = {}
        try:
            xml = xml.toxml() # get ready to blow away all namespaces
            fixed = xml.replace('ser:','').replace('hol:','').replace('mfhd:','').replace('slim:','').replace('item:','') 
            tree = lxml.etree.XML(fixed)
            
            results['bibid'] = self._transform_bib_data(tree, 'controlfield','tag','004')
            results['title'] = self._transform_bib_data(tree, 'datafield','tag','245',secondary='/subfield')
            results['title_clean'] = self._cleanTitle(results['title'])
            results['author'] = self._transform_bib_data(tree, 'datafield','tag','100',secondary='/subfield')
            results['isbn'] = self._only_numbers(self._transform_bib_data(tree, 'datafield','tag','020',secondary='/subfield',limit=1))
            results['publisher'] = self._transform_bib_data(tree, 'datafield','tag','260',secondary='/subfield')
            results['oclc'] = self._transform_bib_data(tree, 'datafield','tag','035',secondary='/subfield')
            results['series'] = self._transform_bib_data(tree, 'datafield','tag','440',secondary='/subfield')
            results['subjects'] = self._transform_bib_data(tree, 'datafield','tag','650',secondary='/subfield')
            results['notes'] = self._transform_bib_data(tree, 'datafield','tag','500',secondary='/subfield')
            results['location'] = self._transform_bib_data(tree, 'datafield','tag','050',secondary='/subfield',limit=1)
            results['databaseName'] = self._transform_bib_data(tree, 'bibData','name','databaseName')
            results['databaseCode'] = self._transform_bib_data(tree, 'bibData','name','databaseCode')
            results['createDate'] = self._transform_bib_data(tree, 'bibData','name','createDate')
            results['statusCode'] = self._transform_bib_data(tree, 'itemData','name','statusCode')
            results['locationDisplayName'] = self._transform_bib_data(tree, 'mfhdData','name','locationDisplayName')
            results['itemCount'] = tree.xpath("//itemCount").pop().text
            
        except Exception as e:
            logger.error(e)
            
        return results

    def _transform_bib_data(self,tree,tag,attr,value,secondary='',delimiter=" ", limit=100000):
        out = ""
        elements = tree.xpath("//"+tag+"[@"+attr+"='"+value+"']"+secondary)[:limit]
        for e in elements:
            out += e.text + delimiter
        return out.strip()
 
    def _only_numbers(self,text):
        return re.sub('[^0-9]+', '', text).strip()

    def _cleanTitle(self,text):
        return text.split("/")[0]










    