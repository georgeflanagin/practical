# -*- coding: utf-8 -*-

import os
import sys

""" Generic, bare functions, not a part of any object or service. """
import argparse
import atexit
import base64
import bs4
import calendar
import croniter
import datetime
import functools
from   functools import reduce
import getpass
import inspect
import json
import multimap
import operator
try:
    import paramiko
except ImportError as e:
    print('gkflib requires paramiko.')
    sys.exit(os.EX_SOFTWARE)

import pandas
import pprint as pp
import pwd
import re
import resource
import shlex
import shutil
import signal
import socket
import string
try:
    import sortedcontainers
except ImportError as e:
    print('gkflib requires sortedcontainers.')
    sys.exit(os.EX_SOFTWARE)

import subprocess
import time
import traceback

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

RED='\033[31m'
YELLOW='\033[33m'
BLUE='\033[34m'
REVERT='\033[0m'
REVERSE = "\033[7m"


START_TIME = time.time()

class SloppyDict: pass

def blind(s:str) -> str:
    global REVERSE
    global REVERT
    return " " + REVERSE + s + REVERT + " "


def tobytes(s:str) -> bytes:
    return bytes(s.encode('utf-8'))


def cron_to_str(cron:tuple) -> dict:
    """
    Return an English explanation of a crontab entry.
    """

    if len(cron) != 5: return "This does not appear to be a cron schedule"

    keynames=["a_minutes","b_hours","c_days","d_months","e_dows"]
    explanation = dict.fromkeys(keynames)

    for time_unit, sched in zip(keynames, cron):

        # This is self explanatory, right?
        if sched == star:
            explanation[time_unit] = 'all ' + time_unit[2:]
            continue

        # Test for the exact value (often the case for min, hr, dow)
        valid = sorted(list(sched))
        if len(valid) == 1:
            explanation[time_unit] = time_unit[2:] + " " + str(valid[0])
            continue

        if valid == list(range(valid[0], valid[-1]+1)):
            explanation[time_unit] = (time_unit[2:] + " " + str(valid[0]) +
                " to " + str(valid[-1]))
            continue

        # Test for every fifth minute, third month, etc. Maybe some
        # explanation is required ... zip() stops when the first target
        # of the pair is empty. We subtract the neighbors (remember, it
        # already sorted), and make a set. If the set only has one
        # element, then the neighbors are equally spaced apart.

        diffs = set([ j - i for i, j in zip(valid, valid[1:]) ])
        if len(diffs) == 1:
            explanation[time_unit] = (time_unit[2:] +
                " every " + str(diffs.pop()) +
                " from " + str(valid[0]) + " to " + str(valid[-1]))
            continue

        # TODO: tune this up a bit.

        explanation[time_unit] = time_unit[2:] + " in " + str(valid)

    return explanation


def crontuple_now():
    """
    Return /now/ as a cron-style tuple.
    """

    return datetime.datetime(*datetime.datetime.now().timetuple()[:6])


def dump_cmdline(args:argparse.ArgumentParser, return_it:bool=False) -> str:
    """
    Print the command line arguments as they would have been if the user
    had specified every possible one (including optionals and defaults).
    """

    if not return_it: print("")
    opt_string = ""
    for _ in sorted(vars(args).items()):
        opt_string += " --"+ _[0].replace("_","-") + " " + str(_[1])
    if not return_it: print(opt_string + "\n")

    return opt_string if return_it else ""


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
        

def flip_dict(kv_mapping:dict) -> Union[dict, multimap.MutableMultiMap]:
    """
    Take the input dictionary, reverse the kv pairs, and return
    the result in a multimap.

    returns -- the flipped dict as a dict if there are no duplicate
        values, otherwise as a multimap.MutableMultiMap.
    """
    vk_mapping = ( {}
        if len(set(kv_mapping.values())) == len(list(kv_mapping.values()))
        else multimap.MutableMultiMap() )

    for k, v in kv_mapping.items():
        vk_mapping[str(v)] = k

    return vk_mapping


available_cpus = len(os.sched_getaffinity(0))
def fork_ok() -> bool:
    return os.getloadavg()[0] < available_cpus and memfree() > 0.5


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


def fcn_signature(*args) -> str:
    """
    provide a string for debugging that resembles a function's actual
    arguments; i.e., how it was called. The zero-th element of args
    should be the name of the function, and then the arguments follow.
    """
    if not args: return "()"

    return args[0] + "(" + (", ".join([str(_) for _ in args[1:]])) + ")"


####
# G
####

