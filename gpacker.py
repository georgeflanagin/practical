# -*- coding: utf-8 -*-
""" Wrapper for basic pickle + bz2 operations """

import typing
from   typing import *

import bz2
import json
import math
import os
import pickle
import sys
import tempfile

try:
    import pandas
    have_pandas = True
except:
    have_pandas = False

# Canøe imports

import fname
from   gdecorators import trap
from   tombstone import tombstone

# Credits
__author__ = 'George Flanagin'
__copyright__ = 'Copyright 2019'
__credits__ = None
__version__ = '0.1'
__maintainer__ = 'George Flanagin'
__email__ = 'gflanagin@richmond.edu'
__status__ = 'Prototype'

__license__ = 'MIT'

class URpacker: 
    pass

class URpacker:
    """
    Class to read and write msgpack files without having to
    know much about how to do it. Effectively, this class restricts
    the options available, provides the hooks for our non-standard
    data types, and handles the exceptions that are raised by
    msgpack.
    """
    
    super_modes = {
        "create":"wbx",
        "read":"rb",
        "write":"wb",
        "append":"ab"
        }

    
    def __init__(self, *,
        encoding:str='utf-8',
        hooks:list=[]) -> None:
        """
        encoding -- essential to converting bytes to strings
        hooks -- a list of functions to do serializations for types
            not supported in the default packing. These are appended to
            the default list of conversions.
        """

        self.encoding = encoding
        self.unit = None
        self.name = None
        self.hooks = hooks if hooks else []
        

    def _hooks(self, o:object) -> object:
        """
        Execute the hooks.
        """
        for fcn in self.hooks:
            o_prime = fcn(o)
            if id(o_prime) == id(o): continue
            return o_prime
        return o


    @trap
    def attachIO(self,
        filename:str, *,
        mode:str='w+b',
        s_mode:str=None) -> bool:
        """
        Open a unit of some kind for use by our program. 

        filename   -- unit for the I/O operations
        mode       -- how to open the unit. The default is read/write,
                        with no truncation for an existing unit.
        s_mode     -- if present, overrides any mode values.
        klobber    -- whether or not to continue if the file exists.

        returns    -- true on success, false otherwise.
        """

        if s_mode is not None:
            mode = URpacker.super_modes.get(s_mode, mode)            

        try:
            self.unit = open(filename, mode)
            return True

        except FileExistsError as e:
            tombstone(f'Cannot create {filename} because it already exists.')

        except FileNotFoundError as e:
            tombstone('File {filename} does not exist.')

        except PermissionError as e:
            if 'r' in mode:
                tombstone('File {filename} exists, but you have no rights to it.')
            else:
                tombstone('You cannot write to {filename}')

        return False


    @trap
    def write(self, o:object, *, show_stats=False) -> bool:
        """
        serialize the argument, and write the serialization to the 
        current file and close the file.

        o -- the Python object to be written

        returns -- true on success, false otherwise.
        """
        try:
            it = pickle.dumps(o) 
            tombstone(f'output {len(it)} bytes.')
            it = bz2.compress(it)
            tombstone(f'BWT reduces to {len(it)} bytes.')
            
        except pickle.PicklingError as e:
            tombstone(str(e))
            return False   

        except Exception as e:
            tombstone(str(e))
            return False

        x = 0
        try:          
            x = self.unit.write(it)
            return True

        except Exception as e:
            tombstone(str(e))
            return False   

        finally:
            self.unit.close()
            self.unit = None

    
    @trap
    def read(self, format:str='python') -> object:
        """
        Read and unpack the info in the object in the unit.

        format  -- how to present the returned data object. The 
            options are 'python' and 'pandas'. Not everything
            can be transformed to a pandas.DataFrame

        returns -- the decoded contents or None. Raises an
            Exception on an unsupported data format. 
        """

        if self.unit is None:
            tombstone('No unit attached.')
            return None

        self.unit.seek(0, 0)
        as_read_data = self.unit.read()
        data = ""

        try:
            data = bz2.decompress(as_read_data)

            try:
                pyobj = pickle.loads(data)
                if format == 'python': 
                    return pyobj
                elif format == 'pandas': 
                    if have_pandas:
                        return pandas.DataFrame.from_dict(pyobj)
                    else:
                        tombstone("Pandas is not installed")
                        raise OSError(os.EX_SOFTWARE, "pandas not installed.")
                else:
                    raise Exception('unsupported data format {format}')

            except Exception as e:
                tombstone(f"Unknown error: {str(e)}"

        except Exception as e:
            # It was not zipped. We can let that one go.
            pass

        finally:
            self.unit.close()
            self.unit = None
            
        return data if len(data) else as_read_data

