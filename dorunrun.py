# -*- coding: utf-8 -*-
""" Generic, bare functions, not a part of any object or service. """

import typing
from   typing import *

import subprocess

from   tombstone import tombstone

# Credits
__author__ = 'George Flanagin'
__copyright__ = 'Copyright 2020, University of Richmond'
__credits__ = None
__version__ = '0.1'
__maintainer__ = 'George Flanagin'
__email__ = 'me@georgeflanagin.com'
__status__ = 'Prototype'

__license__ = 'MIT'

def dorunrun(command:Union[str, list],
    timeout:int=None,
    verbose:bool=False) -> bool:
    """
    A wrapper around (almost) all the complexities of running child 
        processes.

    command -- a string, or a list of strings, that constitute the
        commonsense definition of the command to be attemped. 
    timeout -- generally, we don't
    verbose -- do we want some narrative to stderr?

    returns -- True if the child process returns a zero.
    """

    if verbose: tombstone(f"original command argument: <{command}>")

    if isinstance(command, (list, tuple)):
        command = [str(_) for _ in command]
        shell = False

    elif isinstance(command, str):
        shell = True

    else:
        raise Exception(f"Bad argument type to run: {command}")

    if verbose: tombstone(f"shlex-ed command argument: <{command}>")
    r = None

    try:
        result = subprocess.run(command, 
            timeout=timeout, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            shell=shell)

        r = result.returncode

        # Always show errors even if verbose is False.
        if not r:
            verbose and tombstone("Child process terminated without error.")
        elif r < 0:
            tombstone(f"Child process terminated by signal {-r}")
        else:
            tombstone(f"Child process returned an error: {r}")

        if r or shell or verbose:
            tombstone(f"stdout: {result.stdout}")
            tombstone(f"stderr: {result.stderr}")

    except subprocess.TimeoutExpired as e:
        tombstone(f"Process exceeded time limit at {e.timeout} seconds.")    

    except Exception as e:
        tombstone(f"Unexpected error: {type_and_text(e)}")

    finally:
        return r == 0


