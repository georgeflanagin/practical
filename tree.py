# -*- coding: utf-8 -*-
import typing
from typing import *

"""
This is a definition of the tree structure we require to fully
parse and then compile the recipes.
"""

import collections
import functools
import json
import pprint

# Credits
__author__ = 'George Flanagin'
__copyright__ = ['Copyright 2015, 2016, 2017, University of Richmond',
    'Copyright 2017, 2018 George Flanagin'],
__credits__ = None
__version__ = '0.5'
__license__ = 'https://www.gnu.org/licenses/gpl.html'
__maintainer__ = 'George Flanagin'
__email__ = 'gflanagin@richmond.edu'
__status__ = 'Prototype'

"""
Forward reference to keep the compiler from complaining. This hack
is from Guido van Rossum, 7 Jan 2015 in the discussion of typing
issues in Python 3.6. The hack works in all versions of Python.
"""
class Tree(collections.defaultdict): 
    pass


def tree_to_dict(t:Tree) -> Dict: 
    """
    Some serializers will fail on types from collections.
    """
    dict_of_tree = {}
    for k, v in t.items(): 
        dict_of_tree[k] = tree_to_dict(v) if isinstance(v, Tree) else v

    return dict_of_tree


class Tree(collections.defaultdict):
    """
    Variations of the one line tree (cite: github gist #2012250) have
    been discussed at length on gitHub and the whole of the Internet.
    In them, Tree() is a pseudo-constructor function that returns a
    defaultdict [from collections] whose members are trees. Merely
    referencing a node brings it into being, no matter how deep it is.

    For those who are unfamiliar with the defaultdict, it is just a dict
    that *may* not throw a KeyError when an attempt is made to retrieve
    a value from a key that does not (yet) exist. This defaultdict just
    says "I'll create one for you," although you may create defaultdict-s
    that behave as badly as desired.

    But what about the value associated with this phantom key? The value
    is supplied by a function object passed to default dict that is
    used to create the value. It can be anything that is callable. The
    UR version is based on the extension found in (cite: github gist
    #4451005).

    The only exception is the NotImplemented singleton, raised if you
    attempt to graft a Tree to something that is a non-Tree. 
    """

    def __init__(self, parent=None):
        """
        This is pretty much the bare __init__ with the parent element
        included.
        """
        self.parent = parent
        collections.defaultdict.__init__(self, lambda: Tree(self))


    def __str__(self):
        """
        JSON is the Lingua Franca of data exchange. Given that printing
        is the most common method of debug inspection, the parameters
        here sort keys for ease of comparison, and reject inter-element
        white space.

        Note that json.dumps does not care that this is a class from 
        collections because it uses .keys() and .values() to acquire views
        of the contents.
        """
        return json.dumps(self, sort_keys=True, 
            skipkeys=True, ensure_ascii=False, indent=4,
            separators=(',', ':'), )


    def __eq__(self, other:Tree) -> bool:
        """
        Determine if two trees are the same w/o looking at all the subtrees.
        """
        return id(self) == id(other)        


    def __contains__(self, other:Tree) -> bool:
        """
        Implement the 'in' operator as 'other in self'
        """        
        if not isinstance(other, Tree): 
            return NotImplemented

        p = other.parent
        while p is not None:
            if p == self: return True
            p = p.parent
        else:
            return False


    def __bool__(self) -> bool:
        """
        Test to see if the Tree is empty.
        """
        return bool(len(self.keys()))


    def __len__(self) -> int:
        """
        Counts the child edges in the graph, breadth first.
        """
        edge_count=0
        edge_count += len(self.keys())
        for _ in self.keys():
            edge_count += len(_) if isinstance(_, Tree)  else 1
        return edge_count


    def add_edges(self, path_to_node:List) -> Tree:
        """
        On occasion, it is convenient to add the edges along the graph
        all the way to some rather deep point. This function does the
        trick. The return value is self, allowing you to supply the
        value. For example:

        t = Tree()
        edges = ['toyota', 'prius', 'v', 'color']
        t.add_edges(edges)='black'
        """
        t = Tree(self)
        for edge in path_to_node:
            t = t[edge]

        return self
        

    def all_keys(self, sep:str='.') -> List[str]:
        """
        sep -- a char (str) that is to be used as a separator between
        levels in the tree. Assuming you used the dot, you will
        get.key.names.like.this.

        returns -- a list of all the keys

        NOTE: given that the function is recursive, it doesn't make sense
            to provide it as a option. 
        """
        key_list = []
        key_list.extend(list(self.keys()))   
        for _ in self.keys():
            try:
                key_list.extend(self.all_keys())
            except:
                pass

        return key_list     


    def depth(self) -> int:
        """
        How far down are we?
        """
        i = 0
        while self.parent is not None:
            i += 1
            self = self.parent

        return i


    def find(self, item_name:str) -> List[Tree]:
        """
        Return a list of nodes whose keys are equal to the item_name.
        """
        here = self
        matches = []
            
        pass        


    def get_root(self) -> Tree:
        """
        Get the true root node of this Tree.
        """

        t = self
        while t.parent is not None: t = t.parent
        return t


    def graft(self, other_tree:Tree, as_edge_name:str) -> Tree:
        """
        Often we build two trees independently and need to graft one to
        the other.
        """
        if isinstance(other_tree, Tree):
            self[as_edge_name] = other_tree
            other_tree.parent = self[as_edge_name]
        else:
            return NotImplemented

        return self

    
    def part_of(self, other:Tree) -> bool:
        """
        Decide if two nodes belong to the same Tree.
        """
        if not isinstance(other, Tree): 
            return NotImplemented

        return self.get_root() == other.get_root()


if __name__ == "__main__":
    pass
else:
    pass
