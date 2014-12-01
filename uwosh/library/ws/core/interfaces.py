from zope.interface import Interface,Attribute

    
class IRegisteredService(Interface):
    """ Mr. Marker """
    
class IWebService(Interface):
    """ Controller requirements """
    dependencies = Attribute("""List of Non-Installed Product Dependencies""")
    installed_dependencies = Attribute("""List of Installed Products Dependencies""")
    service_name = Attribute("""Name of Python File""")
    
class IWebResponse(Interface):
    """ Response requirements """
    
    def toXML(self):
        """ Return XML """

    def toJSON(self):
        """ Return JSON """
        
    def toDict(self):
        """ Return Python Dictionary """

class IWebResponse(Interface):
    """ Response requirements """
    
    def toXML(self):
        """ Return XML """

    def toJSON(self):
        """ Return JSON """
        
    def toDict(self):
        """ Return Python Dictionary """
    
    def toCustom(self):
        """ For unique custom responses """