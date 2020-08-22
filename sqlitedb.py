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

try:
    import pandas
    have_pandas = True
except ImportError as e:
    have_pandas = False


from   tombstone import tombstone
from   gdecorators import trap

class SQLiteDB:
    """
    Basic functions for manipulating all sqlite3 databases. 
    If you are building a database, the DDL should be in a global object
    with the name `schema`. This will be used only if the named database
    is not found, or the `force_new_db` parameter to `__init__` is
    True. 
    """

    __slots__ = ( 'stmt', 'OK', 'db', 'cursor', 
        'timeout', 'isolation_level', 'name', 'use_pandas' )
    __values__ = ( '', False, None, None,
        15, 'EXCLUSIVE', '', True)
    __defaults__ = dict(zip(
        __slots__, __values__
        ))

    def __init__(self, path_to_db:str, **kwargs):
        """
        Does what it says. Opens the database if present.
        """
        global have_pandas
        # Set the defaults.
        for k, v in SQLiteDB.__defaults__.items():
            setattr(self, k, v)

        # Make sure it is there.
        self.name = path_to_db if os.path.isfile(path_to_db) else None
        if not self.name:
            tombstone(f"No database named {self.name} found.")
            return

        # Give it a tune up if needed.
        for k, v in kwargs.items(): 
            if k in SQLiteDB.__slots__:
                setattr(self, k, v)

        error_on_init = True
        try:
            self.db = sqlite3.connect(self.name, 
                timeout=self.timeout, isolation_level=self.isolation_level)
            self.cursor = self.db.cursor()
            self.keys_on()
            error_on_init = False

        except sqlite3.OperationalError as e:
            tombstone(str(e))
            
        finally:
            self.use_pandas = have_pandas and self.use_pandas
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

        if not self.db: raise Exception('Not connected!')
        return self.db


    def keys_off(self) -> None:
        self.cursor.execute('pragma foreign_keys = 0')
        self.cursor.execute('pragma synchronous = OFF')


    def keys_on(self) -> None:
        self.cursor.execute('pragma foreign_keys = 1')
        self.cursor.execute('pragma synchronous = FULL')


    @trap
    def commit(self) -> bool:
        """
        Expose this function so that it can be called without having
        to put the dot-notation in the calling code.
        """
        try:
            self.db.commit()
            return True
        except:
            return False


    @trap
    def execute_SQL(self, SQL:str, *args) -> object:
        """
        Wrapper that automagically returns rowsets for SELECTs and 
        number of rows affected for other DML statements.
        
        is_select        -- if we think it is a SELECT statement.
        has_args         -- to avoid the problem with the None-tuple.
        self.use_pandas  -- iff True, return a DataFrame on SELECT statements.

        """        
        is_select = SQL.strip().lower().startswith('select')
        has_args = not not args

        if self.use_pandas and is_select:
            return pandas.read_sql_query(SQL, self.db, *args)
        
        if has_args:
            rval = self.cursor.execute(SQL, args)
        else:
            rval = self.cursor.execute(SQL)

        if is_select: return rval.fetchall()
        self.db.commit()
        return rval



    def row_one(self, SQL:str, parameters:Union[tuple, None]=None) -> dict:
        """
        Return only the first row of the results. When returned,
        it will not be a list with one row, but just the row 
        itself. If the column is provided, then only that column
        is returned as an atomic datum.
        """
       
        results = self.execute_SQL(SQL, parameters)
        return None if not results else results[0]
