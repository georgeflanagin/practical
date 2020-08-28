# Practical Python

## General guide

This small collection of source files is organized around operations
that I have tended need in my code, regardless of the programming language
that I have been using at the time. Because I have been using Python for
the past seven years, it seems logical to code them (again) in Python.

### `beachhead`

This is the only file not mentioned in the init. This is a standalone
utility derived from the need to repeatedly test the `paramiko` library
as new versions come out.

### `devnull`

More of a lark than a utility. This class has a file-like interface, 
and works like `/dev/null`.

### `dorunrun`

A simpler wrapper around `subprocess.run` that allows only one
way to do things.

### `fifo`

A robust wrapper around kernel pipes for interprocess communication.

### `fname`

The interal object, `fname.File`, allows one to have a single object
that represents both the filename and the file object. From the 
comments in the code, and if `f` is your `File`, then:

```
Properties:
    f.all_but_ext -- the name, minus any extension.
    f.busy -- True if we have access but no lock, and we cannot
        lock the file.
    f.directory -- the directory part of the name.
    f.empty -- True even if the file is just white space and no 
        longer than two bytes.
    f.ext -- the extension, if any.
    f.fname -- the file name + extension.
    f.fname_only -- just the file name.
    f.fqn -- the whole, exploded name as a string.
    f.hash -- hash of the contents. Calculates it if the file
        has not yet been read.
    f.is_URI -- if the orginal name started with a scheme.
    f.locked -- True if we have the file locked.
    
Operators and operations:
    f() -- returns the contents of the file.
    f == g, f < g, etc. -- returns True if the names have this
        relationship after all paths and env vars are resolved.
    f @ g -- returns True if the files have the same content. NOTE:
        the names of the files are irrelevant.
    bool(f) -- at the time of the function call, does f refer to 
        an object in the file system that exists and is a file.
    len(f) -- returns the length of the file.     
    str(f) -- the fully qualified and resolved name.      
    f.lock() -- returns True if successful.
    f.unlock() -- only returns True if you had the file locked
        before the call. 
```

### `gdecorators`

OK, there is only one decorator, but it is a nicely implemented 
