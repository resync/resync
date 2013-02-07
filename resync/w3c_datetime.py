"""Write and parse W3C datetime

Each web resource is identified by a URI and may optionally have
other metadata such as timestamp, size, md5. The lastmod property
provides ISO8601 format string access to the timestamp.

The timestamp is assumed to be stored in UTC.
"""

import time
from calendar import timegm
from datetime import datetime
from dateutil import parser as dateutil_parser
import re

def datetime_to_str(dt='now'):
    """The Last-Modified data in ISO8601 syntax, Z notation

    The lastmod is stored as unix timestamp which is already
    in UTC. At preesent this code will return 6 decimal digits
    if any fraction of a second is given. It would perhaps be 
    better to return only the number of decimal digits necessary,
    up to a resultion of 1 microsecond.
    
    Special cases:
    - Returns datetime str for now if no parameter given.
    - Returns None if None is supplied.
    """
    if (dt is None):
        return None
    elif (dt == 'now'):
        dt = time.time()
    return datetime.utcfromtimestamp(dt).isoformat() + 'Z'

def str_to_datetime(s):
    """Set timestamp from an W3C Datetime Last-Modified value

    The sitemaps.org specification says that <lastmod> values
    must comply with the W3C Datetime format 
    (http://www.w3.org/TR/NOTE-datetime). This is a restricted
    subset of ISO8601. In particular, all forms that include a 
    time must include a timezone indication so there is no
    notion of local time (which would be tricky on the web). The
    forms allowed are:

        Year:
          YYYY (eg 1997)
        Year and month:
          YYYY-MM (eg 1997-07)
        Complete date:
          YYYY-MM-DD (eg 1997-07-16)
        Complete date plus hours and minutes:
          YYYY-MM-DDThh:mmTZD (eg 1997-07-16T19:20+01:00)
        Complete date plus hours, minutes and seconds:
          YYYY-MM-DDThh:mm:ssTZD (eg 1997-07-16T19:20:30+01:00)
        Complete date plus hours, minutes, seconds and a decimal fraction 
        of a second
          YYYY-MM-DDThh:mm:ss.sTZD (eg 1997-07-16T19:20:30.45+01:00)
        where:
          TZD  = time zone designator (Z or +hh:mm or -hh:mm)

    We do not anticipate the YYYY and YYYY-MM forms being used but
    interpret them as YYYY-01-01 and YYYY-MM-01 respectively. All
    dates are interpreted as having time 00:00:00.0 UTC.

    Datetimes not specified to the level of seconds are intepreted
    as 00.0 seconds.
    """
    t = None
    if (s is None):
        return(t)
    if (s == ''):
        raise ValueError('Attempt to set empty datetime')
    # Make a date into a full datetime
    m = re.match(r"\d\d\d\d(\-\d\d(\-\d\d)?)?$",s)
    if (m is not None):
        if (m.group(1) is None):
            s += '-01-01'
        elif (m.group(2) is None):
            s += '-01'
        s += 'T00:00:00Z'
    # Now have datetime with timezone info
    m = re.match(r"(.*\d{2}:\d{2}:\d{2})(\.\d+)([^\d].*)?$",s)
    # Chop out fractional seconds
    fractional_seconds = 0
    if (m is not None):
        s = m.group(1)
        if (m.group(3) is not None):
            s += m.group(3)
        fractional_seconds = float(m.group(2))
    # Now check that only allowed formats supplied (the parse
    # function is rather lax)
    m = re.match(r"\d\d\d\d\-\d\d\-\d\dT\d\d:\d\d(:\d\d)?(Z|[+-]\d\d:\d\d)$",s)
    if (m is None):
        raise ValueError("Bad datetime format (%s)" % s)
    dt = dateutil_parser.parse(s)
    # timetuple ignores timezone information
    #offset_seconds = dt.tzinfo.utcoffset(0).total_seconds() #only >=2.7
    offset = dt.tzinfo.utcoffset(0)
    offset_seconds = (offset.seconds + offset.days * 24 * 3600)
    return( timegm(dt.timetuple()) + offset_seconds + fractional_seconds )
