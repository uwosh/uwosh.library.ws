from uwosh.library.ws.util import timeutil
import urllib

def _and():
    return "%20AND%20"

def _or():
    return "%20OR%20"

def _ws():
    return "%20"

def _quotes(contents,enforce_content_quote=True):
    if enforce_content_quote:
        return "%22" + urllib.quote(contents) + "%22"
    return "%22" + contents + "%22"

def _brackets(contents):
    return "%28" + contents + "%29"

def _brackets(contents):
    return "%28" + contents + "%29"