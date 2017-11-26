# -*- coding: utf-8 -*-
import typing
from   typing import *

"""
This is a definition of the tree structure we require to fully
parse and then compile the recipes.
"""

import collections
from   collections import defaultdict
import json

# Credits
__author__ = 'George Flanagin'
__copyright__ = 'Copyright 2015, University of Richmond'
__credits__ = None
__version__ = '0.5'
__maintainer__ = 'George Flanagin'
__email__ = 'gflanagin@richmond.edu'
__status__ = 'Prototype'

"""
Forward reference to keep the compiler from complaining. This hack
is from Guido van Rossum, 7 Jan 2015 in the discussion of typing
issues in Python 3.6. The hack works in all versions of Python.
"""
class Tree(defaultdict): pass

class Tree(defaultdict):
    """
    Variations of the one line tree (cite: github gist #2012250)
    have been discussed at length on gitHub and the whole of the Internet. 
    In them, Tree() is a pseudo-constructor function
    that returns a defaultdict [from collections] whose members are
    trees. Merely referencing a node brings it into being, no matter
    how deep it is.

    For those who are unfamiliar with the defaultdict, it is just a
    dict that does not throw a KeyError when an attempt is made to
    retrieve a value from a key that does not (yet) exist. The 
    defaultdict just says "I'll create one for you." 

    But what about the value associated with this phantom key? The value 
    is supplied by a function object passed to default dict that is used to 
    create the value. It can be anything that is callable. The UR version
    is based on the extension found in (cite: github gist #4451005) 
    """
    def __init__(self, parent=None):
        """
        This is pretty much the bare __init__ with the parent element
        included.
        """

        self.parent = parent
        defaultdict.__init__(self, lambda: Tree(self))


    def __str__(self, **kwargs):
        """
        Dump to JSON for printability.
        """

        kwargs['sort_keys'] = True
        kwargs['indent'] = 4
        return json.dumps(self, kwargs)


    def add_edges(self, path_to_node:list) -> Tree:
        """
        On occasion, it is convenient to add the edges along the
        graph all the way to some rather deep point. This function
        does the trick. The return value is self, allowing you to
        supply the value. For example:

        t = Tree()
        edges = ['toyota', 'prius', 'v', 'color']
        t.add_edges(edges)='black'
        """
        t = Tree(self)
        for edge in path_to_node:
            t = t[edge]

        return self


    def __bool__(self) -> bool:
        """
        Test to see if the Tree is empty.
        """
        return bool(len(self.keys()))


    def __len__(self) -> int:
        """
        TODO: count the edges.
        """
        return 1 if self else 0        


if __name__ == "__main__":
    pass
else:
    pass
