from Products.CMFCore.utils import getToolByName

default_profile = 'profile-uwosh.library.ws:default'

def upgrade(upgrade_product,version):
    """ Decorator for updating the QuickInstaller of a upgrade """
    def wrap_func(fn):
        def wrap_func_args(context,*args):
            p = getToolByName(context,'portal_quickinstaller').get(upgrade_product)
            setattr(p,'installedversion',version)
            return fn(context,*args)
        return wrap_func_args
    return wrap_func


def upgrade_init(context):
    """ Warning """
    print "<<< WARNING >>>"

def upgrade_no_change(context):
    """ Default, nothing changes """


@upgrade('uwosh.library.ws','0.0.3')
def upgrade_to_0_0_3(context):
    print "Upgrading"
    
@upgrade('uwosh.library.ws','0.0.4')
def upgrade_to_0_0_4(context):
    print "Upgrading"
    
@upgrade('uwosh.library.ws','0.0.5')
def upgrade_to_0_0_5(context):
    print "Upgrading"
      
@upgrade('uwosh.library.ws','0.0.6')
def upgrade_to_0_0_6(context):
    print "Upgrading"
      
@upgrade('uwosh.library.ws','0.0.7')
def upgrade_to_0_0_7(context):
    print "Upgrading"
       
@upgrade('uwosh.library.ws','0.0.8')
def upgrade_to_0_0_8(context):
    print "Upgrading"
  
@upgrade('uwosh.library.ws','0.0.9')
def upgrade_to_0_0_9(context):
    print "Upgrading"
    
@upgrade('uwosh.library.ws','0.1.0')
def upgrade_to_0_1_0(context):
    print "Upgrading"
    
@upgrade('uwosh.library.ws','0.1.1')
def upgrade_to_0_1_1(context):
    print "Upgrading"
    
@upgrade('uwosh.library.ws','0.1.2')
def upgrade_to_0_1_2(context):
    print "Upgrading"
    
@upgrade('uwosh.library.ws','0.1.3')
def upgrade_to_0_1_3(context):
    print "Upgrading"
    
@upgrade('uwosh.library.ws','0.1.4')
def upgrade_to_0_1_4(context):
    print "Upgrading"
    
@upgrade('uwosh.library.ws','0.1.5')
def upgrade_to_0_1_5(context):
    print "Upgrading"
       
@upgrade('uwosh.library.ws','0.1.6')
def upgrade_to_0_1_6(context):
    print "Upgrading"   
       
@upgrade('uwosh.library.ws','0.1.7')
def upgrade_to_0_1_7(context):
    print "Upgrading"        
       
@upgrade('uwosh.library.ws','0.1.8')
def upgrade_to_0_1_8(context):
    print "Upgrading"   
       
@upgrade('uwosh.library.ws','0.1.9')
def upgrade_to_0_1_9(context):
    print "Upgrading"   
       
@upgrade('uwosh.library.ws','0.1.10')
def upgrade_to_0_1_10(context):
    print "Upgrading"   
       
@upgrade('uwosh.library.ws','0.1.11')
def upgrade_to_0_1_11(context):
    print "Upgrading"   
       
@upgrade('uwosh.library.ws','0.1.12')
def upgrade_to_0_1_12(context):
    print "Upgrading"   
       
@upgrade('uwosh.library.ws','0.1.13')
def upgrade_to_0_1_13(context):
    print "Upgrading"   
       
@upgrade('uwosh.library.ws','0.1.14')
def upgrade_to_0_1_14(context):
    print "Upgrading"   
       
@upgrade('uwosh.library.ws','0.1.15')
def upgrade_to_0_1_15(context):
    print "Upgrading"   
       
@upgrade('uwosh.library.ws','0.1.16')
def upgrade_to_0_1_16(context):
    print "Upgrading"   
       
@upgrade('uwosh.library.ws','0.1.17')
def upgrade_to_0_1_17(context):
    print "Upgrading"   
       
@upgrade('uwosh.library.ws','0.1.18')
def upgrade_to_0_1_18(context):
    print "Upgrading"       
    
@upgrade('uwosh.library.ws','0.1.19')
def upgrade_to_0_1_19(context):
    print "Upgrading"       
       
@upgrade('uwosh.library.ws','0.1.20')
def upgrade_to_0_1_20(context):
    print "Upgrading"       
       
@upgrade('uwosh.library.ws','0.1.21')
def upgrade_to_0_1_21(context):
    print "Upgrading"       
       
                   
        
              
       
              
       
              
       
              
       
      
              
       
              
       
       
       