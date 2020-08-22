# -*- coding: utf-8 -*-
import typing
from typing import *

"""
These decorators are designed to handle hard errors in operation
and provide a stack unwind and dump. The resulting file will be
named $LOG/YYYY-MM-DD/pid. 

Most of the code during development will have a line that looks
something like this:

from gdecorators import trap

"""

# System imports
import contextlib
from   functools import wraps
import inspect
import os
import sys
import types

import gtime
import gpath
from   tombstone import tombstone


# Credits
__author__ = 'George Flanagin'
__copyright__ = 'Copyright 2015, University of Richmond'
__credits__ = 'Based on Github Gist 1148066 by diosmosis'
__version__ = '0.1'
__maintainer__ = 'George Flanagin'
__email__ = 'gflanagin@richmond.edu'
__status__ = 'Prototype'
__license__ = 'MIT'

def trap(func:object) -> None:
    """
    An amplified version of the show_exceptions decorator.
    """

    @wraps(func)
    def wrapper(*args, **kwds):
        __wrapper_marker_local__ = None
    
        try:
            return func(*args, **kwds)

        except Exception as e:
            print(f"{str(e)}")
            # Who am I?
            pid = f'pid{os.getpid()}'

            # First order of business: create a dump file. The file will be under
            # $LOG (if defined) with today's ISO date string as the dir name.
            new_dir = gpath.path_join(os.environ.get('LOG'), gtime.now_as_string()[:10])
            uu.make_dir_or_die(new_dir)

            # The file name will be the pid (possibly plus something like "A" if this
            # is the second time today this pid has failed).
            candidate_name = uu.path_join(new_dir, pid)
            
            tombstone(f"writing dump to file {candidate_name}")

            with open(candidate_name, 'a') as f:
                with contextlib.redirect_stdout(f):
                    # Protect against further failure -- log the exception.
                    try:
                        e_type, e_val, e_trace = sys.exc_info()
                    except Exception as e:
                        tombstone(str(e))

                    print(f'Exception raised {e_type}: "{e_val}"')
                    
                    # iterate through the frames in reverse order so we print the
                    # most recent frame first
                    for frame_info in inspect.getinnerframes(e_trace):
                        f_locals = frame_info[0].f_locals
                
                        # if there's a local variable named __wrapper_marker_local__, we assume
                        # the frame is from a call of this function, 'wrapper', and we skip
                        # it. The problem happened before the dumping function was called.
                        if '__wrapper_marker_local__' in f_locals: continue

                        # log the frame information
                        print('\n**File <{}>, line {}, in function {}()\n    {}'.format(
                            frame_info[1], frame_info[2], frame_info[3], frame_info[4][0].lstrip()
                            ))

                        # log every local variable of the frame
                        for k, v in f_locals.items():
                            try:
                                print('    {} = {}'.format(k, v))
                            except:
                                pass

                    print('\n')
            sys.exit(-1)

    return wrapper

