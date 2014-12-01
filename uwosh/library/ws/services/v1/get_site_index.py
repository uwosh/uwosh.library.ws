"""
Note to self: This file needs refactoring.
"""

from zope.interface import implements
from Products.CMFCore.utils import getToolByName
from plone.memoize import ram

from uwosh.library.ws.core.webservice import WebServiceBase
from uwosh.library.ws.core.webresponse import WebResponseObject
from uwosh.library.ws.core.interfaces import IRegisteredService

from xml.dom import minidom
from DateTime import DateTime
from time import time
import datetime
import calendar
import simplejson
from huTools import structured
import sys
import traceback
import re
import urllib

import logging
logger = logging.getLogger("WebServices")


class WebsiteIndexHandler(WebServiceBase):
    implements(IRegisteredService)

    def setup(self):
        """ Setup before execution """
        WebServiceBase.setup(self)
        
    def execute(self):
        """ Execution """
        try:
            wio = WebsiteIndexObject(self.context,self.request)
            if self.use_cache != "0":
                wio = self.buildCache(wio)
            else:
                wio = self.build(wio)
        except Exception as e:
            print "Execute: " + str(e)
        self.setResponse(wio)
        
    @ram.cache(lambda *args: time() // (60 * 15))
    def buildCache(self,response):
        return self.build(response)
        
    def build(self,response):
        response = self.indexStandardContent(response, ('Folder'))
        response = self.indexStandardContent(response, ('LibraryLink','LibrarySubjectGuide','LibraryStaff','Document'))
        response = self.indexFilesContent(response)
        response = self.indexNewsContent(response)
        response = self.indexResearchDatabases(response)
        return response
    
    def indexStandardContent(self,response,types):
        brains = getToolByName(self.context,'portal_catalog').searchResults({'portal_type':types,'review_state':'published'})
        for brain in brains:
            response.addBrain(brain)
        return response
    
    def indexNewsContent(self,response):
        brains = getToolByName(self.context,'portal_catalog').searchResults({'portal_type':'WeblogEntry','review_state':'published'})
        for brain in brains:
            response.addNewsItem(brain)
        return response
    
    def indexFilesContent(self,response):
        """ Only 1 review state can be searched against, Files have no state """
        brains = getToolByName(self.context,'portal_catalog').searchResults({'portal_type':'File'})
        for brain in brains:
            response.addBrain(brain)
        return response
            
    def indexResearchDatabases(self,response):
        path = getToolByName(self.context,'portal_properties').get('base_paths','/miss').getProperty('base_atoz_path','/miss')
        brains = getToolByName(self.context,'portal_catalog').searchResults(portal_type='LibraryCache',path={'query':path,'depth':-1})
        for brain in brains:
            caches = brain.getObject().getCache()
            for cache in caches:
                response.addAtoZCache(cache)
        return response
        
        
    
class WebsiteIndexObject(WebResponseObject):

    nodes = []
    exclude_document = []
    type = 'Website'
    ROOT_TITLE = 'Polk Library'
    
    def __init__(self,context,request):
        WebResponseObject.__init__(self,context,request)
        self.nodes = []
        
    def addBrain(self,brain):
        try:
            self.determine_folder_default_views(brain)
            if (brain['review_state'] not in ['internal','internally_published','private','pending'] and bool(brain['exclude_from_nav']) == False):
                if brain.getPath() not in self.exclude_document:
                    self._addBrain(brain)
        
        except Exception as e:
            print "ERROR " + str(e) + " : " + str(brain['Title'])
    
    def _addBrain(self,brain):
            parent = self._determine_site_level(brain)
            subject = self._text_safe(self._subject_cleaup(brain['Subject'])) + self._boost_root_folders(brain,parent)
                                        
            self.nodes.append(self.node(self._text_safe(brain['Title']),
                                        self._text_safe(brain['Description']),
                                        subject,
                                        self._text_safe(brain['portal_type']),
                                        self._text_safe(brain.getURL()),
                                        self._get_full_text(brain),
                                        parent,
                                        self.type
                                        ))
    
    def addNewsItem(self,brain):
        """ News items are subject based which get boosted. Moving subjects to a less boosted field (temporary) """
        try:
            parent = self._determine_site_level(brain)
            subject = self._text_safe(self._subject_cleaup(brain['Subject']))                      
            self.nodes.append(self.node(self._text_safe(brain['Title']),
                                        self._text_safe(brain['Description']),
                                        '',
                                        self._text_safe(brain['portal_type']),
                                        self._text_safe(brain.getURL()),
                                        self._get_full_text(brain) + " " + subject,
                                        parent,
                                        self.type
                                        ))
        except Exception as e:
            print "ERROR " + str(e) + str(brain['Title'])
        
    
    def addAtoZCache(self,cache):
        try:
            self.nodes.append(self.node(self._text_safe(cache['title']),
                                        self._text_safe(cache['db_description']),
                                        self._text_safe(cache['title']),
                                        self._text_safe('LibraryCache'),
                                        self._pad_with_proxy(cache['is_omit_proxy']) + self._text_safe(cache['url']),
                                        'Research Database' + self._text_safe(cache['title']) + self._text_safe(cache['db_description']),
                                        'Research Database',
                                        self.type
                                        ))
        except Exception as e:
            print "ERROR " + str(e) + str(cache['title'])
    
    def node(self,title,description,subject,portal_type,url,full_text,parent_area,type):
        return {'title':title,
                'description':description,
                'subject':subject,
                'portal_type':portal_type,
                'url':url,
                'full_text':full_text,
                'parent_area':parent_area,
                'type':type,
               }
            
    def _pad_with_proxy(self,flag):
        if str(flag) == '0':
            return getToolByName(self.context,'portal_properties').get('external_resources','').getProperty('proxy_server_url','')
        return ''  
    
    def _boost_root_folders(self,brain,parent):
        """ Temporary: Add Title to subject field to heavily boost """
        if self.ROOT_TITLE == parent:
            return ' ' + brain.Title
        return ''
    
    def _determine_site_level(self,brain):
        base_path = getToolByName(self.context,'portal_properties').base_paths.getProperty('base_library_path')
        parent_path = False
        path = brain.getPath()
        
        try:
            path = path.replace(base_path,'')
            paths = path.split('/')
            parent = paths[1]
            if len(paths) > 2:
                parent_path = '/'.join([base_path,parent])
        except:
            pass
        
        parent_title = self._get_item_title_by_path(parent_path)
        return parent_title

    def _get_item_title_by_path(self,path):
        if path == False:
            return self.ROOT_TITLE
        brains = getToolByName(self.context,'portal_catalog').searchResults(path={'query':path,'depth':0})
        return brains[0].Title
        
    def _get_full_text(self,brain):
        if brain.portal_type == 'Folder':
            obj = brain.getObject()
            pre = self._text_safe(obj.getField('prefixText').getAccessor(obj)(mimetype='text/plain'))
            suf = self._text_safe(obj.getField('suffixText').getAccessor(obj)(mimetype='text/plain'))
            return pre + " " + suf
        if brain.portal_type == 'Document':
            obj = brain.getObject()
            return self._text_safe(obj.getText(mimetype='text/plain'))
        return ''
    
    def determine_folder_default_views(self,brain):
        if brain.portal_type == 'Folder':
            obj = brain.getObject()
            views = self.getFolderViews()
            view = obj.defaultView()
            if view not in views:
                self.exclude_document.append(brain.getPath() + '/' + str(view))

    @ram.cache(lambda *args: time() // (60 * 10))
    def getFolderViews(self):
        try:
            views = getToolByName(self.context,'portal_types').get('Folder',[]).view_methods
            return views
        except:
            return []
        
    def _subject_cleaup(self,subject):
        clean = ""
        listing = list(subject)
        clean = ", ".join(listing)
        return clean.strip()
        
    def _text_safe(self,text):
        try:
            bad_chars = {'&':'&amp;','<':'&lt;','>':'&gt;','"':''} # sure this can be done with RE
            for i,k in enumerate(bad_chars):
                text = text.replace(k,bad_chars[k])
            t = text.decode('utf-8')
            return t.encode("ascii", "ignore")
            #return unicode(text,errors="replace") # removes unknown unicode characters from xml
        except Exception as e:
            print "ERROR: " + str(e)
            return "" # for dumb unicode characters which cause xml failure.
    
    def _add_xml_header(self,xml):
        return '<?xml version="1.0"?>' + xml
    
    def toDict(self):
        return {"pages":self.nodes}
    
    def toXML(self):
        return self._add_xml_header(structured.dict2xml(self.toDict(),roottag='siteindex',listnames={'pages': 'page'},pretty=True))
    
    def toJSON(self):
        return simplejson.dumps(self.toDict())
        