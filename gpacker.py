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

class Packer: 
    pass

class Packer:
    """
    Class to read and write data files without having to
    know much about how to do it. Effectively, this class restricts
    the options available in the interest of having a standard
    format.
    """
    
    super_modes = {
        "create":"wbx",
        "read":"rb",
        "write":"wb",
        None:"rb",
        "append":"ab"
        }

    
    def __init__(self, *,
        verbose:bool=False,
        encoding:str='utf-8') -> None:
        """
        encoding -- essential to converting bytes to strings
        """

        self.encoding = encoding
        self.unit = None
        self.name = None
        self.verbose = verbose
        

    @trap
    def attachIO(self,
        filename:str,
        s_mode:str=None) -> bool:
        """
        Open a unit of some kind for use by our program. 

        filename   -- unit for the I/O operations
        s_mode     -- if present, overrides any mode values.

        returns    -- true on success, false otherwise.
        """

        try:
            mode = Packer.super_modes.get(s_mode)            
            self.unit = open(filename, mode)
            self.verbose and tombstone(f"{filename} is open {mode}")
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

        except Exception as e:
            tombstone(f"{filename} could not be attached because {str(e)}")

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
            self.verbose and tombstone(f'output {len(it)} bytes.')
            it = bz2.compress(it)
            self.verbose and tombstone(f'BWT reduces to {len(it)} bytes.')
            
        except pickle.PicklingError as e:
            tombstone(str(e))
            return False   

        except Exception as e:
            tombstone(str(e))
            return False

        x = 0
        try:          
            x = self.unit.write(it)
            self.verbose and tombstone(f"{x} bytes written")
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
            can be transformed to a pandas.DataFrame, but if 
            you know is was a pandas.DataFrame when you wrote 
            it, then this is the parameter you want to use.

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

        except Exception as e:
            # It was not zipped. We can let that one go.
            pass

        try:
            pyobj = pickle.loads(data)
            if format == 'python': 
                return pyobj

            elif format == 'pandas': 
                if have_pandas:
                    return pandas.DataFrame.from_dict(pyobj)
                else:
                    tombstone("Pandas is not installed")
                    return pyobj

            else:
                raise Exception('unsupported data format {format}')

        except Exception as e:
            tombstone(f"Unknown error: {str(e)}")

        finally:
            self.unit.close()
            self.unit = None
            
        return data if len(data) else as_read_data
