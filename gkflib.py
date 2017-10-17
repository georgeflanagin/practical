# -*- coding: utf-8 -*-
import typing
from   typing import *


# Credits
__author__ =        'George Flanagin'
__copyright__ =     'Copyright 2005, 2015, 2016 George Flanagin'
__version__ =       '2.1'
__maintainer__ =    'George Flanagin'
__email__ =         'me@georgeflanagin.com'
__status__ =        'production'
__licence__ =       'http://www.gnu.org/licenses/gpl-3.0.en.html'

import base64
import bs4
import collections
from   datetime import datetime
import functools
import grp
import inspect
import multimap 
import numpy
import operator
import os
import pandas
import pwd
import random
import re
from   scipy.fftpack import fft
import shutil
import sys
from   textwrap import TextWrapper
import time
import traceback

"""
Some utility functions to help us debug the deep crashes
that I am so well known for creating inside programs with large
data structures. They really have nothing to do with Ishtar, and I
use them everywhere.
"""

START_TIME = time.time()

def positions(x_list:list) -> pandas.DataFrame:
    """
    Given a list of hashables, return a pandas DataFrame where the 
    column names are the distinct members of the list, and the
    values at the i-th row are /one/ if that hashable is present at
    i-th row. Otherwise, /zero/. 
    """
    x_set = set(x_list)
    binary_functions = pandas.DataFrame(0, 
            index=numpy.arange(len(x_list)), 
            columns=x_set)
    tombstone('created a dataframe that has shape ' + str(binary_functions.shape))

    for i_pos, x_item in enumerate(x_list):
        binary_functions[x_item][i_pos] = 1
    tombstone('all bits set')
    
    for _ in x_set:
        f = binary_functions[_]
        y = fft(f)
        print(_ + ' => ' + str(y))
    
    return binary_functions
 

def dump_exception(e: Exception,
        line: int=0,
        fcn: str=None,
        module: str=None) -> str:
    """ Tell us what we really [don't] want to know. """

    cf = inspect.stack()[1]
    f = cf[0]
    i = inspect.getframeinfo(f)

    line = str(i.lineno) if line == 0 else line
    module = i.filename if not module else module

    junk, exception_type = str(type(e)).split()
    exception_type = exception_type.strip("'>")

    msg = []
    msg.append("Caught @ line " + line + " in module " + module +
            ".\n" + str(e) + " :: raised by " + exception_type)
    # squeal(msg)
    msg.extend(formatted_stack_trace(True))
    return "\n".join(msg)


def emit(i:int) -> None:
    ELAPSED_TIME = str(round(time.time() - START_TIME, 4))
    print(" ".join(["(", ELAPSED_TIME, ")", str(i), "\r"]), end="")


def empty(o:object) -> bool:
    """
    Roughly equivalent to PHP's empty(), but goes farther. Oddly formed
    JSON constructions like {{}} and {[]} need to be considered empty.
    """
    if not o or not len(o): return True
    try:
        r = functools.reduce(operator.and_, [empty(oo) for oo in o])
    except:
        return False
    
    return r
        

def flip_dict(kv_mapping:dict) -> multimap.MutableMultiMap:
    """
    Take the input dictionary, reverse the kv pairs, and return
    the result in a multimap.
    """

    vk_mapping = multimap.MutableMultiMap()
    for k, v in kv_mapping.items():
        vk_mapping[str(v)] = k
    return vk_mapping


def formatted_stack_trace(as_string: bool = False) -> list:
    """
    Generate some easy to read, tabular output. By default, you get
    a list of lines, each of which represents an executed function
    call in reverse temporal order.
    """
    exc_type, exc_value, exc_traceback = sys.exc_info()
    this_trace = traceback.extract_tb(exc_traceback)
    r = []

    r.append("Stack trace" + "\n" + "-"*80)
    for _ in this_trace:
        r.append(", line ".join([str(_[0]), str(_[1])]) +
            ", fcn <" + str(_[2]) + ">, context=>> " + str(_[3]))
    r.append("="*30 + " End of Stack Trace " + "="*30)
    return ["\n".join(r)] if as_string else r


def ugroups(user:str='') -> List[int]:
    """
    user -- user name of interest.

    returns -- a list of gids associated with that user.
    """
    user = me() if not user else user
    groups = [g.gr_name for g in grp.getgrall() if user in g.gr_mem]
    gid = pwd.getpwnam(user).pw_gid
    groups.append(grp.getgrgid(gid).gr_name)

    return groups

    
def iso_time(seconds: int) -> str:
    """
    Prints an ISO formatted date/time string based on *local* time including
    the time zone, not UTC.
    """
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(seconds))


def listify(x:Any) -> list:
    """ change a single element into a list containing that element, but
    otherwise just leave it alone. """
    try:
        if not x: return []
    except NameError as e:
        return []
    if isinstance(x, list): return x
    return [x]


def me() -> tuple:
    """
    I am always forgetting just who I am.
    """
    my_uid = os.getuid()
    my_name = pwd.getpwuid(my_uid).pw_name
    return my_name, my_uid


def mkdir(s:str) -> None:
    try:
        os.mkdir(s, 0o700)
    except FileExistsError as e:
        pass


def nicely_display(s:str) -> bool:
    term_size = shutil.get_terminal_size()
    chunk = term_size.lines - 5
    s = s.split('\n')
    lines_displayed = 0
    for _ in s:
        print(_)
        lines_displayed = lines_displayed + 1
        if lines_displayed % chunk: continue
        try:
            input("Press <enter> to continue ..... ")
        except KeyboardInterrupt as e:
            return False
    return True


