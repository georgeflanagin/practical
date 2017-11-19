#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
    This is a base class for manipulating all sqlite databases.
"""


#pragma pylint=off
    
# Credits
__author__ =        'George Flanagin'
__copyright__ =     'Copyright 2017 George Flanagin'
__credits__ =       'None. This idea has been around forever.'
__version__ =       '1.0'
__maintainer__ =    'George Flanagin'
__email__ =         'me+git@georgeflanagin.com'
__status__ =        'continual development.'
__license__ =       'MIT'

import typing
from   typing import *

import collections
import csv
from   functools import reduce
import operator
import os
import sqlite3
import sys
import time

from os import walk, remove, stat
 
import gkflib as gkf
import fname

import sqlite3

class SQLiteDB:
    """
    Basic functions for manipulating all sqlite3 databases. 

    If you are building a database, the DDL should be in a global object
    with the name `schema`. This will be used only if the named database
    is not found, or the `force_new_db` parameter to `__init__` is
    True. 
    """
    def __init__(self, path_to_db:str, 
                    force_new_db:bool = False, 
                    local_DDL:list = [],
                    schema:list = []):
        """
        Does what it says. Opens the database if present, and
        creates the database if it is MIA.

        path_to_db -- name of the database file. This name may contain environment
            variables, as well as the Linux/UNIX shortcut names, including 
            relative paths.

        force_new_db -- will attempt to remove anything at `path_to_db`

        local_DDL -- if present, this parameter can provide additional DDL
            statements to be executed after schema statements.

        schema -- DLL statements to build the database anew.
        """
        stmt = ""
        self.OK = None
        self.db = None
        self.cursor = None

        db_file = fname.Fname(path_to_db)
        self.name = str(db_file)
        gkf.tombstone("Database name is {}".format(self.name))

        error_on_init = False
        if force_new_db and db_file:
            try:
                gkf.tombstone("Attempting to remove old database.")
                os.remove(self.name)

            except OSError as e:
                # no harm in deleting a file that does not exist.
                gkf.tombstone("Unable to remove old database.")

            else:
                gkf.tombstone("Removed.")

        if db_file:
            gkf.tombstone("Attempting to open existing database {}".format(self.name))
            self.db = sqlite3.connect(self.name, timeout=30, isolation_level='DEFERRED')
            self.cursor = self.db.cursor()
            gkf.tombstone("Database opened: {}".format(self.name))

            try:
                a = [ self.db.execute(stmt) for stmt in gkf.listify(local_DDL) ]
            except sqlite3.OperationalError as e:
                gkf.tombstone(gkf.type_and_text(e))
                self.OK = False
            finally:
                return 

        try:
            gkf.tombstone("Attempting to create database in {}".format(self.name))
            self.db = sqlite3.connect(self.name, timeout=30, isolation_level='DEFERRED')
            gkf.tombstone("New database created.")

            try:
                gkf.tombstone("Executing DDL statements in schema")
                a = [ self.db.execute(stmt) for stmt in gkf.listify(schema) ]
            except sqlite3.OperationalError as e:
                gkf.tombstone(gkf.type_and_text(e))
                error_on_init = True

        except sqlite3.OperationalError as e:
            gkf.tombstone(str(e))
            gkf.tombstone(stmt)
            exit(os.EX_CANTCREAT)

        else:
            self.cursor = self.db.cursor()
            gkf.tombstone('cursor created.')

            self.keys_on()
            gkf.tombstone('foreign keys are on')

        finally:
            self.OK = not error_on_init


    def __str__(self) -> str:
        """ For simplicity """

        return self.name


    def __bool__(self) -> bool:
        """
        We consider everything "OK" if the object is attached to an open 
        database, and the last operation went well.
        """

        return self.db is not None and self.OK is True


    def __call__(self) -> sqlite3.Cursor:
        """
        This is a bit of syntax sugar to get the cursor object
        out from inside the object. The purpose is to use it
        with the pandas library.
        """

        if not self.cursor: raise Exception('No active cursor!')
        return self.cursor


    def keys_off(self) -> None:
        self.cursor.execute('pragma foreign_keys = 0')
        self.cursor.execute('pragma synchronous = OFF')


    def keys_on(self) -> None:
        self.cursor.execute('pragma foreign_keys = 1')
        self.cursor.execute('pragma synchronous = FULL')


    def executeSQL(self, SQL:str) -> object:
        """
        Wrapper that automagically returns rowsets for SELECTs and 
        number of rows affected for other DML statements.
        """        
        try:
            if SQL.strip().lower().startswith('select'):
                rval = self.cursor.execute(SQL).fetchall()
            else:
                rval = self.cursor.execute(SQL)
            self.OK = True

        except Exception as e:
            gkf.tombstone(gkf.type_and_text(e))
            self.OK = False

        finally:
            return rval

