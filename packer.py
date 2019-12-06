# -*- coding: utf-8 -*-
""" Wrapper for basic msgpack operations """

import typing
from   typing import *

import bz2
import os
import sys
import tempfile

import msgpack
import pandas

# Canøe imports

import fname
import gkflib as gkf
import lexdoc

# Credits
__longname__ = "University of Richmond"
__acronym__ = " UR "
__author__ = 'George Flanagin'
__copyright__ = 'Copyright 2019, University of Richmond'
__credits__ = None
__version__ = '0.1'
__maintainer__ = 'George Flanagin'
__email__ = 'gflanagin@richmond.edu'
__status__ = 'Prototype'

__license__ = 'MIT'

def set_to_list(o:object) -> object:
    if isinstance(o, (set, frozenset)): 
        return list(o)
    return o


def lexword_to_dict(o:object) -> object:
    if isinstance(o, lexdoc.Lexword):
        return o.to_dict()


built_in_hooks = [set_to_list, lexword_to_dict]

class Packer:
    """
    Class to read and write msgpack files without having to
    know much about how to do it. Effectively, this class restricts
    the options available, provides the hooks for our non-standard
    data types, and handles the exceptions that are raised by
    msgpack.
    """

    def __init__(self, *,
        encoding:str='utf-8',
        hooks:list=[],
        suffix:str='msgpack') -> None:
        """
        encoding -- essential to converting bytes to strings
        hooks -- a list of functions to do serializations for types
            not supported in the default packing. These are appended to
            the default list of conversions.
        suffix -- file name extension, minus the dot separator.
        """

        self.suffix = suffix
        self.encoding = encoding
        self.unit = None
        self.name = None
        self.hooks = built_in_hooks + hooks
        

    def _hooks(self, o:object) -> object:
        """
        Execute the hooks.
        """
        for fcn in self.hooks:
            o_prime = fcn(o)
            if id(o_prime) == id(o): continue
            return o_prime
        return o


    def attachIO(self,
        filename:str, *,
        mode:str='wb+',
        klobber:bool=True,
        use_suffix:bool=False) -> bool:
        """
        Open a unit of some kind for use by our program. 

        filename   -- unit for the I/O operations
        mode       -- how to open the unit
        klobber    -- whether or not to continue if the file exists.
        use_suffix -- append the suffix to the file name or not.

        returns -- true on success, false otherwise.
        """

        filename = ".".join([filename, self.suffix]) if use_suffix else filename
        f = fname.Fname(filename)
        if f and not klobber:
            gkf.tombstone('{} exists.'.format(f))
            return False

        self.unit = open(filename, mode)
        return True


    def write(self, o:object, *, show_stats=False) -> bool:
        """
        serialize the argument, and write the serialization to the 
        current file and close the file.

        o -- the Python object to be written

        returns -- true on success, false otherwise.
        """
        try:
            it = msgpack.packb(o, use_bin_type=True, default=self._hooks) 
            it = bz2.compress(it)
            
        except Exception as e:
            gkf.tombstone(gkf.type_and_text(e))
            return False   

        try:          
            x = self.unit.write(it)
            return True

        except Exception as e:
            gkf.tombstone(gkf.type_and_text(e))
            return False   

        finally:
            if show_stats:
                gkf.tombstone('wrote {} bytes.'.format(x))
            self.unit.close()
            self.unit = None

    
    def read(self, format:str='python') -> object:
        """
        Read and unpack the info in the object in the unit.

        returns -- the decoded contents or None.
        """

        if self.unit is None:
            gkf.tombstone('No unit attached.')
            return None

        self.unit.seek(0, 0)
        data = self.unit.read()
        data = bz2.decompress(data)
        self.unit.close()
        self.unit = None

        pyobj = msgpack.unpackb(data, encoding=self.encoding)
        if format == 'python': 
            return pyobj
        elif format == 'pandas': 
            return pandas.DataFrame.from_dict(pyobj)
        else:
            raise Exception()


if __name__ == '__main__':

    x = {'allowed_environments': ['dev', 'test', 'prod'],
 'cleanup': [],
 'comment': ['Test for missing name in xform.'],
 'compiled': (1557504047, '2019-05-10 12:00:47.8'),
 'name': 'test001',
 'origin': '/sw/canoe/gkf_home/src/canoelibs/test004.json',
 'roster': ['source', 'cleanup'],
 'schedule': [[{32, 4, 39, 11, 46, 18, 53, 25},
               '*',
               '*',
               {1, 3, 5, 7, 9, 11},
               {6}]],
 'source': [{'directory': '/sw/canoe/var/data/test001',
             'file': 'it',
             'host': {'connectionattempts': '3',
                      'connecttimeout': '2',
                      'controlpath': '/tmp/ssh-canoe@starr.richmond.edu:22',
                      'hostname': 'starr.richmond.edu',
                      'identityfile': ['/home/canoe/.ssh/id_rsa'],
                      'port': '22',
                      'serveraliveinterval': '59',
                      'user': 'canoe'},
             'localedir': '/sw/canoe/var/data/test001',
             'on_error': ERROR_ACTION.skip,
             'overwrite': True}],
 'this_dir': '/sw/canoe/var/data/test001'}

    my_packer = URpacker(suffix='canoe')
    print("attachIO returned {}".format(my_packer.attachIO('f')))
    print("write returned {}".format(my_packer.write(x)))

    print("attachIO returned {}".format(my_packer.attachIO('f', mode='rb')))
    y = my_packer.read()
    print("{}".format(y))
