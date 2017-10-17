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
                    local_DDL:list = []):
        """
        Does what it says. Opens the database if present, and
        creates the database if it is MIA.

        path_to_db -- name of the database file. This name may contain environment
            variables, as well as the Linux/UNIX shortcut names, including 
            relative paths.

        force_new_db -- will attempt to remove anything at `path_to_db`

        local_DDL -- if present, this parameter can provide additional DDL
            statements to be executed after schema statements.
        """
        stmt = ""
        self.OK = None
        self.db = None
        self.cursor = None

        global schema

        self.name = db_file = fname.Fname(path_to_db)
        gkf.tombstone("Database name is " + str(db_file))
        results = [1]

        if force_new_db:
            try:
                gkf.tombstone("Attempting to remove old database.")
                os.remove(str(db_file))
            except OSError as e:
                # no harm in deleting a file that does not exist.
                gkf.tombstone("Nothing to remove")
            else:
                gkf.tombstone("Removed.")

        if db_file:
            gkf.tombstone("Attempting to open existing database " + str(db_file))
            self.db = sqlite3.connect(str(db_file), timeout=30, isolation_level='DEFERRED')
            self.cursor = self.db.cursor()
            gkf.tombstone("Database opened: " + str(fname.Fname(db_file)))
            return

        try:
            gkf.tombstone("Attempting to create database in " + str(db_file))
            self.db = sqlite3.connect(str(db_file), timeout=30, isolation_level='DEFERRED')
            gkf.tombstone("New database created: " + str(db_file))

            results = [0]
            results.extend([ self.db.execute(stmt) for stmt in gkf.listify(schema) ])

        except sqlite3.OperationalError as e:
            gkf.tombstone(str(e))
            gkf.tombstone(stmt)
            exit(os.EX_CANTCREAT)

        else:
            self.cursor = self.db.cursor()
            gkf.tombstone('cursor created.')
            results.extend([ self.db.execute(stmt) for stmt in gkf.listify(local_DDL) ])
            self.keys_on()
            gkf.tombstone('foreign keys are on')

        finally:
            self.OK = sum(results) == 0


    def __str__(self) -> str:
        """ For simplicity """

        return self.name


    def __bool__(self) -> bool:
        """
        We consider everything "OK" if the object is attached to an open 
        database, and the last operation went well.
        """

        return self.db is not None and self.OK is True


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

