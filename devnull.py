# -*- coding: utf-8 -*-

"""
This is the true null IO object. Every call works, and nothing 
happens. This class solves the problem of returning a "file"
when one is required even if it is impossible to do so.
"""
import typing
from typing import *

import os
import random

# Credits
__author__ = 'George Flanagin'
__copyright__ = 'Copyright 2015, University of Richmond'
__credits__ = None
__version__ = '0.1'
__maintainer__ = 'George Flanagin'
__email__ = 'gflanagin@richmond.edu'
__status__ = 'Prototype'


class DevNull:
    """
    DevNull is a file-like object supporting the context
    manager interface commonly used with files. This is a
    rare case where we are keeping the class name in lower
    case to make it look like the common symbol /dev/null.
    """
    # Support for the context manager:
    #
    #     with('myworthlessname') as f:
    #       f.write('something')
    #
    def __init__(self, name:str = None):
        self.closed = False
        pass


    def __enter__(self):
        return self


    def __exit__(self):
        pass

    
    def __bool__(self) -> bool:
        return not self.closed


    def __len__(self) -> int:
        """
        The length of devnull is always zero.
        """
        if self.closed: 
            raise ValueError('I/O operation on closed file.')

        return 0


    # We don't need an open method, but a close is required.
    # open() is a file factory in Python 3.
    def close(self) -> bool:
        """
        Close always succeeds.
        """
        self.closed = True
        return None


    def closed(self) -> bool:
        return self.closed


    def flush(self) -> None:
        pass

    def write(self, datum) -> int:
        """
        return -- the number of chars not written.
        """
        if self.closed: 
            raise ValueError('I/O operation on closed file.')
        return len(str(datum))


    def read(self, size:int=None) -> str:
        """
        .read is defined to read the entire contents of
        the file. If you give it a size, you get that many
        bytes returned.
        """
        if self.closed: 
            raise ValueError('I/O operation on closed file.')

        if size is None: return ''
        contents = [' ']*size
        for i in range(0, size):
            contents[i] = random.choice("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789+/")
        return "".join(contents)


    def readline(self) -> str:
        """
        .readline is defined to read a line of the file, leaving
        the newline at the end.
        """
        if self.closed: 
            raise ValueError('I/O operation on closed file.')

        return '\n'


    def seek(self, offset:int, from_where:int=0) -> str:
        """
        We need some reasonable behaviours here. 
        """
        if self.closed: 
            raise ValueError('I/O operation on closed file.')

        if from_where not in [0, 1, 2]: raise ValueError('invalid whence')
        if from_where == 2 and offset: raise ValueError("can't do nonzero end-relative seeks")
        if from_where == 1: raise ValueError("can't do nonzero cur-relative seeks")
        if offset < 0: raise ValueError("negative seek position {}".format(offset))
        return offset
        

if __name__ == "__main__":
    pass
else:
    # print(str(os.path.abspath(__file__)) + " compiled.")
    print("*", end="")

