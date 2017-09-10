# -*- coding: utf-8 -*-

""" Fname, a portable class for manipulating long, complex, and
    confusing path and file names on Linux and Windows.

    Experience has taught us that we make a lot of mistakes by placing
    files in the wrong directories, or getting mixed up over extensions.
    In the examples below, we will use the file name:

           f = Fname('/home/data/import/big.file.dat')

    This is implemented a portable way, so the same logic will work
    on Windows NTFS for the above path written as:

           \\home\data\import\big.file.dat

    This class supports all the comparison operators ( ==, !=, <, <=,
    >, >= ) and when doing so it uses the fully qualifed name.
"""


from   functools import total_ordering
import os
from   urllib.parse import urlparse

# Credits
__author__ = 'George Flanagin'
__copyright__ = 'Copyright 2015, University of Richmond'
__credits__ = None
__version__ = '0.6'
__maintainer__ = 'George Flanagin'
__email__ = 'gflanagin@richmond.edu'
__status__ = 'Prototype'

class Fname:
    pass

@total_ordering
class Fname:
    """ Simple class to make filename manipulation more readable.

    Example:

        f = Fname('file.ext')

    The resulting object, f, can be tested with if to see if it exists:

        if not f: ...error...

    Additionally, many manipulations of it are available without constant
    reparsing. A common use is that the str operator returns the fully
    qualified name.

    NOTE: Fname only deals with files' names not their contents!!!
    """

    def __init__(self, s:str):
        """ Create an Fname from a string that is a file name or a well
        behaved URI. An Fname consists of several strings, each of which
        corresponds to one of the commonsense parts of the file name."""

        self._me = s
        self._is_URI = False
        self._fqn = ""
        self.__dir = ""
        self._fname = ""
        self._fname_only = ""
        self._ext = ""
        self._all_but_ext = ""

        if not s or not isinstance(s, str) or not len(s): return

        self._is_URI = True if "://" in s else False
        if self._is_URI and 'file://' in s:
            tup = urlparse(s)
            self._fqn = tup.path
        else:
            self._fqn = os.path.abspath(s)
        self._dir, self._fname = os.path.split(self._fqn)
        self._fname_only, self._ext = os.path.splitext(self._fname)
        self._all_but_ext = self._dir + os.path.sep + self._fname_only


    def __bool__(self) -> bool:
        """ 
        returns: -- True if the Fname object is associated with something
        that exists in the file system AT THE TIME THE FUNCTION IS CALLED.

        Note: this allows one to build the Fname object at a time when "if"
        would return False, open the file for write, test again, and "if"
        will then return True.
        """

        return os.path.isfile(self._fqn)


    def __call__(self, sep:str=None) -> object:
        """
        Return the contents of the file as an str object.
        """

        if not self: return None
        with open(str(self)) as f:
            if sep is None: return f.read()
            else: return f.read().split(sep)


    def __len__(self) -> int:
        """
        returns -- number of bytes in the file
        """
        if not self: return 0
        else: return os.stat(str(self)).st_size


    def __str__(self) -> str:
        """ 
        returns: -- The fully qualified name.

        str(f) =>> '/home/data/import/big.file.dat'
        """

        return self._fqn


    def __eq__(self, other) -> bool:
        """ 
        The two fname objects are equal if and only if their fully
        qualified names are equal. 
        """

        if isinstance(other, Fname):
            return str(self) == str(other)
        elif isinstance(other, str):
            return str(self) == other
        else:
            return NotImplemented


    def __lt__(self, other) -> bool:
        """ 
        The less than operation is done with the fully qualified names. 
        """

        if isinstance(other, Fname):
            return str(self) < str(other)
        elif isinstance(other, str):
            return str(self) < other
        else:
            return NotImplemented


    def __and__(self, other) -> bool:
        """
        returns True if the files' contents are the same. We will
        check to ensure that each is really a file that exists, and
        then check the size before we check the contents.
        """
        if str(other) == other: other=Fname(other)
        if not self or not other: return False
        if len(self) != len(other): return False
        return self() == other()


    def is_URI(self) -> bool:
        """ 
        Returns true if the original string used in the ctor was
            something like "file://..." or "http://..." 
        """

        return self._is_URI


    def fqn(self) -> str:
        """ 
        returns: -- The fully qualified name.

        f.fqn() =>> '/home/data/import/big.file.dat'

        NOTE: this is the same result as you get with str(f)
        """

        return self._fqn


    def directory(self, terminated:bool=False) -> str:
        """ 
        returns: -- The directory part of the name.

        f.directory() =>> '/home/data/import' ... note the lack of a
            trailing solidus in the default behavior.
        """

        if terminated:
            return self._dir + os.sep
        else:
            return self._dir


    def fname(self) -> str:
        """ 
        returns: -- The filename only (no directory), including the extension.

        f.fname() =>> 'big.file.dat'
        """

        return self._fname


    def ext(self) -> str:
        """ 
        returns: -- The extension, if any.

        f.ext() =>> 'dat'
        """

        return self._ext


    def all_but_ext(self) -> str:
        """ 
        returns: -- The directory, with the filename stub, but no extension.

        f.all_but_ext() =>> '/home/data/import/big.file' ... note lack of trailing dot
        """

        return self._all_but_ext


    def fname_only(self) -> str:
        """ 
        returns: -- The filename only. No directory. No extension.

        f.fname_only() =>> 'big.file'
        """

        return self._fname_only


    def show(self) -> None:
        """ 
            this is a diagnostic function only. Probably not used
            in production. 
        """
        print(("if test returns       " + str(int(self._bool__()))))
        print(("str() returns         " + str(self)))
        print(("fqn() returns         " + self.fqn()))
        print(("fname() returns       " + self.fname()))
        print(("fname_only() returns  " + self.fname_only()))
        print(("directory() returns   " + self.directory()))
        print(("ext() returns         " + self.ext()))
        print(("all_but_ext() returns " + self.all_but_ext()))
        print(("len() returns         " + str(len(self))))
        s = self()
        print(("() returns            " + s[0:30] + ' .... ' + s[-30:]))

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("You must provide a file name to parse.")
        exit(1)
    f = Fname(sys.argv[1])
    f.show()
else:
    # print(str(os.path.abspath(__file__)) + " compiled.")
    print("*", end="")

