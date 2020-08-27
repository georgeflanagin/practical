# -*- coding: utf-8 -*-
""" A few useful time/date functions for logging. """

# Added for Python 3.5+
import typing
from typing import *

import datetime
import time


# Credits
__author__ = 'George Flanagin'
__copyright__ = 'Copyright 2020, University of Richmond'
__credits__ = None
__version__ = '0.1'
__maintainer__ = 'George Flanagin'
__email__ = 'me@georgeflanagin.com'
__status__ = 'Prototype'

__license__ = 'MIT'

###
# C
###

# Some point in the distant past, namely 14 May 2014
def crontuple_of(t:Any=None) -> datetime.datetime:
    """
    Return t (or "now") as a datetime object. t should be in whole 
    minutes.
    """
    global arbitrarily_long_ago

    if t is None:
        moment = datetime.datetime.now()

    # This branch allows us to distinguish between minutes and seconds of the epoch.
    elif isinstance(t, (int, float)):
        t = -t*60 if t < 0 else t
        moment = datetime.datetime.fromtimestamp(t) 

    # Maybe the caller has already converted?
    elif isinstance(t, datetime.datetime):
        moment = t

    # Or perhaps the caller did not know what he was doing?
    else:
        raise Exception(f'bad arg type {type(t)} to crontuple_of()')

    # Get us the crontab relevant parts.
    return datetime.datetime(*moment.timetuple()[:6])


###
# I
###

def iso_time(seconds:int=None) -> str:
    if seconds is None: seconds = time.time()
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(seconds))


def iso_seconds(timestring:str=None) -> int:
    if timestring is None: timestring = iso_time()
    dt = datetime.datetime.strptime(timestring, '%Y-%m-%d %H:%M:%S')
    return int(dt.strftime("%s"))

###
# N
###

def now_as_seconds() -> int:
    return time.clock_gettime(0)


def now_as_string() -> str:
    """ Return full timestamp for printing. """
    return datetime.datetime.now().isoformat()[:21].replace('T',' ')


