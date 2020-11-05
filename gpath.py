# -*- coding: utf-8 -*-
""" Useful functions to manipulate path names and expand env vars. """

# Added for Python 3.5+
import typing
from typing import *

import fnmatch
import os
import sys

from tombstone import tombstone

# Credits
__author__ = 'George Flanagin'
__copyright__ = 'Copyright 2020'
__credits__ = None
__version__ = '0.1'
__maintainer__ = 'George Flanagin'
__email__ = 'me@georgeflanagin.com'
__status__ = 'Prototype'

__license__ = 'MIT'


###
# A
###

def all_files_in(s:str) -> str:
    """
    A generator to cough up the full file names for every
    file in a directory.
    """
    s = expandall(s)
    for c, d, files in os.walk(s):
        for f in files:
            yield os.path.join(c, f)


def all_files_like(s:str) -> str:
    """
    Returns a list of all files that match the argument
    """
    s = expandall(s)
    return [ f for f in all_files_in(os.path.dirname(s))
        if fnmatch.fnmatch(os.path.basename(f), os.path.basename(s)) ]

####
# B
####

def build_file_list(f:str) -> List[str]:
    """
    Resolve all the symbolic names that might be embedded in the filespec,
    and return a list of all the files that match it **at the time the
    function is called.**

    f -- a file name "spec."

    returns -- a possibly empty list of file names.
    """
    return glob.glob(file_name_filter(f))
    

####
# D
####

def date_filter(filename:str, *, 
    year:str="YYYY", 
    year_contracted:str="Y?",
    month:str="MM", 
    month_contracted:str="M?",
    month_name:str="bbb",
    week_number:str="WW",
    day:str="DD",
    day_contracted:str="D?",
    hour:str="hh",
    minute:str="mm",
    second:str="ss",
    date_offset:int=0) -> str:
    """
    Remove placeholders from a filename and use today's date (with
    an optional offset).

    NOTE: all the placeholders are non-numeric, and all the replacements 
        are digits. Thus the function works because the two are disjoint
        sets. Break that .. and the function doesn't work.
    """
    if not isinstance(filename, str): return filename

    #Return unmodified file name if there isn't at least one set of format delimiters "{" and "}"
    if not re.match(".*?\{.*?\}.*?", filename):
        return filename

    today = crontuple_now() + datetime.timedelta(days=date_offset)

    # And now ... for Petrarch's Sonnet 47
    this_year = str(today.year)
    this_year_contracted = this_year[2:]
    this_month_name = calendar.month_abbr[today.month].upper()
    this_month = str('%02d' % today.month)
    this_month_contracted = this_month if this_month[0] == '1' else this_month[1]
    this_week = str('%02d' % datetime.date.today().isocalendar()[1])
    this_day =  str('%02d' % today.day)
    this_day_contracted = this_day if this_day[0] != '0' else this_day[1]
    this_hour = str('%02d' % today.hour)
    this_minute = str('%02d' % today.minute)
    this_second = str('%02d' % today.second)

    #Initialize new_filename so we can use it later
    new_filename = filename
    
    #Iterate through each pair of "{" and "}" in filename and replace placeholder values
    #with date literals
    for date_exp in [ m.group(0) for m in re.finditer("\{.*?\}",filename) ]:
        #Start with the sliced substring excluding the "{" and "}" charactes and
        #begin replacing pattern date strings with literals
        new_name = date_exp[1:-1].replace(year, this_year)
        new_name = new_name.replace(year_contracted, this_year_contracted)
        new_name = new_name.replace(month_name, this_month_name)
        new_name = new_name.replace(month, this_month)
        new_name = new_name.replace(month_contracted, this_month_contracted)
        new_name = new_name.replace(week_number, this_week)
        new_name = new_name.replace(day, this_day)
        new_name = new_name.replace(day_contracted, this_day_contracted)
        new_name = new_name.replace(hour, this_hour)
        new_name = new_name.replace(minute, this_minute)
        new_name = new_name.replace(second, this_second)
        #Now replace the original string including the "{" and "}" with the translated string
        new_filename = new_filename.replace(date_exp,new_name)

    #Return result and strip { and } format containers
    return new_filename


####
# E
####

def expandall(s:str) -> str:
    """
    Expand all the user vars into an absolute path name. If the 
    argument happens to be None, it is OK.
    """
    return "" if s is None else os.path.abspath(os.path.expandvars(os.path.expanduser(s)))
    

####
# F
####

def file_name_filter(filename:str, env:str='.') -> str:
    """
    Modify the filename in the following ways, and in this order:

    1. Apply the date filtering.
    2. Expand any environment variables or directory shorthand.
    3. Join the environment if the name does not start with an
        absolute path.
    """
    filename = expandall(date_filter(filename))

    if not filename.startswith(os.sep): 
        filename = os.path.join(env, filename)

    return filename


####
# M
####

def make_dir_or_die(dirname:str, mode:int=0o700) -> None:
    """
    Do our best to make the given directory (and any required 
    directories upstream). If we cannot, then die trying.
    """
    dirname = expandall(dirname)

    try:
        os.makedirs(dirname, mode)

    except FileExistsError as e:
        # It's already there!
        if not os.path.isdir(dirname): 
            tombstone(f'{dirname} is not a directory.')
            sys.exit(os.EX_IOERR)

    except PermissionError as e:
        # This is bad.
        tombstone("Permissions error creating/using " + dirname)
        sys.exit(os.EX_NOPERM)

    if (os.stat(dirname).st_mode & 0o777) < mode:
        tombstone("Permissions on " + dirname + " less than requested.")


####
# P
####

def path_join(dir_part:str, file_part:str) -> str:
    """
    Like os.path.join(), but trapping the None-s and replacing
    them with appropriate structures.
    """
    if dir_part is None:
        dir_part = ""

    if file_part is None:
        file_part = ""

    dir_part = os.path.expandvars(os.path.expanduser(dir_part))
    file_part = os.path.expandvars(os.path.expanduser(file_part))
    return os.path.join(dir_part, file_part)
 

