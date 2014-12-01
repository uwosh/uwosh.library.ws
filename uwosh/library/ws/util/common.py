"""
Common Utility Function used by almost all web services.
"""

def has_dependencies(depends):
    """ Checks if module exists."""
    try:
        for d in depends:
            __import__(d)
        return True
    except:
        return False
    
def get_ip(request):
    """  Extract the client IP address from the HTTP request in proxy compatible way.

    @return: IP address as a string or None if not available
    """
    if "HTTP_X_FORWARDED_FOR" in request.environ:
        # Virtual host
        ip = request.environ["HTTP_X_FORWARDED_FOR"]
    elif "HTTP_HOST" in request.environ:
        # Non-virtualhost
        ip = request.environ["REMOTE_ADDR"]
    else:
        # Unit test code?
        ip = None

    return ip