def get_ssh_host_info(host_name:str=None, config_file:str=None) -> list:
    """
    Utility function to get all the ssh config info, or just that
    for one host.

    host_name -- if given, it should be something that matches an entry
        in the ssh config file that gets parsed.
    config_file -- if given (at it usually is not) the usual default
        config file is used.
    """

    if config_file is None: config_file = os.path.expanduser("~") + "/.ssh/config"

    try:
        ssh_conf = paramiko.SSHConfig()
        ssh_conf.parse(open(config_file))
    except:
        raise Exception("could not understand ssh config file " + config_file) from None

    if not host_name: return ssh_conf
    if host_name == 'all': return ssh_conf.get_hostnames()

    return None if host_name not in ssh_conf.get_hostnames() else ssh_conf.lookup(host_name)


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
    except:
        return []
    else:
        return x if isinstance(x, list) else [x]


def me() -> tuple:
    """
    I am always forgetting just who I am.
    """
    my_uid = os.getuid()
    my_name = pwd.getpwuid(my_uid).pw_name
    return my_name, my_uid


def loc_splitter(s: str) -> tuple:
    """
    Allow us to deal with remote and local and files.
    """

    parts = s.split(":")
    if len(parts) < 2: return None, None, s

    lpart = parts[0]
    frontmatter = lpart.split("@")
    if len(frontmatter) < 2:
        return me(), frontmatter[0], parts[1]
    else:
        return frontmatter[0], frontmatter[1], parts[1]


####
# M
####

def make_dir_or_die(dirname:str, mode=None):
    """
    Do our best to make the given directory (and any required
    directories upstream). If we cannot, then die trying.
    """

    if not mode: mode=0o700

    try:
        os.makedirs(dirname, mode)

    except FileExistsError as e:
        # It's already there.
        pass

    except PermissionError as e:
        # This is bad.

        tombstone()
        tombstone("Permissions error creating/using " + dirname)
        sys.exit(os.EX_NOPERM)

    except NotADirectoryError as e:
        tombstone()
        tombstone(dirname + " exists, but it is not a directory")
        sys.exit(os.EX_CANTCREAT)

    except Exception as e:
        tombstone()
        tombstone(type_and_text(e))
        sys.exit(os.EX_IOERR)

    if (os.stat(dirname).st_mode & 0o777) >= mode:
        return
    else:
        tombstone("{} created. Permissions less than requested.".format(dirname))


total_mem = 0
def memfree() -> float:
    global total_mem
    """
    return the percentage of free memory.
    """
    with open('/proc/meminfo') as mf:
        lines = mf.read().split("\n")
        avail = int(lines[2].split()[1])
        try:
            return avail/total_mem
        except:
            total_mem = int(lines[0].split()[1])
            return avail/total_mem    


def mkdir(s:str) -> bool:
    
    try:
        os.mkdir(s, 0o700)
    except FileExistsError as e:
        pass
    except Exception as e:
        return False

    return True  


def mymem() -> SloppyDict:
    info = resource.getrusage(resource.RUSAGE_SELF)
    return SloppyDict({k:getattr(info, k) for k in dir(info) if k.startswith("ru") })


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
    return datetime.datetime.now().isoformat()[:21].replace("T",s)


###
# O
###

class objectify(dict):
    """
    Make a dict into an object for notational convenience.
    """
    def __getattr__(self, k:str) -> object:
        if k in self: return self[k]
        else: raise AttributeError("No element named {}".format(k))

    def __setattr__(self, k:str, v:object) -> None:
        self[k] = v

    def __delattr__(self, k:str) -> None:
        if k in self: del self[k]
        else: raise AttributeError("No element named {}".format(k))


def sloppy(o:object) -> objectify:
    """
    This function lives up to its name
    """
    return o if isinstance(o, objectify) else objectify(o)


def pids_of(partial_process_name:str, anywhere:bool=False) -> list:
    """
    This function gets a list of matching process IDs.

    partial_process_name -- a text shred containing the bit you want
        to find.
    anywhere -- If False, we effectively look for the a user associated
        with the process name. If True, then we look for the shred anywhere
        in the name not just at the beginning.

    returns -- a possibly empty list of ints containing the pids
        whose names match the text shred.
    """

    # Yes, this function could all be one line, but I'm trying to avoid
    # stressing out the human reader's comprehension with a nested
    # list comprehension.
    try:
        matches = [ _ for _ in
            subprocess.check_output(shlex.split("/bin/ps -ef"),
                universal_newlines=True).split("\n")
            if partial_process_name in _
            ] \
        if anywhere else \
            [ _ for _ in
            subprocess.check_output(shlex.split("/bin/ps -ef"),
                universal_newlines=True).split("\n")
            if _.startswith(partial_process_name)
            ]
    except Exception as e:
        tombstone(type_and_text(e))
        return []

    pids = []
    try:

        # Now we are really looking for the process name.
        pids = [ int(_.split()[1])
            for _ in matches
                if partial_process_name in _.split()[-1]]

    except Exception as e:
        tombstone(type_and_text(e))

    return pids


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
        

