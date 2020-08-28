# -*- coding: utf-8 -*-
"""  
A connection to version 2.0 of the NIST Randomness Beacon
"""
import typing
from typing import *

import os
import sys

import json
import shlex
import shutil
import subprocess
import tempfile

# Credits
__author__ = 'George Flanagin'
__copyright__ = 'Copyright 2020'
__version__ = 2.0
__maintainer__ = 'George Flanagin'
__email__ = 'gflanagin@richmond.edu'
__status__ = 'Production'
__license__ = 'MIT'


__required_version__ = (3, 6)
if sys.version_info < __required_version__:
    print("This software requires Python " + str(__required_version__))
    sys.exit(os.EX_SOFTWARE)

####
# N
####

class NISTBeacon2:
    """
    Class wrapper for the functionality.

    raises Exception if curl is not available.
    """

    def __init__(self):
        """
        set up the class.

        self.blob -- the full response from our request.
        self.data -- the random bits.
        """

        self.blob = None
        self.data = None
        self.curl_exe = shutil.which('curl')
        if not self.curl_exe:
            raise Exception('operation not supported in this environment.')
        

    def __call__(self) -> Union[bool, str]:
        """
        Get the current 512 bits of random goodness.

        returns -- None if the request fails, otherwise the data as 
            a hexadecimal string
        """

        result = subprocess.run(
            shlex.split(f"{self.curl_exe} --silent https://beacon.nist.gov/beacon/2.0/pulse/last"),
            stdout=subprocess.PIPE
            )
        if result.returncode != 0:
            return None
        
        self.blob = json.loads(result.stdout)
        self.data = self.blob['pulse']['localRandomValue']

        return self.data

    
    def __str__(self) -> str:
        """
        returns -- the most recently retrieved data if there is any, otherwise
            go get some fresh data and return it.
        """
        if not self.data:
            self()

        return self.data

    
    @property
    def msg(self) -> dict:
        return self.blob['pulse']['timeStamp'], self.data

    

####
# R
####

def random_file(name_prefix:str, *, length:int=None, break_on:str=None) -> tuple:
    """
    Generate a new file, with random contents, consisting of printable
    characters.

    name_prefix -- In case you want to isolate them later.
    length -- if None, then a random length <= 1MB
    break_on -- For some testing, perhaps you want a file of "lines."

    returns -- a tuple of file_name and size.
    """    
    f_name = None
    num_written = -1

    file_size = length if length is not None else random.choice(range(0, 1<<20))
    fcn_signature('random_string', file_size)
    s = random_string(file_size, True)

    if break_on is not None:
        if isinstance(break_on, str): break_on = break_on.encode('utf-8')
        s = s.replace(break_on, b'\n')    

    try:
        f_no, f_name = tempfile.mkstemp(suffix='.txt', prefix=name_prefix)
        num_written = os.write(f_no, s)
        os.close(f_no)
    except Exception as e:
        tombstone(str(e))
    
    return f_name, num_written
    


def random_string(length:int=10, want_bytes:bool=False, all_alpha:bool=True) -> str:
    """
    Random data of a given length.
    """
    
    s = base64.b64encode(os.urandom(length*2))
    if want_bytes: return s[:length]

    s = s.decode('utf-8')
    if not all_alpha: return s[:length]

    t = "".join([ _ for _ in s if _.isalpha() ])[:length]
    return t


