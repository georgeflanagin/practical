# -*- coding: utf-8 -*-

""" 
Fname, a portable class for manipulating long, complex, and
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


import  fcntl
from   functools import total_ordering
import hashlib
import os
import typing
from   typing import *
from   urllib.parse import urlparse

# Credits
__author__ = 'George Flanagin'
__copyright__ = 'Copyright 2015, University of Richmond'
__credits__ = None
__version__ = '0.6'
__maintainer__ = 'George Flanagin'
__email__ = 'gflanagin@richmond.edu'
__status__ = 'Prototype'

"""
This is Guido's hack to allow forward references for types not yet
defined.
"""
class Fname:
    pass

@total_ordering
class Fname:
    """ 
    Simple class to make filename manipulation more readable.
    Example:
        f = Fname('file.ext')
    The resulting object, f, can be tested with if to see if it exists:
        if not f: ...error...
    Additionally, many manipulations of it are available without constant
    reparsing. A common use is that the str operator returns the fully
    qualified name.
    """

    BUFSIZE = 65536 
    __slots__ = [ '_me', '_is_URI', '_fqn', '_dir', '_fname',
        '_fname_only', '_ext', '_all_but_ext', '_content_hash',
        '_is_URI', '_lock_handle']

    def __init__(self, s:str):
        """ 
        Create an Fname from a string that is a file name or a well
        behaved URI. An Fname consists of several strings, each of which
        corresponds to one of the commonsense parts of the file name.
        Members:
            _me -- whatever you used to create the object.
            _is_URI -- boolean
            _fqn -- calculated full name
            _dir -- just the directory part of the name
            _fname -- the file and the extension
            _fname_only -- no dir and no extension
            _ext -- just the extension (if it has one)
            _all_but_ext -- the complement of _ext
            _content_hash -- hexdigit string representing the contents
                the last time the file was read.
            _lock_handle -- an entry in the logical unit table.
        Raises a ValueError if the argument is empty.
        """

        if not s or not isinstance(s, str): 
            raise ValueError('Cannot create empty Fname object.')

        self._me = s
        self._is_URI = False
        self._fqn = ""
        self._dir = ""
        self._fname = ""
        self._fname_only = ""
        self._ext = ""
        self._all_but_ext = ""
        self._content_hash = ""

        self._is_URI = True if "://" in s else False
        if self._is_URI and 'file://' in s:
            tup = urlparse(s)
            self._fqn = tup.path
        else:
            self._fqn = os.path.abspath(os.path.expandvars(os.path.expanduser(s)))
        self._dir, self._fname = os.path.split(self._fqn)
        self._fname_only, self._ext = os.path.splitext(self._fname)
        self._all_but_ext = self._dir + os.path.sep + self._fname_only

        self._lock_handle = None


    def __bool__(self) -> bool:
        """ 
        returns: -- True if the Fname object is associated with something
        that exists in the file system AT THE TIME THE FUNCTION IS CALLED.
        Note: this allows one to build the Fname object at a time when "if"
        would return False, open the file for write, test again, and "if"
        will then return True.
        """

        return os.path.isfile(self._fqn)


    def __call__(self, new_content:str=None) -> Union[bytes, Fname]:
        """
        Return the contents of the file as an str object.
        """

        content = ""
        if new_content is None:
            with open(str(self), 'rb') as f:
                content = f.read()
        else:
            with open(str(self), 'wb+') as f:
                f.write(bytes(new_content))
            
        return content if new_content is None else self
        


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


    def __matmul__(self, other) -> bool:
        """
        returns True if the files' contents are the same. We will
        check to ensure that each is really a file that exists, and
        then check the size before we check the contents.
        """
        if not isinstance(other, Fname):
            return NotImplemented

        if not self or not other: return False
        if len(self) != len(other): return False

        # Gotta look at the contents. See if our hash is known.
        if not len(self._content_hash): self()
            
        # Make sure the other object's hash is known.
        if not len(other._content_hash): other()
        return self._content_hash == other._content_hash


    @property
    def all_but_ext(self) -> str:
        """ 
        returns: -- The directory, with the filename stub, but no extension.
        f.all_but_ext() =>> '/home/data/import/big.file' ... note lack of trailing dot
        """

        return self._all_but_ext


    @property
    def busy(self) -> bool:
        """
        returns: -- 
                True: iff the file exists, we have access, and we cannot 
                    get get an exclusive lock.
                None: if the file does not exist, or if it exists and we 
                    have no access to the file (therefore we can never 
                    lock it).
                False: otherwise. 
        """
        
        # 1: does the file exist?
        if not self: return None

        # 2: if the file is locked by us, then it is not "busy".
        if self.locked: return False

        # 3: are we allowed to open the file?
        if not os.access(str(self), os.R_OK): 
            print('No access to {}.'.format(str(self)))
            return None

        # 4: OK, we are allowed access, but can we open it? 
        try:
            fd = os.open(str(self), os.O_RDONLY)
        except Exception as e:
            print('Cannot open {}, so it is busy.'.format(str(self)))
            return True

        # 5: Can we lock it?
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)

        except BlockingIOError as e:
            print('No lock available on {}, so it is busy'.format(str(self)))
            rval = True

        except Exception as e:
            print(str(e))
            rval = None

        else:
            print('{} is locked.'.format(str(self)))
            rval = False

        finally:
            try:
                os.close(fd)
            except:
                pass
            return rval


    @property
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


    @property
    def ext(self) -> str:
        """ 
        returns: -- The extension, if any.
        f.ext() =>> 'dat'
        """

        return self._ext


    @property
    def fname(self) -> str:
        """ 
        returns: -- The filename only (no directory), including the extension.
        f.fname() =>> 'big.file.dat'
        """

        return self._fname


    @property
    def fname_only(self) -> str:
        """ 
        returns: -- The filename only. No directory. No extension.
        f.fname_only() =>> 'big.file'
        """

        return self._fname_only


    @property
    def fqn(self) -> str:
        """ 
        returns: -- The fully qualified name.
        f.fqn() =>> '/home/data/import/big.file.dat'
        NOTE: this is the same result as you get with str(f)
        """

        return self._fqn


    @property
    def hash(self) -> str:
        """
        Return the hash if it has already been calculated, otherwise
        calculate it and then return it. 
        """
        if len(self._content_hash) > 0: 
            return self._content_hash

        hasher = hashlib.md5()

        with open(str(self), 'rb') as f:
            while True:
                segment = f.read(Fname.BUFSIZE)
                if not segment: break
                hasher.update(segment)
        
        self._content_hash = hasher.hexdigest()
        return self._content_hash


    @property
    def is_URI(self) -> bool:
        """ 
        Returns true if the original string used in the ctor was
            something like "file://..." or "http://..." 
        """

        return self._is_URI


    def lock(self, exclusive:bool = True, nowait:bool = True) -> bool:
        mode = fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH
        if nowait: mode = mode | fcntl.LOCK_NB
        
        try:
            self._lock_handle = os.open(str(self), os.O_RDONLY)
            fcntl.flock(self._lock_handle, mode)
        except Exception as e:
            print(str(e))
            return False
        else:
            return True
            

    @property
    def locked(self) -> bool:
        """
        Test it...  Note that this function returns True if this process
            has the file locked. self.busy checks if someone else has the
            file locked.
        """
        return self._lock_handle is not None


    def show(self) -> None:
        """ 
            this is a diagnostic function only. Probably not used
            in production. 
        """
        print("if test returns       " + str(int(self.__bool__())))
        print("str() returns         " + str(self))
        print("fqn() returns         " + self.fqn)
        print("fname() returns       " + self.fname)
        print("fname_only() returns  " + self.fname_only)
        print("directory() returns   " + self.directory)
        print("ext() returns         " + self.ext)
        print("all_but_ext() returns " + self.all_but_ext)
        print("len() returns         " + str(len(self)))
        s = self()
        try:
            print("() returns            \n" + s[0:30] + ' .... ' + s[-30:])
        except TypeError as e:
            print("() doesn't make sense on a binary file.")
        print("hash() returns        " + self.hash)
        print("locked() returns      " + str(self.locked))


    def unlock(self) -> bool:
        """
        returns: -- True iff the file was locked before the call,
            False otherwise.
        """
        try:
            fcntl.flock(self._lock_handle, fcntl.LOCK_UN)
        except Exception as e:
            print(str(e))
            return False
        else:
            return True
        finally:
            self._lock_handle = None
            

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("You must provide a file name to parse.")
        exit(1)
    f = Fname(sys.argv[1])
    f.show()
    f()
else:
    # print(str(os.path.abspath(__file__)) + " compiled.")
    pass