def scrub(s:str, scrubbing:int=1) -> str:
    """
    s - the text shred to scrub.

    scrubbing is a bit mask, with the following meanings:
        1 - character substitutions for annoying problems found
            in many texts.
        2 - Remove SGML type tags.
        4 - Flatten to UTF-8 to ASCII-7.
    """

    # If there is no input or we are not scrubbing, bail out.
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
            ,('\r\n', '\n')
            ,(' & ', ' and ')]

    tombstone("Scrubbing " + str(len(s)) + " chars of input.")

    if scrubbing & 2:
        tombstone("Removing SGML tags.")
        s = bs4.BeautifulSoup(s, 'lxml').get_text()

    if scrubbing & 1:
        for _ in subs:
            original_len = len(s)
            s = re.sub(_[0], _[1], s)
            new_len = len(s)
            if _ == subs[-1]: continue

    if scrubbing & 4:
        gkf.tombstone("Flattening to ASCII")
        s = s.encode('ascii', 'ignore')
        gkf.tombstone("Smack! Flat ASCII remains.")

    tombstone("Scrubbed text is now " + str(len(s)) + " chars.")

    return s


def show_args(pargs:object) -> None:
    """
    Print out the program arguments as they would have been typed
    in. Command line arguments have a -- in the front, and embedded
    dashes in the option itself. These are removed and changed to
    an underscore, respectively.
    """
    print("")
    opt_string = ""
    for _ in sorted(vars(pargs).items()):
        opt_string += " --"+ _[0].replace("_","-") + " " + str(_[1])
    print(opt_string + "\n")    


class SloppyDict(dict):
    """
    Make a dict into an object for notational convenience.
    """
    def __getattr__(self, k:str) -> object:
        if k in self: return self[k]
        raise AttributeError("No element named {}".format(k))

    def __setattr__(self, k:str, v:object) -> None:
        self[k] = v

    def __delattr__(self, k:str) -> None:
        if k in self: del self[k]
        else: raise AttributeError("No element named {}".format(k))

    def reorder(self, some_keys:list=[], self_assign:bool=True) -> SloppyDict:
        new_data = SloppyDict()
        unmoved_keys = sorted(list(self.keys()))

        for k in some_keys:
            try:
                new_data[k] = self[k]
                unmoved_keys.remove(k)
            except KeyError as e:
                pass

        for k in unmoved_keys:
            new_data[k] = self[k]

        if self_assign: 
            self = new_data
            return self
        else:
            return copy.deepcopy(new_data)       

    def __str__(self) -> str:
        return "\n".join([ "{} : {}".format(k, self[k]) for k in self ])


def deepsloppy(o:dict) -> Union[SloppyDict, object]:
    """
    Multi level slop.
    """
    if isinstance(o, dict): 
        o = SloppyDict(o)
        for k, v in o.items():
            o[k] = deepsloppy(v)

    elif isinstance(o, list):
        for i, _ in enumerate(o):
            o[i] = deepsloppy(_)

    else:
        pass

    return o


def stalk_and_kill(process_name:str) -> bool:
    """
    This function finds process_name ... and
    kills them by sending them a SIGTERM.

    returns True or False based on whether we assassinated our
        ancestral impostors. If there are none, we return True because
        in the logical meaning of "we got them all," we did.
    """

    tombstone('Attempting to remove processes beginning with ' + process_name)
    # Assume all will go well.
    got_em = True

    for pid in pids_of(process_name, True):

        # Be nice about it.
        try:
            os.kill(pid, signal.SIGTERM)
        except:
            tombstone("Process " + str(pid) + " may have terminated before SIGTERM was sent.")
            continue

        # wait two seconds
        time.sleep(2)
        try:
            # kill 0 will fail if the process is gone
            os.kill(pid, 0)
        except:
            tombstone("Process " + str(pid) + " has been terminated.")
            continue

        # Darn! It's still running. Let's get serious.
        os.kill(pid, signal.SIGKILL)
        time.sleep(2)
        try:
            # As above, kill 0 will fail if the process is gone
            os.kill(pid, 0)
            tombstone("Process " + str(pid) + " has been killed.")
        except:
            continue
        tombstone(str(pid) + " is obdurate, and will not die.")
        got_em = False

    return got_em


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

    
def version(full:bool = True) -> str:
    """
    Do our best to determine the git commit ID ....
    """
    try:
        v = subprocess.check_output(
            ["/usr/bin/git", "rev-parse", "--short", "HEAD"],
            universal_newlines=True
            ).strip()
        if not full: return v
    except:
        v = 'unknown'
    else:
        mods = subprocess.check_output(
            ["/usr/bin/git", "status", "--short"],
            universal_newlines=True
            )
        if mods.strip() != mods:
            v += (", with these files modified: \n" + str(mods))
    finally:
        return v


