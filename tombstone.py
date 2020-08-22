# -*- coding: utf-8 -*-
""" Generic, bare functions, not a part of any object or service. """

import typing
from typing import *

import os
import sys

import gtime

# Credits
__author__ = 'George Flanagin'
__copyright__ = 'Copyright 2020, University of Richmond'
__credits__ = None
__version__ = '0.1'
__maintainer__ = 'George Flanagin'
__email__ = 'me@georgeflanagin.com'
__status__ = 'Prototype'

__license__ = 'MIT'

# Cheap hack to get sequence numbers for tombstones.
class Accumulator(object):
    """
    This only works in a multi-processing environment because
    we care about the monotonic increasing property of the 
    numbers, not their values or whether the set of values is
    duplicated in a forked process.

    Syntax:

        i = Sequence()
    """
    ax = 0

    @classmethod
    def reset(cls):
        Accumulator.ax = 0

    def __init__(self):
        pass

    def __call__(self):
        Accumulator.ax += 1
        return Accumulator.ax

    def __int__(self):
        return Accumulator.ax


# And here is the accumulator itself.
AX=Accumulator()


def tombstone(args:Any=None) -> Tuple[int, str]:
    """
    Print out a message, data, whatever you pass in, along with
    a timestamp and the PID of the process making the call. 
    Along with printing it out, the function returns the string
    representation of the args.

    """
    i = AX()

    s = f"{i} {gtime.now_as_string()} :: {os.getpid()} :: {args}"
    sys.stderr.write(s + "\n")

    return i, s
    

