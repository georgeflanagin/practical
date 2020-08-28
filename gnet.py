# -*- coding: utf-8 -*-
""" Network helpers. """

# Added for Python 3.5+
import typing
from typing import *

import os
import paramiko
import pwd
import sys

import gpath

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
# G
####

def get_ssh_host_info(host_name:str=None, config_file:str=None) -> List[Dict]:
    """ Utility function to get all the ssh config info, or just that
    for one host.

    host_name -- if given, it should be something that matches an entry
        in the ssh config file that gets parsed.
    config_file -- if not given (as it usually is not) the usual default
        config file is used.
    """

    if config_file is None:
        config_file = gpath.expandall("~/.ssh/config")

    ssh_conf = paramiko.SSHConfig()
    ssh_conf.parse(open(config_file))

    if not host_name: return ssh_conf
    if host_name == 'all': return ssh_conf.get_hostnames()
    return None if host_name not in ssh_conf.get_hostnames() else ssh_conf.lookup(host_name)


####
# M
####

def me() -> tuple:
    """
    I am always forgetting just who I am.
    """
    my_uid = os.getuid()
    my_name = pwd.getpwuid(my_uid).pw_name
    return my_name, my_uid


####
# T
####

def tobytes(s:str) -> bytes:
    return bytes(s.encode('utf-8'))


