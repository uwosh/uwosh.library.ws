"""
Generic Time Utility Functions.
"""

from DateTime import DateTime
from time import time as fromtime, mktime
import datetime
import time

def isWithinHours(hours):
    """ 
    Is it within start and end of the Hours Object.
    @param hours: is Hours() object 
    @param now: (optional) overrides datetime.datetime.now()
    """
    now = datetime.datetime.now()
    now = mktime(now.timetuple())
    start = mktime( datetime.datetime.strptime(hours['start'],'%Y-%m-%d %H:%M').timetuple())
    end = mktime( datetime.datetime.strptime(hours['end'],'%Y-%m-%d %H:%M').timetuple())

    
    if now < end and now > start: 
        return True
    return False

def determineOpenStatus(yesterday,today):
    check = isWithinHours(yesterday)
    if check:
        return {'times':yesterday,'is_open':check}
    return {'times':today,'is_open':isWithinHours(today)}
    
    
def offsets():
    try:
        timezone = str(time.tzname[0])
    except Exception:
        timezone = str(time.tzname)
        
    return {'seconds':str(DateTime().tzoffset()),
            'is_daylight_savings':str(time.daylight),
            'timezone':timezone
           } 
    
def removeTrailingZero(time):
    return time.split('.')[0]
    
def removeLeadingZero(time):
    if time[0] == '0':
        return time[1:]
    return time
    
def tz_hour_offset(dt):
    tz = (dt.tzoffset() / 60) / 60
    return str(tz)

def gmt_offset(dt):
    return "GMT" + tz_hour_offset(dt)

def adapter_enforce_gmt(dt=None):
    if dt != None:
        dt = DateTime(dt)
        t = dt.timeTime()
        gmt_date = DateTime(t,gmt_offset(dt))
        return gmt_date
    return DateTime()
    

def _translate_from_term_code(term):
    term = str(term).lower().strip()
    try:
        year = int(term[0:3]) + 1945
        offset = int(term[3])
        season = ""
        
        if offset == 0:
            season = "Fall"
        elif offset == 3:
            season = "Winter"
        elif offset == 5:
            season = "Spring"
        elif offset == 8:
            season = "Summer"
            
        if offset >= 5:
            year += 1
        
        return season + " " + str(year)
    except:
        return "UNKNOWN"

def _translate_to_term_code(term):
    return "Not implemented"


