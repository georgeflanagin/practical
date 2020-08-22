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

# Credits
__author__ = 'George Flanagin'
__copyright__ = 'Copyright 2020, University of Richmond'
__version__ = 2.0
__maintainer__ = 'George Flanagin'
__email__ = 'gflanagin@richmond.edu'
__status__ = 'Production'
__license__ = 'MIT'


__required_version__ = (3, 6)
if sys.version_info < __required_version__:
    print("This software requires Python " + str(__required_version__))
    sys.exit(os.EX_SOFTWARE)

class NIST_Beacon2:
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

    
if __name__ == "__main__":
    beacon = NIST_Beacon2()
    print(beacon())
    print(beacon.msg)     

