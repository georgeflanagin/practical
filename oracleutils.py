# -*- coding: utf-8 -*-
""" Oracle helpers. """

# Added for Python 3.5+
import typing
from typing import *

# Credits
__author__ = 'George Flanagin'
__copyright__ = 'Copyright 2020, University of Richmond'
__credits__ = None
__version__ = '0.1'
__maintainer__ = 'George Flanagin'
__email__ = 'me@georgeflanagin.com'
__status__ = 'Prototype'
__license__ = 'MIT'

###
# D
###

def datetime_encoder(obj:Any) -> str:
    """
    If Oracle DATETIME objects come back to the program via cx_Oracle,
    they are a non-serializable type. This class is a hook that 
    spots them, and returns the YYYY-MM-DD part of the ISO 8601 
    formatted string.

    If the argument is /not/ a DATETIME type, then we pass it along
    to the bog standard encoder.
    """
    try:
        return obj.isoformat()[:10]
    except:
        return obj


###
# E
###

def empty_to_null_literal(s:str) -> str:
    """ For creating database statements with a literal NULL

    s -- string to assess
    returns: -- s or 'NULL'
    """

    return (str(s) if (not isinstance(s, str) or len(s) > 0) else 'NULL')


####
# M
####

def make_IN_clause(a:Union[List,str]) -> str:
    """ Changes the argument, often a list, into an 'IN (e, e, e)' clause

    a -- a value, or a list of more than one value. The type of a is
        irrelevant.
    returns: -- An SQL fragment suitable for inclusion in an SQL statement.
    """

    if not isinstance(a, list): a = [a]
    return " IN (" + (",".join([q(_) for _ in a])) + ") "


###
# Q
###

Q1="'"
Q2='"'
Q3="`"
BACKSLASH = "\\"

def q0(ins:str, esc=None) -> str:
    """
    Do nothing.
    """
    return ins

def q1(ins:str, esc=None) -> str:
    """
    ANSI SQL 99 single quoting. No escaping.
    """
    return Q1 + re.sub(Q1,  Q1+Q1, ins) + Q1


def q2(ins:str, esc:str=BACKSLASH) -> str:
    """
    Ordinary double quotes, escaped within.
    """
    return Q2 + ins.replace(Q2, esc+Q2) + Q2


def q3(ins:str, esc:str=BACKSLASH) -> str:
    """
    Back tick quoting (think bash evaluations)
    """
    return Q3 + ins.replace(Q3, esc+Q3) + Q3


def q4(ins:str, esc=None) -> str:
    """
    Microsoft PowerShell quoting. It is rather Byzantine,
    and there is no escaping.
    """
    return NotImplemented


def q5(ins:str, esc:str=BACKSLASH) -> str:
    """
    Ordinary single quotes, escaped.
    """
    return Q1 + ins.replace(Q1, esc+Q1) + Q1


quote_strategies = [ q0, q1, q2, q3, q4, q5 ]

def q_(s:str, strategy:int=1, esc:str=BACKSLASH) -> str:
    try:
        return quote_strategies[strategy](s, esc)
    except:
        message = 'unknown quote strategy {} for string (({}))'.format(strategy, s)
        raise Exception(message)


def q(ins:str, quoteType:int=1) -> str:
    """A general purpose string quoter and Houdini (mainly for SQL)

    ins -- an input string
    quote_type -- an integer between 0 and 5. Meanings:
        0 : do nothing
        1 : ordinary single quotes.
        2 : ordinary double quotes.
        3 : Linux/UNIX backquotes.
        4 : PowerShell escape and quoting.
        5 : SQL99 escaping only.
    returns: -- some version of 's'.
    """

    quote = "'"
    if quoteType == 1:
        return quote + ins.replace("'", "''") + quote
    elif quoteType == 2:
        quote = '"'
        return quote + ins.replace('"', '\\"') + quote
    elif quoteType == 3:
        quote = '`'
        return quote + ins + quote
    elif quoteType == 4: # Powershell
        ins = re.sub('^', '^^', ins)
        ins = re.sub('&', '^&', ins)
        ins = re.sub('>', '^>', ins)
        ins = re.sub('<', '^<', ins)
        ins = re.sub('|', '^|', ins)
        ins = re.sub("'", "''", ins)
        return quote + ins + quote
    elif quoteType == 5: # SQL 99 .. quotes only.
        return quote + re.sub("'",  "''", ins) + quote
    else:
        pass
    return ins


def q64(s:str, quote_type:int=1) -> bytes:
    """ Convert to Base64 before quoting.

    s -- a string to convert to Base64.
    returns: -- same thing as q()
    """
    return b"'" + encodebytes(s.encode('utf-8')) + b"'"


def q_like(s:str) -> str:
    """ Prepend and append a %

    s -- a string
    returns: -- %s%
    """
    return q("%" + s + "%")


def q_like_pre(s:str) -> str:
    """ append a %

    s -- a string
    returns: -- s%
    """

    return q("%" + s)


def q_like_post(s:str) -> str:
    """ Append a %

    s -- a string
    returns: -- s%
    """

    return q(s + "%")


