#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Talk to a Davis Instruments weather station.
"""

__author__ = 'George Flanagin'
__copyright__ = 'Copyright 2018'
__credits__ = None
__version__ = '0.1'
__maintainer__ = 'George Flanagin'
__email__ = 'me+davis@georgeflanagin.com'
__status__ = 'Prototype'
__required_version__ = (3,6)

# Builtins
import argparse
import cmd
import enum
import logging
import os
import pdb
import socket
import subprocess
import sys
import time
import typing
from   typing import *

# Paramiko
import logging

import fname
import setproctitle
import gkflib as gkf
import beachhead

run_debugger = False

utf8 = 'utf-8'

def prep(s:str) -> bytearray:
    """
    Convert a string to a bytearray suitable for sending through
    a socket connection.
    """
    return bytearray(s, 'utf-8')


def prepx(s:str) -> bytearray:
    """
    As above, but the string is assumed to be a collection of hex
    digits (0-9A-F). 
    """
    try:
        return bytearray.fromhex(s)
    except ValueError as e:
        gkf.tombstone('{} cannot be converted to hex'.format(s))
        raise e from None


class DavisCommand(enum.Enum):
    """
    These commands are sent to the Vantage[x] console. They
    have been taken from pages 6-21 of Rev 2.6.1 of the 
    Vantage Serial Protocol document, March 29, 2013.

    Commands with a NL ('\n') appended, are complete, whereas 
    ones that do not include the new line must be supplied
    parameters. The line breaks below represent the inclusion
    of the commands in sections of the document.
    """
    WAKEUP = prepx('0A')

    TEST = prep('TEST\n')    
    WRD = prep('WRD').extend(prepx('124D0A'))
    RXCHECK = prep('RXCHECK\n')
    VER = prep('RXTEST\n')
    RECEIVERS = prep('RECEIVERS\n')
    NVER = prep('NVER\n')
    
    LOOP = prep('LOOP')
    LPS = prep('LPS')
    HILOWS = prep('HILOWS')
    PUTRAIN = prep('PUTRAIN')
    PUTEST = prep('PUTET')

    DMP = prep('DMP\n')
    DMPAFT = prep('DMPAFT')
    
    GETEE = prep('GETEE\n')
    EEWR = prep('EEWR')
    EERD = prep('EERD')
    EEBWR = prep('EEBWR')
    EEBRD = prep('EEBRD')

    

class DavisResponse(enum.Enum):
    ACK = prepx('06')
    OK = prep('\n\rOK\n\r')
    DONE = prep('DONE\n\r')
    AWAKE = prepx('0A0D')

class Davis(cmd.Cmd):

    use_rawinput = True
    doc_header = 'To get a little overall guidance, type `help general`'
    # intro = "\n".join(banner)

    def __init__(self):
        
        cmd.Cmd.__init__(self)
        Davis.prompt = "\n[Davis]: "
        self.connection = None


    
    def __bool__(self) -> bool: 
        return self.sock is not None


    def preloop(self) -> None:
        setproctitle.setproctitle('Davis')


    def default(self, data:str="") -> None:
        gkf.tombstone(beachhead.red('unknown command {}'.format(data)))
        self.do_help(data)


    def do_connect(self, info:str="") -> None:
        """
        Usage: connect {IP|name} {port}
        """
        info = info.strip().split()
        self.connection = beachhead.SocketConnection()
        try:
            self.connection.open_socket(info[0], int(info[1]))
        except Exception as e:
            gkf.tombstone(gkf.type_and_text(e))
            return
        else:
            print(str(self.connection))

        print('Connected to /something/ at {}:{}'.format(info[0],info[1]))
        print('Ready to talk. Sending TEST')
        self.connection.send('TEST')
        reply = self.read()
        print('Received {} as reply'.format(reply))


    def do_exit(self, info:str="") -> None:
        """
        Usage: exit
        """
        self.connection.close()
        sys.exit(os.EX_OK)


if __name__ == "__main__":

    # subprocess.call('clear',shell=True)
    while True:
        try:
            Davis().cmdloop()

        except KeyboardInterrupt:
            gkf.tombstone("Exiting via control-C.")
            sys.exit(os.EX_OK)

        except Exception as e:
            gkf.tombstone(gkf.type_and_text(e))
            gkf.tombstone(gkf.formatted_stack_trace(True))
            sys.exit(1) 
