#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Beachhead is a program that allows interactive operation of
the paramiko stack. The purpose is to diagnose, triage, and
log connectivity problems.
"""

__author__ = 'George Flanagin'
__credits__ = None
__version__ = '0.1'
__maintainer__ = 'George Flanagin'
__email__ = 'gflanagin@richmond.edu'
__status__ = 'Prototype'
__required_version__ = (3,6)
__license__ = 'MIT'

# Universal imports
import os
import sys
import typing
from   typing import *

# Check
if sys.version_info < __required_version__:
    tombstone('This program requires Python {} or greater.'.format(__required_version__))
    sys.exit(os.EX_SOFTWARE)

# Builtins
import argparse
import cmd
import logging
import socket

# Installables.

try:
    # Paramiko
    import paramiko 
except ImportError as e:
    sys.stderr.write('This program requires paramiko.')
else:
    from paramiko import SSHClient, SSHConfig, SSHException

# From this library.

from   dorunrun import dorunrun
import fname
import gnet
import socketconnection
from   socketconnection import SocketConnection
from   stopwatch import Stopwatch
from   tombstone import tombstone

########################################################

def elapsed_time(t1, t2) -> str:
    if t1 > t2: 
        t1, t2 = t2, t1
    e = t2 - t1
    units = ' milliseconds' if e < 1.0 else ' seconds'
    if e < 1.0: e *= 1000
    return str(round(e,3)) + units

indent = "     "
banner = [
    "\n\nWelcome to Beachhead.\n\n"
]

class Beachhead: pass
class Beachhead(cmd.Cmd):
    """
    Beachhead is not a tool for the weak.
    """    

    use_rawinput = True
    doc_header = 'To get a little overall guidance, type `help general`'
    intro = "\n".join(banner)

    def __init__(self):
        
        cmd.Cmd.__init__(self)
        Beachhead.prompt = "\n[beachhead]: "
        self.conn = SocketConnection()

    
    def __bool__(self) -> bool: 
        return self.sock is not None


    def __str__(self) -> str:
        return "{}:{}".format(self.conn.remote_host, self.conn.remote_port)


    def preloop(self) -> None:
        pass


    def default(self, data:str="") -> None:
        tombstone('unknown command {}'.format(data))
        self.do_help(data)


    """ ***********************************************************************************
    These are our console commands.
    *********************************************************************************** """

    def do_close(self, data="") -> None:
        """
        Close the open socket connection (if any)
        """
        if self.conn: self.conn.close()
        else: tombstone('nothing to do')


    def do_debug(self, data:str="") -> None:
        """
        debug [ value ]

            With no parameter, this function prints the current debug level,
            otherwise, it will attempt to set the level. The allowable debug
            levels are:

                CRITICAL (50)
                ERROR    (40)
                WARNING  (30)
                INFO     (20)
                DEBUG    (10)
                NOTSET    (0)


        """
        if not len(data):
            tombstone(blue('debug level is {}'.format(self.conn.debug_level())))
            return


        data = data.strip().upper()
        if data not in logging_levels.keys() and data not in logging_levels.values():
            tombstone('not sure what this level means: {}'.format(data))
            return
            
        try:
            level = int(data)
        except:
            level = int(logging_levels[data])
        finally:
            self.conn.debug_level(level)
            


    def do_do(self, data:str="") -> None:
        """
        do { something }

            attempt to exit a command by stuffing the text through the channel
        """
        if not self.channel: 
            self.do_help('do')
            return

        try:
            tombstone('attempting remote command {}'.format(data))
            in_, out_, err_ = self.conn.channel.exec_command(data)

        except KeyboardInterrupt as e:
            tombstone('aborting. Control-C pressed.')

        except Exception as e:
            tombstone(str(e))

        else:
            out_.channel.recv_exit_status();
            tombstone(out_.readlines())

        finally:
            self.conn.open_channel()


    def do_error(self, data:str="") -> None:
        """
        error [reset]

        [re]displays the error of the connection, and optionally resets it
        """
        tombstone(self.conn.error)
        if 'reset'.startswith(data.strip().lower()): self.conn.error = None


    def do_exit(self, data:str="") -> None:
        """
        exit:
            leave very abruptly.
        """
        sys.exit(os.EX_OK)


    def do_general(self, data:str="") -> None:
        """
        Beachhead, version _ (do you really care?). 

        This program allows you to explore network connections step-by-step,
        using the Python 3 library named `paramiko`. To make (or attempt to
        make) a connection to a remote host, the following is recommended:

        hosts                       <- This will give a list of "known hosts"
        open socket host port       <- Specify your target, and create a connection.
        set password AbraCadabra    <- Only if you need it; keys don't require
                                        a password.
        open session                <- Using the info from ~/.ssh/config
        open transport              <- You will need this if you intend to do anything
                                        beyond sitting at your desk admiring what 
                                        you have done so far.
        
        Now, if you want to execute a command on the remote host, you will need
        a channel. If you want to transfer a file (something we do a lot of), you
        will need an sftp client. Unsurprisingly, the commands are:

        open channel 
        open sftp

        """
        print(self.do_general.__doc__)


    def do_get(self, data:str="") -> None:
        """
        get a file from the remote host.
        """
        if not self.conn.sftp:
            tombstone('sftp channel is not open.')
            return

        start_time = time.time()
        OK = self.conn.sftp.get(data, Fname(data).fname())
        stop_time = time.time()
        if OK: tombstone('success')
        else: tombstone('failure ' + self.conn.error_msg())
        tombstone('elapsed time: ' + elapsed_time(stop_time, start_time))


    def do_hosts(self, data:str="") -> None:
        """
        hosts:
            print a list of the available (known) hosts
        """
        tombstone("\n"+"\n".join(sorted(list(gnet.get_ssh_host_info('all')))))


    def do_open(self, data:str="") -> None:
        """
        open { 
                socket { host port } |
                session |
                transport |
                channel [ type ] |
                sftp
             }

        Usually, the order of opening is:

            1. get a *socket* connection.
            2. create an ssh *session*.
            3. create a *transport* layer.
            4. open a *channel* in the established transport layer.
        """

        if not len(data): return
        data = data.strip().split()
        f = getattr(self, '_do_'+data[0], None)

        if f: f(data[1:]) 
        else: tombstone('no operation named {}'.format(data))


    def do_put(self, data:str="") -> None:
        """
        send a file to the remote host.
        """
        if not self.conn.sftp:
            tombstone('sftp channel is not open.')
            return

        if not data:
            tombstone('you have to send something ...')
            return

        f = fname.Fname(data)
        if not f:
            tombstone('no file named {}'.format(str(f)))
            return

        start_time = time.time()
        OK = None
        try:
            OK = self.conn.sftp.put(str(f), f.fname())
        except Exception as e:
            tombstone(str(e))
        stop_time = time.time()
        if OK: tombstone('success')
        else: tombstone('failure ' + self.conn.error_msg())
        tombstone('elapsed time: ' + elapsed_time(stop_time, start_time))


    def do_quit(self, data:str="") -> None:
        """
        quit:
            close up everything gracefully, and then exit.
        """
        self.conn.sock.close()
        os.closerange(3,1024)
        self.do_exit(data)


    def do_read(self, line:str="") -> str:
        """
        Try to read the socket.

        returns -- None or the contents of the socket.
        """
        message = None
        try:
            message = self.conn.sock.read()
        except Exception as e:
            tombstone(str(e))
            tombstone('socket not readable.')
            return
        
        bmessage = list(gnet.tobytes(message))
        if set(message) - set(string.printable):
            for i, _ in enumerate(bmessage):
                print("{} ".format(_), '')
                if not i % 16: print('\n')
        else:
            print(message)


    def do_send(self, data:str="") -> None:
        """
        send { file filename | string }

        Sends stuff over the channel.
        """
        if not self.conn.channel: 
            tombstone('channel not open.')
            self.do_help('send')
            return

        if data.startswith('file'):
            try:
                _, filename = data.split()
                f = fname.Fname(filename)
                if f: data=f()
            except Exception as e:
                tombstone(str(e))
            
        try:
            i = self.conn.channel.send(data)
            tombstone('sent {} bytes.'.format(i))

        except KeyboardInterrupt:
            tombstone('aborting. Control-C pressed.')

        except Exception as e:
            tombstone(str(e))
            
        finally:
            self.conn.open_channel()


    def do_write(self, msg:str="") -> int:
        """
        Write the message to the socket.

        msg -- a str object that gets converted to bytes.

        returns -- number of bytes sent.
        """
        try:
            if not isinstance(msg, bytes):
                msg = gnet.tobytes(msg)
            i = self.conn.sock.send(msg)
        except Exception as e:
            tombstone(str(e))
        else:    
            tombstone('wrote {} bytes to the socket.'.format(i))


    def do_setpass(self, data:str="") -> None:
        """
        setpass [password]
        
            sets, displays, or clears ('none') the password to be used.
        """
        data = data.strip()

        if data.lower() == 'none': self.conn.password = None
        elif not data: tombstone('password is set to {}'.format(self.conn.password))
        else: self.conn.password = data        


    def do_setsockdomain(self, data:str="") -> None:
        """
        setsockdomain [{ af_inet | af_unix }]

            af_inet -- internet sockets
            af_unix -- a socket on local host that most people call a 'pipe'
        """

        if not data: tombstone('socket domain is {}'.format(self.conn.sock_domain)); return
        data = data.strip().lower()

        if data == 'af_inet': self.conn.sock_domain = socket.AF_INET
        elif data == 'af_unix': self.conn.sock_domain = socket.AF_UNIX
        else: tombstone('unknown socket domain: {}'.format(data))


    def do_setsocktype(self, data:str="") -> None:
        """
        setsocktype [{ stream | dgram | raw }]

            stream -- ordinary TCP socket
            dgram  -- ordinary UDP socket
            raw    -- bare metal 
        """
        sock_types = {'stream':socket.SOCK_STREAM, 'dgram':socket.SOCK_DGRAM, 'raw':socket.SOCK_RAW }
        if not data: tombstone('socket type is {}'.format(self.conn.sock_type)); return

        try:
            self.conn.sock_type = sock_types[data.strip().lower()]                

        except:
            tombstone('unknown socket type: {}'.format(data))


    def do_settimeout(self, data:str="") -> None:
        """
        settimeout [ { tcp | auth | banner } {seconds} ]

        Without parameters, settimeout will show the current socket timeout values.
        Otherwise, set it and don't forget it.
        """
        if not data: 
            tombstone('timeouts (tcp, auth, banner): ({}, {}, {})'.format(
                self.conn.tcp_timeout, self.conn.auth_timeout, self.conn.banner_timeout))
            return

        data = data.strip().split()
        if len(data) < 2:
            tombstone('missing timeout value.')
            self.do_help('settimeout')
            return

        try:
            setattr(self.conn, data[0]+'_timeout', float(data[1]))
        except AttributeError as e:
            tombstone('no timeout value for ' + data[0])
        except ValueError as e:
            tombstone('bad value for timeout: {}' + data[1])
        else:
            self.do_settimeout()


    def do_status(self, data:str="") -> None:
        """
        status

            displays the current state of the connection.
        """
        tombstone("debug level: {}".format(self.conn.debug_level()))
        if not self.conn.sock: tombstone('not connected.'); return

        tombstone("local end:   {}".format(self.conn.sock.getsockname()))
        tombstone("remote end:  {}".format(self.conn.sock.getpeername()))
        tombstone("type/domain: {} / {}".format(self.conn.sock_type, self.conn.sock_domain))
        tombstone("ssh session: {}".format(self.conn.client))
        tombstone("transport:   {}".format(self.conn.transport))
        tombstone("sftp layer:  {}".format(self.conn.sftp))
        tombstone("channel:     {}".format(self.conn.channel))


    def do_version(self, data:str="") -> None:
        """
        version

            prints the version
        """
        tombstone("This is the only version you will ever need.")
        tombstone("What difference does it make?")


    """ ***********************************************************************************
    The following functions cannot be called directly, but rather through "open"
    *********************************************************************************** """

    def _do_channel(self, data:list=[]) -> None:
        """
        channel [ session | forward | direct | x11 ]

            Acquire a channel of the desired type. "session" is the default.
        """
        data = 'session' if not data else data[0].lower()
        channel_types = {"session":"session", "forward":"forwarded-tcpip", 
            "direct":"direct-tcpip", "x":"x11"}

        if data not in channel_types.keys() and data not in channel_types.values():
            tombstone('unknown channel type: {}'.format(data))
            return

        tombstone('attempting to create a channel of type {}'.format(data))

        start_time = time.time()
        OK = self.conn.transport.open_channel(data)
        stop_time = time.time()

        if OK: tombstone('success')
        else: tombstone('failed ' + self.conn.error_msg())

        tombstone('elapsed time: {}'.format(elapsed_time(start_time, stop_time)))


    def _do_session(self, data:list=[]) -> None:
        """
        session

            Attempt to create an SSH session with the remote host using
            the socket, transport, and channel that we [may] have already
            openend.
        """
        self.conn.client = SSHClient()
        self.conn.client.load_system_host_keys()
        self.conn.client.set_missing_host_key_policy(paramiko.AutoAddPolicy)
    
        start_time = time.time()
        OK = self.conn.open_session()
        stop_time = time.time()

        if OK: tombstone('ssh session established.')
        else: tombstone('failed '+self.conn.error_msg())

        tombstone('elapsed time: {}'.format(elapsed_time(start_time, stop_time)))


    def _do_sftp(self, data:list=[]) -> None:
        """
        Open an sftp connection to the remote host.
        """
        if not self.conn.transport:
            tombstone('Transport layer is not open. You must create it first.')
            return

        tombstone('creating sftp client.')
        start_time = time.time()
        OK = self.conn.open_sftp()
        stop_time = time.time()

        if OK: tombstone('success')
        else: tombstone('failure '+self.conn.error_msg())

        tombstone('elapsed time: {}'.format(elapsed_time(start_time, stop_time)))
            

    def _do_socket(self, data:list=[]) -> None:
        """
        Attemps to open a new socket with the current parameters.
        """

        if len(data) < 1: 
            tombstone('nothing to do.')
            return

        elif len(data) == 1:
            data.append(None)

        start_time = time.time()
        OK = self.conn.open_socket(data[0], data[1])
        stop_time = time.time()
        if OK: tombstone('connected.')
        else: tombstone(self.conn.error_msg())          
        
        tombstone('elapsed time: {}'.format(elapsed_time(start_time, stop_time)))


    def _do_transport(self, data:str="") -> None:
        """
        Creates a transport layer from an open/active ssh session.
        """
        if not self.conn.client:
            tombstone('You must create an ssh session before you can create a transport layer atop it.')
            return

        tombstone('attempting to create a transport layer')
        start_time = time.time()
        OK = self.conn.open_transport()
        stop_time = time.time()
        if OK: tombstone('success')
        else: tombstone('failed '+self.conn.error_msg())
        tombstone('elapsed time: {}'.format(elapsed_time(start_time, stop_time)))
        

if __name__ == "__main__":

    dorunrun('clear',shell=True)
    while True:
        try:
            Beachhead().cmdloop()

        except KeyboardInterrupt:
            tombstone("Exiting via control-C.")
            sys.exit(os.EX_OK)

        except Exception as e:
            tombstone(str(e))
            sys.exit(1) 
