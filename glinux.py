# -*- coding: utf-8 -*-
""" Linux system conveniences. """

import os
import sys

# Credits
__author__ = 'George Flanagin'
__copyright__ = 'Copyright 2020, University of Richmond'
__credits__ = None
__version__ = '0.1'
__maintainer__ = 'George Flanagin'
__email__ = 'me@georgeflanagin.com'
__status__ = 'Prototype'
__license__ = 'MIT'


####
# M
####

def memavail() -> tuple:
    """
    Return a fraction representing the available memory to run
    new processes, and the absolute amount.
    """
    with open('/proc/meminfo') as m:
        info = [ _.split() for _ in m.read().split('\n') ]

    return float(info[2][1])/float(info[0][1]) , int(info[0][1]) << 10


####
# P
####

def parse_proc(pid:int=None) -> dict:
    """
    Parse the proc file for a given PID and return the values
    as a dict with keys set to lower without the "vm" in front,
    and the values converted to ints.
    """
    if pid is None: pid = os.getpid()
    lines = []
    kv = {}
    proc_file = f'/proc/{pid}/status'

    try:
        with open(proc_file, 'r') as f:
            rows = f.read().split("\n")
    except:
        return kv

    if not len(rows): return kv

    interesting_keys = ( 
            'VmSize', 'VmLck', 'VmHWM',
            'VmRSS', 'VmData', 'VmStk', 
            'VmExe', 'VmSwap' )

    for row in rows:
        if ":" in row:
            k, v = row.split(":", 1)
        else:
            continue
        if k in interesting_keys:
            kv[k.lower()[2:]] = int(v.split()[0]) << 10

    return kv
