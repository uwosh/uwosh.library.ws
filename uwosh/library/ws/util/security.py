"""
Generic Security Utility Functions.
"""

import re

def _security_strip_only_ints(text):
    """ Strips everything but a through z and 0 though 9 also spaces and commas allowed """
    return re.sub('[^0-9]+', '', text).strip()

def _security_strip_allow_asterisk_ints(text):
    """ Strips everything but a through z and 0 though 9 also spaces and commas allowed """
    return re.sub('[^0-9\*]+', '', text).strip()


def _security_strip_all(text):
    """ Strips everything but a through z and 0 though 9 also spaces and commas allowed """
    return re.sub('[^A-Za-z0-9\s]+', '', text).strip()

def _security_strip_less(text):
    """ Strips everything but a through z and 0 though 9 also spaces and commas allowed """
    return re.sub('[^A-Za-z0-9,\s_-]+', '', text).strip()

def _security_strip_callback(text):
    """ Strips everything but a through z and 0 though 9 also spaces and commas allowed """
    return re.sub('[^A-Za-z0-9?]+', '', text).strip()


def _security_component(component):
    ALLOWED_SOLR_COMPONENTS = ["select","suggest","spell","boosted"]
    if component in ALLOWED_SOLR_COMPONENTS:
        return True
    return False