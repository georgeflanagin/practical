#!/usr/bin/env python
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

# Builtins
import argparse
import cmd
import logging
import os
import socket
import subprocess
import sys
import time
import typing
from   typing import *

# Paramiko
import logging
import paramiko 
from   paramiko import SSHClient, SSHConfig, SSHException

import fname
import gnet
from   tombstone import tombstone

if sys.version_info < __required_version__:
    tombstone('This program requires Python {} or greater.'.format(__required_version__))
    sys.exit(os.EX_SOFTWARE)

class SocketConnection:

    """
    __slots__ = [
        'my_host', 'user', 'remote_host', 'remote_port',
        'ssh_info', 'auth_timeout', 'banner_timeout',' tcp_timeout',
        'sock_type', 'sock_domain', 'password', 'sock',
        'sock_transport', 'channel', 'client', 'sftp',
        'error'
        ]
    """

    def __init__(self):
        # Identification members
        self.my_host = socket.getfqdn().replace('-','.')
        self.user = gnet.me()
        self.remote_host = ""
        self.remote_port = 0
        self.ssh_info = None

        # Performance parameters.
        self.auth_timeout = 1.0
        self.banner_timeout = 1.0
        self.tcp_timeout = 1.0

        # Socket types
        self.sock_type = socket.SOCK_STREAM
        self.sock_domain = socket.AF_INET

        # Connection parameters.
        self.password = None
        self.sock = None
        self.transport = None
        self.channel = None
        self.client = None
        self.sftp = None

        # Most recent error.
        self.error = None
        logging.getLogger("paramiko").setLevel(logging.CRITICAL)
        paramiko.util.log_to_file("beachhead.log")


    
    def __bool__(self) -> bool: 
        return self.error is None and self.sock is not None


    def __str__(self) -> str:
        description = []
        description.append( "no connection" if not self.sock else "{}:{} {}".format(
            self.remote_host, self.remote_port, self.error_msg()))
        for slot in SocketConnection.__slots__:
            description.append("{} = {}".format(slot, getattr(self, slot)))
        return "\n".join(description)


    def block(self) -> None:
        self.sock.settimeout(None)


    def blocking(self) -> bool:
        return self.sock.getblocking()


    def unblock(self) -> None:
        self.sock.settimeout(0.0)


    def close(self) -> None:
        if self.sftp: self.sftp.close(); self.sftp = None
        if self.channel: self.channel.close(); self.channel = None
        if self.transport: self.transport.close(); self.transport = None
        if self.client: self.client.close(); self.client = None
        if self.sock: self.sock.close(); self.sock = None


    def debug_level(self, level:int=None) -> int:
        """
        Manipulate the logging level.
        """

        if level is None:
            return logging.getLogger('paramiko').getEffectiveLevel()      
        else:
            logging.getLogger('paramiko').setLevel(level)
            return self.debug_level()  


    def error_msg(self) -> str:
        return str(self.error)


    def open_channel(self, channel_type:str="session") -> bool:
        """
        Acquire a channel of the desired type. "session" is the default.
        """
        self.error = None
        channel_types = {
            "session":"session", "forward":"forwarded-tcpip", "direct":"direct-tcpip", "x":"x11"
            }

        if data not in channel_types.keys() and data not in channel_types.values():
            self.error = 'unknown channel type: {}'.format(data)
            return False

        try:
            self.channel = self.transport.open_channel(data)
        except Exception as e:
            self.error = str(e)
        finally:
            return self.error is not None


    def open_session(self) -> bool:
        """
        Attempt to create an SSH session with the remote host using
        the socket, transport, and channel that we [may] have already
        openend.
        """
        self.error = None
        self.client = SSHClient()
        self.client.load_system_host_keys()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy)

        try:
            if not self.password:
                self.client.connect(self.ssh_info['hostname'],
                    int(self.ssh_info['port']),
                    username=self.ssh_info['user'],
                    key_filename=self.ssh_info['identityfile'],
                    sock=self.sock)        

            else:
                self.client.connect(self.ssh_info['hostname'], 
                    int(self.ssh_info['port']), 
                    username=self.ssh_info['user'], 
                    password=self.password,
                    sock=self.sock)

        except paramiko.ssh_exception.BadAuthenticationType as e:
            self.error = str(e)

        except Exception as e:
            self.error = str(e)

        finally:
            return self.error is None


    def open_sftp(self, data:list=[]) -> bool:
        """
        Open an sftp connection to the remote host.
        """
        self.error = None
        try:
            self.sftp = paramiko.SFTPClient.from_transport(self.transport)

        except Exception as e:
            self.error = str(e)

        finally:
            return self.error is None


    def open_socket(self, host:str, port:int=None) -> bool:
        """
        Attemps to open a new socket with the current parameters.
        """
        self.error = None
        self.ssh_info = gnet.get_ssh_host_info(host)
        if not self.ssh_info: 
            self.error = 'unknown host'
            return False

        hostname = self.ssh_info['hostname'] 
        try:
            port = int(port)
        except:
            port = int(self.ssh_info['port'])

        self.sock = socket.socket(self.sock_domain, self.sock_type)
        try:
            self.sock.settimeout(self.tcp_timeout)
            self.sock.connect((hostname,port))
        except socket.timeout as e:
            self.error = 'timeout of {} seconds exceeded.'.format(self.tcp_timeout)
        except Exception as e:
            self.error = str(e)
        else:
            self.remote_host = hostname
            self.remote_port = port
        
        return self.error is None


    def open_transport(self, data:str="") -> bool:
        """
        Creates a transport layer from an open/active ssh session.
        """
        self.error = None
        if not self.client:
            self.error = 'no open session for transport'
            return False

        try:
            self.transport = self.client.get_transport()

        except Exception as e:
            self.error = str(e)

        finally:
            return self.error is None


    def read(self, buffsize:int=4096) -> str:
        """
        Read from the socket. 

        buffsize -- read chunks in this size.
        """
        message = None
        try:
            message = self.sock.recv(buffsize)
        except KeyboardInterrupt as e:
            print('Tired of waiting, eh?')
        except Exception as e:
            tombstone(str(e))
            
        return '' if message is None else message.decode('utf-8')
            

            
    def send(self, message:str='') -> int:
        """
        write the message to the socket.
    
        message -- can be bytes or str; always converted to bytes.

        returns -- number of bytes read.
        """
        if isinstance(message, str):
            messsage = gnet.tobytes(message)
        result = self.sock.sendall(message)
        return result

    
    def timeouts(self) -> tuple:
        return self.tcp_timeout, self.auth_timeout, self.banner_timeout


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
        self.hop = SocketConnection()

    
    def __bool__(self) -> bool: 
        return self.sock is not None


    def __str__(self) -> str:
        return "{}:{}".format(self.hop.remote_host, self.hop.remote_port)


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
        if self.hop: self.hop.close()
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
            tombstone(blue('debug level is {}'.format(self.hop.debug_level())))
            return

        logging_levels = {
            "CRITICAL":"50",
            "ERROR":"40",
            "WARNING":"30",
            "INFO":"20",
            "DEBUG":"10",
            "NOTSET":"0" }

        data = data.strip().upper()
        if data not in logging_levels.keys() and data not in logging_levels.values():
            tombstone('not sure what this level means: {}'.format(data))
            return
            
        try:
            level = int(data)
        except:
            level = int(logging_levels[data])
        finally:
            self.hop.debug_level(level)
            


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
            in_, out_, err_ = self.hop.channel.exec_command(data)

        except KeyboardInterrupt as e:
            tombstone('aborting. Control-C pressed.')

        except Exception as e:
            tombstone(str(e))

        else:
            out_.channel.recv_exit_status();
            tombstone(out_.readlines())

        finally:
            self.hop.open_channel()


    def do_error(self, data:str="") -> None:
        """
        error [reset]

        [re]displays the error of the connection, and optionally resets it
        """
        tombstone(self.hop.error)
        if 'reset'.startswith(data.strip().lower()): self.hop.error = None


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

        hosts  <- This will give a list of "known hosts"
        open socket host port  <- Specify your target, and create a connection.
        set password AbraCadabra <- Only if you need it; keys don't require
            a password.
        open session <- Using the info from ~/.ssh/config
        open transport <- You will need this if you intend to do anything
            beyond sitting at your desk admiring what you have done so far.
        
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
        if not self.hop.sftp:
            tombstone('sftp channel is not open.')
            return

        start_time = time.time()
        OK = self.hop.sftp.get(data, Fname(data).fname())
        stop_time = time.time()
        if OK: tombstone('success')
        else: tombstone('failure ' + self.hop.error_msg())
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
        if not self.hop.sftp:
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
            OK = self.hop.sftp.put(str(f), f.fname())
        except Exception as e:
            tombstone(str(e))
        stop_time = time.time()
        if OK: tombstone('success')
        else: tombstone('failure ' + self.hop.error_msg())
        tombstone('elapsed time: ' + elapsed_time(stop_time, start_time))


    def do_quit(self, data:str="") -> None:
        """
        quit:
            close up everything gracefully, and then exit.
        """
        self.hop.sock.close()
        os.closerange(3,1024)
        self.do_exit(data)


    def do_read(self, line:str="") -> str:
        """
        Try to read the socket.

        returns -- None or the contents of the socket.
        """
        message = None
        try:
            message = self.hop.sock.read()
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
        if not self.hop.channel: 
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
            i = self.hop.channel.send(data)
            tombstone('sent {} bytes.'.format(i))

        except KeyboardInterrupt:
            tombstone('aborting. Control-C pressed.')

        except Exception as e:
            tombstone(str(e))
            
        finally:
            self.hop.open_channel()


    def do_write(self, msg:str="") -> int:
        """
        Write the message to the socket.

        msg -- a str object that gets converted to bytes.

        returns -- number of bytes sent.
        """
        try:
            if not isinstance(msg, bytes):
                msg = gnet.tobytes(msg)
            i = self.hop.sock.send(msg)
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

        if data.lower() == 'none': self.hop.password = None
        elif not data: tombstone('password is set to {}'.format(self.hop.password))
        else: self.hop.password = data        


    def do_setsockdomain(self, data:str="") -> None:
        """
        setsockdomain [{ af_inet | af_unix }]

            af_inet -- internet sockets
            af_unix -- a socket on local host that most people call a 'pipe'
        """

        if not data: tombstone('socket domain is {}'.format(self.hop.sock_domain)); return
        data = data.strip().lower()

        if data == 'af_inet': self.hop.sock_domain = socket.AF_INET
        elif data == 'af_unix': self.hop.sock_domain = socket.AF_UNIX
        else: tombstone('unknown socket domain: {}'.format(data))


    def do_setsocktype(self, data:str="") -> None:
        """
        setsocktype [{ stream | dgram | raw }]

            stream -- ordinary TCP socket
            dgram  -- ordinary UDP socket
            raw    -- bare metal 
        """
        sock_types = {'stream':socket.SOCK_STREAM, 'dgram':socket.SOCK_DGRAM, 'raw':socket.SOCK_RAW }
        if not data: tombstone('socket type is {}'.format(self.hop.sock_type)); return

        try:
            self.hop.sock_type = sock_types[data.strip().lower()]                

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
                self.hop.tcp_timeout, self.hop.auth_timeout, self.hop.banner_timeout))
            return

        data = data.strip().split()
        if len(data) < 2:
            tombstone('missing timeout value.')
            self.do_help('settimeout')
            return

        try:
            setattr(self.hop, data[0]+'_timeout', float(data[1]))
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
        tombstone("debug level: {}".format(self.hop.debug_level()))
        if not self.hop.sock: tombstone('not connected.'); return

        tombstone("local end:   {}".format(self.hop.sock.getsockname()))
        tombstone("remote end:  {}".format(self.hop.sock.getpeername()))
        tombstone("type/domain: {} / {}".format(self.hop.sock_type, self.hop.sock_domain))
        tombstone("ssh session: {}".format(self.hop.client))
        tombstone("transport:   {}".format(self.hop.transport))
        tombstone("sftp layer:  {}".format(self.hop.sftp))
        tombstone("channel:     {}".format(self.hop.channel))


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
        OK = self.hop.transport.open_channel(data)
        stop_time = time.time()

        if OK: tombstone('success')
        else: tombstone('failed ' + self.hop.error_msg())

        tombstone('elapsed time: {}'.format(elapsed_time(start_time, stop_time)))


    def _do_session(self, data:list=[]) -> None:
        """
        session

            Attempt to create an SSH session with the remote host using
            the socket, transport, and channel that we [may] have already
            openend.
        """
        self.hop.client = SSHClient()
        self.hop.client.load_system_host_keys()
        self.hop.client.set_missing_host_key_policy(paramiko.AutoAddPolicy)
    
        start_time = time.time()
        OK = self.hop.open_session()
        stop_time = time.time()

        if OK: tombstone('ssh session established.')
        else: tombstone('failed '+self.hop.error_msg())

        tombstone('elapsed time: {}'.format(elapsed_time(start_time, stop_time)))


    def _do_sftp(self, data:list=[]) -> None:
        """
        Open an sftp connection to the remote host.
        """
        if not self.hop.transport:
            tombstone('Transport layer is not open. You must create it first.')
            return

        tombstone('creating sftp client.')
        start_time = time.time()
        OK = self.hop.open_sftp()
        stop_time = time.time()

        if OK: tombstone('success')
        else: tombstone('failure '+self.hop.error_msg())

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
        OK = self.hop.open_socket(data[0], data[1])
        stop_time = time.time()
        if OK: tombstone('connected.')
        else: tombstone(self.hop.error_msg())          
        
        tombstone('elapsed time: {}'.format(elapsed_time(start_time, stop_time)))


    def _do_transport(self, data:str="") -> None:
        """
        Creates a transport layer from an open/active ssh session.
        """
        if not self.hop.client:
            tombstone('You must create an ssh session before you can create a transport layer atop it.')
            return

        tombstone('attempting to create a transport layer')
        start_time = time.time()
        OK = self.hop.open_transport()
        stop_time = time.time()
        if OK: tombstone('success')
        else: tombstone('failed '+self.hop.error_msg())
        tombstone('elapsed time: {}'.format(elapsed_time(start_time, stop_time)))
        

if __name__ == "__main__":

    subprocess.call('clear',shell=True)
    while True:
        try:
            Beachhead().cmdloop()

        except KeyboardInterrupt:
            tombstone("Exiting via control-C.")
            sys.exit(os.EX_OK)

        except Exception as e:
            tombstone(str(e))
            sys.exit(1) 