def now_as_seconds(nths:int = -1) -> int:
    """
    Returns the "epoch," also known as the number of seconds since
    the birth of Scott E. Lewis on 1 January 1970.
    """
    t = time.clock_gettime(0)
    return t if nths < 0 else round(t,nths)


def now_as_string(s:str = "T") -> str:
    """
    Return full timestamp, fixed width for printing, parsing, and readability:

    2007-02-07 @ 23:11:45
    """
    return datetime.now().isoformat()[:21].replace("T",s)


def polish(args:dict, doc:str) -> str:
    """
    You never know who is going to read these things, so let's allow
    for a little clean-up based on the arguments we were given.
    """
    new_doc = []
    sentence_ticker = 0

    for i in range(len(doc) - 1):
        new_doc.append(doc[i])
        # Might this be the end of a sentence?
        if doc[i] in ['.', '?', '!'] and doc[i+1] == ' ':
            sentence_ticker = sentence_ticker + 1
            if sentence_ticker >= random.gauss(args.pp, args.mu):
                new_doc.extend(['\n','\n'])
                sentence_ticker = 0

    wrapper = TextWrapper(width=args.width,
        expand_tabs = True, tabsize = 1,
        replace_whitespace = False,
        break_on_hyphens = True)

    return wrapper.fill(''.join(new_doc))


def q64(s, quote_type=1):
    """ Convert to Base64 before quoting.

    s -- a string to convert to Base64.
    returns: -- same thing as q()
    """
    return b"'" + encodebytes(s.encode('utf-8')) + b"'"


def q_like_post(s):
    """ Append a %

    s -- a string
    returns: -- s%
    """

    return q(s + "%")


def q_like_pre(s):
    """ append a %

    s -- a string
    returns: -- s%
    """

    return q("%" + s)


def q_like(s):
    """ Prepend and append a %

    s -- a string
    returns: -- %s%
    """
    return q("%" + s + "%")


def q(ins, quoteType=1):
    """A general purpose string quoter and Houdini (mainly for SQL)

    ins -- an input string
    quote_type -- an integer between 0 and 5. Meanings:
        0 : do nothing
        1 : ordinary single quotes.
        2 : ordinary double quotes.
        3 : Linux/UNIX backquotes.
        4 : PowerShell escape and quoting.
        5 : SQL99 escaping only.
    returns: -- some version of 's'.
    """

    quote = "'"
    if quoteType == 1:
        return quote + ins.replace("'", "''") + quote
    elif quoteType == 2:
        quote = '"'
        return quote + ins.replace('"', '\\"') + quote
    elif quoteType == 3:
        quote = '`'
        return quote + ins + quote
    elif quoteType == 4: # Powershell
        ins = re.sub('^', '^^', ins)
        ins = re.sub('&', '^&', ins)
        ins = re.sub('>', '^>', ins)
        ins = re.sub('<', '^<', ins)
        ins = re.sub('|', '^|', ins)
        ins = re.sub("'", "''", ins)
        return quote + ins + quote
    elif quoteType == 5: # SQL 99 .. quotes only.
        return quote + re.sub("'",  "''", ins) + quote
    else:
        pass
    return ins



def random_string(length:int=10, all_alpha:bool=True) -> str:
    s = base64.b64encode(os.urandom(length*2)).decode('utf-8')     
    t = ""
    for _ in s: 
        if not all_alpha:
            t = t + _
        elif _.isalpha():
            t = t + _
        else:
            pass 
     
    return t[:length]       
        

def scrub(s:str, args:object, scrubbing:int) -> str:
    """
    If there is no input or we are not scrubbing, bail out.
    """
    if not len(s) * scrubbing: return s

    subs = [ 
             (u'\u2014', "---")
            ,(u'\u2013', "--")
            ,(u'\u2012', '-')
            ,(u'\u2010', '-')
            ,(u'\u2011', '-')
            ,('[“”"]', "")
            ,('’', "'")   
            ,("''", "'")
            ,('…', '')
            ,('\r\n', '\n')]

    tombstone("Scrubbing " + str(len(s)) + " chars of input.")

    if scrubbing & 1:
        for _ in subs:
            original_len = len(s)
            s = re.sub(_[0], _[1], s)
            new_len = len(s)
            if _ == subs[-1]: continue

    if scrubbing & 2:
        tombstone("Removing SGML tags.")
        s = bs4.BeautifulSoup(s, 'lxml').get_text()

    if scrubbing & 4:
        tombstone("Scrubbing > 2, so flattening to ASCII")
        s = s.encode('ascii', 'ignore')
        tombstone("Smack! Flat ASCII remains.")

    tombstone("Scrubbed text is now " + str(len(s)) + " chars.")

    return s


def tombstone(args=None) -> int:
    """
    This is an augmented print() statement that has the advantage
    of always writing to "unit 2." In console programs, unit 2 is
    connected to the console, but in system daemons, unit 2 is
    connected to something appropriate like a logfile. Consequently,
    you can all tombstone("Hello world") without having to worry
    about the mode of function of your program at the time the
    function is called.
    """
    ELAPSED_TIME = time.time() - START_TIME
    a = [now_as_string(" @ ") + " :: (", str(round(ELAPSED_TIME,3)), ")(" + str(os.getpid()) + ")"]
    if args is None:
        args=formatted_stack_trace(True)
    if isinstance(args, list):
        for _ in args:
            a.append(str(_))
    else:
        a.append(str(args))
    sys.stderr.write(" ".join(a) + "\n")


def type_and_text(e:Exception) -> str:
    type_name = str(type(e)).split()[1][1:-2]
    text = str(e)
    return "object of type {} equal to {}".format(type_name, text)


