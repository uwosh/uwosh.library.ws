from zope.interface import implements
from Products.CMFCore.utils import getToolByName

from uwosh.library.ws.core.interfaces import IRegisteredService
from uwosh.library.ws.util import timeutil,security,solr
from uwosh.library.ws.services.v1.get_suggested_courses import CourseSuggestions

import urllib
import simplejson


class SiteSuggestion(CourseSuggestions):
    implements(IRegisteredService)


    def setup(self):
        CourseSuggestions.setup(self)
        self.grouplimit = security._security_strip_only_ints(self.request.form.get('group.limit','10'))
        self.groupoffset = security._security_strip_only_ints(self.request.form.get('group.offset','0'))

    def _build_query(self):
        return "q=" + self._query() \
                + self._additional_query_params() \
                + self._groupings()

    def _filter_query(self):
        return  urllib.quote('-(-') +  'term:' + self._get_current_term() + solr._and() + 'term:' + urllib.quote('[* TO *])') + \
                solr._and() + urllib.quote('(is_combined_course:0)')
    
    def _groupings(self):
        return "&group=true&group.field=type" \
             + "&group.limit=" + self.grouplimit \
             + "&group.offset=" + self.groupoffset