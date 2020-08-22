# -*- coding: utf-8 -*-
""" Various sloppy, forgiving data structures. """

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

class SloppyDict(dict):
    """
    Make a dict into an object for notational convenience.
    """
    def __getattr__(self, k:str) -> object:
        if k in self: return self[k]
        raise AttributeError(f"No element named {k}")

    def __setattr__(self, k:str, v:object) -> None:
        self[k] = v

    def __delattr__(self, k:str) -> None:
        if k in self: del self[k]
        else: raise AttributeError(f"No element named {k}")


def sloppy(o:object) -> SloppyDict:
    return o if isinstance(o, SloppyDict) else SloppyDict(o)


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


class SloppyTree(dict):
    """
    Like SloppyDict(), only worse -- much worse.
    """
    def __missing__(self, k:str) -> object:
        self[k] = SloppyTree()
        return self[k]

    def __getattr__(self, k:str) -> object:
        return self[k]

    def __setattr__(self, k:str, v:object) -> None:
        self[k] = v

    def __delattr__(self, k:str) -> None:
        if k in self: del self[k]


