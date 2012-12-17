import datetime
import re

TYPE_CONVERSIONS = (
    (re.compile('^[+-]?\d+$'), int),
    (re.compile('^[+-]?\d*\.\d+$'), float),
    (re.compile('^[+-]?\d*\.\d+[eE][+-]?\d+$'), float),
    (re.compile('^\d{4}-\d{1,2}-\d{1,2} \d{1,2}:\d{1,2}'), 
     lambda x: datetime.datetime.strptime(x, '%Y-%m-%d %H:%M')),
    (re.compile('^\d{4}-\d{1,2}-\d{1,2}'), 
     lambda x: datetime.datetime.strptime(x, '%Y-%m-%d')),
    (re.compile('^(true|false)$', re.I), 
     lambda x: {'true': True, 'false': False}[x.lower()]),
    (re.compile('^None$', re.I), lambda x: None),
    (re.compile('^.*$'), lambda x: x),
    )


def convert(s):
    """Attempts to convert `s` into a native Python type
    """
    for rxp, fn in TYPE_CONVERSIONS:
        m = rxp.match(s)
        if m:
            return fn(s)
    return s

