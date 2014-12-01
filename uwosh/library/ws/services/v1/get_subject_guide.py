from zope.interface import implements
from Products.CMFCore.utils import getToolByName
from plone.memoize import ram

from uwosh.library.ws.core.webservice import WebServiceBase
from uwosh.library.ws.core.webresponse import WebResponseObject
from uwosh.library.ws.core.interfaces import IRegisteredService

from DateTime import DateTime
from xml.dom import minidom
from huTools import structured
from time import time
from operator import itemgetter
import simplejson

import logging
logger = logging.getLogger("WebServices")

def toAscii(s): return "".join(i for i in s if ord(i)<128)

def _subject_cache_key(method, self, subject_id, key): 
    """ Unique cache key for each subject (seconds * minutes * hours) """
    return "ws_subject_guide_%s/%s" % (subject_id + '-' + key, time() // (60 * 60 * 8))

class Handler(WebServiceBase):
    implements(IRegisteredService)
    
    subject = None
    url = ''
    subject_id = ''
    unique_key = 'default'
    limits = {'books' : 1,
              'campus_resources' : 3,
              'emc' : 3,
              'government' : 3,
              'archives' : 3,
              'journals' : 3,
              'news' : 3,
              'primary' : 1,
              'reference' : 3,
              'voyager' : 3,
               }
    
    def setup(self):
        """ Setup before execution """
        WebServiceBase.setup(self)
        self.subject_id = self.request.form.get('subject_id','')
        self.referring_url = self.request.form.get('url','')
        self.limits['books'] = int(self.request.form.get('book_limit',1))
        self.limits['campus_resources'] = int(self.request.form.get('campus_resources_limit',3))
        self.limits['emc'] = int(self.request.form.get('emc_limit',3))
        self.limits['archives'] = int(self.request.form.get('archives_limit',3))
        self.limits['government'] = int(self.request.form.get('government_limit',3))
        self.limits['journals'] = int(self.request.form.get('journals_limit',3))
        self.limits['news'] = int(self.request.form.get('news_limit',3))
        self.limits['primary'] = int(self.request.form.get('primary_sources_limit',1))
        self.limits['reference'] = int(self.request.form.get('reference_limit',3))
        self.limits['voyager'] = int(self.request.form.get('voyager_limit',3))
        self.unique_key = self.request.form.get('unique_key','default')
        
    def execute(self):
        self.subject = self.get_subject()
        if self.use_cache == "0":
            self.setResponse(self.get_response())
        elif self.subject:
            self.setResponse(self.cached_response(self.subject.getId, self.unique_key))
        else:
            self.setResponse(Response(self.context,self.request))

    @ram.cache(_subject_cache_key)
    def cached_response(self,subject,key):
        return self.get_response()
    
    def get_response(self):
        response = Response(self.context, self.request)
        response.build(self.limits, self.subject.getObject(), self.get_cache().getObject())
        return response
    
    def get_cache(self):
        if self.subject:
            brains = getToolByName(self.context, 'portal_catalog').searchResults(portal_type='LibraryCache', path={'query':self.subject.getPath(),'depth':2})
            if brains: return brains[0]
        return None
  
    def get_subject_id_by_url(self):
        urls = getToolByName(self.context,'portal_properties').get('webservice_properties').getProperty('url_to_subject_guide')
        for url in urls:
            try:
                parsed = url.split('|')
                if str(self.referring_url).find(parsed[0]) != -1:
                    return parsed[1]
            except: pass
        return None # default?
    
    def get_subject(self):
        if not self.subject_id:
            self.subject_id = self.get_subject_id_by_url()
            if not self.subject_id:
                return None
        brains = getToolByName(self.context,'portal_catalog').searchResults(portal_type='LibrarySubjectGuide',id=self.subject_id)
        if brains:
            return brains[0]
         
         
class Response(WebResponseObject):
    
    output = {}
    
    def __init__(self,context,request):
        WebResponseObject.__init__(self,context,request)
        self.output = {}
        
    def build(self,limits,guide,cache_data):
        trans = Transformer(self.context, self.request)
        self.output = trans.transform(limits,guide,cache_data)
         
    def toDict(self):
        return self.output
    
    def toXML(self):
        return structured.dict2xml(self.toDict(),roottag='subject',pretty=True)
    
    def toJSON(self):
        return simplejson.dumps(self.toDict())
    
    
class Transformer(object):
    """ This class will help guarantee that if data changes in the subject it will be controlled here.  """
    
    content = {}
    limits = None
    cache = None
    guide = None
    
    def __init__(self,context,request):
        self.context = context
        self.request = request
        self.content = {}
        self.limits = None
        self.cache = None
        self.guide = None
        
    
    def transform(self,limits,guide,cache):
        self.limits = limits
        self.guide = guide
        self.cache = cache.getCache()
    
        self.additionl_information()
        self.transform_databases()
        self.transform_emc()
        self.transform_archives()
        self.transform_government()
        self.transform_news()
        self.transform_voyager()
        self.transform_films()
        
        return self.content
        
    
    def additionl_information(self):
        self.content['information'] = {'title' : self.guide.Title(),
                                       'url' : self.guide.absolute_url()}
        

    def transform_films(self):
        try:
            film = self.guide.getNextFilm()
            url = self._get_url(0,'http://digital.films.com/PortalPlaylists.aspx?aid=3068&xtid=' + film['id'])
            
            self.content['films_on_demand_heading'] = {'url' : self.guide.getProxiedFilmsOnDemandMoreLink(),
                                                       'title' : 'Films on Demand'}
            
            self.content['films_on_demand_link'] = {'title' : film['Title'],
                                                    'url' : url,
                                                    'image' : 'http://digital.films.com/Common/FMGimages/' + film['id'] + '_full.jpg',
                                                    }
        except Exception as e:
            print str(e)
            self.content['films_on_demand_heading'] = ""
            self.content['films_on_demand_link'] = ""
        

    def transform_news(self):
        
        try:
            self.content['news_heading'] = {'title':'News',
                                            'url': self.portal.absolute_url() + '/news/topics/' +self.guide.getNewsTopic(),}
            
            self.content['news_links'] = []
            timespan = getToolByName(self.context, 'portal_properties').get('site_properties').getProperty('news_limit_days',90)
            from_start = DateTime() - timespan
            brains = getToolByName(self.context,'portal_catalog').searchResults(portal_type="WeblogEntry", 
                                                                                Subject=self.guide.getNewsTopic(),
                                                                                sort_on='created', 
                                                                                sort_order='descending',
                                                                                review_state='published',
                                                                                created={'query':(from_start,DateTime('2045-11-19 11:59:00')),
                                                                                         'range': 'min:max'}
                                                                                )[0:self.limits['news']]
            for brain in brains:
                self.content['news_links'].append({'title':toAscii(brain.Title),
                                                   'description':toAscii(brain.Description),
                                                   'url':brain.getURL(),})
        except:
            self.content['news_heading'] = ""
            self.content['news_links'] = []


    def transform_emc(self):
        try:
            self.content['emc_heading'] = {'title' : 'K-12 Education Materials',
                                           'description' : 'Education Materials Center',
                                           'url' : self.guide.getEMCMoreContent(),}
            self.content['emc_links'] = []
            links = self.guide.getEMCListContent()[0:self.limits['emc']]
            for link in links:
                self.content['emc_links'].append({'title' : toAscii(link['name']),
                                                  'description' : toAscii(link['Description']),
                                                  'url' : toAscii(link['url']),})
        except:
            self.content['emc_heading'] = ""
            self.content['emc_links'] = []  
            
    def transform_archives(self):
        try:
            self.content['archives_heading'] = {'title' : 'Archives',
                                                          'description' : '',
                                                          'url' : self.guide.getArchivesMoreContent(),}
            self.content['archives_links'] = []
            links = self.guide.getArchivesListContent()[0:self.limits['archives']]
            for link in links:
                self.content['archives_links'].append({'title' : toAscii(link['name']),
                                                         'description' : toAscii(link['Description']),
                                                         'url' : toAscii(link['url']),})
        except:
            self.content['archives_heading'] = ""
            self.content['archives_links'] = [] 
            
    def transform_government(self):
        try:
            self.content['government_information_heading'] = {'title' : 'Government Information',
                                                              'description' : '',
                                                              'url' : self.guide.getGovernmentMoreContent(),}
            self.content['government_information_links'] = []
            links = self.guide.getGovernmentListContent()[0:self.limits['government']]
            for link in links:
                self.content['government_information_links'].append({'title' : toAscii(link['name']),
                                                                     'description' : toAscii(link['Description']),
                                                                     'url' : toAscii(link['url']),})
        except:
            self.content['government_information_heading'] = ""
            self.content['government_information_links'] = [] 
            
    def transform_databases(self):
        self.content['research_databases_heading'] = {'title':'Research Databases',
                                                      'url':self.guide.absolute_url() + '/databases'}
        self.content['journal_links'] = []
        self.content['books_links'] = []
        self.content['primary_sources_links'] = []
        self.content['reference_background_heading'] = {'title':'Reference & Background',
                                                        'url':self.guide.absolute_url() + '/background'}
        self.content['reference_background_links'] = []
        self.content['campus_resources_heading'] = {'title':'Campus Resources',
                                                    'url':self.guide.absolute_url() + '/campus-resources'}
        self.content['campus_resources_links'] = []
        self.content['featured_database'] = []
        
        results = sorted(self.cache['departmentsRef'],key=itemgetter('subsection','index'))
        results = filter(lambda x: x['exclude_from_guides'] == 0 , results)
        reference = filter(lambda x: x['section'] == 1 , results)
        books = filter(lambda x: x['section'] == 2 , results)
        research = filter(lambda x: x['section'] == 3 , results)
        primary = filter(lambda x: x['section'] == 4 , results)
        campus = filter(lambda x: x['section'] == 5 , results)
        featured = research[3:99] + books[1:99] + primary[1:99]
        featured_all = research + books + primary + reference
        
        self._db_add(research[0:self.limits['journals']],'journal_links')
        self._db_add(books[0:self.limits['books']],'books_links')
        self._db_add(primary[0:self.limits['primary']],'primary_sources_links')
        self._db_add(reference[0:self.limits['reference']],'reference_background_links')
        self._db_add(campus[0:self.limits['campus_resources']],'campus_resources_links')
        if featured:
            self._db_add([featured[(DateTime().day() % len(featured))]],'featured_database')
        else:
            self._db_add([featured_all[(DateTime().day() % len(featured_all))]],'featured_database')
            
            
    def _db_add(self,results,name):
        for db in results:
            try:
               self.content[name].append({'full_text' : self._safe(db,'is_some_full_text'),
                                                        'description' : self._safe(db,'description'),
                                                        'db_description' : self._safe(db,'db_description'),
                                                        'title' : self._safe(db,'title'),
                                                        'url' : self._get_url(self._safe(db,'is_omit_proxy'),self._safe(db,'url')),
                                                        'trial_message' : self._safe(db,'trial_message'),
                                                        'warning_message' : self._safe(db,'warning_message'),
                                                        'subsection' : self._safe(db,'subsection'),
                                                        'section' : self._safe(db,'section'),
                                                        'index' : self._safe(db,'index'),
                                                     })
            except:
                pass
            
        
    def transform_voyager(self):
        try:
            self.content['voyager_heading'] = {'title' : self.cache['callrange_description'],
                                               'url' : 'http://oshlib.wisconsin.edu/vwebv/search?searchArg=' 
                                                        + self.cache['callrange'] +
                                                       '&searchCode=CALL&searchType=1&sortBy=PUB_DATE_DESC'}
            self.content['voyager_links'] = []
            books = self.cache['voyager'][0:self.limits['voyager']]
            for book in books:
                self.content['voyager_links'].append({'isbn' : self._safe(book,'isbn'),
                                                'issn' : self._safe(book,'issn'),
                                                'title' : self._safe(book,'title_clean'),
                                                'author' : self._safe(book,'author'),
                                                'bibId' : self._safe(book,'bibId'),
                                                'location' : self._safe(book,'location'),
                                                'itemCount' : self._safe(book,'itemCount'),
                                                })
        except:
            self.content['voyager_heading'] = ""
            self.content['voyager_links'] = []
        
        
    def _safe(self,d,k):
        try: return d[k]
        except: return ''
    
    def _get_url(self,omit,url):
        proxy = getToolByName(self.context,'portal_properties').get('external_resources').getProperty('proxy_server_url','')
        if bool(omit): return url
        return proxy + url
     
    @property
    def portal(self):
        return getToolByName(self.context, 'portal_url').getPortalObject()
     
        
    
